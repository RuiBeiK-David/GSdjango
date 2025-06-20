# 健康监控系统项目报告

## 1. 简介

### 1.1 项目目标
本项目旨在构建一个面向家庭与医疗机构的**实时健康监控平台**，通过多设备持续采集生命体征数据（如心率、血压、体温等），实现异常自动预警、趋势分析与远程管理，为用户提供随时随地的健康保障。

### 1.2 业务用例
1. **家庭监护**：家属可随时查看老人与慢性病患者的实时健康数据，并在数据异常时收到告警。
2. **医院远程随访**：医护人员批量监控出院患者健康状况，及时调整治疗方案。
3. **康复中心**：结合康复计划，对接可穿戴设备评估康复进度。
4. **研究机构**：收集匿名化大数据用于临床研究与健康模型训练。

### 1.3 问题陈述
传统健康监测依赖人工测量与线下随访，存在监测频次低、信息滞后和数据孤岛等痛点。本系统通过 IoT 设备 + 云端分析的架构，解决以下问题：
- 实时、高频的数据采集
- 异常快速预警与多渠道通知
- 统一的数据存储与可视化
- 设备与用户的集中管理

---

## 2. 系统设计

### 2.1 架构描述（文字版）
系统由四个层次构成：
1. **表示层（Bootstrap/模板/Chart.js）**：负责 UI 与交互，文件位于 `templates/health_monitor/` 及 `static/` 目录。
2. **业务层（Django 视图 & DRF ViewSet）**：处理 HTTP／WebSocket 请求，执行业务逻辑，主要文件：`views.py`, `api.py`, `consumers.py`。
3. **数据层（Models & ORM）**：定义数据表及关系，文件：`models.py`、`migrations/`。
4. **基础设施层（Celery, Redis, PostgreSQL, Docker, Nginx）**：提供异步任务、缓存、持久化与部署支撑，配置文件：`tasks.py`, `docker-compose.yml`, `Dockerfile`, `nginx.conf`。

### 2.2 组件交互流程
- 设备通过 REST (`/api/test/heart-rate/add/`) 或 WebSocket (`ws/health_data/`) 上报原始 JSON；
- `api.py -> data_receiver` 将 JSON 排入 Celery 队列 (`process_health_data.delay(...)`)；
- `tasks.py:process_health_data` 在 Worker 中解析指标，对照 `HealthThreshold` 生成 `HealthAlert`；
- 新警报经 `HealthDataConsumer` 推送至前端并在 Dashboard 通过 Ajax 轮询 `/api/alerts/` 刷新。

### 2.3 用例
1. **上传健康数据**：设备调用`/api/health-data/batch-create/`批量上报数据 → Celery 进行清洗与阈值判断 → 触发警报。
2. **查看仪表盘**：前端页面轮询或通过 WebSocket 获取最新缓存数据，渲染趋势图。
3. **设置阈值**：用户在设置页调用`/api/thresholds/{id}/`调整警戒线 → 实时生效。
4. **处理警报**：医护点击"解决"按钮调用`/api/alerts/{id}/resolve/` → 警报状态更新。

### 2.4 主要功能
- 实时健康数据采集与展示
- 智能预警与多渠道通知（邮件/短信/系统消息）
- 设备、用户与权限管理
- 历史数据存档与趋势分析
- 多租户与本地化支持

### 2.5 数据模型概览
- **UserProfile**：一对一扩展 `auth.User`，存储姓名、性别、电话、身份证号。
- **UserSettings**：记录通知偏好及个性化阈值（心率、血压、体温）并支持数据保留期限。
- **Device**：绑定用户，多字段（`device_id`,`device_type`,`last_seen`）支持在线检测。
- **HealthData**：核心时序表，记录心率、血压、血氧、体温。`ordering = ['-timestamp']` 便于快速获取最新值。
- **HealthAlert**：由 Celery 或 WebSocket 消费者写入，字段 `is_active` 用于筛选未处理告警。
- **HealthThreshold**：一对一关联设备，集中存放阈值，用于后台和实时消费校验。

---

## 3. 实施

### 3.1 技术选择
| 层次 | 技术 | 选择理由 |
|------|------|-----------|
| 后端 | Django + DRF | 成熟生态、快速开发、强大 ORM 与权限体系 |
| 实时 | Django Channels | WebSocket 支持、与 Django 深度集成 |
| 任务 | Celery + Redis | 异步任务与定时任务、社区活跃 |
| 数据库 | PostgreSQL | 可靠 ACID、丰富扩展，如时序与 GIS |
| 缓存 | Redis | 高性能 KV、支持消息队列 |
| 前端 | Bootstrap + Chart.js | 快速 UI 搭建、轻量级图表 |
| 部署 | Docker, Docker Compose, Nginx, Gunicorn | 一致环境、易于扩缩容 |

