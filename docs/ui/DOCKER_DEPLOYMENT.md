# Docker部署指南

**项目**: AI-Narrated Recap Analyst Web UI  
**版本**: v1.0  
**日期**: 2026-02-10

---

## 目录

1. [部署架构](#1-部署架构)
2. [Docker镜像构建](#2-docker镜像构建)
3. [Docker Compose部署](#3-docker-compose部署)
4. [环境配置](#4-环境配置)
5. [运维管理](#5-运维管理)

---

## 1. 部署架构

```
┌─────────────────────────────────────────────────┐
│                   Nginx (Port 80)                │
│  ┌────────────┐  ┌─────────────────────────┐   │
│  │  前端静态   │  │  反向代理                │   │
│  │  文件服务   │  │  /api/ → backend:8000   │   │
│  │            │  │  /ws/  → backend:8000    │   │
│  └────────────┘  └─────────────────────────┘   │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────┐
│          FastAPI Backend (Port 8000)            │
│  ┌────────────────────────────────────────┐    │
│  │  API服务 + WebSocket                   │    │
│  │  集成现有Workflow和Tools               │    │
│  └────────────────────────────────────────┘    │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────┐
│               数据持久化                         │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ data/      │  │ output/    │  │ logs/    │ │
│  │ (项目数据)  │  │ (输出文件)  │  │ (日志)   │ │
│  └────────────┘  └────────────┘  └──────────┘ │
└──────────────────────────────────────────────────┘
```

---

## 2. Docker镜像构建

### 2.1 前端Dockerfile

**`Dockerfile.frontend`**:
```dockerfile
# ========== 构建阶段 ==========
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY frontend-new/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY frontend-new/ ./

# 构建生产版本
RUN npm run build

# ========== 生产阶段 ==========
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
```

### 2.2 后端Dockerfile

**`Dockerfile.backend`**:
```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-api.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-api.txt

# 复制源代码
COPY src/ ./src/
COPY .env.example .env

# 创建数据目录
RUN mkdir -p data output logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# 启动应用
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3 Nginx配置

**`nginx.conf`**:
```nginx
server {
    listen 80;
    server_name localhost;

    # 前端静态文件
    root /usr/share/nginx/html;
    index index.html;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss;

    # 前端路由（SPA）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket超时设置
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

---

## 3. Docker Compose部署

### 3.1 基础配置

**`docker-compose.yml`**:
```yaml
version: '3.8'

services:
  # 后端服务
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: recap-analyst-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # 数据持久化
      - ./data:/app/data
      - ./output:/app/output
      - ./logs:/app/logs
      # 代码热重载（开发环境）
      # - ./src:/app/src
    environment:
      # LLM配置
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - CLAUDE_BASE_URL=${CLAUDE_BASE_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DEEPSEEK_BASE_URL=${DEEPSEEK_BASE_URL}
      # 应用配置
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PYTHONUNBUFFERED=1
    networks:
      - recap-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  # 前端服务
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: recap-analyst-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - recap-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s

networks:
  recap-network:
    driver: bridge

volumes:
  data-volume:
  output-volume:
  logs-volume:
```

### 3.2 开发环境配置

**`docker-compose.dev.yml`**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    volumes:
      # 代码热重载
      - ./src:/app/src
      - ./data:/app/data
      - ./output:/app/output
      - ./logs:/app/logs
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - LOG_LEVEL=DEBUG

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      target: builder  # 只构建到builder阶段
    volumes:
      - ./frontend-new/src:/app/src
    command: npm run dev -- --host 0.0.0.0 --port 5173
    ports:
      - "5173:5173"
```

**启动开发环境**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## 4. 环境配置

### 4.1 环境变量

**`.env.example`**:
```bash
# ===== LLM配置 =====

# Claude配置
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_BASE_URL=https://chatapi.onechats.ai/v1/
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=16000

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_V32_MODEL=deepseek-chat
DEEPSEEK_V32_THINKING_MODEL=deepseek-reasoner

# ===== 应用配置 =====

# 日志级别
LOG_LEVEL=INFO

# 数据目录
DATA_DIR=./data
OUTPUT_DIR=./output
LOGS_DIR=./logs

# ===== API配置 =====

# CORS允许的源
CORS_ORIGINS=http://localhost:5173,http://localhost:80

# API速率限制
API_RATE_LIMIT=100  # 每分钟请求数

# ===== 数据库配置（可选） =====

# SQLite（本地）
DATABASE_URL=sqlite:///./data/recap_analyst.db

# PostgreSQL（生产）
# DATABASE_URL=postgresql://user:password@localhost:5432/recap_analyst
```

**复制并配置**:
```bash
cp .env.example .env
# 编辑 .env 填入实际的API Key
```

### 4.2 配置验证

**创建验证脚本** (`scripts/ui/validate_config.sh`):
```bash
#!/bin/bash

echo "🔍 验证配置..."

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在，请复制 .env.example 并配置"
    exit 1
fi

# 检查API Key
if grep -q "sk-ant-xxx" .env; then
    echo "⚠️  警告: Claude API Key未配置"
fi

if grep -q "sk-xxx" .env; then
    echo "⚠️  警告: DeepSeek API Key未配置"
fi

echo "✅ 配置验证完成"
```

---

## 5. 运维管理

### 5.1 常用命令

```bash
# ===== 构建与启动 =====

# 构建镜像
docker-compose build

# 启动服务（后台）
docker-compose up -d

# 启动服务（前台，查看日志）
docker-compose up

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 停止服务并删除卷
docker-compose down -v

# ===== 日志查看 =====

# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs backend
docker-compose logs frontend

# 实时跟踪日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100

# ===== 进入容器 =====

# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# ===== 数据管理 =====

# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/ output/ logs/

# 恢复数据
tar -xzf backup-20260210.tar.gz

# ===== 监控 =====

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats

# 查看网络
docker network ls
docker network inspect recap-network
```

### 5.2 健康检查

**检查脚本** (`scripts/ui/health_check.sh`):
```bash
#!/bin/bash

echo "🏥 健康检查..."

# 检查后端
echo "检查后端..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ 后端健康"
else
    echo "❌ 后端异常 (HTTP $HTTP_CODE)"
fi

# 检查前端
echo "检查前端..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ 前端健康"
else
    echo "❌ 前端异常 (HTTP $HTTP_CODE)"
fi

# 检查WebSocket
echo "检查WebSocket..."
wscat -c ws://localhost/ws/health --execute "ping" 2>&1 | grep -q "pong" && \
    echo "✅ WebSocket健康" || \
    echo "❌ WebSocket异常"
```

### 5.3 日志管理

**日志轮转配置** (`logrotate.conf`):
```
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    copytruncate
}
```

**Docker日志配置** (在`docker-compose.yml`中):
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5.4 性能监控

**安装Prometheus + Grafana** (可选):
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus-data:
  grafana-data:
```

---

## 6. 生产部署清单

### 6.1 部署前检查

- [ ] 环境变量配置完整（.env文件）
- [ ] API Key有效且有余额
- [ ] 数据目录权限正确（data/, output/, logs/）
- [ ] 防火墙规则配置（开放80, 8000端口）
- [ ] SSL证书配置（HTTPS）
- [ ] 域名DNS解析正确

### 6.2 安全加固

**HTTPS配置** (使用Let's Encrypt):
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... 其他配置
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**防火墙规则**:
```bash
# ufw (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 6.3 自动部署

**GitHub Actions示例** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/AI-Narrated-Recap-Analyst
            git pull origin main
            docker-compose down
            docker-compose build
            docker-compose up -d
```

---

## 7. 故障排查

### 常见问题

**问题1: 容器无法启动**
```bash
# 查看日志
docker-compose logs backend

# 常见原因:
# - 端口被占用 → 修改端口映射
# - 环境变量缺失 → 检查.env文件
# - 依赖安装失败 → 重新构建镜像
```

**问题2: API无法访问**
```bash
# 检查容器状态
docker-compose ps

# 检查网络
docker network inspect recap-network

# 测试后端连接
curl http://localhost:8000/api/health
```

**问题3: WebSocket连接失败**
```bash
# 检查Nginx配置
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf

# 检查WebSocket路由
wscat -c ws://localhost/ws/health
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-10  
**维护者**: AI-Narrated Recap Analyst Team
