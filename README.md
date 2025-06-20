# Health Monitoring System

docker-compose up -d --build #run the project

This is a Django-based intelligent health monitoring platform for real-time monitoring of user health data, providing alerts and data analysis functions. The system is suitable for families and medical institutions that need to remotely monitor the health status of the elderly or patients.

## Features Overview

- **Real-time Health Monitoring**: 24/7 continuous monitoring of vital signs, including heart rate, blood pressure, and temperature
- **Intelligent Alert System**: Automatic alerts for abnormal data, supporting multiple notification methods
- **Data Analysis**: Professional health data analysis, generating intuitive reports to help understand health trends
- **User Management**: Support for multi-user systems, allowing creation of separate accounts for family members
- **Device Management**: Support for connecting and managing multiple devices
- **Security Assurance**: Strict data encryption and privacy protection measures

## Project Structure

```
GSsite/
├── GSsite/                  # Main project configuration directory
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing configuration
│   ├── wsgi.py              # WSGI configuration
│   ├── asgi.py              # ASGI configuration
│   └── celery_app.py        # Celery configuration
├── health_monitor/          # Health monitoring application
│   ├── models.py            # Data model definitions
│   ├── views.py             # View functions
│   ├── urls.py              # URL mappings
│   ├── api_urls.py          # API endpoint mappings
│   ├── forms.py             # Form definitions
│   ├── tasks.py             # Celery tasks
│   ├── consumers.py         # WebSocket consumers
│   └── templates/           # HTML templates
├── static/                  # Static files
│   ├── css/                 # CSS style files
│   ├── js/                  # JavaScript files
│   └── src/                 # Images and other resources
├── templates/               # Global templates
├── media/                   # User-uploaded files
├── staticfiles/             # Collected static files
├── logs/                    # Log files
├── docker-compose.yml       # Docker orchestration configuration
├── Dockerfile               # Docker build file
├── requirements.txt         # Python dependencies
├── entrypoint.sh            # Docker entry script
└── nginx.conf               # Nginx configuration
```

## Core Technology Stack

- **Backend**: Django, Django REST Framework, Celery
- **Database**: SQLite (development), PostgreSQL (production)
- **Cache**: Redis
- **Frontend**: Bootstrap, jQuery, Chart.js
- **Message Queue**: Redis
- **Containerization**: Docker, Docker Compose
- **Server**: Nginx, Gunicorn

## Getting Started

### Production Environment

Use Docker Compose for quick deployment:

```bash
docker-compose up -d
```

This will start the following services:
- Django application (Gunicorn)
- PostgreSQL database
- Redis (cache and message queue)
- Nginx (reverse proxy)
- Celery worker and beat

## Implementation Details

### 1. Content Management

#### Admin Backend Interface for Core Application Content
The project utilizes Django Admin to provide a powerful backend management interface, allowing administrators to directly manipulate data models. The main models in the system include:

- `User`: Inherits from Django's built-in user model, used for user authentication and permission management
- `UserProfile`: Extends user information, including gender, phone number, and ID number
- `UserSettings`: Stores user personalization settings, such as notification preferences and health thresholds
- `Device`: Manages health monitoring devices bound to users
- `HealthData`: Records health data, such as heart rate, blood pressure, etc.
- `HealthAlert`: Stores alerts generated based on health data

Administrators can directly access these models through the Django Admin interface to perform CRUD operations. The URL is `/admin/`.

#### CRUD Operations on Business-Related Models
In addition to Django Admin, the system also implements custom view functions and API endpoints, allowing the frontend interface to operate on various models:

- Device Management: Add, edit, delete devices (`add_device`, `edit_device`, `delete_device`)
- User Profile: Update user personal information (`update_profile`)
- Health Data: Upload and query health data via API (`add_heart_rate_data`, `get_heart_rate_data`)
- Alert Handling: View and process alerts (`alerts`, `alert_detail`)

These operations are implemented through Django view functions or DRF API, with appropriate permission controls to ensure users can only access their own data.

### 2. Security

#### Protection Against XSS, CSRF, and SQL Injection Attacks
The system implements multi-layered security measures:

- **XSS Protection**: 
  - Using Django template system's automatic escaping feature
  - Applying `Content-Security-Policy` headers
  - Validating and sanitizing user input

- **CSRF Protection**: 
  - Enabling Django's CSRF middleware
  - Including CSRF tokens in all forms
  - Requiring correct CSRF headers for API calls

- **SQL Injection Protection**:
  - Using Django ORM's parameterized queries
  - Avoiding direct SQL statement concatenation
  - Implementing data access layer abstraction

#### Using .env and .gitignore to Hide Sensitive Environment Variables
The project uses environment variables to manage sensitive information:

- Using the `python-environ` library to load configurations from `.env` files
- Ensuring `.env` files are not committed to version control systems via `.gitignore`
- Sensitive information includes: database credentials, keys, API tokens, etc.
- Using Docker secrets or environment variable injection in production environments

### 3. Testing

#### Backend Unit Tests (Models, Views, Serializers, etc.)
The project includes comprehensive unit tests to ensure the normal functioning of various components:

- **Model Tests**: Verify fields, methods, constraints, and signal handlers of data models
- **View Tests**: Test view function responses, permission controls, and exception handling
- **Serializer Tests**: Ensure the accuracy of data serialization and deserialization
- **Form Tests**: Verify form validation and handling logic

Tests can be run using the following command:
```bash
python manage.py test
```

