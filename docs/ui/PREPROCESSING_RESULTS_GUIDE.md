# 预处理结果查看指南

## 📋 问题：上传文件后，处理结果在哪里？

### ✅ 解决方案

上传raw文件后，系统会**自动执行预处理**，处理结果保存在多个位置：

---

## 🎯 预处理流程

### 1️⃣ **上传raw文件**

**位置**: `data/projects/{project_id}/raw/`

```
raw/
├── novel/
│   └── 序列公路求生.txt      # 小说原文
└── srt/
    ├── ep01.srt             # SRT字幕
    ├── ep02.srt
    └── ...
```

### 2️⃣ **自动预处理执行**

**触发时机**: 上传完成后立即执行

**处理内容**:

#### Novel预处理
- ✅ 编码检测与统一（UTF-8）
- ✅ 章节边界检测
- ✅ 元数据提取（标题、作者、标签、简介）
- ✅ 生成章节索引

#### Script预处理
- ✅ SRT格式验证
- ✅ 文本提取（移除时间轴）
- ✅ LLM智能添加标点符号
- ✅ 实体标准化

**处理时间**:
- Novel: 30-60秒
- Script: 1-2分钟/集

---

## 📂 处理结果位置

### Novel处理结果

**目录**: `data/projects/{project_id}/processed/novel/`

```
processed/novel/
├── chapters.json          # ⭐ 章节索引（重要）
├── metadata.json          # ⭐ 元数据（标题、作者、标签、简介）
└── standardized.txt       # 规范化后的小说文本
```

#### 📄 `chapters.json` 内容示例

```json
{
  "total_chapters": 50,
  "chapters": [
    {
      "chapter_number": 1,
      "title": "第一章 末日降临",
      "start_line": 1,
      "end_line": 245,
      "word_count": 2847
    },
    {
      "chapter_number": 2,
      "title": "第二章 公路求生",
      "start_line": 246,
      "end_line": 512,
      "word_count": 3102
    }
  ]
}
```

#### 📄 `metadata.json` 内容示例

```json
{
  "title": "序列公路求生：我在末日升级物资",
  "author": "作者名",
  "tags": ["末日", "公路", "升级流", "系统"],
  "description": "末日降临，主角在公路上求生...",
  "genre": "科幻",
  "word_count": 142350
}
```

---

### Script处理结果

**目录**: `data/projects/{project_id}/processed/script/`

```
processed/script/
├── ep01.md               # ⭐ 提取的文本（Markdown格式）
├── ep02.md
├── ep03.md
└── ...
```

#### 📄 `ep01.md` 内容示例

```markdown
# Episode 01

收音机里传来消息，上沪市彻底沦陷了。

那是在上一周的时候，一场规模庞大的沙尘暴席卷了整个华国，接着世界各地诡异生物开始爆发。

人类彻底被打懵了，到处是诡异生物屠杀人类的场面...
```

---

## 🖥️ 在前端查看结果

### 方式1：通过Step 1页面

1. 进入 **Step 1: Import** 页面
2. 上传文件后，自动显示**预处理状态横幅**：
   - ✅ 绿色 √ = 预处理完成
   - 🔵 旋转图标 = 正在处理
   - ⏰ 时钟图标 = 等待处理

3. 点击 **"View Results"** 按钮查看：
   - **Novel**: 查看`chapters.json`（章节索引）
   - **Script**: 查看`processed/script`目录（所有集数）

### 方式2：通过浏览器直接访问

#### 查看Novel章节索引
```
http://localhost:8000/api/v2/projects/{project_id}/files/processed/novel/chapters.json
```

#### 查看Novel元数据
```
http://localhost:8000/api/v2/projects/{project_id}/files/processed/novel/metadata.json
```

#### 查看Script文本
```
http://localhost:8000/api/v2/projects/{project_id}/files/processed/script/ep01.md
```

#### 列出processed目录
```
http://localhost:8000/api/v2/projects/{project_id}/files/processed/novel
```

---

## 🔍 状态检查

### 方法1：查看meta.json

```json
// data/projects/{project_id}/meta.json

{
  "workflow_stages": {
    "preprocess": {
      "status": "completed",  // ✅ 预处理完成
      "started_at": "2026-02-11T18:41:59",
      "completed_at": "2026-02-11T18:46:09",
      "tasks": [
        {
          "task_id": "novel",
          "task_type": "novel",
          "status": "completed",
          "progress": "50 chapters detected"
        },
        {
          "task_id": "ep01",
          "task_type": "script",
          "status": "completed",
          "progress": "3675 chars processed"
        }
      ]
    }
  },
  "sources": {
    "has_novel": true,
    "has_script": true,
    "novel_chapters": 50,
    "script_episodes": 5
  }
}
```