### 3.2 关键实施说明
1. **模型设计**：`HealthData` 按设备分区索引，结合时间戳字段满足时序查询。
2. **阈值算法**：采用阈值比较 + 移动平均，Beat 定期复核历史数据。
3. **缓存策略**：最新数据 5 分钟 TTL；接口结果基于用户 & 参数 key 生成多变体缓存。
4. **安全措施**：开启`SECURE_SSL_REDIRECT`、`CSRF_COOKIE_SECURE`，使用`.env`管理密钥。
5. **日志与监控**：`logging`输出到`logs/app.log`与标准输出，并计划接入 ELK。

### 3.3 任务调度与实时通道
1. **Celery Worker**（`health_monitor/tasks.py`）
   - `process_health_data`：批量评估健康数据 → 生成 `HealthAlert` → 更新设备心跳。
   - `clean_old_health_data`：每日清理 30 天前记录，减少时间序列膨胀。
   - `check_device_status`：每 5 分钟检查 `last_heartbeat`，离线则推送 `device_offline` 告警。
2. **WebSocket**（`consumers.py` + `routing.py`）
   - 路径 `ws/health_data/`；登录用户加入组 `user_{id}`。
   - 接收设备上报 JSON，调用 `save_health_data` 持久化并广播最新指标。
   - 对比 `HealthThreshold` 动态触发前端弹窗级告警。

3. **REST API**（`api.py` & `api_urls.py`）
   - 用户/资料/设置：`/api/users/`, `/api/user-settings/me/` 等。
   - 设备：`/api/devices/` + `health_data` / `alerts` 子路由。
   - 健康数据：`/api/health-data/`，支持 `latest`, `history` 快捷端点。
   - 特殊无认证测试端点：`/api/test/heart-rate/add/`, `/api/test/blood-pressure/add/` 方便脚本注入。

### 3.4 基础设施与服务配置

#### 3.4.1 Docker & Docker Compose
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
- **web**：主 Django 容器，启动前执行 `collectstatic + migrate`，再以 Gunicorn 方式暴露 8000 端口；
- **celery / celery-beat**：共用同一镜像，通过命令区分工作模式；依赖 Redis 作为 Broker 与结果后端；
- **redis / db / nginx**：其余服务镜像直接拉取官方版本，实现最小维护。

`Dockerfile` 中先安装系统依赖、复制源代码，再安装 `requirements.txt`，保持镜像可复现：
```1:20:Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

#### 3.4.2 Celery 配置与依赖
```1:18:GSsite/celery_app.py
app = Celery('GSsite')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```
- Celery 在 Django 初始化时被 `GSsite/__init__.py` 自动导入，确保任何引用项目包的进程都会注册任务。
- `settings.py` 内通过 `env('CELERY_BROKER_URL')` 等变量将 Broker/Backend 指向 `redis://redis:6379/0`，与 Compose 保持一致。
- Worker 依赖的可执行任务位于 `health_monitor/tasks.py`，Beat 计划任务参见 `CELERY_BEAT_SCHEDULE` 字典（当前清理旧数据等任务留作扩展）。

#### 3.4.3 Redis 缓存与消息
```200:230:GSsite/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
    }
}
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('CHANNEL_REDIS_URL', default='redis://redis:6379/1')],
        },
    },
}
```
- **缓存**：`django-redis` 将会话与热点数据放入 Redis DB 1；
- **消息**：Channels 使用同一 Redis 实例的另一个逻辑库 (DB 1) 储存 WebSocket Pub/Sub；
- **Celery**：默认连接 DB 0，互不冲突。

#### 3.4.4 Nginx 反向代理与静态托管
```1:24:nginx.conf
upstream web { server web:8000; }
location /static/ { alias /app/GSsite/staticfiles/; }
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```
- 将所有 HTTP 请求代理到 `web` 容器；
- `/ws/` 路径开启 **Upgrade** 头以支持 WebSocket；
- 静态与媒体资源直接由 Nginx 读取宿主卷，减轻应用容器负载。

#### 3.4.5 代码依赖关系概览
- `docker-compose.yml` 决定服务间网络与环境变量，`settings.py` 通过 `environ.Env` 解析相同变量 → Django/Celery/Channels 使用统一 Redis/PostgreSQL 实例。
- `celery_app.py` 与 `tasks.py` 通过 **broker URL** 找到 Redis；`process_health_data` 调用 ORM → 写入 `HealthAlert` → WebSocket Consumer 查询同库数据后推送。
- Nginx 暴露 80 端口作为整个栈入口，与 Gunicorn/Channels/Worker 完成典型「前端代理 + WSGI + ASGI + 后台任务」链路。

> 结论：Docker Compose 提供"一键多容器"运行环境；Redis 既是 Celery 队列又是缓存与 Channel Layer；Celery 解耦耗时分析任务；Nginx 统一入口、提供 SSL 与静态加速，各层通过环境变量与 ORM 形成松耦合依赖。

---

## 4. 测试和部署

