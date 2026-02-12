# Workflow Execution Guide

## 概述

本文档说明如何在前端UI中触发和监控workflow处理流程。

## 🔄 已实现功能

### 1️⃣ **自动预处理（Preprocess）**

**触发方式**：上传raw文件后自动执行

**处理内容**：
- Novel: 导入 → 编码检测 → 章节检测 → 元数据提取
- Script: 导入 → SRT解析 → 文本提取（带LLM标点修复）

**状态查看**：
- `meta.json` 中的 `workflow_stages.preprocess`
- 前端 Step 1 页面显示导入状态

---

### 2️⃣ **Script处理Workflow (Step 2)**

**触发方式**：
1. 进入 `/project/{projectId}/workflow/step_2_script`
2. 点击 **"Start Analysis"** 按钮

**处理内容**（按集数处理）：
- Phase 1: SRT导入与规范化
- Phase 2: 文本提取与智能修复
- Phase 3: Hook边界检测（仅ep01）
- Phase 4: Hook内容分析（可选）
- Phase 5: 脚本语义分段
- Phase 6: ABC类型分类
- Phase 7: 质量验证

**配置**：
```python
ScriptProcessingConfig(
    enable_hook_detection=True,      # ep01启用
    enable_hook_analysis=False,      # 暂不启用深度分析
    enable_abc_classification=True,  # 启用ABC分类
    segmentation_provider="deepseek", # DeepSeek降低成本
    min_quality_score=70
)
```

**成本估算**：
- ep01（含Hook）: ~$0.19
- ep02-10（无Hook）: ~$0.29/集
- 10集总计: ~$2.80

**输出位置**：
```
data/projects/{project_id}/
├── processing/
│   └── script/
│       ├── ep01_segmentation.json
│       ├── ep01_hook.json
│       └── ...
└── artifacts/
    └── script_segmenter/
        └── {episode_name}/
            └── result_latest.json
```

---

### 3️⃣ **Novel处理Workflow (Step 3)**

**触发方式**：
1. 进入 `/project/{projectId}/workflow/step_3_novel`
2. 点击 **"Start Analysis"** 按钮

**处理内容**（按章节并行处理）：
- Step 1: 小说导入与规范化
- Step 2: 提取小说元数据
- Step 3: 检测章节边界
- Step 4: 章节并行分段（Two-Pass）
- Step 5: 章节并行标注（Three-Pass）
- Step 6: 全书系统元素分析
- Step 7: 章节系统元素检测与追踪
- Step 8: 质量验证与报告生成

**配置**：
```python
NovelProcessingConfig(
    enable_parallel=True,
    max_concurrent_chapters=3,        # 并发3章
    chapter_range=(1, 10),           # 处理前10章
    enable_functional_tags=False,    # 暂不启用功能标签
    enable_system_analysis=True,     # 启用系统分析
    segmentation_provider="claude",  # 使用Claude保证质量
    annotation_provider="claude",
    output_markdown_reports=True,
    continue_on_error=True
)
```

**成本估算**：
- 单章成本: ~$0.15
- 10章总计: ~$1.50
- 100章总计: ~$15.00

**输出位置**：
```
data/projects/{project_id}/
├── processing/
│   └── novel/
│       ├── step4_segmentation/
│       │   └── chapter_001.json
│       ├── step5_annotation/
│       │   └── chapter_001.json
│       └── reports/
│           └── step4_segmentation_report.md
└── artifacts/
    └── novel_segmenter/
        └── chapter_001/
            └── result_latest.json
```

---

### 4️⃣ **对齐Workflow (Step 4)**

**状态**：🚧 待实现

**触发方式**：
1. 进入 `/project/{projectId}/workflow/step_4_alignment`
2. 点击 **"Start Analysis"** 按钮

**前置依赖**：
- Step 2 (Script处理) 已完成
- Step 3 (Novel处理) 已完成

---

## 📊 实时监控

### WebSocket连接

前端自动建立WebSocket连接，接收实时更新：

```typescript
const ws = workflowStateApi.createWebSocket(projectId)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  switch (data.type) {
    case 'step_started':
      // 步骤开始
      break
    case 'progress_update':
      // 进度更新
      break
    case 'step_completed':
      // 步骤完成
      break
    case 'step_failed':
      // 步骤失败
      break
  }
}
```

