# Workflow Implementation Summary

## ✅ 已完成功能

### 1. 后端API实现

**文件**: `src/api/routes/workflow_state.py`

**新增功能**：

#### 异步Workflow执行函数

1. **`_execute_script_workflow(project_id)`**
   - 批量处理所有SRT文件（ep01, ep02, ...）
   - ep01启用Hook检测
   - 使用DeepSeek降低成本
   - 实时广播进度更新
   - 错误处理和日志记录

2. **`_execute_novel_workflow(project_id)`**
   - 处理小说文件（默认前10章）
   - 并行处理3章
   - 使用Claude保证质量
   - 支持系统元素分析
   - 实时进度监控

3. **`_execute_alignment_workflow(project_id)`**
   - 待实现（已预留接口）

#### WebSocket实时通信

- 进度更新广播
- 步骤完成/失败通知
- 心跳监控

---

### 2. 前端UI实现

**文件**: `frontend-new/src/pages/ProjectWorkflowPage.tsx`

**新增功能**：

#### Workflow触发逻辑

```typescript
const handleStartStep = async (stepId: string) => {
  try {
    await workflowStateApi.startStep(projectId, stepId)
    // 显示成功通知
    // 刷新状态
  } catch (error) {
    // 显示错误通知
    // 记录日志
  }
}
```

#### 按钮连接

- Step 2 Script分析 → `onStart={() => handleStartStep('step_2_script')}`
- Step 3 Novel分析 → `onStart={() => handleStartStep('step_3_novel')}`
- Step 4 对齐分析 → `onStart={() => handleStartStep('step_4_alignment')}`

#### 通知系统

- 桌面通知（需要用户授权）
- 错误提示（alert + console）
- WebSocket实时更新

---

## 📋 使用流程

### 步骤1：上传raw文件

1. 进入项目详情页
2. 点击"Step 1: Import"
3. 上传小说文件（novel.txt）和SRT文件（ep01.srt, ep02.srt, ...）
4. 等待自动预处理完成（约1-2分钟）

**预处理内容**：
- ✅ 导入raw文件
- ✅ 编码检测与规范化
- ✅ 章节边界检测（Novel）
- ✅ 元数据提取（Novel）
- ✅ SRT文本提取（Script）

---

### 步骤2：Script分析

1. 进入"Step 2: Script Analysis"页面
2. 点击 **"Start Analysis"** 按钮
3. 等待处理完成

**处理时间**：
- 单集约2-3分钟
- 5集约10-15分钟

**处理内容**：
- ✅ Hook检测（仅ep01）
- ✅ 语义分段
- ✅ ABC类型分类
- ✅ 质量验证

**输出**：
- `data/projects/{project_id}/artifacts/script_segmenter/{episode_name}/result_latest.json`
- `data/projects/{project_id}/artifacts/hook_detector/ep01/result_latest.json`

---

### 步骤3：Novel分析

1. 进入"Step 3: Novel Analysis"页面
2. 点击 **"Start Analysis"** 按钮
3. 等待处理完成

**处理时间**：
- 10章约10-20分钟
- 100章约2-3小时

**处理内容**：
- ✅ 章节分段（Two-Pass）
- ✅ 章节标注（Three-Pass）
- ✅ 系统元素分析
- ✅ 质量验证

**输出**：
- `data/projects/{project_id}/processing/novel/step4_segmentation/chapter_*.json`
- `data/projects/{project_id}/processing/novel/step5_annotation/chapter_*.json`
- `data/projects/{project_id}/processing/novel/reports/*.md`

---

### 步骤4：对齐分析

**状态**: 🚧 待实现

---

## 🎛️ 配置说明

### Script处理配置

```python
ScriptProcessingConfig(
    enable_hook_detection=True,      # ep01启用Hook检测
    enable_hook_analysis=False,      # 暂不启用深度分析（节约成本）
    enable_abc_classification=True,  # 启用ABC类型分类
    segmentation_provider="deepseek", # 使用DeepSeek（速度快、成本低）
    text_extraction_provider="deepseek",
    hook_detection_provider="deepseek",
    min_quality_score=70,            # 最低质量评分
    retry_on_error=True,
    max_retries=3
)
```

### Novel处理配置

```python
NovelProcessingConfig(
    enable_parallel=True,            # 启用并行处理
    max_concurrent_chapters=3,       # 最多同时处理3章
    chapter_range=(1, 10),          # 只处理前10章（测试）
    enable_functional_tags=False,    # 暂不启用功能标签
    enable_system_analysis=True,     # 启用系统元素分析
    segmentation_provider="claude",  # 使用Claude（质量高）
    annotation_provider="claude",
    output_markdown_reports=True,    # 输出Markdown报告
    continue_on_error=True,          # 单章失败继续处理
)
```

---

## 💰 成本估算

### Script处理成本

| 场景 | 成本/集 | 10集总计 |
|------|---------|---------|
| ep01（含Hook） | ~$0.19 | - |
| ep02-10（无Hook） | ~$0.29 | ~$2.61 |
| **总计** | - | **~$2.80** |

**优化建议**：
- 使用DeepSeek替代Claude（当前已实现）
- 关闭Hook深度分析（当前已关闭）
- 批量处理优化API调用

### Novel处理成本

| 场景 | 成本/章 | 10章 | 100章 |
|------|---------|------|-------|
| 分段 + 标注 | ~$0.15 | ~$1.50 | ~$15.00 |

**优化建议**：
- 限制处理范围（当前10章）
- 关闭系统元素追踪（可选）
- 关闭功能标签（当前已关闭）