### 方法2：查看前端UI

**预处理状态横幅** - Step 1页面顶部：

```
┌─────────────────────────────────────────────────┐
│ ✅ Auto Preprocessing Completed                 │
│ 6 files processed                               │
│                                    [View Results]│
│                                                  │
│ ✅ Novel: 序列公路求生.txt - 50 chapters detected│
│ ✅ Script: ep01.srt - 3675 chars processed      │
│ ✅ Script: ep02.srt - 1591 chars processed      │
└─────────────────────────────────────────────────┘
```

---

## ❓ 常见问题

### Q1: 上传后没有自动处理？

**检查**：
1. 后端API是否运行（`http://localhost:8000/api/health`）
2. 上传时是否勾选了"Auto preprocess"（默认开启）
3. 查看后端日志是否有错误

**手动触发预处理**：
```bash
# 使用Python脚本手动触发
python -c "
from src.workflows.preprocess_service import PreprocessService
service = PreprocessService()
result = service.preprocess_project('PROJ_001')
print(result)
"
```

---

### Q2: 预处理失败怎么办？

**查看错误信息**：
```json
// meta.json
{
  "workflow_stages": {
    "preprocess": {
      "status": "failed",
      "error_message": "Novel file not found"  // ← 错误原因
    }
  }
}
```

**常见错误及解决**：

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Novel file not found` | 找不到.txt文件 | 确保文件在`raw/novel/`或`raw/`目录 |
| `No SRT files found` | 找不到.srt文件 | 确保文件在`raw/srt/`或`raw/`目录 |
| `Chapter detection failed` | 章节格式不规范 | 检查章节标题格式（第X章） |
| `LLM API timeout` | LLM调用超时 | 检查网络，稍后重试 |

---

### Q3: 如何查看完整的原始文件？

**Novel原文**：
```
http://localhost:8000/api/v2/projects/{project_id}/files/view?filename=序列公路求生.txt&category=novel
```

**SRT字幕**：
```
http://localhost:8000/api/v2/projects/{project_id}/files/view?filename=ep01.srt&category=srt
```

---

### Q4: 下一步是什么？

预处理完成后，可以执行更深入的分析：

**Step 2: Script Analysis** → 语义分段、Hook检测、ABC分类
- 进入: `/project/{project_id}/workflow/step_2_script`
- 点击: **"Start Analysis"**
- 时间: 约10-15分钟（5集）
- 成本: ~$2.80

**Step 3: Novel Analysis** → 章节分段、标注、系统分析
- 进入: `/project/{project_id}/workflow/step_3_novel`
- 点击: **"Start Analysis"**
- 时间: 约10-20分钟（前10章）
- 成本: ~$1.50

---

## 📊 预处理vs深度分析对比

| 阶段 | 预处理（Auto） | 深度分析（Step 2/3） |
|-----|--------------|------------------|
| **触发** | 上传后自动 | 手动点击"Start" |
| **处理** | 基础格式化 | LLM深度分析 |
| **时间** | 1-2分钟 | 10-30分钟 |
| **成本** | $0.00 | $2-5 |
| **Novel** | 章节检测、元数据 | 分段、标注、系统分析 |
| **Script** | 文本提取、标点 | 语义分段、Hook检测、ABC分类 |

---

## 🎯 快速开始

### 上传文件 → 查看结果（3步）

1. **上传文件**
   ```
   访问: http://localhost:5173/project/PROJ_001/workflow/step_1_import
   点击: "Upload Files"
   选择: novel.txt + ep01.srt, ep02.srt, ...
   ```

2. **等待预处理**（1-2分钟）
   - 页面自动刷新
   - 横幅显示 ✅ "Auto Preprocessing Completed"

3. **查看结果**
   - 点击 **"View Results"** 按钮
   - 或访问: `http://localhost:8000/api/v2/projects/PROJ_001/files/processed/novel/chapters.json`

---

*最后更新: 2026-02-11*
*相关文档: [WORKFLOW_EXECUTION_GUIDE.md](WORKFLOW_EXECUTION_GUIDE.md)*