### 状态轮询

如果WebSocket不可用，使用轮询机制（2-10秒间隔）：

```typescript
const { data } = useQuery({
  queryKey: ['workflow-state', projectId],
  queryFn: () => workflowStateApi.getWorkflowState(projectId),
  refetchInterval: (query) => {
    const hasRunningStep = /* 检查是否有步骤在运行 */
    return hasRunningStep ? 2000 : 10000
  }
})
```

---

## 🎛️ API端点

### 获取workflow状态

```
GET /api/v2/projects/{project_id}/workflow-state
```

**响应**：
```json
{
  "phase_name": "Phase I: Analyst Agent",
  "overall_status": "running",
  "overall_progress": 45.0,
  "step_1_import": { ... },
  "step_2_script": { ... },
  "step_3_novel": { ... },
  "step_4_alignment": { ... }
}
```

### 启动步骤

```
POST /api/v2/projects/{project_id}/workflow/{step_id}/start
```

**step_id**: `step_1_import` | `step_2_script` | `step_3_novel` | `step_4_alignment`

**响应**：
```json
{
  "message": "步骤 Script 分析 已启动",
  "step_id": "step_2_script"
}
```

### WebSocket连接

```
WS ws://localhost:8000/api/v2/projects/{project_id}/ws
```

**消息格式**：
```json
{
  "type": "progress_update",
  "step_id": "step_2_script",
  "progress": 45.5,
  "current_task": "Processing ep03 (3/5)",
  "timestamp": "2026-02-11T10:30:00"
}
```

---

## 🔧 故障排查

### 问题1：点击"Start"按钮没有反应

**检查**：
1. 浏览器控制台是否有错误
2. 后端API是否正常运行（`http://localhost:8000/docs`）
3. 项目依赖是否满足（Step 2需要先完成Step 1）

### 问题2：Workflow执行失败

**检查**：
1. 查看 `meta.json` 中的 `error_message` 字段
2. 查看后端日志（`python src/api/main.py` 的输出）
3. 检查raw文件是否存在且格式正确

### 问题3：进度不更新

**检查**：
1. WebSocket连接是否正常（控制台应有"WebSocket connected"日志）
2. 后端是否在执行（查看CPU使用率）
3. 尝试手动刷新页面

---

## 📋 使用流程

### 完整流程示例

1. **创建项目**
   ```
   POST /api/v2/projects
   {
     "name": "test_project",
     "description": "测试项目"
   }
   ```

2. **上传raw文件**
   ```
   POST /api/v2/projects/{project_id}/files
   - novel.txt (小说)
   - ep01.srt, ep02.srt, ... (脚本)
   ```

3. **等待自动预处理完成**
   - 导入raw文件
   - 检测章节
   - 提取元数据
   - 提取SRT文本

4. **启动Script处理**
   - 进入Step 2页面
   - 点击"Start Analysis"
   - 等待处理完成（约2-5分钟/集）

5. **启动Novel处理**
   - 进入Step 3页面
   - 点击"Start Analysis"
   - 等待处理完成（约10-30分钟/10章）

6. **启动对齐分析**
   - 进入Step 4页面
   - 点击"Start Analysis"
   - 等待处理完成

---

## 🚀 优化建议

### 成本优化

1. **使用DeepSeek代替Claude**（节约70%成本）
   - Script处理：DeepSeek v3.2
   - Novel元数据提取：DeepSeek
   - Novel分段/标注：Claude（保证质量）

2. **限制处理范围**
   - 测试时：只处理前10章、前3集
   - 生产时：逐步增加范围

3. **关闭可选功能**
   - `enable_functional_tags=False`
   - `enable_hook_analysis=False`
   - `enable_system_analysis=False`（如不需要系统元素追踪）

### 性能优化

1. **并行处理**
   - `max_concurrent_chapters=3`（Novel）
   - 批量处理多集Script

2. **断点续传**
   - 失败后从中断处继续
   - 使用`resume_from_step`参数

3. **后台处理**
   - 使用异步任务队列
   - 避免阻塞用户界面

---

*最后更新: 2026-02-11*
