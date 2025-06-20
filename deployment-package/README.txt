# Health Monitoring System Deployment Package

This deployment package contains all the necessary files for the Health Monitoring System and helps you deploy the system quickly.

## Package Contents

1. Docker image files:
   - `gsdjproject-celery.tar`: Celery Worker service
   - `gsdjproject-web.tar`: Django Web application service
   - `gsdjproject-celery-beat.tar`: Celery Beat service
   - `postgres.tar`: PostgreSQL database service
   - `nginx.tar`: Nginx web server

2. Configuration files:
   - `docker-compose.yml`: Docker Compose configuration file
   - `.env.example`: Example environment variable file
   - `nginx.conf`: Nginx configuration file

3. Documentation:
   - `README.md`: Detailed project description
   - `DEPLOYMENT.md`: Detailed deployment guide
   - `DEPLOYMENT_PACKAGE.md`: Deployment package preparation guide

## Quick Deployment Steps

1. Load Docker images:
   ```bash
   docker load -i gsdjproject-celery.tar
   docker load -i gsdjproject-web.tar
   docker load -i gsdjproject-celery-beat.tar
   docker load -i postgres.tar
   docker load -i nginx.tar
   ```

2. Create the environment variable file:
   ```bash
   cp .env.example .env
   # Edit the .env file and set your environment variables
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the system:
   - Website: http://localhost
   - Admin panel: http://localhost/admin

