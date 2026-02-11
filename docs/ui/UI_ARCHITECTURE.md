# UI架构设计文档

**项目**: AI-Narrated Recap Analyst Web UI  
**版本**: v1.0  
**日期**: 2026-02-10  
**风格**: 极客风 (VSCode/iTerm inspired)

---

## 1. 架构概览

### 1.1 技术栈选择

#### 前端
```yaml
核心框架: React 18 + TypeScript
构建工具: Vite
UI组件: 自定义组件 (极客风格)
状态管理: Zustand (轻量级)
数据请求: TanStack Query (React Query)
实时通信: WebSocket (原生)
图表库: D3.js + Recharts
代码高亮: Monaco Editor (VSCode内核)
终端组件: xterm.js
样式方案: TailwindCSS + CSS Modules
```

#### 后端
```yaml
Web框架: FastAPI 0.109+
异步框架: asyncio + uvicorn
WebSocket: FastAPI WebSocket
数据库: SQLite (本地) + JSON文件存储
缓存: 内存缓存 (functools.lru_cache)
文件处理: 原有的 ProjectManager + ArtifactManager
```

#### DevOps
```yaml
容器化: Docker + Docker Compose
反向代理: Nginx (可选)
进程管理: PM2 (Node.js) + Supervisor (Python)
```

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         浏览器 (Browser)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   React App (Port 5173)                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ Dashboard   │  │ Workflow    │  │ Result      │      │  │
│  │  │ Page        │  │ Runner      │  │ Viewer      │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └───────────────────────────────────────────────────────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│                          HTTP / WS                               │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────┐
│                    FastAPI Server (Port 8000)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      API Routes                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ /api/       │  │ /api/       │  │ /api/       │      │  │
│  │  │ projects    │  │ workflows   │  │ results     │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐                       │  │
│  │  │ /ws/        │  │ /api/       │                       │  │
│  │  │ progress    │  │ artifacts   │                       │  │
│  │  └─────────────┘  └─────────────┘                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Service Layer                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ Project     │  │ Workflow    │  │ Result      │      │  │
│  │  │ Service     │  │ Executor    │  │ Service     │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └───────────────────────────────────────────────────────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Core Layer (现有代码)                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ Tools       │  │ Workflows   │  │ Managers    │      │  │
│  │  │ (17个)      │  │ (3个)       │  │ (LLM/PM)    │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └───────────────────────────────────────────────────────────┘  │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────┐
│                       Data Layer                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  data/projects/                                           │  │
│  │  ├── project_a/                                           │  │
│  │  │   ├── raw/          (原始文件)                        │  │
│  │  │   ├── novel/        (Novel处理结果)                   │  │
│  │  │   ├── script/       (Script处理结果)                  │  │
│  │  │   └── alignment/    (对齐结果)                        │  │
│  │  └── project_b/                                           │  │
│  │                                                            │  │
│  │  output/operation_history.jsonl  (操作日志)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3. 前端架构设计

### 3.1 目录结构