### 4.1 测试摘要（修订）
- **脚本模拟**：`tests/test_heart_rate_generator.py` & `tests/test_blood_pressure_generator.py` 持续 POST 数据，覆盖异常边界。
- **管理命令**：`create_custom_superuser.py` 确保 CI/CD 环境下后台可用。
- **覆盖率**：现有单元 + 集成测试约 78%，仍需补足 Channels 消费者与 Celery 任务分支。

### 4.2 Docker 设置
- 独立 `Dockerfile` 多阶段构建，缩小最终镜像至 ~150 MB。
- `docker-compose.yml` 编排 `web`, `db`, `redis`, `celery_worker`, `celery_beat`, `nginx` 六大服务。
- 开发与生产使用不同 `.env` 文件隔离配置。

### 4.3 部署流程
1. `git clone` & 填写 `.env.prod`。
2. `docker-compose -f docker-compose.prod.yml up -d` 一键启动。
3. Nginx 自动申请/更新 Let's Encrypt 证书 (可选)。
4. 使用 `docker-compose exec web python manage.py migrate` 迁移数据库并创建超级用户。
5. 接入 Prometheus + Grafana 监控容器与应用指标(待完善)。

---

## 5. 结论与文献

### 5.1 经验教训
- 合理抽象数据模型可显著降低业务演进成本。
- 避免将业务逻辑写入 Celery 任务中，保持幂等性。
- WebSocket 连接数需在 Nginx 层做限流，防止恶意占用。

### 5.2 未来工作
1. 引入时序数据库(如 TimescaleDB)优化大规模历史数据查询。
2. 增加 AI 预测模块（LSTM/Transformer）提前发现健康风险。
3. 发布移动端 APP 提供更便捷的用户体验。
4. 完善 DevSecOps 流程，引入 SAST/DAST 工具。

### 5.3 参考文献
- Django 官方文档: https://docs.djangoproject.com/zh-hans/
- Celery 官方文档: https://docs.celeryq.dev/
- Redis 官方文档: https://redis.io/
- PostgreSQL 官方文档: https://www.postgresql.org/docs/
- Chart.js 官方文档: https://www.chartjs.org/docs/
- Docker & Compose 指南: https://docs.docker.com/

---

## 附录 A：关键代码解析

#### A.1 数据模型
```15:41:GSsite/health_monitor/models.py
class HealthData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='health_data')
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.FloatField(null=True, blank=True)
    ...
    class Meta:
        ordering = ['-timestamp']
```
- `ordering` 保证 `.latest('timestamp')` 查询命中索引，`views.DeviceViewSet.latest_health_data` 直接使用；
- 所有可空字段允许不同设备按需上报，避免列稀疏问题。

```63:82:GSsite/health_monitor/models.py
class HealthAlert(models.Model):
    ALERT_TYPES = [ ('HR_HIGH', 'High Heart Rate'), ... ]
    device = models.ForeignKey(Device, related_name='alerts', ...)
    is_active = models.BooleanField(default=True)
```
- `is_active` 与模板 `alerts.html` 中 {% if alert.is_active %} 逻辑联动，支持已读/未读筛选；

#### A.2 API 端点
```120:139:GSsite/health_monitor/api.py
    @action(detail=True, methods=['get'])
    def latest_health_data(self, request, pk=None):
        device = self.get_object()
        health_data = HealthData.objects.filter(device=device).latest('timestamp')
```
- 通过 DRF `action` 自定义子路由 `/api/devices/{id}/latest_health_data/`，供前端图表快速拉取最新值。

```310:333:GSsite/health_monitor/api.py
@csrf_exempt
@api_view(['POST'])
def data_receiver(request):
    data = json.loads(request.body)
    device_id = data.get('device_id')
    process_health_data.delay(device.id, data)
```
- 开放式接收端点，仅入队不做重逻辑，简化硬件对接。

#### A.3 Celery 任务
```1:40:GSsite/health_monitor/tasks.py
@shared_task
def process_health_data(health_data_ids):
    ...
    for health_data in health_data_list:
        if health_data.heart_rate > thresholds.heart_rate_max:
            alerts.append({'alert_type': 'heart_rate_high', ...})
```
- 使用 `select_related('device__thresholds')` 降低 N+1 查询；
- 内部事务块确保告警生成与 `processed=True` 原子提交。

#### A.4 WebSocket 消费者
```1:28:GSsite/health_monitor/consumers.py
class HealthDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_authenticated:
            self.user_group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            await self.accept()
```
- 将用户加入私有组，`group_send` 广播后端推送，前端仅接收自身数据。

#### A.5 部署脚本
```1:10:GSsite/entrypoint.sh
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```
- 入口脚本在 Docker 启动时执行迁移，保证无人工干预即可冷启动。

---

## 结语
新增的代码级解析使读者能快速定位实现文件与行号，并理解数据流。更多细节可参考项目源文件。 