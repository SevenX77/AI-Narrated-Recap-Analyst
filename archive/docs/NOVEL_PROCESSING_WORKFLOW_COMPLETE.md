# 小说处理完整Workflow（从0开始）

**更新日期**: 2026-02-08  
**版本**: v3.2（R1模型为主）  
**状态**: ✅ 当前正确流程

---

## 📋 前置条件

### 1. 模型配置（重要！）

**配置文件**: `src/core/config.py`

```python
# 双模型支持：R1为主（阅读理解优先），V3 Fallback
primary_model: str = "deepseek-reasoner"   # DeepSeek R1（主模型）✅
fallback_model: str = "deepseek-chat"      # DeepSeek V3（备用）✅
enable_fallback: bool = True
```

**为什么R1为主？**
- 小说分段是**阅读理解任务**，需要深度推理
- R1的推理能力远超V3，分段更准确
- V3容易过度聚合（如把3段合成1段）

### 2. 原始数据准备

```
分析资料/有原小说/01_末哥超凡公路/
└── novel/
    └── novel.txt  ← 原始小说文本（逐行格式）
```

---

## 🔄 完整处理流程

### 流程图

```
原始小说 (分析资料/)
    ↓
[Step 1] 数据摄入
    ↓
raw/novel.txt
    ↓
[Step 2] 简介提取 + LLM过滤
    ↓
novel/chpt_0000_简介.md
    ↓
[Step 3] 功能段分析（R1模型）
    直接从 raw/novel.txt 读取章节并分析
    ↓
functional_analysis/
├── chpt_XXXX_functional_analysis_latest.json
├── 第X章完整分段分析.md
└── history/
    └── chpt_XXXX_functional_analysis_vXXXXXX.json
```

**⚠️ 注意**: 
- ❌ **不需要** 生成 `novel/chpt_0001.md` 等单章文件（冗余）
- ✅ **直接** 从 `raw/novel.txt` 读取并分析
- ✅ 功能段分析已经包含了更精细的分段

---

## 📝 各步骤详解

### Step 1: 数据摄入

**工具**: 手动复制（或使用迁移脚本）

**操作**:
```bash
cp "分析资料/有原小说/01_末哥超凡公路/novel/novel.txt" \
   "data/projects/with_novel/末哥超凡公路/raw/novel.txt"
```

**输出**:
- `data/projects/with_novel/末哥超凡公路/raw/novel.txt`

---

### Step 2: 简介提取 + LLM过滤

**工具**: `MetadataExtractor(use_llm=True)`

**文件**: `src/tools/novel_chapter_processor.py`

**功能**:
1. 提取书名、作者、标签
2. **LLM过滤简介**（去除封面链接、"又有书名"、分隔符等）
3. 输出纯净简介

**执行方式**:
```python
from src.tools.novel_chapter_processor import MetadataExtractor

extractor = MetadataExtractor(use_llm=True)
metadata = extractor.execute(novel_text)
```

**输出**:
- `novel/chpt_0000_简介.md` ✅ 纯净简介
- `metadata.json` （书名、作者、标签）

**示例输出**:
```markdown
# 序列公路求生：我在末日升级物资

## 简介

诡异降临，城市成了人类禁区。
人们只能依靠序列超凡不停的迁徙，定居生活方式变成了迁徙生活方式。

在迁徙的过程之中，陈野觉醒了升级系统。
生锈的自行车在他手中蜕变为装甲战车。
破旧帐篷进化成移动堡垒。
...
```

**⚠️ 常见错误**:
- ❌ 使用简单正则提取 `content[:first_chapter.start()]`
- ✅ 必须使用 `MetadataExtractor(use_llm=True)`

---

### Step 3: 功能段分析（核心步骤）

**工具**: `NovelChapterAnalyzer()`

**文件**: `src/tools/novel_chapter_analyzer.py`

**模型**: **DeepSeek R1**（`deepseek-reasoner`）✅

**功能**:
1. **LLM驱动的语义分段**（不是规则分段）
2. 多维度标签提取：
   - 叙事功能（故事推进、核心设定、关键道具等）
   - 叙事结构（钩子、伏笔、回应伏笔等）
   - 角色关系（人物塑造、对立关系等）
   - 浓缩优先级（P0-骨架、P1-血肉、P2-皮肤）
3. 浓缩建议（保留什么、删除什么）
4. 章节级摘要和洞察