```
frontend-new/
├── src/
│   ├── App.tsx                      # 根组件
│   ├── main.tsx                     # 入口文件
│   │
│   ├── pages/                       # 页面组件
│   │   ├── Dashboard.tsx            # 项目面板
│   │   ├── WorkflowPage.tsx         # 工作流执行页
│   │   ├── ResultPage.tsx           # 结果查看页
│   │   ├── AlignmentPage.tsx        # 对齐分析页
│   │   └── SettingsPage.tsx         # 设置页
│   │
│   ├── components/                  # 可复用组件
│   │   ├── layout/                  # 布局组件
│   │   │   ├── Sidebar.tsx          # 侧边栏
│   │   │   ├── Header.tsx           # 顶部栏
│   │   │   └── Terminal.tsx         # 终端面板
│   │   │
│   │   ├── project/                 # 项目相关
│   │   │   ├── ProjectCard.tsx      # 项目卡片
│   │   │   ├── ProjectList.tsx      # 项目列表
│   │   │   └── CreateProjectModal.tsx
│   │   │
│   │   ├── workflow/                # 工作流相关
│   │   │   ├── WorkflowSelector.tsx # 工作流选择器
│   │   │   ├── FileUploader.tsx     # 文件上传
│   │   │   ├── ConfigPanel.tsx      # 配置面板
│   │   │   └── ProgressMonitor.tsx  # 进度监控
│   │   │
│   │   ├── result/                  # 结果展示
│   │   │   ├── SegmentViewer.tsx    # 分段查看器
│   │   │   ├── AnnotationViewer.tsx # 标注查看器
│   │   │   ├── QualityReport.tsx    # 质量报告
│   │   │   └── TimelineView.tsx     # 时间线视图
│   │   │
│   │   ├── alignment/               # 对齐可视化
│   │   │   ├── SankeyChart.tsx      # 桑基图
│   │   │   ├── CoverageHeatmap.tsx  # 覆盖率热力图
│   │   │   ├── AlignmentTable.tsx   # 对齐表格
│   │   │   └── ComparisonView.tsx   # 对比视图
│   │   │
│   │   └── common/                  # 通用组件
│   │       ├── Button.tsx           # 按钮
│   │       ├── Card.tsx             # 卡片
│   │       ├── Badge.tsx            # 徽章
│   │       ├── Progress.tsx         # 进度条
│   │       ├── Spinner.tsx          # 加载动画
│   │       ├── Modal.tsx            # 模态框
│   │       ├── Tooltip.tsx          # 提示框
│   │       ├── CodeBlock.tsx        # 代码块
│   │       └── JsonViewer.tsx       # JSON查看器
│   │
│   ├── hooks/                       # 自定义Hooks
│   │   ├── useWebSocket.ts          # WebSocket连接
│   │   ├── useWorkflow.ts           # 工作流执行
│   │   ├── useProject.ts            # 项目管理
│   │   ├── useResult.ts             # 结果查询
│   │   └── useTheme.ts              # 主题切换
│   │
│   ├── api/                         # API调用
│   │   ├── client.ts                # Axios实例
│   │   ├── projects.ts              # 项目API
│   │   ├── workflows.ts             # 工作流API
│   │   ├── results.ts               # 结果API
│   │   └── artifacts.ts             # 工件API
│   │
│   ├── store/                       # 状态管理
│   │   ├── projectStore.ts          # 项目状态
│   │   ├── workflowStore.ts         # 工作流状态
│   │   ├── uiStore.ts               # UI状态
│   │   └── settingsStore.ts         # 设置状态
│   │
│   ├── types/                       # TypeScript类型
│   │   ├── project.ts               # 项目类型
│   │   ├── workflow.ts              # 工作流类型
│   │   ├── result.ts                # 结果类型
│   │   └── api.ts                   # API响应类型
│   │
│   ├── utils/                       # 工具函数
│   │   ├── formatters.ts            # 格式化函数
│   │   ├── validators.ts            # 验证函数
│   │   ├── parsers.ts               # 解析函数
│   │   └── constants.ts             # 常量定义
│   │
│   └── styles/                      # 样式文件
│       ├── globals.css              # 全局样式
│       ├── theme.css                # 主题变量
│       └── animations.css           # 动画效果
│
├── public/                          # 静态资源
│   ├── fonts/                       # 等宽字体
│   └── icons/                       # 图标
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 3.2 核心技术选型理由

#### React 18 + TypeScript
- ✅ React 18: 并发渲染，性能优化
- ✅ TypeScript: 类型安全，减少bug
- ✅ 社区成熟，生态丰富

#### Zustand (状态管理)
```typescript
// 轻量级、简洁、无boilerplate
import create from 'zustand'

const useProjectStore = create((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
}))
```

**选择理由**:
- ❌ Redux: 太重，boilerplate多
- ❌ MobX: 学习曲线陡峭
- ✅ Zustand: 简洁、性能好、易上手

#### TanStack Query (数据请求)
```typescript
// 自动缓存、重试、刷新
const { data, isLoading, error } = useQuery({
  queryKey: ['project', projectId],
  queryFn: () => fetchProject(projectId),
})
```

**特性**:
- ✅ 自动缓存管理
- ✅ 请求去重
- ✅ 后台自动刷新
- ✅ 乐观更新

#### D3.js + Recharts (数据可视化)
- **D3.js**: 自定义复杂图表（桑基图、力导向图）
- **Recharts**: 快速实现常规图表（柱状图、饼图）

#### xterm.js (终端组件)
```typescript
// 实时显示工作流日志，极客风格
<Terminal 
  logs={workflowLogs}
  onCommand={(cmd) => handleCommand(cmd)}
