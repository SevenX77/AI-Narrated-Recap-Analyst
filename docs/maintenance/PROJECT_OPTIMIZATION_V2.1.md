# 项目结构优化 v2.1

**日期**: 2026-02-05  
**版本**: v2.1  
**基于**: v2.0  
**状态**: ✅ 完成

---

## 📋 优化概览

### 优化目标

在 v2.0 的基础上进一步优化：

1. **目录分离**: raw/ 仅存原始文件，novel/ 存处理后的章节文件
2. **章节拆分**: 简介单独文件（chpt_0000.txt），正文按10章一组分文件
3. **元数据增强**: 提取标签到 metadata.json

---

## 🏗️ 新的目录结构

### 完整结构

```
data/projects/with_novel/末哥超凡公路/
├── raw/                              # 原始文件（未处理）
│   ├── novel.txt                     # 原始小说文本（逐行格式）
│   ├── ep01.srt                      # 原始字幕
│   ├── ep02.srt
│   └── ...
│
├── novel/                            # 处理后的小说（新增）
│   ├── chpt_0000.txt                 # 简介（仅正文，无标题作者）
│   ├── chpt_0001-0010.txt            # 第1-10章
│   ├── chpt_0011-0020.txt            # 第11-20章
│   ├── chpt_0021-0030.txt            # 第21-30章
│   ├── ...
│   └── processing_report.json        # 章节处理报告
│
├── alignment/
├── analysis/
├── ground_truth/
└── metadata.json                     # 项目元数据（含标签）
```

### 与 v2.0 的差异

| 项目 | v2.0 | v2.1 (优化后) |
|------|------|--------------|
| raw/novel.txt | 已分段处理 | **原始逐行格式** ✅ |
| 处理后的小说 | raw/ 目录 | **独立 novel/ 目录** ✅ |
| 章节组织 | 单一文件 | **按10章拆分多文件** ✅ |
| 简介 | 混在正文中 | **独立 chpt_0000.txt** ✅ |
| 标签 | 无 | **提取到 metadata.json** ✅ |

---

## 📂 文件说明

### 1. raw/novel.txt

**内容**: 原始小说文本（保持从源文件拷贝的原始格式）

```
[封面: https://...]

Title: 序列公路求生：我在末日升级物资
Author: 山海呼啸
====================

简介:
【题材新颖+非无脑爽文+...】
诡异降临，城市成了人类禁区。
...
```

**用途**: 
- 作为原始数据备份
- 可用于重新处理或验证

### 2. novel/chpt_0000.txt

**内容**: 仅包含简介正文（不含标题、作者、标签）

```
诡异降临，城市成了人类禁区。

人们只能依靠序列超凡不停的迁徙，定居生活方式变成了迁徙生活方式。

在迁徙的过程之中，陈野觉醒了升级系统。
...
```

**格式**: 自然段落（段内连续，段间双空行）

### 3. novel/chpt_0001-0010.txt

**内容**: 第1-10章的完整内容

```
=== 第1章 车队第一铁律 ===

"滋滋……现在的时间是2030年10月13日上午10:23。"

"这或许是本电台最后一次广播！"...

=== 第2章 ... ===

...
```

**格式**: 自然段落（段内连续，段间双空行）

### 4. novel/processing_report.json

**内容**: 章节处理详情

```json
{
  "total_chapters": 50,
  "introduction_file": "chpt_0000.txt",
  "chapter_files": [
    "chpt_0001-0010.txt",
    "chpt_0011-0020.txt",
    ...
  ],
  "chapters_per_file": 10,
  "metadata": {
    "title": "序列公路求生：我在末日升级物资",
    "author": "山海呼啸",
    "tags": ["题材新颖", "非无脑爽文", ...]
  }
}
```

### 5. metadata.json

**增强的元数据** (项目根目录)

```json
{
  "project_name": "末哥超凡公路",
  "category": "with_novel",
  "novel": {
    "title": "序列公路求生：我在末日升级物资",
    "author": "山海呼啸",
    "tags": [
      "题材新颖",
      "非无脑爽文",
      "非无敌",
      "序列魔药",
      "诡异",
      "公路求生",
      "升级物资",
      "心狠手辣"
    ],
    "introduction": "诡异降临，城市成了人类禁区...",
    "chapters": {
      "total": 50,
      "files": {
        "chpt_0000.txt": "简介",
        "chpt_0001-0010.txt": "第1-10章",
        "chpt_0011-0020.txt": "第11-20章",
        ...
      }
    }
  }
}
```

