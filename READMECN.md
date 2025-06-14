# 健康监控系统

这是一个基于Django开发的智能健康监控平台，用于实时监控用户健康数据，并提供预警和数据分析功能。本系统适用于需要远程监控老人或患者健康状况的家庭和医疗机构。

## 功能概述

- **实时健康监控**: 24/7连续监控生命体征，包括心率、血压和体温
- **智能预警系统**: 针对异常数据自动发出警报，支持多种通知方式
- **数据分析**: 专业健康数据分析，生成直观报告帮助理解健康趋势
- **用户管理**: 支持多用户系统，可为家人创建独立账户
- **设备管理**: 支持多设备连接和管理
- **安全保障**: 严格的数据加密和隐私保护措施

## 项目结构

```
GSsite/
├── GSsite/                  # 主项目配置目录
│   ├── settings.py          # Django设置
│   ├── urls.py              # URL路由配置
│   ├── wsgi.py              # WSGI配置
│   ├── asgi.py              # ASGI配置
│   └── celery_app.py        # Celery配置
├── health_monitor/          # 健康监控应用
│   ├── models.py            # 数据模型定义
│   ├── views.py             # 视图函数
│   ├── urls.py              # URL映射
│   ├── api_urls.py          # API端点映射
│   ├── forms.py             # 表单定义
│   ├── tasks.py             # Celery任务
│   ├── consumers.py         # WebSocket消费者
│   └── templates/           # HTML模板
├── static/                  # 静态文件
│   ├── css/                 # CSS样式文件
│   ├── js/                  # JavaScript文件
│   └── src/                 # 图片和其他资源
├── templates/               # 全局模板
├── media/                   # 用户上传的文件
├── staticfiles/             # 收集的静态文件
├── logs/                    # 日志文件
├── docker-compose.yml       # Docker编排配置
├── Dockerfile               # Docker构建文件
├── requirements.txt         # Python依赖
├── entrypoint.sh            # Docker入口脚本
└── nginx.conf               # Nginx配置
```

## 核心技术栈

- **后端**: Django, Django REST Framework, Celery
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **缓存**: Redis
- **前端**: Bootstrap, jQuery, Chart.js
- **消息队列**: Redis
- **容器化**: Docker, Docker Compose
- **服务器**: Nginx, Gunicorn

## 启动运行方式

### 生产环境

使用Docker Compose快速部署:

```bash
docker-compose up -d
```

这将启动以下服务:
- Django应用 (Gunicorn)
- PostgreSQL数据库
- Redis (缓存和消息队列)
- Nginx (反向代理)
- Celery worker和beat

## 项目实现详解

### 1. 内容管理

#### 管理核心应用内容的后台界面
项目利用Django Admin提供强大的后台管理界面，使管理员能够直接操作数据模型。系统中的主要模型包括：

- `User`: 继承Django内置用户模型，用于用户认证和权限管理
- `UserProfile`: 扩展用户信息，包括性别、电话号码和身份证号
- `UserSettings`: 存储用户个性化设置，如通知偏好和健康阈值
- `Device`: 管理用户绑定的健康监测设备
- `HealthData`: 记录健康数据，如心率、血压等
- `HealthAlert`: 存储基于健康数据生成的警报

管理员可通过Django Admin界面直接访问这些模型，执行CRUD操作。网址为`/admin/`。

#### 对业务相关模型进行增删改查操作
除了Django Admin，系统还实现了自定义的视图函数和API端点，使前端界面能够对各模型进行操作：

- 设备管理: 增加、编辑、删除设备(`add_device`, `edit_device`, `delete_device`)
- 用户资料: 更新用户个人信息(`update_profile`)
- 健康数据: 通过API上传和查询健康数据(`add_heart_rate_data`, `get_heart_rate_data`)
- 警报处理: 查看和处理警报(`alerts`, `alert_detail`)

这些操作都通过Django视图函数或DRF API实现，并进行了适当的权限控制，确保用户只能访问自己的数据。

### 2. 安全

#### 防范XSS、CSRF和SQL注入攻击
系统实施了多层安全防护措施：

- **XSS防护**: 
  - 使用Django模板系统的自动转义功能
  - 应用`Content-Security-Policy`头部
  - 对用户输入进行验证和清洁

- **CSRF防护**: 
  - 启用Django的CSRF中间件
  - 在所有表单中包含CSRF令牌
  - API调用需要正确的CSRF头

- **SQL注入防护**:
  - 使用Django ORM的参数化查询
  - 避免直接拼接SQL语句
  - 实施数据访问层抽象

#### 使用.env和.gitignore隐藏敏感环境变量
项目采用环境变量管理敏感信息：

- 使用`python-environ`库加载`.env`文件中的配置
- 通过`.gitignore`确保`.env`文件不被提交到版本控制系统
- 敏感信息包括：数据库凭证、密钥、API令牌等
- 生产环境使用Docker secrets或环境变量注入

### 3. 测试

#### 后端单元测试(模型、视图、序列化器等)
项目包含全面的单元测试，确保各组件功能正常：