#### Integration or End-to-End Testing Using Django Test Client or Selenium/Cypress
The project also implements higher-level tests:

- **Integration Tests**: Using Django test client to simulate HTTP request-response cycles
- **End-to-End Tests**: Using Selenium to test real user interaction scenarios
- **API Tests**: Verifying the functionality and security of API endpoints

#### Frontend Testing
Frontend JavaScript code is tested through:

- **Unit Tests**: Testing independent JavaScript functions and components
- **Interaction Tests**: Verifying user interface interactions and event handling
- **Responsive Design Tests**: Ensuring the interface displays normally on various devices

### 4. Containerization

#### Containerizing Frontend and Backend
The project uses Docker containerization to achieve environment consistency and simplify deployment:

- Using `Dockerfile` to define the application container build process
- Including all necessary dependencies and configurations
- Multi-stage builds to optimize image size and security

#### Using Docker Compose to Orchestrate Services (Frontend, Backend, Database, Redis)
The project uses Docker Compose to orchestrate multi-container applications:

```yaml
services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - ./.env
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: gunicorn GSsite.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    env_file:
      - ./.env
  
  nginx:
    image: nginx:1.23
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/home/app/staticfiles
      - media_volume:/home/app/media
    depends_on:
      - web
  
  celery_worker:
    build: .
    command: celery -A GSsite worker -l info
    depends_on:
      - redis
      - web
    env_file:
      - ./.env

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### Using Production-Level Web Servers/Proxies Like Nginx
Nginx serves as a reverse proxy and static file server:

- Handling static file requests to improve performance
- Providing SSL termination and security headers
- Load balancing and request limiting
- Caching static content to reduce the burden on application servers

#### Separating .env Configurations for Development and Production Environments
The project supports configuration management for different environments:

- Development environment uses local `.env.dev` file
- Production environment uses `.env.prod` file or environment variable injection
- Configuration separation ensures security and environment-specific settings

### 5. Logging

#### Implementing Structured Logging in the Backend
The system implements a comprehensive logging strategy:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR.parent / 'logs' / 'app.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

Logs record key events such as:
- User authentication and authorization
- Data access and modification
- System errors and exceptions
- Performance monitoring metrics

#### Logging to Files or Standard Output
The logging configuration supports multiple output targets:
- Console output for real-time feedback in development environments
- File output for persistent recording of system behavior
- JSON formatting for advanced log analysis

#### Appropriate Use of Log Levels (INFO, DEBUG, WARNING, ERROR)
The system uses appropriate log levels for different information:
- **ERROR**: System errors, exceptions, and failed operations
- **WARNING**: Potential problems or exceptional situations that need attention
- **INFO**: Regular operations and status changes
- **DEBUG**: Detailed debugging information, enabled only in development environments

### 6. Caching

#### Using Redis (or Similar Tools) to Cache Page Queries or Frequently Accessed Data
The system uses Redis to implement a multi-layered caching strategy:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

Main caching scenarios:
- User session management
- Frequently accessed health data
- Dashboard views and statistics
- API response caching

The system implements custom caching logic, for example:
```python
def save(self, *args, **kwargs):
    """Override save method to update cache"""
    super().save(*args, **kwargs)
    # Update the latest data cache
    cache_key = f"latest_health_data_{self.device_id}"
    cache.set(cache_key, self, timeout=300)  # Cache for 5 minutes
```

#### Caching Strategy in README.md
The caching strategies implemented by the system include:

1. **Data Layer Caching**:
   - Hot data caching (such as user profiles, device information)
   - Query result caching
   - Object instance caching

2. **Session Management**:
   - Using Redis to store session data
   - Supporting distributed session management

3. **Cache Invalidation Strategy**:
   - Time-based expiration (TTL)
   - Event-based cache invalidation
   - Cache warming mechanism

4. **API Caching**:
   - Caching frequently accessed API responses
   - Cache variations based on users and parameters

### 7. Documentation and Code Quality

#### Providing a Clear, Structured README.md
This document provides a comprehensive overview of the project, including:
- Project description and features
- Installation and configuration guide
- Technology stack and architecture description
- Core functionalities and implementation methods
- Development and deployment processes

#### Project Description, Development and Production Environment Setup, Testing
The README.md describes in detail:
- **Project Description**: Clearly describes the purpose, functionality, and value of the system
- **Environment Setup**:
  - Development environment configuration steps
  - Production environment deployment guide
  - Environment variable and configuration management
- **Testing Guide**:
  - Commands and processes for running tests
  - Test coverage description
  - Test data preparation

## API Documentation

The system provides RESTful API interfaces, mainly including:

- `/api/devices/`: Device management
- `/api/health-data/{device_id}/`: Health data read/write
- `/api/alerts/`: Alert management
- `/api/user/profile/`: User profile management

Detailed API documentation can be accessed via `/api/docs/` after the system is running.

## Project Dependencies

Main module dependencies of the system:

1. **User Authentication and Authorization**:
   - Django Auth → UserProfile → UserSettings

2. **Device and Data Management**:
   - User → Device → HealthData → HealthAlert

3. **Background Task Processing**:
   - Celery → Redis → Django ORM

4. **Frontend Interaction**:
   - Web Interface → Django Views → Django ORM → Database

5. **API Call Flow**:
   - Client Request → DRF API Views → Serializers → Models → Database

## Contributing

Contributions of code, issue reports, or improvement suggestions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Submit a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