---

## 🔧 技术实现

### 新增工具

#### 1. NovelChapterProcessor

**文件**: `src/tools/novel_chapter_processor.py`

**功能**:
- 解析小说结构（元数据 + 章节）
- 提取简介（chpt_0000.txt）
- 按章节分组（每10章一个文件）
- 生成章节文件（chpt_XXXX-YYYY.txt）

**核心方法**:

```python
class NovelChapterProcessor(BaseTool):
    def execute(self, novel_text: str, output_dir: Path) -> Dict:
        # 1. 解析结构
        metadata, chapters = self._parse_novel_structure(novel_text)
        
        # 2. 生成简介文件
        self._write_introduction(output_dir / "chpt_0000.txt", metadata.introduction)
        
        # 3. 章节分组
        chapter_groups = self._group_chapters(chapters)
        
        # 4. 写入章节文件
        for group in chapter_groups:
            self._write_chapter_file(output_dir / group.filename, group.content)
```

**章节识别模式**:
- `^===\s*第\s*(\d+)\s*章\s*(.*)===`  → `=== 第1章 标题 ===`
- `^第\s*([零一二...]+)\s*章[：:\s]+(.*)`  → `第一章：标题`

#### 2. MetadataExtractor

**文件**: `src/tools/novel_chapter_processor.py`

**功能**:
- 从小说文本提取标题、作者
- 解析标签（从 `【标签1+标签2+...】` 格式）
- 提取简介正文

**标签提取**:

```python
pattern = r'【([^】]+)】'
# 匹配: 【题材新颖+非无脑爽文+非无敌】
# 分割: 按 '+' 分隔
tags = ["题材新颖", "非无脑爽文", "非无敌"]
```

### 工作流更新

**文件**: `src/workflows/migration_workflow.py`

**关键变更**:

```python
# 1. 创建 novel/ 目录
novel_dir = target_dir / "novel"
novel_dir.mkdir(parents=True, exist_ok=True)

# 2. 保存原始文件到 raw/
raw_novel_path = raw_dir / "novel.txt"
with open(raw_novel_path, "w") as f:
    f.write(original_text)  # 原始格式

# 3. 处理分段
result = self.novel_tool.execute(original_text)
processed_text = result.paragraphs[0]

# 4. 章节处理
chapter_report = self.chapter_processor.execute(processed_text, novel_dir)

# 5. 元数据提取
extracted_metadata = self.metadata_extractor.execute(original_text)
```

---

## 📊 处理统计

### 项目处理结果

| 项目 | 总章节数 | 章节文件数 | 文件列表 |
|------|---------|-----------|---------|
| 末哥超凡公路 | 50 | 5 | chpt_0001-0010 ~ chpt_0041-0050 |
| 天命桃花 | 85 | 9 | chpt_0001-0010 ~ chpt_0081-0085 |
| 永夜悔恨录 | 25 | 3 | chpt_0001-0010 ~ chpt_0021-0025 |

### 文件分布

```
每个 with_novel 项目:
├── raw/
│   ├── novel.txt         (~0.5-1.5 MB 原始文件)
│   └── ep*.srt           (5-10 个字幕文件)
├── novel/
│   ├── chpt_0000.txt     (1-3 KB 简介)
│   ├── chpt_XXXX-YYYY.txt (20-50 个章节文件)
│   └── processing_report.json (1 KB)
└── metadata.json         (2-3 KB)

总计: ~15-20 个文件/项目
```

---

## 🎯 优势与收益

### 1. 清晰的数据分层

