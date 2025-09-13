# E-Commerce Application Deployment Guide

This guide provides comprehensive instructions for deploying the e-commerce application using various DevOps practices and platforms.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git
- PostgreSQL (for production)
- Redis (for production)

## 🐳 Docker Deployment

### Local Development with Docker

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd devops-assign
   ```

2. **Start the application**
   ```bash
   # Start all services (development mode)
   docker-compose up --build
   
   # Start in background
   docker-compose up -d --build
   ```

3. **Access the application**
   - Web Application: http://localhost:8000
   - Admin Interface: http://localhost:8000/admin
   - Health Check: http://localhost:8000/health/
   - API Endpoints: http://localhost:8000/api/

4. **View logs**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f web
   ```

### Production Deployment with Docker

1. **Build production image**
   ```bash
   docker build --target production -t ecommerce:latest .
   ```

2. **Run production container**
   ```bash
   docker run -d \
     --name ecommerce-prod \
     -p 8000:8000 \
     -e DEBUG=False \
     -e SECRET_KEY=your-secret-key \
     -e DATABASE_URL=postgresql://user:pass@host:5432/db \
     ecommerce:latest
   ```

3. **Using Docker Compose (Production)**
   ```bash
   # Start production services
   docker-compose --profile production up -d
   
   # Start with monitoring
   docker-compose --profile production --profile monitoring up -d
   ```

## 🌐 Free Hosting Deployment

### Option 1: Render.com

1. **Create Render account**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub repository

2. **Create Web Service**
   - **Name**: ecommerce-app
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn ecommerce.wsgi:application`
   - **Environment Variables**:
     ```
     DEBUG=False
     SECRET_KEY=your-secret-key
     DATABASE_URL=postgresql://user:pass@host:5432/db
     ALLOWED_HOSTS=your-app.onrender.com
     ```

3. **Create PostgreSQL Database**
   - Add PostgreSQL service
   - Copy connection string to `DATABASE_URL`

4. **Deploy**
   - Render will automatically deploy on every push to main branch
   - Access your app at the provided URL

### Option 2: Railway

1. **Create Railway account**
   - Sign up at [railway.app](https://railway.app)
   - Connect your GitHub repository

2. **Deploy application**
   - Railway will auto-detect Django project
   - Add PostgreSQL plugin
   - Set environment variables

3. **Configure domain**
   - Railway provides custom domain
   - Can connect custom domain

### Option 3: PythonAnywhere

1. **Create PythonAnywhere account**
   - Sign up at [pythonanywhere.com](https://pythonanywhere.com)

2. **Upload code**
   ```bash
   git clone <your-repo-url>
   cd your-project
   ```

3. **Create virtual environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 ecommerce
   pip install -r requirements.txt
   ```

4. **Configure WSGI file**
   - Edit `/var/www/username_pythonanywhere_com_wsgi.py`
   - Point to your Django application

5. **Set up static files**
   ```bash
   python manage.py collectstatic
   ```

## 🔄 CI/CD Pipeline Deployment

### GitHub Actions Setup

1. **Repository Secrets**
   Add these secrets in your GitHub repository:
   ```
   RENDER_API_KEY=your-render-api-key
   RENDER_STAGING_SERVICE_ID=your-staging-service-id
   RENDER_PRODUCTION_SERVICE_ID=your-production-service-id
   SLACK_WEBHOOK_URL=your-slack-webhook-url
   ```

2. **Environment Protection**
   - Go to Settings > Environments
   - Create `staging` and `production` environments
   - Add required reviewers for production

3. **Automatic Deployment**
   - Push to `develop` branch → Deploy to staging
   - Push to `main` branch → Deploy to production
   - Create release → Deploy to production

### Pipeline Stages

1. **Code Quality**
   - Black formatting check
   - Flake8 linting
   - MyPy type checking
   - Security scanning (Bandit, Safety)

2. **Testing**
   - Unit tests with coverage
   - Multiple Python versions
   - Database migrations

3. **Security**
   - Trivy vulnerability scanning
   - OWASP dependency check
   - Container image scanning

4. **Building**
   - Multi-platform Docker images
   - GitHub Container Registry
   - Image vulnerability scanning

5. **Deployment**
   - Staging environment
   - Production environment
   - Health checks
   - Smoke tests

6. **Monitoring**
   - Performance testing
   - Monitoring setup
   - Slack notifications

## 📊 Monitoring & Observability

### Health Checks

1. **Application Health**
   - Endpoint: `/health/`
   - Checks: Database, cache, storage, disk usage

2. **API Health**
   - Endpoint: `/api/health/`
   - JSON response with system status

### Prometheus Metrics