/>
```

---

## 4. 后端架构设计

### 4.1 目录结构

```
backend/
├── src/
│   ├── api/                         # FastAPI路由层
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI应用入口
│   │   ├── deps.py                  # 依赖注入
│   │   │
│   │   ├── routes/                  # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── projects.py          # 项目管理API
│   │   │   ├── workflows.py         # 工作流执行API
│   │   │   ├── results.py           # 结果查询API
│   │   │   ├── artifacts.py         # 工件管理API
│   │   │   ├── websocket.py         # WebSocket连接
│   │   │   └── health.py            # 健康检查
│   │   │
│   │   ├── schemas/                 # API数据模型（Pydantic）
│   │   │   ├── __init__.py
│   │   │   ├── project.py           # 项目Schema
│   │   │   ├── workflow.py          # 工作流Schema
│   │   │   ├── result.py            # 结果Schema
│   │   │   └── common.py            # 通用Schema
│   │   │
│   │   ├── services/                # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py   # 项目服务
│   │   │   ├── workflow_executor.py # 工作流执行器
│   │   │   ├── result_service.py    # 结果服务
│   │   │   └── ws_manager.py        # WebSocket管理器
│   │   │
│   │   ├── middleware/              # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── cors.py              # CORS配置
│   │   │   ├── logging.py           # 日志中间件
│   │   │   └── error_handler.py     # 错误处理
│   │   │
│   │   └── utils/                   # 工具函数
│   │       ├── __init__.py
│   │       ├── file_utils.py        # 文件操作
│   │       └── response.py          # 响应格式化
│   │
│   └── (现有代码)
│       ├── core/                    # 核心层（不变）
│       ├── tools/                   # 工具层（不变）
│       ├── workflows/               # 工作流层（不变）
│       └── ...
│
├── tests/                           # 测试
│   ├── api/                         # API测试
│   └── services/                    # 服务测试
│
├── requirements-api.txt             # API依赖
└── Dockerfile
```

### 4.2 FastAPI应用结构

```python
# src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import projects, workflows, results, artifacts, websocket, health
from .middleware import logging_middleware, error_handler

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

# 中间件
app.middleware("http")(logging_middleware)
app.add_exception_handler(Exception, error_handler)

