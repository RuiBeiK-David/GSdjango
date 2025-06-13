# 健康监控系统

这是一个基于Django开发的实时健康监控系统，用于监控和管理用户的健康数据。系统支持多设备数据采集、实时数据处理、健康警报和数据可视化等功能。

## 主要功能

- 实时健康数据采集和监控
- 多设备管理
- 健康指标阈值设置
- 实时警报系统
- 数据可视化和趋势分析
- 用户认证和授权
- 设备在线状态监控

## 技术栈

- **后端框架**: Django + Django REST framework
- **数据库**: PostgreSQL
- **缓存**: Redis
- **任务队列**: Celery
- **WebSocket**: Channels
- **前端**: Bootstrap + Chart.js
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx + Gunicorn

## 系统要求

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose

## 快速开始

1. 克隆项目：
   ```bash
   git clone https://github.com/yourusername/health-monitoring-system.git
   cd health-monitoring-system
   ```

2. 创建环境变量文件：
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入你的配置
   ```

3. 使用Docker Compose启动服务：
   ```bash
   docker-compose up -d
   ```

4. 创建超级用户：
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. 访问系统：
   - 网站: http://localhost
   - 管理后台: http://localhost/admin

## 开发设置

1. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   .\venv\Scripts\activate  # Windows
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行迁移：
   ```bash
   python manage.py migrate
   ```

4. 启动开发服务器：
   ```bash
   python manage.py runserver
   ```

## API文档

系统提供了完整的RESTful API：

- `GET /api/devices/`: 获取设备列表
- `POST /api/devices/`: 注册新设备
- `GET /api/health-data/`: 获取健康数据
- `POST /api/health-data/batch-create/`: 批量创建健康数据
- `GET /api/alerts/`: 获取警报列表
- `POST /api/alerts/{id}/resolve/`: 解决警报
- `GET /api/thresholds/`: 获取阈值设置
- `PUT /api/thresholds/{id}/`: 更新阈值设置

完整的API文档可以在 `/api/docs/` 查看。

## 数据处理

系统使用Celery处理后台任务：

1. 数据验证和清洗
2. 健康指标分析
3. 警报触发
4. 数据聚合
5. 历史数据清理

## 缓存策略

系统使用Redis进行缓存：

1. 会话管理
2. 实时数据缓存
3. API响应缓存
4. 设备状态缓存

## 测试

运行测试：
```bash
pytest
```

生成测试覆盖率报告：
```bash
coverage run -m pytest
coverage report
```

## 部署

1. 修改生产环境配置：
   - 设置 `DEBUG=False`
   - 配置安全的 `SECRET_KEY`
   - 更新 `ALLOWED_HOSTS`
   - 配置SSL证书

2. 使用Docker Compose部署：
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 贡献

欢迎提交Pull Request或Issue。

## 许可证

MIT License 