1. **Enable Prometheus**
   ```bash
   # Start monitoring services
   docker-compose --profile monitoring up -d
   ```

2. **Access Metrics**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin123)

### Logging

1. **Structured Logging**
   - JSON format in production
   - File and console output
   - Log rotation

2. **ELK Stack**
   ```bash
   # Start ELK stack
   docker-compose --profile monitoring up -d
   ```
   - Elasticsearch: http://localhost:9200
   - Kibana: http://localhost:5601

## 🔒 Security Configuration

### Environment Variables

1. **Development (.env)**
   ```env
   DEBUG=True
   SECRET_KEY=dev-secret-key
   DATABASE_URL=sqlite:///db.sqlite3
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

2. **Production**
   ```env
   DEBUG=False
   SECRET_KEY=your-secure-secret-key
   DATABASE_URL=postgresql://user:pass@host:5432/db
   ALLOWED_HOSTS=your-domain.com
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

### Security Headers

1. **HTTPS Configuration**
   ```nginx
   # Nginx configuration
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   add_header X-Frame-Options "DENY" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-XSS-Protection "1; mode=block" always;
   ```

2. **CORS Configuration**
   ```python
   CORS_ALLOWED_ORIGINS = [
       "https://your-domain.com",
       "https://www.your-domain.com"
   ]
   ```

## 📈 Performance Optimization

### Caching Strategy

1. **Redis Configuration**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
           'OPTIONS': {
               'CLIENT_CLASS': 'django_redis.client.DefaultClient',
           }
       }
   }
   ```

2. **View Caching**
   ```python
   from django.views.decorators.cache import cache_page
   
   @cache_page(60 * 15)  # Cache for 15 minutes
   def product_list(request):
       # Your view logic
   ```

### Database Optimization

1. **Indexes**
   ```python
   class Meta:
       indexes = [
           models.Index(fields=['name']),
           models.Index(fields=['category']),
           models.Index(fields=['is_active']),
       ]
   ```

2. **Query Optimization**
   ```python
   # Use select_related and prefetch_related
   products = Product.objects.select_related('category').prefetch_related('tags')
   ```

## 🧪 Testing Strategy

### Running Tests

1. **Unit Tests**
   ```bash
   # Run all tests
   python manage.py test
   
   # Run specific app tests
   python manage.py test store
   
   # Run with coverage
   coverage run --source='.' manage.py test
   coverage report
   ```

2. **Performance Tests**
   ```bash
   # Install Locust
   pip install locust
   
   # Run performance tests
   locust -f tests/performance/locustfile.py --host=http://localhost:8000
   ```

### Test Configuration

1. **Test Settings**
   ```python
   # settings_test.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': ':memory:',
       }
   }
   ```

2. **Test Data**
   ```python
   # Use factories for test data
   from factory.django import DjangoModelFactory
   
   class ProductFactory(DjangoModelFactory):
       class Meta:
           model = Product
   ```

## 🔧 Maintenance & Updates

### Database Migrations

1. **Create Migrations**
   ```bash
   python manage.py makemigrations
   ```

2. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Rollback Migrations**
   ```bash
   python manage.py migrate store 0001
   ```

### Backup Strategy

1. **Database Backup**
   ```bash
   # PostgreSQL
   pg_dump -h localhost -U username -d database > backup.sql
   
   # SQLite
   cp db.sqlite3 backup.sqlite3
   ```

2. **Media Files Backup**
   ```bash
   tar -czf media_backup.tar.gz media/
   ```

### Update Process

1. **Code Updates**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

2. **Docker Updates**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection**
   ```bash
   # Check database status
   python manage.py dbshell
   
   # Test connection
   python manage.py check --database default
   ```

2. **Static Files**
   ```bash
   # Collect static files
   python manage.py collectstatic --noinput
   
   # Check static files location
   python manage.py findstatic admin/css/base.css
   ```

3. **Permissions**
   ```bash
   # Fix file permissions
   sudo chown -R www-data:www-data /path/to/your/app
   sudo chmod -R 755 /path/to/your/app
   ```

### Log Analysis

1. **Application Logs**
   ```bash
   # View Django logs
   tail -f logs/django.log
   
   # View application logs
   docker-compose logs -f web
   ```

2. **System Logs**
   ```bash
   # System logs
   sudo journalctl -u your-service -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/access.log
   ```

## 📚 Additional Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Monitoring Tools
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [ELK Stack](https://www.elastic.co/)

### Deployment Platforms
- [Render](https://render.com/)
- [Railway](https://railway.app/)
- [PythonAnywhere](https://pythonanywhere.com/)

---

**Note**: This deployment guide covers the most common scenarios. Adjust configurations based on your specific requirements and infrastructure.
