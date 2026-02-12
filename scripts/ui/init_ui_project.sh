#!/bin/bash

# UI项目快速初始化脚本
# 作用: 一键创建前后端项目结构
# 使用: ./scripts/ui/init_ui_project.sh

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        echo "  macOS: brew install $2"
        echo "  Linux: sudo apt-get install $2"
        exit 1
    fi
}

# 主函数
main() {
    print_header "AI-Narrated Recap Analyst - UI项目初始化"
    
    print_info "开始初始化UI项目..."
    
    # 1. 检查依赖
    print_header "步骤 1/5: 检查依赖"
    
    print_info "检查 Node.js..."
    check_command "node" "node@18"
    print_success "Node.js 已安装: $(node --version)"
    
    print_info "检查 npm..."
    check_command "npm" "node@18"
    print_success "npm 已安装: $(npm --version)"
    
    print_info "检查 Python..."
    check_command "python3" "python3"
    print_success "Python 已安装: $(python3 --version)"
    
    print_info "检查 pip..."
    check_command "pip3" "python3-pip"
    print_success "pip 已安装: $(pip3 --version)"
    
    # 2. 创建前端项目
    print_header "步骤 2/5: 创建前端项目"
    
    if [ -d "frontend" ]; then
        print_warning "frontend/ 目录已存在，跳过创建"
    else
        print_info "使用 Vite 创建 React + TypeScript 项目..."
        npm create vite@latest frontend -- --template react-ts
        print_success "前端项目创建完成"
    fi
    
    # 3. 安装前端依赖
    print_header "步骤 3/5: 安装前端依赖"
    
    cd frontend
    
    print_info "安装核心依赖..."
    npm install react-router-dom zustand @tanstack/react-query axios
    
    print_info "安装UI库和工具..."
    npm install xterm d3 recharts date-fns clsx
    
    print_info "安装TailwindCSS..."
    npm install -D tailwindcss postcss autoprefixer
    npx tailwindcss init -p
    
    print_info "安装类型定义..."
    npm install -D @types/d3
    
    print_info "安装测试工具..."
    npm install -D vitest @testing-library/react @testing-library/jest-dom
    
    print_success "前端依赖安装完成"
    
    cd ..
    
    # 4. 配置TailwindCSS
    print_header "步骤 4/5: 配置TailwindCSS"
    
    cat > frontend/tailwind.config.js << 'EOF'
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
EOF
    
    # 更新 index.css
    cat > frontend/src/index.css << 'EOF'
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

body {
  min-height: 100vh;
}
EOF
    
    print_success "TailwindCSS配置完成"
    
    # 5. 创建后端项目结构
    print_header "步骤 5/5: 创建后端项目结构"
    
    print_info "创建API目录..."
    mkdir -p src/api/routes
    mkdir -p src/api/schemas
    mkdir -p src/api/services
    mkdir -p src/api/middleware
    
    # 创建 __init__.py
    touch src/api/__init__.py
    touch src/api/routes/__init__.py
    touch src/api/schemas/__init__.py
    touch src/api/services/__init__.py
    touch src/api/middleware/__init__.py
    
    # 创建FastAPI入口
    cat > src/api/main.py << 'EOF'
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
EOF
    
    # 创建requirements-api.txt
    cat > requirements-api.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6
python-dotenv==1.0.0
websockets==12.0
EOF
    
    print_info "安装后端依赖..."
    pip3 install -r requirements-api.txt
    
    print_success "后端项目结构创建完成"
    
    # 6. 创建启动脚本
    print_header "创建启动脚本"
    
    mkdir -p scripts/ui
    
    cat > scripts/ui/dev.sh << 'EOF'
#!/bin/bash

# 开发环境启动脚本

echo "🚀 启动开发环境..."

# 启动后端
echo "📡 启动后端服务 (Port 8000)..."
cd "$(dirname "$0")/../.."
uvicorn src.api.main:app --reload --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 2

# 启动前端
echo "🎨 启动前端服务 (Port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务已启动:"
echo "  - 后端: http://localhost:8000"
echo "  - API文档: http://localhost:8000/api/docs"
echo "  - 前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号
trap "echo ''; echo '🛑 停止所有服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" EXIT INT TERM

# 等待
wait
EOF
    
    chmod +x scripts/ui/dev.sh
    
    print_success "启动脚本创建完成"
    
    # 7. 完成
    print_header "初始化完成！"
    
    echo ""
    print_success "项目结构已创建完成！"
    echo ""
    print_info "项目结构:"
    echo "  frontend/           # React前端项目"
    echo "  src/api/            # FastAPI后端API"
    echo "  scripts/ui/dev.sh   # 开发环境启动脚本"
    echo ""
    print_info "下一步:"
    echo "  1. 启动开发环境:"
    echo "     ${GREEN}./scripts/ui/dev.sh${NC}"
    echo ""
    echo "  2. 访问应用:"
    echo "     前端: ${BLUE}http://localhost:5173${NC}"
    echo "     API文档: ${BLUE}http://localhost:8000/api/docs${NC}"
    echo ""
    echo "  3. 阅读文档:"
    echo "     ${BLUE}docs/ui/README.md${NC}"
    echo ""
    print_success "祝开发顺利！🚀"
    echo ""
}

# 运行主函数
main
