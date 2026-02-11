# UI系统文档总览

**项目**: AI-Narrated Recap Analyst Web UI  
**版本**: v1.0  
**状态**: 设计完成，待实施  
**日期**: 2026-02-10

---

## 📚 文档索引

### 核心文档

| 文档 | 说明 | 阅读时长 |
|------|------|---------|
| **[QUICKSTART.md](QUICKSTART.md)** ⭐ | 快速启动指南 - 从0到运行 | 15分钟 |
| **[UI_ARCHITECTURE.md](UI_ARCHITECTURE.md)** | UI架构设计 - 技术栈与系统架构 | 30分钟 |
| **[API_SPECIFICATION.md](API_SPECIFICATION.md)** | API接口规范 - 完整的REST API文档 | 45分钟 |
| **[UI_DESIGN_GEEK_STYLE.md](UI_DESIGN_GEEK_STYLE.md)** | 极客风格UI设计 - 配色/组件/交互 | 30分钟 |
| **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** | 实施计划 - 4周开发路线图 | 20分钟 |

---

## 🚀 快速开始

### 1分钟了解项目

**这是什么？**
- 一个 **极客风格** 的Web UI系统
- 为 **AI-Narrated Recap Analyst** 项目提供可视化界面
- 技术栈: **React + FastAPI + WebSocket + D3.js**

**核心功能**:
- ✅ 项目管理 (创建、上传、删除)
- ✅ 工作流执行 (Novel/Script处理、对齐分析)
- ✅ 实时进度监控 (WebSocket推送)
- ✅ 结果可视化 (分段、标注、对齐关系)
- ✅ 数据导出 (JSON/PDF/Excel)

**视觉风格**:
- 🎨 深色主题 (Gruvbox配色)
- 💻 终端美学 (xterm.js集成)
- ⌨️ 快捷键优先 (Ctrl+K, Ctrl+P等)
- 📊 数据密度高 (实时指标、日志流)

---

### 5分钟快速启动

```bash
# 1. 安装依赖
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install

# 2. 启动后端
uvicorn src.api.main:app --reload --port 8000

# 3. 启动前端
npm run dev

# 4. 访问
open http://localhost:5173
```

**详细步骤**: 查看 [QUICKSTART.md](QUICKSTART.md)

---

## 📖 文档阅读指南

### 对于开发者

**我是前端工程师**:
1. 先读 [QUICKSTART.md](QUICKSTART.md) - 搭建环境
2. 再读 [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) - 了解架构
3. 参考 [UI_DESIGN_GEEK_STYLE.md](UI_DESIGN_GEEK_STYLE.md) - 实现UI
4. 遵循 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 按周开发

**我是后端工程师**:
1. 先读 [QUICKSTART.md](QUICKSTART.md) - 搭建环境
2. 再读 [API_SPECIFICATION.md](API_SPECIFICATION.md) - 实现API
3. 参考 [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) - 理解数据流
4. 遵循 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 按周开发

**我是全栈工程师**:
1. 快速浏览所有文档（2小时）
2. 重点关注 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
3. 按优先级逐周实现功能

### 对于设计师

**我想了解UI设计**:
1. 直接阅读 [UI_DESIGN_GEEK_STYLE.md](UI_DESIGN_GEEK_STYLE.md)
2. 查看配色方案、组件设计、交互规范
3. 参考ASCII原型图

### 对于项目经理

**我想了解项目进度**:
1. 阅读 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
2. 查看里程碑和交付物
3. 评估风险和时间线

---

## 🎯 项目概览

### 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   浏览器 (Browser)                   │
│  ┌───────────────────────────────────────────────┐  │
│  │  React + TypeScript + TailwindCSS             │  │
│  │  Zustand + TanStack Query + xterm.js + D3.js  │  │
│  └─────────────────┬─────────────────────────────┘  │
│                    │ HTTP / WebSocket                │
└────────────────────┼─────────────────────────────────┘
                     │
┌────────────────────┼─────────────────────────────────┐
│             FastAPI Server (Port 8000)               │
│  ┌─────────────────────────────────────────────┐    │
│  │  /api/projects  /api/workflows  /ws/progress│    │
│  │  /api/results   /api/artifacts              │    │
│  └─────────────────┬───────────────────────────┘    │
│                    │                                 │
│  ┌─────────────────────────────────────────────┐    │
│  │  现有Workflow: NovelProcessingWorkflow      │    │
│  │               ScriptProcessingWorkflow      │    │
│  │  现有Tools: 17个处理工具                    │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

### 开发周期

```
Week 1 (2/11-2/17): 基础架构 + 项目管理
  ├─ 前后端项目初始化
  ├─ UI组件库搭建
  └─ 项目CRUD功能

Week 2 (2/18-2/24): 工作流执行 + 进度监控
  ├─ 工作流启动与配置
  ├─ WebSocket实时通信
  └─ 终端日志展示

Week 3 (2/25-3/3): 结果查看 + 对齐可视化
  ├─ Novel/Script结果查看
  ├─ 桑基图对齐可视化
  └─ 工件管理

Week 4 (3/4-3/10): 优化 + 测试 + 部署
  ├─ 性能优化
  ├─ 用户体验优化
  ├─ E2E测试
  └─ Docker部署
```

### 核心页面

| 页面 | 路由 | 功能 |
|------|------|------|
| Dashboard | `/` | 项目列表、创建项目、搜索 |
| Workflow | `/workflow` | 选择工作流、配置参数、启动 |
| Progress | `/workflow/:taskId` | 实时进度、日志、指标 |
| Result (Novel) | `/result/:projectId/novel` | 分段结果、标注数据、质量报告 |
| Result (Script) | `/result/:projectId/script` | Hook检测、分段结果、质量报告 |
| Alignment | `/alignment/:projectId` | 桑基图、覆盖率热力图、对齐表格 |
| Artifacts | `/artifacts` | 工件列表、下载、删除 |
| Settings | `/settings` | LLM配置、用户偏好 |

