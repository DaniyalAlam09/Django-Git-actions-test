import importlib
import json
from dataclasses import asdict, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from .util import dict_dump

from ..config.schemas.v3_0 import main as v3_0
from .base import (
    EPSSExploitabilityLabels,
    IgnoredItemDetail,
    IgnoredItems,
    PolicyConfigSchemaVersion,
    SafetyBaseModel,
    SafetyConfigBaseModel,
    VulnerabilitySeverityLabels,
    FileType
)
from .ecosystem import PythonEcosystemIgnoreConfigModel


@dataclass
class ScanConfigModel:
    max_depth: int = 6
    ignore: List[str] = field(default_factory=lambda: [])
    include_files: Dict[FileType, List[Path]] = field(default_factory=lambda: {})
    system_targets: List[str] = field(default_factory=lambda: [])

@dataclass
class FailConfig:
    enabled: bool = True
    cvss_severity: List[VulnerabilitySeverityLabels] = field(
        default_factory=lambda: [
            VulnerabilitySeverityLabels.CRITICAL,
            VulnerabilitySeverityLabels.HIGH,
            VulnerabilitySeverityLabels.MEDIUM,
        ]
    )
    exploitability: List[EPSSExploitabilityLabels] = field(
        default_factory=lambda: [
            EPSSExploitabilityLabels.CRITICAL,
            EPSSExploitabilityLabels.HIGH,
            EPSSExploitabilityLabels.MEDIUM,
        ]
    )


@dataclass
class SecurityUpdates:
    class UpdateLevel(Enum):
        MAJOR = "major"
        MINOR = "minor"
        PATCH = "patch"

    auto_security_updates_limit: List[UpdateLevel] = field(
        default_factory=lambda: [SecurityUpdates.UpdateLevel.PATCH]
    )


@dataclass
class DependencyVulnerabilityConfig:
    enabled: bool = True
    ignore_vulnerabilities: Optional[IgnoredItems] = None
    ignore_cvss_severity: List[VulnerabilitySeverityLabels] = field(
        default_factory=lambda: []
    )
    python_ignore: PythonEcosystemIgnoreConfigModel = field(
        default_factory=lambda: PythonEcosystemIgnoreConfigModel()
    )
    fail_on: FailConfig = field(default_factory=lambda: FailConfig())
    security_updates: SecurityUpdates = field(default_factory=lambda: SecurityUpdates())


