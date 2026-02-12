# Phase I Analyst Workflow 实施文档

**创建时间**: 2026-02-11  
**状态**: 🚧 核心架构已完成，详细页面开发中

---

## 🎯 设计目标

重新设计项目界面，将侧边栏改为基于流程的工作流管理界面，展示 Phase I Analyst Agent 的 4 个步骤：

1. **步骤 1**: 文件导入与标准化
2. **步骤 2**: Script 分析 (7个Phase)
3. **步骤 3**: Novel 分析 (8个Step)
4. **步骤 4**: Script-Novel 对齐 (句子级)

---

## ✅ 已完成工作

### 1. 后端架构 (100% 完成)

#### 1.1 Schema 定义 (`src/core/schemas_project.py`)

新增 Phase I 工作流状态定义：

- ✅ `PhaseStatus` 枚举：locked/ready/running/completed/failed/cancelled
- ✅ `DependencyCheck`：依赖检查结果
- ✅ `SubTaskProgress`：子任务进度
- ✅ `PhaseStepState`：步骤状态基类
- ✅ `Step1ImportState`：文件导入状态（扩展字段：novel_imported, script_episodes 等）
- ✅ `Step2ScriptAnalysisState`：Script 分析状态（episodes_status）
- ✅ `Step3NovelAnalysisState`：Novel 分析状态（novel_steps）
- ✅ `Step4AlignmentState`：对齐状态（alignment_pairs）
- ✅ `PhaseIAnalystState`：Phase I 完整状态
- ✅ `ProjectMeta.initialize_phase_i()`：初始化方法

#### 1.2 API 接口 (`src/api/routes/workflow_state.py`)

新增 Workflow State Management API：

- ✅ `GET /api/v2/projects/{project_id}/workflow-state` - 获取工作流状态
- ✅ `POST /api/v2/projects/{project_id}/workflow/{step_id}/start` - 启动步骤
- ✅ `POST /api/v2/projects/{project_id}/workflow/{step_id}/complete` - 完成步骤
- ✅ `POST /api/v2/projects/{project_id}/workflow/{step_id}/fail` - 失败步骤
- ✅ `POST /api/v2/projects/{project_id}/workflow/{step_id}/progress` - 更新进度
- ✅ `WS /api/v2/projects/{project_id}/ws` - WebSocket 实时连接

**关键特性**：
- ✅ 自动依赖检查（步骤依赖未满足时自动锁定）
- ✅ 状态自动更新（完成步骤后解锁后续步骤）
- ✅ WebSocket 实时广播（进度、日志、事件）
- ✅ ConnectionManager 管理多个客户端连接

---

### 2. 前端架构 (70% 完成)

#### 2.1 类型定义 (`frontend-new/src/types/workflow.ts`)

- ✅ `PhaseStatus` 类型
- ✅ `PhaseStepState` 及各步骤扩展接口
- ✅ `PhaseIAnalystState` 完整状态
- ✅ `WebSocketMessage` 联合类型（支持 8 种消息类型）

#### 2.2 API 客户端 (`frontend-new/src/api/workflowState.ts`)

- ✅ `getWorkflowState()` - 获取工作流状态
- ✅ `startStep()` - 启动步骤
- ✅ `completeStep()` - 完成步骤
- ✅ `failStep()` - 失败步骤
- ✅ `updateProgress()` - 更新进度
- ✅ `createWebSocket()` - 创建 WebSocket 连接

#### 2.3 核心组件

**WorkflowSidebar** (`frontend-new/src/components/workflow/WorkflowSidebar.tsx`)  
✅ 已完成

- 流程图样式（风格 A）
- 状态图标和颜色编码
- 步骤卡片（显示进度、质量评分、错误信息）
- 子任务展开/收起
- 连接线可视化
- 统计信息（LLM 调用、成本、时间）

**ProjectDashboard** (`frontend-new/src/components/workflow/ProjectDashboard.tsx`)  
✅ 已完成

- 整体进度卡片（4 个关键指标）
- 步骤摘要卡片网格（2x2 布局）
- 下一步操作提示
- 点击卡片跳转到步骤详情