---

## 🔍 实时监控

### WebSocket消息类型

1. **`connected`** - 连接成功
```json
{
  "type": "connected",
  "project_id": "PROJ_001",
  "message": "WebSocket 连接成功"
}
```

2. **`step_started`** - 步骤开始
```json
{
  "type": "step_started",
  "step_id": "step_2_script",
  "step_name": "Script 分析"
}
```

3. **`progress_update`** - 进度更新
```json
{
  "type": "progress_update",
  "step_id": "step_2_script",
  "progress": 45.5,
  "current_task": "Processing ep03 (3/5)"
}
```

4. **`step_completed`** - 步骤完成
```json
{
  "type": "step_completed",
  "step_id": "step_2_script",
  "message": "Completed 5/5 episodes ($2.80)"
}
```

5. **`step_failed`** - 步骤失败
```json
{
  "type": "step_failed",
  "step_id": "step_2_script",
  "error_message": "Novel file not found"
}
```

---

## 🐛 故障排查

### 问题1：点击按钮没反应

**检查**：
1. 浏览器控制台是否有错误
2. 后端API是否运行（访问 `http://localhost:8000/api/docs`）
3. 依赖是否满足：
   - Step 2需要Step 1完成（Script已导入）
   - Step 3需要Step 1完成（Novel已导入）
   - Step 4需要Step 2和Step 3完成

**解决**：
```bash
# 启动后端API
cd /Users/sevenx/Documents/coding/AI-Narrated\ Recap\ Analyst
python -m src.api.main

# 启动前端
cd frontend-new
npm run dev
```

---

### 问题2：Workflow执行失败

**检查**：
1. 查看`meta.json`中的`error_message`
2. 查看后端日志
3. 检查文件路径是否正确

**常见错误**：

#### "Novel file not found"
- 原因：Novel文件路径不正确
- 解决：检查是否存在以下任一路径：
  - `data/projects/{project_id}/processed/novel/standardized.txt`
  - `data/projects/{project_id}/raw/novel.txt`

#### "No SRT files found"
- 原因：SRT文件路径不正确
- 解决：确保SRT文件在以下位置：
  - `data/projects/{project_id}/raw/srt/*.srt`
  - 或 `data/projects/{project_id}/raw/*.srt`

#### "依赖未满足"
- 原因：前置步骤未完成
- 解决：按顺序完成Step 1 → Step 2/3 → Step 4

---

### 问题3：进度不更新

**检查**：
1. WebSocket连接状态（控制台应有"WebSocket connected"）
2. 后端是否在执行（查看CPU使用率）
3. 浏览器是否支持WebSocket

**解决**：
- 刷新页面重新连接WebSocket
- 使用轮询替代WebSocket（自动降级）
- 检查防火墙设置

---

## 📂 文件结构

### 项目目录结构

```
data/projects/{project_id}/
├── meta.json                    # 项目元数据（含workflow状态）
├── raw/                         # 原始文件
│   ├── novel.txt               # 小说原文
│   └── srt/                    # SRT字幕文件
│       ├── ep01.srt
│       ├── ep02.srt
│       └── ...
├── processed/                   # 预处理结果
│   ├── novel/
│   │   └── standardized.txt    # 规范化后的小说
│   └── script/
│       └── ep01.md             # 提取的脚本文本
├── processing/                  # Workflow中间结果
│   ├── novel/
│   │   ├── step4_segmentation/ # 分段结果
│   │   ├── step5_annotation/   # 标注结果
│   │   └── reports/            # Markdown报告
│   └── script/
│       └── ep01_segmentation.json
└── artifacts/                   # 工具输出（版本化）
    ├── novel_segmenter/
    │   └── chapter_001/
    │       └── result_latest.json
    └── script_segmenter/
        └── ep01/
            └── result_latest.json
```

---

## 🚀 后续优化

### 短期优化（1-2周）

1. **性能优化**
   - [ ] 增加并发数（5章同时处理）
   - [ ] 优化LLM调用（batch请求）
   - [ ] 添加缓存机制

2. **成本优化**
   - [ ] 更多任务使用DeepSeek
   - [ ] 智能降级策略
   - [ ] Token使用优化

3. **用户体验**
   - [ ] 添加进度条详细信息
   - [ ] 支持暂停/恢复
   - [ ] 添加取消功能

### 中期优化（1-2月）

1. **功能增强**
   - [ ] 实现Step 4对齐分析
   - [ ] 支持自定义配置
   - [ ] 添加质量报告页面

2. **稳定性提升**
   - [ ] 添加断点续传
   - [ ] 错误自动恢复
   - [ ] 任务队列管理

3. **监控和日志**
   - [ ] 实时日志流式输出
   - [ ] 性能指标监控
   - [ ] 成本统计分析

---

## 📝 更新日志

### 2026-02-11

**新增**：
- ✅ Script处理workflow执行逻辑
- ✅ Novel处理workflow执行逻辑
- ✅ 前端Start按钮连接
- ✅ WebSocket实时监控
- ✅ 桌面通知支持
- ✅ 错误处理和日志记录

**配置**：
- ✅ Script使用DeepSeek（降低成本）
- ✅ Novel使用Claude（保证质量）
- ✅ 并行处理（3章）
- ✅ 限制范围（前10章）

**文档**：
- ✅ 创建使用指南
- ✅ 创建实现总结
- ✅ API文档更新

---

*最后更新: 2026-02-11*
*作者: AI Assistant*