| 层级 | 用途 | 特点 |
|------|------|------|
| **raw/** | 原始数据 | 不可变、可追溯 |
| **novel/** | 处理数据 | 结构化、易访问 |
| **metadata.json** | 元数据 | 索引、标签、统计 |

### 2. 模块化访问

```python
# 只读取简介
with open("novel/chpt_0000.txt") as f:
    intro = f.read()

# 只读取前10章
with open("novel/chpt_0001-0010.txt") as f:
    first_chapters = f.read()

# 按需加载，避免加载整个小说
```

### 3. 标签驱动分析

```python
# 根据标签筛选项目
projects = load_projects()
action_novels = [p for p in projects if "心狠手辣" in p.metadata.novel.tags]
```

### 4. 便于版本管理

- raw/ 文件不变 → Git 稳定
- novel/ 可重新生成 → 可忽略或单独管理
- metadata.json 小文件 → 易于 diff 和合并

---

## 📝 使用示例

### 读取项目小说

```python
from pathlib import Path
import json

# 1. 读取元数据
project_dir = Path("data/projects/with_novel/末哥超凡公路")
with open(project_dir / "metadata.json") as f:
    metadata = json.load(f)

# 2. 获取标签
tags = metadata["novel"]["tags"]
print(f"标签: {', '.join(tags)}")

# 3. 读取简介
with open(project_dir / "novel/chpt_0000.txt") as f:
    intro = f.read()

# 4. 读取指定章节
with open(project_dir / "novel/chpt_0001-0010.txt") as f:
    chapters = f.read()
```

### 批量处理章节

```python
# 遍历所有章节文件
novel_dir = project_dir / "novel"
chapter_files = sorted(novel_dir.glob("chpt_[0-9]*-[0-9]*.txt"))

for chapter_file in chapter_files:
    with open(chapter_file) as f:
        content = f.read()
        # 处理章节内容...
```

### 根据标签筛选项目

```python
def find_projects_by_tag(tag: str) -> List[str]:
    """根据标签查找项目"""
    projects = []
    for project_dir in Path("data/projects/with_novel").iterdir():
        metadata_file = project_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                if tag in metadata.get("novel", {}).get("tags", []):
                    projects.append(metadata["project_name"])
    return projects

# 查找所有"公路求生"类小说
road_survival_projects = find_projects_by_tag("公路求生")
```

---

## 🔄 与现有系统的兼容性

### Alignment 模块

- ✅ 从 `raw/ep*.srt` 读取字幕（无变化）
- ✅ 从 `novel/chpt_XXXX-YYYY.txt` 读取对应章节
- ✅ 元数据增强：可根据标签筛选项目

### Writer 模块

- ✅ 从 `novel/` 读取章节内容（更快速）
- ✅ 简介单独文件，便于生成摘要
- ✅ 标签信息可用于风格指导

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `src/tools/novel_chapter_processor.py` | 章节处理工具 |
| `src/workflows/migration_workflow.py` | 更新后的迁移工作流 |
| `docs/architecture/logic_flows.md` | 架构文档（待更新） |
| `data/migration_report_20260205.json` | 迁移报告 |

---

## ✅ 验证清单

- [x] raw/ 仅包含原始文件（novel.txt + ep*.srt）
- [x] novel/ 包含处理后的章节文件
- [x] chpt_0000.txt 仅包含简介正文
- [x] chpt_XXXX-YYYY.txt 包含对应章节（10章/文件）
- [x] metadata.json 包含标签数组
- [x] 所有章节文件格式正确（自然段落）
- [x] processing_report.json 统计准确
- [x] 3个项目全部处理完成

---

## 🚀 下一步建议

### 1. 更新现有模块

确保 Alignment 和 Writer 模块能正确使用新结构：

```python
# 更新读取路径
novel_dir = project_dir / "novel"  # 不再是 raw/
chapter_files = sorted(novel_dir.glob("chpt_[0-9]*-[0-9]*.txt"))
```

### 2. 标签驱动功能

基于标签实现：
- 项目智能分类
- 风格相似度分析
- 个性化推荐

### 3. 版本控制

```bash
git add .
git commit -m "feat: 优化项目结构v2.1 - 目录分离 + 章节拆分 + 标签提取

- raw/ 和 novel/ 目录分离
- 按10章拆分小说文件
- 简介独立为 chpt_0000.txt
- 标签提取到 metadata.json

See: docs/maintenance/PROJECT_OPTIMIZATION_V2.1.md"

git tag -a v2.1.0 -m "Project Structure Optimization v2.1"
```

---

**优化完成！** 🎉 项目结构更加清晰、模块化，为后续的 alignment 和 writer 训练提供了更好的数据基础。

---
*完成日期: 2026-02-05*