---

## 💡 设计亮点

### 极客风格

**配色** (Gruvbox Dark):
- 背景: #0d1117 (深色，护眼)
- 文本: #c9d1d9 (高对比度)
- 强调: 蓝/绿/黄/红/紫/青 (6色系统)

**字体**:
- 等宽字体: JetBrains Mono (支持连字)
- 代码/数据: 全部使用等宽
- 清晰易读

**终端组件**:
- xterm.js实时日志流
- ANSI颜色支持
- 类iTerm2体验

### 实时监控

**WebSocket推送**:
- 进度更新 (0.45 → 0.50 → ... → 1.0)
- Token消耗 (实时统计)
- 预估成本 (动态计算)
- 日志流 (逐行推送)

**性能指标**:
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Token消耗   │ 预估成本    │ 已用时间    │ 预计剩余    │
│ 12,543      │ $0.15       │ 2分15秒     │ 1分15秒     │
│ / 18,000    │             │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### 数据可视化

**桑基图** (D3.js):
- Novel段落 → Script句子
- 改写策略用颜色区分
- 置信度用线宽表示

**覆盖率热力图** (Recharts):
- 事件覆盖率 (85%)
- 设定覆盖率 (100%)
- 按章节/集数统计

---

## 🔧 技术选型

### 前端

| 类别 | 技术 | 理由 |
|------|------|------|
| 框架 | React 18 | 成熟、生态丰富、并发渲染 |
| 类型 | TypeScript | 类型安全、减少bug |
| 构建 | Vite | 快速HMR、ESM原生支持 |
| 状态 | Zustand | 轻量级、简洁、无boilerplate |
| 请求 | TanStack Query | 自动缓存、重试、刷新 |
| 样式 | TailwindCSS | 原子化CSS、快速开发 |
| 终端 | xterm.js | VSCode同款、功能强大 |
| 图表 | D3.js + Recharts | D3复杂图、Recharts常规图 |

### 后端

| 类别 | 技术 | 理由 |
|------|------|------|
| 框架 | FastAPI | 异步、高性能、自动文档 |
| 服务器 | Uvicorn | ASGI服务器、WebSocket支持 |
| 数据校验 | Pydantic | 类型安全、自动验证 |
| WebSocket | FastAPI WS | 原生支持、简单易用 |

### DevOps

| 类别 | 技术 | 理由 |
|------|------|------|
| 容器化 | Docker | 环境一致、易部署 |
| 编排 | Docker Compose | 多容器管理、网络配置 |
| 反向代理 | Nginx | 高性能、静态文件服务 |

---

## 📊 开发进度

### 当前状态: 设计完成 ✅

- [x] UI架构设计
- [x] API接口设计
- [x] 实施计划制定
- [x] 快速启动文档
- [x] 极客风格设计

### 下一步: 开始开发 🚀

**Week 1任务** (2/11 - 2/17):
- [ ] 前端项目初始化
- [ ] 后端API框架搭建
- [ ] UI组件库实现
- [ ] 项目管理功能

**预计完成**: 2026-03-10 (4周后)

---

## 🤝 贡献指南

### 开发流程

1. **阅读文档**: 先读完所有文档
2. **搭建环境**: 按 [QUICKSTART.md](QUICKSTART.md) 操作
3. **创建分支**: `git checkout -b feature/ui-system`
4. **遵循规范**: 参考 `docs/DEV_STANDARDS.md`
5. **提交PR**: 清晰的commit message

### 代码规范

**前端**:
- ESLint + Prettier格式化
- TypeScript严格模式
- 组件命名: PascalCase
- 文件命名: kebab-case

**后端**:
- Ruff (Linter)
- Black (Formatter)
- Type Hints必填
- Docstring必写

### 测试要求

- 单元测试覆盖率 > 70%
- 关键路径集成测试
- E2E测试核心流程

---

## 📞 联系方式

**问题反馈**:
- 查看 [常见问题](QUICKSTART.md#5-常见问题)
- 提交Issue到GitHub

**技术讨论**:
- 项目Wiki
- 技术文档评论区

---

## 📝 更新日志

### v1.0 (2026-02-10)
- ✅ 完成UI架构设计
- ✅ 完成API接口设计
- ✅ 完成实施计划
- ✅ 完成极客风格设计
- ✅ 完成快速启动文档

### 待办事项
- [ ] 前端项目实现 (Week 1-2)
- [ ] 后端API实现 (Week 1-2)
- [ ] 可视化组件 (Week 3)
- [ ] 测试与优化 (Week 4)
- [ ] Docker部署 (Week 4)

---

## 🎉 总结

这是一个**完整的UI系统设计文档包**，涵盖:

✅ **架构设计** - 前后端技术栈、系统架构、数据流  
✅ **API规范** - 完整的REST API + WebSocket协议  
✅ **UI设计** - 极客风格配色、组件、交互、动画  
✅ **实施计划** - 4周开发路线图、任务拆分、风险管理  
✅ **快速启动** - 从0到运行的完整指南  

**总阅读时长**: 约2小时  
**总代码量**: 预计 10,000+ 行 (前端6000 + 后端4000)  
**开发周期**: 4周 (1人全栈) / 2周 (前后端分工)

---

**准备好了吗？**

👉 从 [QUICKSTART.md](QUICKSTART.md) 开始你的开发之旅！

---

**文档版本**: v1.0  
**最后更新**: 2026-02-10  
**维护者**: AI-Narrated Recap Analyst Team