**执行方式**:
```python
import re
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager

# 1. 读取原始小说
with open('raw/novel.txt', 'r', encoding='utf-8') as f:
    novel_text = f.read()

# 2. 识别章节（从 raw/novel.txt 直接提取）
chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
matches = list(re.finditer(chapter_pattern, novel_text))

# 3. 初始化分析器（使用R1模型）
analyzer = NovelChapterAnalyzer()

# 4. 逐章分析
for i, match in enumerate(matches):
    chapter_number = int(match.group(1))
    chapter_title = match.group(2).strip()
    
    # 提取章节内容
    start_pos = match.end()
    end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(novel_text)
    chapter_content = novel_text[start_pos:end_pos].strip()
    
    # 分析
    analysis = analyzer.execute(
        chapter_content=chapter_content,
        chapter_number=chapter_number,
        chapter_title=chapter_title
    )
    
    # 保存（使用ArtifactManager进行版本管理）
    ArtifactManager.save_artifact(
        content=analysis.model_dump(mode='json'),
        artifact_type=f"chpt_{chapter_number:04d}_functional_analysis",
        project_id="末哥超凡公路",
        base_dir=str(analysis_dir),
        extension="json"
    )
```

**关键点**:
- ✅ **直接从 `raw/novel.txt` 读取**，不需要预先生成单章文件
- ✅ 使用正则识别章节边界
- ✅ 逐章提取内容并分析
- ✅ 不产生冗余的中间文件

**输出**:
1. **JSON文件**（机器可读）:
   ```
   functional_analysis/
   ├── chpt_0001_functional_analysis_latest.json ← 最新版本指针
   ├── chpt_0002_functional_analysis_latest.json
   └── history/
       ├── chpt_0001_functional_analysis_v20260208_052641.json ← 时间戳版本
       └── chpt_0002_functional_analysis_v20260208_053012.json
   ```

2. **Markdown文件**（人类可读）:
   ```
   novel/
   ├── 第1章完整分段分析.md
   ├── 第2章完整分段分析.md
   └── ...
   ```
   
   **⚠️ 注意**: Markdown文件输出到 `novel/` 目录，JSON文件输出到 `novel/functional_analysis/` 目录

**JSON数据结构**:
```json
{
  "chapter_id": "chpt_001",
  "chapter_number": 1,
  "chapter_title": "车队第一铁律",
  "segments": [
    {
      "segment_id": "func_seg_chpt_001_01",
      "title": "段落1：开篇钩子（广播）",
      "content": "原文内容...",
      "tags": {
        "narrative_function": ["故事推进", "核心故事设定(首次)"],
        "structure": ["钩子-悬念制造"],
        "character": ["人物塑造-陈野"],
        "priority": "P0-骨架",
        "location": "车队",
        "time": "2030年10月13日上午"
      },
      "metadata": {
        "word_count": 185,
        "contains_first_appearance": true,
        "repetition_items": ["不要前往"],
        "foreshadowing": {
          "type": "埋设",
          "content": "红月、影子、死者复活规则",
          "reference": null
        }
      },
      "condensation_suggestion": "保留：时间、上沪沦陷、三条生存规则..."
    }
  ],
  "chapter_summary": {
    "total_segments": 11,
    "p0_count": 4,
    "p1_count": 5,
    "p2_count": 2,
    "key_events": ["上沪沦陷", "系统觉醒", "升级决定"],
    "foreshadowing_planted": ["掉队必死"],
    "foreshadowing_paid_off": []
  },
  "structure_insight": {
    "narrative_rhythm": "前慢后快，第9段转折",
    "emotional_arc": "绝望→惊喜→希望",
    "turning_points": ["系统觉醒（段落9）"]
  },
  "analyzed_at": "2026-02-08T05:26:41.826Z",
  "version": "20260208_052641"
}
```

**Markdown格式示例**:
```markdown
# 第1章 - 车队第一铁律

**功能段数**: 11
**P0段落**: 4
**P1段落**: 5
**P2段落**: 2

---

## 段落1：开篇钩子（广播）

**ID**: `func_seg_chpt_001_01`

**叙事功能**: 故事推进, 核心故事设定(首次)
**叙事结构**: 钩子-悬念制造
**优先级**: P0-骨架
**地点**: 车队
**时间**: 2030年10月13日上午

### 📄 内容

"滋滋……现在的时间是2030年10月13日上午10:23。"
...

### 💡 浓缩建议

保留：时间、上沪沦陷、三条生存规则...
删除：广播的戏剧性措辞...
```

---

## 🔧 版本管理规范

### 策略：Latest Pointer + 时间戳版本

**主目录**（只有 `_latest.json`）:
```
functional_analysis/
├── chpt_0001_functional_analysis_latest.json  ← 指向最新版本
├── chpt_0002_functional_analysis_latest.json
└── ...
```

