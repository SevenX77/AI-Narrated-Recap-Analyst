from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 导入路由
from src.api.routes import projects, workflows, projects_v2, workflow_state, analyst_results

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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177", "http://localhost:5178", "http://localhost:5179", "http://localhost:5180"],  # Vite开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# ... (existing imports)

# 注册路由
app.include_router(projects.router, prefix="/api/projects", tags=["Projects (V1)"])
app.include_router(projects_v2.router, prefix="/api/v2/projects", tags=["Projects (V2)"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(workflow_state.router, prefix="/api/v2/projects", tags=["Workflow State"])
app.include_router(analyst_results.router, tags=["Analyst Results"])

# 静态文件服务 (用于访问生成的 Markdown 文件)
# 确保 data 目录存在
os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

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
