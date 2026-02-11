# UI系统快速启动指南

**项目**: AI-Narrated Recap Analyst Web UI  
**版本**: v1.0  
**日期**: 2026-02-10

---

## 📋 目录

1. [环境准备](#1-环境准备)
2. [项目初始化](#2-项目初始化)
3. [开发环境启动](#3-开发环境启动)
4. [生产环境部署](#4-生产环境部署)
5. [常见问题](#5-常见问题)

---

## 1. 环境准备

### 1.1 系统要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | ≥ 18.0.0 | 前端运行环境 |
| Python | ≥ 3.8.0 | 后端运行环境 |
| Docker | ≥ 20.10 | 容器化部署（可选） |
| Git | ≥ 2.30 | 版本控制 |

### 1.2 安装依赖工具

**macOS**:
```bash
# 安装Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Node.js
brew install node@18

# 安装Python
brew install python@3.11

# 安装Docker（可选）
brew install --cask docker
```

**Linux**:
```bash
# Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python
sudo apt-get install python3.11 python3-pip

# Docker
sudo apt-get install docker.io docker-compose
```

**Windows**:
```powershell
# 使用Chocolatey
choco install nodejs python docker-desktop
```

---

## 2. 项目初始化

### 2.1 克隆仓库（如果已有Git仓库）

```bash
git clone <repository-url>
cd AI-Narrated-Recap-Analyst
```

### 2.2 创建前端项目

```bash
# 创建Vite + React + TypeScript项目
npm create vite@latest frontend -- --template react-ts

cd frontend

# 安装依赖
npm install

# 安装核心库
npm install react-router-dom zustand @tanstack/react-query axios

# 安装UI库和工具
npm install tailwindcss postcss autoprefixer
npm install xterm @xterm/xterm d3 recharts
npm install date-fns clsx

# 安装开发依赖
npm install -D @types/d3 vitest @testing-library/react

# 初始化TailwindCSS
npx tailwindcss init -p
```

**配置TailwindCSS** (`tailwind.config.js`):
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0d1117',
        'bg-secondary': '#161b22',
        'bg-tertiary': '#21262d',
        'bg-hover': '#30363d',
        'text-primary': '#c9d1d9',
        'text-secondary': '#8b949e',
        'text-muted': '#6e7681',
        'border': '#30363d',
        'accent-blue': '#58a6ff',
        'accent-green': '#3fb950',
        'accent-yellow': '#d29922',
        'accent-red': '#f85149',
        'accent-purple': '#bc8cff',
        'accent-cyan': '#39c5cf',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

**更新 `src/index.css`**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: #0d1117;
  color: #c9d1d9;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
```

### 2.3 创建后端项目结构

```bash
# 创建API目录
mkdir -p src/api/routes
mkdir -p src/api/schemas
mkdir -p src/api/services
mkdir -p src/api/middleware

# 创建requirements文件
touch requirements-api.txt
```

**`requirements-api.txt`**:
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
python-dotenv==1.0.0
```

**安装后端依赖**:
```bash
pip install -r requirements-api.txt
```

### 2.4 创建FastAPI入口文件

**`src/api/main.py`**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Narrated Recap Analyst API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "AI-Narrated Recap Analyst"
    }

# 根路径
@app.get("/")
async def root():
    return {
        "message": "AI-Narrated Recap Analyst API",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. 开发环境启动

### 3.1 启动后端

```bash
# 方式1: 直接运行
python src/api/main.py

# 方式2: 使用uvicorn（推荐）
uvicorn src.api.main:app --reload --port 8000

# 输出:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

**验证后端**:
```bash
# 健康检查
curl http://localhost:8000/api/health

# 访问API文档
open http://localhost:8000/api/docs
```

### 3.2 启动前端

```bash
cd frontend

# 启动开发服务器
npm run dev

# 输出:
# VITE v5.0.0  ready in 500 ms
#
# ➜  Local:   http://localhost:5173/
# ➜  Network: use --host to expose
```

**验证前端**:
```bash
open http://localhost:5173
```

### 3.3 并行启动（推荐）

**创建启动脚本** (`scripts/dev.sh`):
```bash
#!/bin/bash

# 启动后端（后台）
echo "🚀 启动后端服务..."
cd "$(dirname "$0")/.."
uvicorn src.api.main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
echo "🚀 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

# 等待
wait
```

**赋予执行权限并运行**:
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

---

## 4. 生产环境部署

### 4.1 Docker Compose部署（推荐）

**创建 `Dockerfile.frontend`**:
```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app
COPY frontend-new/package*.json ./
RUN npm ci

COPY frontend-new/ ./
RUN npm run build

# 生产阶段
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**创建 `Dockerfile.backend`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# 复制代码
COPY src/ ./src/
COPY data/ ./data/
COPY output/ ./output/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**创建 `docker-compose.yml`**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**创建 `nginx.conf`**:
```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket代理
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**构建并启动**:
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

**访问应用**:
```bash
open http://localhost
```

### 4.2 手动部署

**构建前端**:
```bash
cd frontend
npm run build

# 输出到 dist/ 目录
```

**部署前端到Nginx**:
```bash
# 复制构建产物
sudo cp -r dist/* /var/www/html/

# 重启Nginx
sudo systemctl restart nginx
```

**部署后端**:
```bash
# 使用Supervisor管理进程
sudo apt-get install supervisor

# 创建配置文件 /etc/supervisor/conf.d/recap-analyst.conf
[program:recap-analyst-api]
command=/usr/bin/python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
directory=/path/to/AI-Narrated-Recap-Analyst
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/recap-analyst/api.err.log
stdout_logfile=/var/log/recap-analyst/api.out.log

# 重新加载Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start recap-analyst-api
```

---

## 5. 常见问题

### Q1: 前端无法连接后端

**检查**:
```bash
# 1. 确认后端已启动
curl http://localhost:8000/api/health

# 2. 检查CORS配置
# src/api/main.py 中 allow_origins 是否包含前端地址
```

**解决**:
```python
# src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 确保端口正确
    ...
)
```

---

### Q2: WebSocket连接失败

**检查**:
```bash
# 测试WebSocket连接
wscat -c ws://localhost:8000/ws/health
```

**解决**:
```python
# 确保WebSocket路由已注册
from fastapi import WebSocket

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"message": "connected"})
```

---

### Q3: Docker构建失败

**检查**:
```bash
# 查看构建日志
docker-compose build --no-cache

# 查看容器日志
docker-compose logs backend
docker-compose logs frontend
```

**常见问题**:
- ❌ Node.js版本不匹配 → 使用 `node:18-alpine`
- ❌ Python依赖安装失败 → 检查 `requirements-api.txt`
- ❌ 文件路径错误 → 确认 `COPY` 路径正确

---

### Q4: 端口被占用

**查找占用进程**:
```bash
# macOS/Linux
lsof -i :8000  # 后端端口
lsof -i :5173  # 前端端口

# 杀死进程
kill -9 <PID>
```

**使用其他端口**:
```bash
# 后端
uvicorn src.api.main:app --port 8001

# 前端
npm run dev -- --port 5174
```

---

### Q5: 热重载不生效

**前端**:
```bash
# 清除缓存
rm -rf frontend-new/node_modules/.vite
npm run dev
```

**后端**:
```bash
# 确保使用 --reload 参数
uvicorn src.api.main:app --reload
```

---

## 6. 开发工具推荐

### 6.1 VSCode插件

```json
// .vscode/extensions.json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-azuretools.vscode-docker"
  ]
}
```

### 6.2 浏览器插件

- **React DevTools**: 调试React组件
- **Redux DevTools**: 调试状态管理（如果使用Redux）
- **JSON Viewer**: 美化JSON响应

### 6.3 终端工具

```bash
# HTTPie: 测试API
brew install httpie
http GET http://localhost:8000/api/health

# wscat: 测试WebSocket
npm install -g wscat
wscat -c ws://localhost:8000/ws/test

# jq: 解析JSON
brew install jq
curl http://localhost:8000/api/projects | jq
```

---

## 7. 下一步

✅ 环境准备完成  
✅ 项目初始化完成  
✅ 开发环境启动成功

**接下来**:
1. 阅读 [UI架构设计](UI_ARCHITECTURE.md)
2. 查看 [API接口规范](API_SPECIFICATION.md)
3. 参考 [实施计划](IMPLEMENTATION_PLAN.md)
4. 开始编写代码！

---

## 8. 快速命令参考

```bash
# ===== 开发环境 =====
# 启动后端
uvicorn src.api.main:app --reload --port 8000

# 启动前端
cd frontend && npm run dev

# 运行测试
npm run test             # 前端测试
pytest tests/            # 后端测试

# ===== 生产环境 =====
# Docker部署
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# ===== 工具命令 =====
# 格式化代码
npm run format           # 前端
black src/               # 后端

# 类型检查
npm run type-check       # 前端
mypy src/                # 后端

# Lint检查
npm run lint             # 前端
ruff check src/          # 后端
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-10  
**维护者**: AI-Narrated Recap Analyst Team

如有问题，请查看 [常见问题](#5-常见问题) 或提交Issue。