**history/ 目录**（所有历史版本）:
```
functional_analysis/history/
├── chpt_0001_functional_analysis_v20260208_052641.json
├── chpt_0001_functional_analysis_v20260208_043012.json (旧版本)
└── ...
```

**实现工具**: `src/core/artifact_manager.py`

```python
# ✅ 正确用法
ArtifactManager.save_artifact(
    content=analysis_dict,
    artifact_type="chpt_0001_functional_analysis",
    project_id="末哥超凡公路",
    base_dir=str(analysis_dir),
    extension="json"
)

# ❌ 错误：不要自己实现版本管理！
```

---

## 🚨 常见错误与避免方法

### 错误1：使用V3而不是R1

**症状**: 分段过度聚合（把3段合成1段）

**原因**:
```python
# ❌ 错误配置
primary_model: str = "deepseek-chat"  # V3
```

**修复**:
```python
# ✅ 正确配置
primary_model: str = "deepseek-reasoner"  # R1
```

### 错误2：简介未清理

**症状**: 简介包含"又有书名"、封面链接、分隔符

**原因**:
```python
# ❌ 错误：使用正则
intro = content[:first_chapter.start()].strip()
```

**修复**:
```python
# ✅ 正确：使用MetadataExtractor
extractor = MetadataExtractor(use_llm=True)
metadata = extractor.execute(novel_text)
intro = metadata['novel']['introduction']
```

### 错误3：自定义版本管理

**症状**: 主目录有 `_vXXXXXX.json` 文件，没有 `history/` 目录

**原因**:
```python
# ❌ 错误：自己实现
def save_with_version(...):
    versioned_file = f"chpt_{num}_v{timestamp}.json"
    latest_file = f"chpt_{num}_latest.json"
    # 保存到同一目录
```

**修复**:
```python
# ✅ 正确：使用ArtifactManager
ArtifactManager.save_artifact(...)
```

### 错误4：使用废弃工具

**废弃工具**:
- ❌ `NovelSegmentationTool`（规则分段，已归档）
- ❌ `process_novel_v3.py`（错误实现，已废弃）

**正确工具**:
- ✅ `NovelChapterAnalyzer`（LLM分段）
- ✅ `process_novel_v3_refactored.py`（或重命名为 `process_novel_v3.py`）

---

## 📊 质量验证清单

### 简介检查

```python
# 读取简介
with open('novel/chpt_0000_简介.md', 'r') as f:
    intro = f.read()

# 验证
assert '又有书名' not in intro  # ✅ 不包含
assert '【' not in intro        # ✅ 不包含标签
assert 'Title:' not in intro    # ✅ 不包含元信息
assert '[封面:' not in intro    # ✅ 不包含封面
assert '====' not in intro      # ✅ 不包含分隔符
```

### 分段检查

```python
# 读取第1章分析
with open('functional_analysis/chpt_0001_functional_analysis_latest.json', 'r') as f:
    analysis = json.load(f)

# 验证
seg1 = analysis['segments'][0]
print(f"第1段字数: {seg1['metadata']['word_count']}")

# 第1段应该只包含广播，不包含世界观和主角行动
assert '几个月前' not in seg1['content']  # ✅ 不应该在第1段
assert '从江城逃出来' not in seg1['content']  # ✅ 不应该在第1段
```

### 版本管理检查

```bash
# 主目录应该只有 _latest.json
ls functional_analysis/*.json | grep -v latest
# 输出应该为空 ✅

# history/ 应该包含所有版本
ls functional_analysis/history/*.json | wc -l
# 输出应该 > 0 ✅
```

---

## 🎯 完整执行脚本

推荐使用：`scripts/process_novel_v3_refactored.py`

**特点**:
- ✅ 使用 `MetadataExtractor`（LLM过滤）
- ✅ 使用 `NovelChapterProcessor`（章节拆分）
- ✅ 使用 `NovelChapterAnalyzer`（功能分析，R1模型）
- ✅ 使用 `ArtifactManager`（版本管理）

**执行**:
```bash
cd "/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst"
python3 scripts/process_novel_v3_refactored.py
```

**单章测试**:
```bash
python3 scripts/test_refactored_process.py
```

---

## 📚 相关文档

- `docs/DEV_STANDARDS.md` - 工具列表和架构规范
- `docs/architecture/logic_flows.md` - 系统架构和数据流
- `docs/NOVEL_SEGMENTATION_METHODOLOGY.md` - 分段方法论
- `src/prompts/novel_chapter_functional_analysis.yaml` - 分析Prompt
- `src/core/artifact_manager.py` - 版本管理实现

---

**最后更新**: 2026-02-08  
**维护者**: AI Assistant  
**版本**: v3.2（R1模型为主）
