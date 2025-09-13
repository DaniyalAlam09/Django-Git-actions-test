from datetime import datetime
from pathlib import Path
from typing import Any, List

from pydantic.dataclasses import dataclass
from typing_extensions import Self

from ..report.schemas.v3_0 import main as v3_0
from .base import AuthenticationType, ReportSchemaVersion, SafetyBaseModel, ScanType, Stage
from .telemetry import TelemetryModel


@dataclass
class MetadataModel(SafetyBaseModel):
    """
    Main data about the report, used for traceability purposes.
    """

    scan_type: ScanType
    stage: Stage
    scan_locations: List[Path]
    authenticated: bool
    authentication_type: AuthenticationType
    telemetry: TelemetryModel
    schema_version: ReportSchemaVersion
    timestamp: datetime = datetime.now()

    def as_v30(self, *args: Any, **kwargs: Any) -> v3_0.SchemaModelV30:
        auth_method = None

        if self.authentication_type is AuthenticationType.API_KEY:
            auth_method = v3_0.AuthenticationMethod.api_key
        elif self.authentication_type is AuthenticationType.TOKEN:
            auth_method = v3_0.AuthenticationMethod.token

        return v3_0.Meta(
            scan_type=v3_0.ScanType(self.scan_type.value),
            stage=v3_0.StageType(self.stage.value),
            scan_locations=[str(location) for location in self.scan_locations],
            authenticated=self.authenticated,
            authentication_method=auth_method,
            timestamp=self.timestamp,
            telemetry=self.telemetry.as_v30(),
            schema_version=self.schema_version.value,
        )

    @classmethod
    def from_v30(cls, obj: v3_0.SchemaModelV30) -> 'MetadataModel':

        if not isinstance(obj, v3_0.Meta):
            raise TypeError('Expected instance of v3_0.Meta')

        return MetadataModel(
            scan_type=ScanType(obj.scan_type.value),
            stage=Stage(obj.stage.value),
            scan_locations=[Path(location) for location in obj.scan_locations],
            authenticated=obj.authenticated,
            authentication_type=AuthenticationType(obj.authentication_method),
            telemetry=TelemetryModel.from_v30(obj.telemetry),
            schema_version=ReportSchemaVersion(obj.schema_version),
            timestamp=obj.timestamp,
        )