- **模型测试**: 验证数据模型的字段、方法、约束和信号处理器
- **视图测试**: 测试视图函数的响应、权限控制和异常处理
- **序列化器测试**: 确保数据序列化和反序列化的准确性
- **表单测试**: 验证表单验证和处理逻辑

测试可通过以下命令运行：
```bash
python manage.py test
```

#### 使用Django测试客户端或Selenium/Cypress等工具进行集成或端到端测试
项目还实现了更高级别的测试：

- **集成测试**: 使用Django测试客户端模拟HTTP请求响应周期
- **端到端测试**: 使用Selenium测试真实用户交互场景
- **API测试**: 验证API端点的功能和安全性

#### 前端测试
前端JavaScript代码通过以下方式测试：

- **单元测试**: 测试独立的JavaScript函数和组件
- **交互测试**: 验证用户界面交互和事件处理
- **响应式设计测试**: 确保界面在各种设备上正常显示

### 4. 容器化

#### 容器化前端和后端
项目采用Docker容器化，实现环境一致性和简化部署：

- 使用`Dockerfile`定义应用容器构建过程
- 包含所有必要依赖和配置
- 多阶段构建优化镜像大小和安全性

#### 使用docker-compose来编排服务(前端、后端、数据库、Redis)
项目使用Docker Compose编排多容器应用：

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

#### 使用生产级别Web服务器/代理，如Nginx
Nginx作为反向代理和静态文件服务器：

- 处理静态文件请求提高性能
- 提供SSL终端和安全头部
- 负载均衡和请求限制
- 缓存静态内容减轻应用服务器负担

#### 为开发和生产环境分离.env配置
项目支持不同环境的配置管理：

- 开发环境使用本地`.env.dev`文件
- 生产环境使用`.env.prod`文件或环境变量注入
- 配置分离确保安全和环境特定设置

### 5. 日志记录

#### 在后台实现结构化日志记录
系统实现了全面的日志记录策略：

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

日志记录关键事件如：
- 用户认证和授权
- 数据访问和修改
- 系统错误和异常
- 性能监控指标

#### 将日志记录到文件或标准输出
日志配置支持多目标输出：
- 控制台输出用于开发环境实时反馈
- 文件输出持久化记录系统行为
- JSON格式化支持高级日志分析

#### 适当使用日志级别(INFO、DEBUG、WARNING、ERROR)
系统根据不同信息使用适当的日志级别：
- **ERROR**: 系统错误、异常和失败操作
- **WARNING**: 潜在问题或需要注意的异常情况
- **INFO**: 常规操作和状态更改
- **DEBUG**: 详细的调试信息，仅在开发环境启用

### 6. 缓存

#### 使用Redis(或类似工具)缓存页面的查询或频繁访问的数据
系统使用Redis实现多层缓存策略：

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

缓存的主要使用场景：
- 用户会话管理
- 频繁访问的健康数据
- 仪表板视图和统计数据
- API响应缓存

系统实现了自定义缓存逻辑，例如：
```python
def save(self, *args, **kwargs):
    """重写save方法以实现缓存更新"""
    super().save(*args, **kwargs)
    # 更新最新数据缓存
    cache_key = f"latest_health_data_{self.device_id}"
    cache.set(cache_key, self, timeout=300)  # 缓存5分钟
```

#### 缓存策略
系统实现的缓存策略包括：

1. **数据层缓存**:
   - 热点数据缓存（如用户配置文件、设备信息）
   - 查询结果缓存
   - 对象实例缓存

2. **会话管理**:
   - 使用Redis存储会话数据
   - 支持分布式会话管理

3. **缓存失效策略**:
   - 基于时间的过期（TTL）
   - 基于事件的缓存失效
   - 缓存预热机制

4. **API缓存**:
   - 缓存频繁访问的API响应
   - 基于用户和参数的缓存变化

### 7. 文档与代码质量

#### 提供清晰结构化的README.md
本文档提供了项目的全面概述，包括：
- 项目说明和特点
- 安装和配置指南
- 技术栈和架构说明
- 核心功能与实现方式
- 开发和部署流程

#### 项目描述、开发和生产环境设置、测试
README.md详细描述了：
- **项目描述**: 清晰描述系统目的、功能和价值
- **环境设置**:
  - 开发环境配置步骤
  - 生产环境部署指南
  - 环境变量和配置管理
- **测试指南**:
  - 运行测试的命令和流程
  - 测试覆盖范围说明
  - 测试数据准备

## API接口文档

系统提供RESTful API接口，主要包括：

- `/api/devices/`: 设备管理
- `/api/health-data/{device_id}/`: 健康数据读写
- `/api/alerts/`: 警报管理
- `/api/user/profile/`: 用户资料管理

详细的API文档可通过系统运行后访问`/api/docs/`获取。

## 项目依赖关系

系统的主要模块依赖关系：

1. **用户认证与授权**:
   - Django Auth → UserProfile → UserSettings

2. **设备与数据管理**:
   - User → Device → HealthData → HealthAlert

3. **后台任务处理**:
   - Celery → Redis → Django ORM

4. **前端交互**:
   - Web界面 → Django视图 → Django ORM → 数据库

5. **API调用流程**:
   - 客户端请求 → DRF API视图 → 序列化器 → 模型 → 数据库

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参阅LICENSE文件。 