**ProjectWorkflowPage** (`frontend-new/src/pages/ProjectWorkflowPage.tsx`)  
✅ 已完成

- 左右分栏布局（侧边栏 + 主内容区）
- WebSocket 实时连接和事件处理
- 桌面通知集成（任务完成/失败）
- 自动轮询（有运行中步骤时每 5 秒刷新）
- 路由集成（支持 `/project/:projectId/workflow/:stepId`）

#### 2.4 路由配置 (`frontend-new/src/App.tsx`)

- ✅ `/project/:projectId` - 显示工作流首页（Dashboard）
- ✅ `/project/:projectId/workflow` - 工作流页面
- ✅ `/project/:projectId/workflow/:stepId` - 步骤详情页

---

## 🚧 待完成工作

### 3. 步骤详细页面 (0% 完成)

需要创建 4 个步骤的详细操作页面：

#### 3.1 Step1ImportPage

**文件**: `frontend-new/src/components/workflow/steps/Step1ImportPage.tsx`

**设计要求**：
- 复用现有 `ProjectDetailPage` 的文件上传组件
- 左右分栏：Novel 文件 | Script 文件
- 实时日志输出
- 操作按钮：重新上传、预览内容、查看元数据、删除
- 自动触发标准化处理

#### 3.2 Step2ScriptAnalysisPage

**文件**: `frontend-new/src/components/workflow/steps/Step2ScriptAnalysisPage.tsx`

**设计要求**：
- 集数列表（ep01-ep05）
- 每集显示 7 个 Phase 的进度：
  1. SRT 导入
  2. 文本提取
  3. Hook 检测（仅 ep01）
  4. Hook 分析（可选）
  5. 语义分段
  6. ABC 分类
  7. 质量验证
- 实时日志输出（包括 LLM 思考过程）
- 配置选项（LLM 模型、并发、Hook 开关）
- 成本统计

#### 3.3 Step3NovelAnalysisPage

**文件**: `frontend-new/src/components/workflow/steps/Step3NovelAnalysisPage.tsx`

**设计要求**：
- 显示 8 个 Step 的进度：
  1. 小说导入
  2. 提取元数据
  3. 检测章节边界
  4. 章节并行分段
  5. 章节并行标注（事件时间线）
  6. 全书系统元素分析
  7. 系统元素追踪
  8. 质量验证
- 关键指标卡片（章节数、段落数、事件数、设定数、系统元素数）
- 实时日志输出
- 并行处理进度可视化

#### 3.4 Step4AlignmentPage

**文件**: `frontend-new/src/components/workflow/steps/Step4AlignmentPage.tsx`

**设计要求** (重要！)：
- **句子级对齐**（不是段落级）
- **左右分栏对应展示**：
  - 左侧：Script 句子
  - 右侧：Novel 段落
- **非线性对齐可视化**：
  - Script 句子对应 Novel 第 10 段 → 第 10 段需要颜色标注，并在原位置留空档
  - 未对应的 Novel 段落保持显示（不省略）
- **匹配度进度条**（0-100%）
- **改编策略标签**（exact/paraphrase/summarize/expand）
- **ABC 类型一致性检查**
- **统计报告**（事件覆盖率、设定覆盖率）

---

### 4. LogViewer 组件 (0% 完成)

**文件**: `frontend-new/src/components/workflow/LogViewer.tsx`

**设计要求**：
- 实时日志输出（WebSocket 推送）
- 自动滚动到最新日志
- 日志级别过滤（info/warning/error）
- LLM 思考过程展示（可折叠）
  - Prompt 摘要
  - Response 摘要
  - Token 消耗
  - 耗时
- 日志搜索和高亮
- 导出日志功能

---

### 5. 桑基图可视化 (0% 完成)

**文件**: `frontend-new/src/components/workflow/AlignmentSankeyDiagram.tsx`

**技术选型**：
- 推荐使用 `react-flow` 或 `d3-sankey`

