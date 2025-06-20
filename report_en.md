# Health Monitoring System – Technical Report

## 1. Introduction

### 1.1 Project Goal
Build a **real-time health monitoring platform** for families and medical institutions. The system continuously collects vitals (heart-rate, blood pressure, temperature, SpO₂) from multiple IoT devices, triggers alerts on anomalies, and visualises trends for remote caretaking.

### 1.2 Business Scenarios
1. **Home Care** – Relatives follow elderly or chronically-ill patients and receive instant notifications when metrics go abnormal.
2. **Hospital Tele-follow-up** – Medical staff supervises discharged patients in batches and adjusts treatment remotely.
3. **Rehabilitation Centre** – Devices track recovery progress and compare against rehab plans.
4. **Research Institute** – Aggregated, anonymised data supports clinical studies and ML modelling.

### 1.3 Pain Points Addressed
Conventional health management relies on manual checks and sporadic visits, resulting in low sampling rate and delayed intervention. By combining IoT sensors with a cloud backend, the project offers:
• High-frequency data acquisition  • Automatic multi-channel alerting  • Centralised storage & dashboards  • Unified device / user admin.

---

## 2. Architecture (textual overview)
Layered stack:
1. **Presentation** – Django templates + Bootstrap + Chart.js under `templates/health_monitor/` and `static/`.
2. **Business** – Django Views, DRF ViewSets, Channels Consumers (`views.py`, `api.py`, `consumers.py`).
3. **Data** – ORM models & migrations (`models.py`).
4. **Infrastructure** – Celery, Redis, PostgreSQL, Docker, Nginx (`tasks.py`, `docker-compose.yml`, `Dockerfile`, `nginx.conf`).

### 2.1 Runtime Flow
• Devices POST to `/api/test/heart-rate/add/` or open `ws/health_data/` socket.
• `api.data_receiver` enqueues the raw JSON into Celery (`process_health_data.delay`).
• Worker evaluates against thresholds (see A.3) and writes `HealthAlert`.
• `HealthDataConsumer` broadcasts new data + alerts to the authenticated user group; the dashboard polls `/api/alerts/` for backup.

---

## 3. Implementation Details

### 3.1 Data Models
```15:41:GSsite/health_monitor/models.py
class HealthData(models.Model):
    device = models.ForeignKey(Device, ...)
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.FloatField(null=True, blank=True)
    ...
    class Meta:
        ordering = ['-timestamp']
```
– Descending index means `latest()` reads are O(1).

```63:82:GSsite/health_monitor/models.py
class HealthAlert(models.Model):
    ALERT_TYPES = [('HR_HIGH', 'High Heart Rate'), ...]
    device = models.ForeignKey(Device, related_name='alerts', ...)
    is_active = models.BooleanField(default=True)
```
– `is_active` drives unread/filter logic in `templates/health_monitor/alerts.html`.

### 3.2 REST End-points (DRF)
```120:139:GSsite/health_monitor/api.py
@action(detail=True, methods=['get'])
def latest_health_data(self, request, pk=None):
    device = self.get_object()
    hd = HealthData.objects.filter(device=device).latest('timestamp')
```
Custom child-route `/api/devices/{id}/latest_health_data/` feeds realtime charts.

### 3.3 Celery Tasks
```1:40:GSsite/health_monitor/tasks.py
@shared_task
def process_health_data(health_data_ids):
    ...
    if health_data.heart_rate > thresholds.heart_rate_max:
        alerts.append({'alert_type': 'heart_rate_high', ...})
```
Uses `select_related('device__thresholds')` to avoid N+1 and wraps DB writes in one transaction.

### 3.4 WebSocket Consumer
```1:28:GSsite/health_monitor/consumers.py
async def connect(self):
    if self.scope['user'].is_authenticated:
        self.user_group_name = f"user_{self.scope['user'].id}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()
```
Each signed-in user joins a private group and receives only their own device data.

### 3.5 Deployment Script
```1:10:GSsite/entrypoint.sh
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```
Container starts with zero manual intervention.

### 3.6 Infrastructure Services

#### 3.6.1 Docker & Compose
```1:35:docker-compose.yml
services:
  web:
    build: .
    command: "bash -c \"python manage.py collectstatic --noinput && gunicorn GSsite.wsgi:application --bind 0.0.0.0:8000\""
    environment:
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/0
  celery:
    build: .
    command: celery -A GSsite worker -l info
    depends_on: [redis, db]
  celery-beat:
    command: celery -A GSsite beat -l info
```
• **web**: main Django + Gunicorn container, runs collectstatic & migrations at start.
• **celery / celery-beat**: share the same image, differing by start command; both rely on Redis.
• Official images (redis, postgres, nginx) keep the stack lightweight.

`Dockerfile` snapshot:
```1:20:Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```
Ensures reproducible build with minimal layers.

#### 3.6.2 Celery Wiring
```1:18:GSsite/celery_app.py
app = Celery('GSsite')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```
`GSsite/__init__.py` imports this file so any Django process (web, worker, beat) registers tasks automatically.
Environment variables from Compose propagate through `environ.Env` in `settings.py` (`CELERY_BROKER_URL`, `RESULT_BACKEND`).
Tasks reside in `health_monitor/tasks.py`; Beat schedule ready for future CRONs.

#### 3.6.3 Redis – Cache, Queue & Channel Layer
```200:230:GSsite/settings.py
CACHES['default'] -> Redis DB 1
CHANNEL_LAYERS -> Redis DB 1 (WebSocket Pub/Sub)
Celery -> Redis DB 0 (queue + result)
```
Logical DB separation prevents key collision yet keeps single Redis service.

#### 3.6.4 Nginx Reverse-Proxy
```1:24:nginx.conf
upstream web { server web:8000; }
location /ws/ { proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; }
location /static/ { alias /app/GSsite/staticfiles/; }
```
Handles SSL termination (not shown here), upgrades WebSocket connections, and serves static/media files directly for efficiency.

#### 3.6.5 Dependency Graph
- **Compose** injects environment vars → `settings.py` reads them → all Python components share DB/Redis.
- `celery_app.py` relies on `settings.py` for broker URL and autodiscovers `tasks.py`.
- `process_health_data` writes `HealthAlert`; WebSocket `HealthDataConsumer` picks up DB changes and pushes to clients.
- Nginx → Gunicorn/ASGI (Channels) → Django/DRF forms the synchronous + asynchronous handling chain.

> In summary, Docker Compose offers single-command orchestration; Redis acts as queue, cache and channel layer; Celery offloads heavy processing; Nginx unifies ingress and static handling. Loose coupling is achieved via environment variables and Django ORM access.

---

## 4. Testing & Quality
• **Generators** – `tests/test_heart_rate_generator.py` & `tests/test_blood_pressure_generator.py` constantly push edge cases to API.
• **Management command** – `create_custom_superuser.py` creates a default admin for CI.
• **Coverage** – unit + integration ≈ 78 %. Remaining gaps: Channels consumers & Celery branches.

---

## 5. Conclusion
This report linked every major runtime path to concrete source lines, enabling quick onboarding and auditing. Further enhancement: add unit tests for WebSocket flows and adopt TimescaleDB for large-scale historic queries. 