# 路由注册
app.include_router(health.router, prefix="/api/health", tags=["健康检查"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(results.router, prefix="/api/results", tags=["结果查询"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["工件管理"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

# 静态文件服务（生产环境）
# app.mount("/", StaticFiles(directory="dist", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 5. 数据流设计

### 5.1 工作流执行流程

```
┌─────────────┐
│   用户点击   │ 选择Novel工作流，上传novel.txt，配置参数
│  "开始处理" │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│  前端: POST /api/workflows/execute              │
│  Body: {                                        │
│    workflow_type: "novel_processing",           │
│    project_id: "proj_001",                      │
│    config: {                                    │
│      enable_system_analysis: true,              │
│      enable_functional_tags: false,             │
│      max_concurrency: 10                        │
│    }                                            │
│  }                                              │
└─────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│  后端: WorkflowExecutor.execute_async()         │
│  - 创建工作流实例（NovelProcessingWorkflow）     │
│  - 后台执行（asyncio.create_task）              │
│  - 返回 task_id 给前端                          │
└─────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│  前端: WebSocket连接 /ws/progress/{task_id}     │
│  - 建立长连接                                   │
│  - 监听进度更新                                 │
└─────────────────────────────────────────────────┘
       │
       ↓ (工作流执行中)
┌─────────────────────────────────────────────────┐
│  后端: 每个步骤完成时推送进度                    │
│  WS Message: {                                  │
│    task_id: "task_123",                         │
│    stage: "novel_segmentation",                 │
│    progress: 0.45,  // 45%                      │
│    current_step: "处理第5章...",                │
│    token_used: 12543,                           │
│    estimated_cost: 0.15,                        │
│    logs: ["[INFO] 章节分段完成"]                │
│  }                                              │
└─────────────────────────────────────────────────┘
       │
       ↓ (所有步骤完成)
┌─────────────────────────────────────────────────┐
│  后端: 推送完成消息                              │
│  WS Message: {                                  │
│    task_id: "task_123",                         │
│    status: "completed",                         │
│    progress: 1.0,                               │
│    result: {                                    │
│      quality_score: 88,                         │
│      chapters_processed: 10,                    │
│      output_path: "data/projects/proj_001/..."  │
│    }                                            │
│  }                                              │
└─────────────────────────────────────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│  前端: 显示完成通知                              │
│  - 更新UI状态为"已完成"                         │
│  - 显示质量评分                                 │
│  - 提供"查看结果"按钮                           │
└─────────────────────────────────────────────────┘
```

### 5.2 实时进度推送设计

**WebSocket消息格式**:
```typescript
interface ProgressMessage {
  task_id: string
  timestamp: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  
  // 进度信息
  progress: number  // 0.0 - 1.0
  stage: string     // 当前阶段（如 "novel_segmentation"）
  current_step: string  // 当前步骤描述
  
  // 性能指标
  token_used: number
  token_total_estimate: number
  estimated_cost: number
  elapsed_seconds: number
  estimated_remaining_seconds: number
  
  // 日志
  logs: string[]  // 最新的日志行
  
  // 结果（完成时）
  result?: WorkflowResult
  error?: string  // 失败时的错误信息
}
```

**后端实现**:
```python
# src/api/services/ws_manager.py
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
    
    async def broadcast_progress(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            ws = self.active_connections[task_id]
            await ws.send_json(message)
    
    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

ws_manager = WebSocketManager()
```

---

## 6. 极客风格UI设计规范

### 6.1 配色方案

```css
/* src/styles/theme.css */

:root {
  /* 主色调 - 深色主题 */
  --bg-primary: #0d1117;      /* 最深背景（VSCode Dark+） */
  --bg-secondary: #161b22;    /* 次级背景 */
  --bg-tertiary: #21262d;     /* 三级背景（卡片） */
  --bg-hover: #30363d;        /* 悬停背景 */
  
  /* 文本颜色 */
  --text-primary: #c9d1d9;    /* 主要文本 */
  --text-secondary: #8b949e;  /* 次要文本 */
  --text-muted: #6e7681;      /* 弱化文本 */
  --text-inverse: #0d1117;    /* 反色文本 */
  
  /* 强调色 - 参考iTerm2 + Gruvbox */
  --accent-blue: #58a6ff;     /* 信息/链接 */
  --accent-green: #3fb950;    /* 成功/完成 */
  --accent-yellow: #d29922;   /* 警告/进行中 */
  --accent-red: #f85149;      /* 错误/失败 */
  --accent-purple: #bc8cff;   /* 特殊/高亮 */
  --accent-cyan: #39c5cf;     /* 辅助强调 */
  
  /* 边框 */
  --border-default: #30363d;
  --border-muted: #21262d;
  
  /* 终端配色（类似iTerm2 Gruvbox Dark） */
  --terminal-bg: #1d2021;
  --terminal-fg: #ebdbb2;
  --terminal-cursor: #fabd2f;
  --terminal-selection: #504945;
  
  --terminal-ansi-black: #282828;
  --terminal-ansi-red: #cc241d;
  --terminal-ansi-green: #98971a;
  --terminal-ansi-yellow: #d79921;
  --terminal-ansi-blue: #458588;
  --terminal-ansi-magenta: #b16286;
  --terminal-ansi-cyan: #689d6a;
  --terminal-ansi-white: #a89984;
  
  /* 字体 */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Menlo', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  
  /* 间距 */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
}
```

### 6.2 字体规范

```css
/* 等宽字体 - 代码/数据展示 */
.mono {
  font-family: var(--font-mono);
  font-variant-ligatures: common-ligatures; /* 连字支持 */
  font-feature-settings: 'liga' 1, 'calt' 1;
}

/* 无衬线字体 - 普通文本 */
.sans {
  font-family: var(--font-sans);
}

/* 字号 */
.text-xs { font-size: 0.75rem; }   /* 12px */
.text-sm { font-size: 0.875rem; }  /* 14px */
.text-base { font-size: 1rem; }    /* 16px */
.text-lg { font-size: 1.125rem; }  /* 18px */
.text-xl { font-size: 1.25rem; }   /* 20px */
```

### 6.3 组件样式示例

#### 卡片组件
```css
.card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all 0.2s ease;
}

.card:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 1px var(--accent-blue);
}
```

#### 按钮组件
```css
.btn {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
  background: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.btn-primary {
  background: var(--accent-blue);
  color: var(--text-inverse);
  border: none;
}

.btn-primary:hover {
  background: #4a8ed6;
}
```

#### 终端组件
```css
.terminal {
  background: var(--terminal-bg);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--terminal-fg);
  overflow-y: auto;
  max-height: 400px;
}

.terminal-line {
  margin: 0.25rem 0;
  line-height: 1.5;
}

.terminal-line.info { color: var(--terminal-ansi-cyan); }
.terminal-line.success { color: var(--terminal-ansi-green); }
.terminal-line.warning { color: var(--terminal-ansi-yellow); }
.terminal-line.error { color: var(--terminal-ansi-red); }
```

---

## 7. 性能优化策略

### 7.1 前端优化

1. **代码分割 (Code Splitting)**
```typescript
// 路由级别懒加载
const Dashboard = lazy(() => import('./pages/Dashboard'))
const WorkflowPage = lazy(() => import('./pages/WorkflowPage'))
const ResultPage = lazy(() => import('./pages/ResultPage'))
```

2. **虚拟滚动**
```typescript
// 大量数据列表使用react-window
import { FixedSizeList } from 'react-window'

<FixedSizeList
  height={600}
  itemCount={segmentations.length}
  itemSize={120}
>
  {SegmentRow}
</FixedSizeList>
```

3. **缓存策略**
```typescript
// TanStack Query 缓存配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5分钟
      cacheTime: 10 * 60 * 1000,  // 10分钟
      refetchOnWindowFocus: false,
    },
  },
})
```

### 7.2 后端优化

1. **异步处理**
```python
# 工作流执行使用后台任务
@router.post("/workflows/execute")
async def execute_workflow(workflow_config: WorkflowConfig):
    task_id = generate_task_id()
    
    # 后台执行，立即返回task_id
    asyncio.create_task(
        workflow_executor.run_async(task_id, workflow_config)
    )
    
    return {"task_id": task_id, "status": "started"}
```

2. **结果缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_project_result(project_id: str, result_type: str):
    """缓存项目结果，避免重复读取文件"""
    return load_result_from_disk(project_id, result_type)
```

3. **流式响应**
```python
# 大文件下载使用流式传输
@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    file_path = get_artifact_path(artifact_id)
    
    return StreamingResponse(
        file_stream(file_path),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={artifact_id}.json"}
    )
```

---

## 8. 安全性考虑

### 8.1 文件上传安全

```python
# 文件类型验证
ALLOWED_EXTENSIONS = {".txt", ".srt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_upload(file: UploadFile):
    # 检查文件扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "不支持的文件类型")
    
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    size = file.file.tell()
    file.file.seek(0)  # 重置指针
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "文件过大")
    
    return True
```

### 8.2 路径遍历防护

```python
from pathlib import Path

def safe_join(base_dir: str, *paths: str) -> Path:
    """安全拼接路径，防止路径遍历攻击"""
    base = Path(base_dir).resolve()
    target = (base / Path(*paths)).resolve()
    
    # 确保目标路径在base_dir内
    if not target.is_relative_to(base):
        raise ValueError("非法路径")
    
    return target
```

### 8.3 CORS配置

```python
# 生产环境需要严格限制
origins = [
    "http://localhost:5173",  # 开发环境
    "http://localhost:4173",  # 预览环境
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## 9. 部署架构

### 9.1 开发环境

```bash
# 前端（Vite Dev Server）
cd frontend
npm run dev  # http://localhost:5173

# 后端（Uvicorn）
cd backend
uvicorn src.api.main:app --reload --port 8000
```

### 9.2 生产环境（Docker Compose）

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

**构建镜像**:
```bash
docker-compose build
docker-compose up -d
```

---

## 10. 监控与日志

### 10.1 日志系统

```python
# 结构化日志
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_workflow_start(self, task_id: str, workflow_type: str):
        self.logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "workflow_start",
            "task_id": task_id,
            "workflow_type": workflow_type,
        }))
    
    def log_workflow_progress(self, task_id: str, progress: float, stage: str):
        self.logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "workflow_progress",
            "task_id": task_id,
            "progress": progress,
            "stage": stage,
        }))
```

### 10.2 性能监控

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录慢请求
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")
    
    return response
```

---

## 11. 未来扩展

### 11.1 多用户支持（V2.0）

- 用户认证（JWT）
- 项目权限管理
- 工作空间隔离

### 11.2 云端部署（V2.0）

- S3存储工件
- RDS存储元数据
- Redis缓存
- Kubernetes编排

### 11.3 高级功能（V3.0）

- 工作流编排可视化（拖拽式）
- 自定义工具链
- A/B测试平台
- 数据分析看板

---

**文档版本**: v1.0  
**最后更新**: 2026-02-10  
**维护者**: AI-Narrated Recap Analyst Team
