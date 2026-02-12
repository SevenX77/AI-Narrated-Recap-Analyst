#!/bin/bash

echo "🚀 启动后端服务..."

cd "$(dirname "$0")/../.."

# 检查依赖
if ! python3 -c "import fastapi" > /dev/null 2>&1; then
    echo "📦 安装后端依赖..."
    pip3 install -r requirements-api.txt
fi

# 启动服务
echo "✅ 后端服务启动中 (http://localhost:8000)"
echo "📖 API文档: http://localhost:8000/api/docs"
echo ""

python3 -m uvicorn src.api.main:app --reload --port 8000