**设计要求**：
- Novel 段落 → Script 句子的流向图
- 粗细表示匹配度（≥90%: 粗线, 70-89%: 中线, <70%: 虚线）
- 颜色表示类型（A 类: 蓝色, B 类: 绿色, C 类: 紫色）
- 灰色节点表示未覆盖内容
- 交互：悬停显示详细信息，点击跳转到详细对比

---

## 📊 进度总结

| 模块 | 状态 | 完成度 |
|------|------|--------|
| **后端架构** | ✅ 完成 | 100% |
| 　└─ Schema 定义 | ✅ 完成 | 100% |
| 　└─ API 接口 | ✅ 完成 | 100% |
| 　└─ WebSocket | ✅ 完成 | 100% |
| **前端核心** | ✅ 完成 | 100% |
| 　└─ 类型定义 | ✅ 完成 | 100% |
| 　└─ API 客户端 | ✅ 完成 | 100% |
| 　└─ WorkflowSidebar | ✅ 完成 | 100% |
| 　└─ ProjectDashboard | ✅ 完成 | 100% |
| 　└─ ProjectWorkflowPage | ✅ 完成 | 100% |
| 　└─ 路由配置 | ✅ 完成 | 100% |
| 　└─ 桌面通知 | ✅ 完成 | 100% |
| **步骤详细页** | 🚧 待开发 | 0% |
| 　└─ Step1ImportPage | 🚧 待开发 | 0% |
| 　└─ Step2ScriptAnalysisPage | 🚧 待开发 | 0% |
| 　└─ Step3NovelAnalysisPage | 🚧 待开发 | 0% |
| 　└─ Step4AlignmentPage | 🚧 待开发 | 0% |
| **辅助组件** | 🚧 待开发 | 0% |
| 　└─ LogViewer | 🚧 待开发 | 0% |
| 　└─ AlignmentSankeyDiagram | 🚧 待开发 | 0% |

**整体完成度**: **约 60%**（核心架构完成，详细实现待开发）

---

## 🚀 下一步开发计划

### 优先级 P0（必须完成）

1. **Step1ImportPage** (预计 2-3 小时)
   - 复用现有文件上传组件
   - 集成实时日志输出

2. **Step2ScriptAnalysisPage** (预计 4-5 小时)
   - 7 个 Phase 进度展示
   - 集成 LogViewer 组件

3. **Step3NovelAnalysisPage** (预计 3-4 小时)
   - 8 个 Step 进度展示
   - 关键指标卡片

4. **Step4AlignmentPage** (预计 6-8 小时) ⚠️ 最复杂
   - 句子级对齐展示
   - 非线性可视化
   - 左右分栏对应

### 优先级 P1（强烈建议）

5. **LogViewer 组件** (预计 3-4 小时)
   - 实时日志流
   - LLM 思考过程展示

### 优先级 P2（可选）

6. **桑基图可视化** (预计 6-8 小时)
   - 需要调研可视化库
   - 交互设计

---

## 🎨 设计规范

### 颜色编码

- **Locked**: 灰色 (`text-muted-foreground`)
- **Ready**: 蓝色 (`text-blue-500`)
- **Running**: 黄色 (`text-yellow-500`)
- **Completed**: 绿色 (`text-green-500`)
- **Failed**: 红色 (`text-red-500`)

### 图标使用

- Locked: `<Lock />`
- Ready: `<Clock />`
- Running: `<Loader2 className="animate-spin" />`
- Completed: `<CheckCircle />`
- Failed: `<XCircle />`

### 进度条

- 高度: `h-2` (Dashboard), `h-1.5` (Sidebar)
- 颜色: 自动根据主题色

---

## 📚 相关文档

- [Script Processing Workflow](./script_processing_workflow.md)
- [Novel Processing Workflow](./novel_processing_workflow.md)
- [Workflow ROADMAP](./ROADMAP.md)
- [DEV_STANDARDS](../DEV_STANDARDS.md)

---

**最后更新**: 2026-02-11  
**维护者**: Cursor AI Agent  
**状态**: ✅ 核心架构完成，等待详细页面实现