@dataclass
class ConfigModel(SafetyConfigBaseModel):
    telemetry_enabled: bool = True
    scan: ScanConfigModel = field(default_factory=lambda: ScanConfigModel())
    depedendency_vulnerability: DependencyVulnerabilityConfig = field(
        default_factory=lambda: DependencyVulnerabilityConfig()
    )

    def as_v30(self, *args: Any, **kwargs: Any) -> v3_0.SchemaModelV30:
        include_files = []
        for file_type, paths in self.scan.include_files.items():
            include_files.extend(
                [v3_0.IncludeFile(
                    file_type=v3_0.AllowedFileType(file_type.value),
                    path=str(p))
                    for p in paths])

        scan_config = v3_0.ScanSettings(
            max_depth=self.scan.max_depth, exclude=list(self.scan.ignore),
            include_files=include_files,
            system=v3_0.System(targets=self.scan.system_targets)
        )
        ignored_data: Optional[IgnoredItems] = self.depedendency_vulnerability.ignore_vulnerabilities
        ignored_vulns = None

        if ignored_data:
            ignored_vulns = {
                id: v3_0.IgnoredVulnerability(reason=details.reason, 
                                              expires=details.expires, # type: ignore
                                              specifications=details.specifications) # type: ignore
                for id, details in ignored_data.items()
            }

        ignore_severities = [
            v3_0.CVSSSeverityLabels(label.value)
            for label in self.depedendency_vulnerability.ignore_cvss_severity
        ]

        python_config = v3_0.PythonEcosystemSettings(
            ignore_environment_results=self.depedendency_vulnerability.python_ignore.environment_results,
            ignore_unpinned_requirements=self.depedendency_vulnerability.python_ignore.unpinned_specifications,
        )

        auto_ignore = v3_0.AutoIgnoreInReportDependencyVulnerabilities(
            python=python_config,
            vulnerabilities=ignored_vulns,
            cvss_severity=ignore_severities,
        )

        report_on_config = v3_0.Report(
            dependency_vulnerabilities=v3_0.ReportDependencyVulnerabilities(
                enabled=self.depedendency_vulnerability.enabled, auto_ignore=auto_ignore
            )
        )

        update_limit = [
            v3_0.SecurityUpdatesLimits(label.value)
            for label in self.depedendency_vulnerability.security_updates.auto_security_updates_limit  # noqa: E501
        ]

        updates = v3_0.SecurityUpdatesSettings(
            dependency_vulnerabilities=v3_0.SecurityUpdatesDependencyVulnerabilities(
                auto_security_updates_limit=update_limit
            )
        )

        fail_on_severity = [
            v3_0.CVSSSeverityLabels(label.value)
            for label in self.depedendency_vulnerability.fail_on.cvss_severity
        ]

        fail_on_exploitability = [
            v3_0.EPSSExploitabilityLabels(label.value)
            for label in self.depedendency_vulnerability.fail_on.exploitability
        ]

        fail_scan = v3_0.FailScan(
            dependency_vulnerabilities=v3_0.FailScanDependencyVulnerabilities(
                enabled=self.depedendency_vulnerability.fail_on.enabled,
                fail_on_any_of=v3_0.FailOnAnyOf(
                    cvss_severity=fail_on_severity,
                    exploitability=fail_on_exploitability,
                ),
            )
        )

        return v3_0.Config(
            scan=scan_config,
            report=report_on_config,
            fail_scan=fail_scan,
            security_updates=updates,
        )

    @classmethod
    def from_v30(cls, obj: v3_0.SchemaModelV30) -> 'ConfigModel':

        if not isinstance(obj, v3_0.Config):
            raise TypeError('Expected instance of v3_0.Config')

        scan = ScanConfigModel()
        dep_vuln = DependencyVulnerabilityConfig()

        if obj.scan:
            if obj.scan.max_depth:
                scan.max_depth = obj.scan.max_depth

            if obj.scan.exclude:
                scan.ignore = obj.scan.exclude
            
            if obj.scan.include_files:
                for include_file in obj.scan.include_files:
                    file_type = FileType(include_file.file_type.value)

                    if file_type not in scan.include_files:
                        scan.include_files[file_type] = []

                    scan.include_files[file_type].append(Path(include_file.path))
            
            if obj.scan.system and obj.scan.system.targets:
                scan.system_targets = obj.scan.system.targets

        if obj.report and obj.report.dependency_vulnerabilities:
            if obj.report.dependency_vulnerabilities.enabled:
                dep_vuln.enabled = obj.report.dependency_vulnerabilities.enabled

            auto_ignore = obj.report.dependency_vulnerabilities.auto_ignore

            if auto_ignore:
                vulns_to_ignore = auto_ignore.vulnerabilities

                if vulns_to_ignore:
                    dep_vuln.ignore_vulnerabilities = IgnoredItems(
                        {
                            vuln_id: IgnoredItemDetail(**dict_dump(ignore_details))
                            for vuln_id, ignore_details in vulns_to_ignore.items()
                        }
                    )

                if auto_ignore.python:
                    kwargs = {}

                    if auto_ignore.python.ignore_unpinned_requirements is not None:
                        kwargs["unpinned_specifications"] = bool(
                            auto_ignore.python.ignore_unpinned_requirements
                        )

                    if auto_ignore.python.ignore_environment_results is not None:
                        kwargs["environment_results"] = bool(
                            auto_ignore.python.ignore_environment_results
                        )

                    dep_vuln.python_ignore = PythonEcosystemIgnoreConfigModel(**kwargs)

                if auto_ignore.cvss_severity:
                    dep_vuln.ignore_cvss_severity = [
                        VulnerabilitySeverityLabels(label.value)
                        for label in auto_ignore.cvss_severity
                    ]

        if obj.fail_scan and obj.fail_scan.dependency_vulnerabilities:
            fail_on = obj.fail_scan.dependency_vulnerabilities

            if fail_on.enabled is not None:
                dep_vuln.fail_on.enabled = bool(fail_on.enabled)

            if fail_on.fail_on_any_of:
                if fail_on.fail_on_any_of.cvss_severity:
                    dep_vuln.fail_on.cvss_severity = [
                        VulnerabilitySeverityLabels(label.value)
                        for label in fail_on.fail_on_any_of.cvss_severity
                    ]

                if fail_on.fail_on_any_of.exploitability:
                    dep_vuln.fail_on.exploitability = [
                        EPSSExploitabilityLabels(label.value)
                        for label in fail_on.fail_on_any_of.exploitability
                    ]

        if obj.security_updates and obj.security_updates.dependency_vulnerabilities:
            auto_security_limits = (
                obj.security_updates.dependency_vulnerabilities.auto_security_updates_limit
            )

            if auto_security_limits:
                dep_vuln.security_updates = SecurityUpdates(
                    [
                        SecurityUpdates.UpdateLevel(level.value)
                        for level in auto_security_limits
                    ]
                )

        return ConfigModel(scan=scan, depedendency_vulnerability=dep_vuln)

    @classmethod
    def parse_policy_file(
        cls,
        raw_report: Union[str, Path],
        schema: PolicyConfigSchemaVersion = PolicyConfigSchemaVersion.v3_0,
    ) -> 'ConfigModel':
        if isinstance(raw_report, Path):
            raw_report = raw_report.expanduser().resolve()
            with open(raw_report) as f:
                raw_report = f.read()

        try:
            from ruamel.yaml import YAML

            yaml = YAML(typ="safe", pure=True)
            yml_raw = yaml.load(raw_report)
        except Exception:
            raise ValueError("Broken YAML file.")

        parse = "parse_obj"
        target_schema = schema.value.replace(".", "_")
        module_name = (
            "safety_schemas." "config.schemas." f"v{target_schema}.main"
        )  # Example: Selecting v1_1

        module = importlib.import_module(module_name)
        config_model = module.Config

        # This will raise a validation error if the content is wrong
        validated_policy_file = getattr(config_model, parse)(yml_raw)

        # TODO: Select the from from the version passed
        return ConfigModel.from_v30(obj=validated_policy_file)

    def save_policy_file(self, dest: Path):
        POLICY_NAME = ".safety-policy.yml"

        dest = dest.expanduser().resolve()
        if dest.is_dir():
            dest = dest / POLICY_NAME
        policy_config = self.as_v30().json(by_alias=True, exclude_none=True)

        from ruamel.yaml.emitter import Emitter

        class MyEmitter(Emitter):
            def expect_block_mapping_key(self, first=False):
                if len(self.indents) == 1 and not first:
                    self.write_line_break()
                    self.write_line_break()
                super().expect_block_mapping_key(first)

        try:
            from ruamel.yaml import YAML

            yaml = YAML(typ="safe", pure=True)
            yaml.default_flow_style = False
            yaml.sort_base_mapping_type_on_output = False
            yaml.indent(mapping=2, sequence=4, offset=2)
            yaml.Emitter = MyEmitter

            with open(dest, "w") as f:
                yaml.dump(json.loads(policy_config), f)

        except Exception as e:
            raise ValueError(f"Unable to generate or save YAML, {e}")
