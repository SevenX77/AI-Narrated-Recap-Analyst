# 功能性标签体系

## 概述

功能性标签体系是 `NovelAnnotator` Pass 3 的核心功能，基于 `NOVEL_SEGMENTATION_METHODOLOGY.md` 设计，用于为每个段落标注功能性作用，指导小说浓缩改编。

**设计目标**：
- ✅ 明确哪些内容必须保留（P0-骨架）
- ✅ 识别哪些内容可以压缩（P1-血肉）
- ✅ 区分哪些内容可以删除（P2-皮肤）
- ✅ 追踪伏笔、钩子、首次信息
- ✅ 提供具体的浓缩建议

---

## 标签维度

### 维度1：叙事功能

标识段落在故事中的基本作用：

| 标签 | 说明 | 示例 |
|------|------|------|
| `故事推进` | 推动情节向前发展 | "车队得知上沪沦陷" |
| `核心故事设定（首次）` | 第一次出现的世界观规则 | "诡异无法被杀死" |
| `核心故事设定` | 重复强调的设定 | "不要掉队！不要掉队！不要掉队！" |
| `关键信息` | 重要线索、事实、细节 | "手弩对诡异无效，但能威慑人类" |
| `关键道具（首次）` | 重要物品初次出现 | "陈野骑着二八大杠" |
| `关键道具（升级）` | 物品状态改变 | "二八大杠变成三轮车" |
| `背景交代` | 补充说明性内容 | "几个月前，全球诡异爆发" |

---

### 维度2：叙事结构

标识段落在整体结构中的位置和作用：

| 标签 | 说明 | 示例 |
|------|------|------|
| `钩子-悬念制造` | 提出问题但不解答 | "【升级完成！】（未说明效果）" |
| `钩子-悬念释放` | 揭晓答案 | "二八大杠变成了三轮车" |
| `伏笔（明确）` | 明显的铺垫 | "强子，不如咱们把车抢过来？" |
| `伏笔` | 隐晦的暗示 | "车队结构分层（暗示阶级冲突）" |
| `回应伏笔` | 回收之前埋下的线索 | "强子真的来抢车" |
| `重复强调x次` | 重要信息的反复出现 | "不要掉队"重复3次 |

---

### 维度3：角色与关系

标识人物塑造和关系变化：

| 标签 | 说明 | 示例 |
|------|------|------|
| `人物登场：角色名` | 角色首次出现 | "人物登场：佳佳" |
| `人物塑造：角色名 - 特质` | 刻画角色性格 | "人物塑造：陈野 - 果断务实" |
| `对立关系：A vs B` | 冲突、矛盾建立 | "对立关系：陈野 vs 佳佳+强子" |
| `同盟关系：A + B` | 合作、联盟建立 | "同盟关系：陈野 + 车队" |

---

### 维度4：浓缩优先级 ⭐ 最重要

标识段落在浓缩改编时的重要程度：

#### P0-骨架（20-30%）

- **定义**：主线情节，删除后故事无法理解
- **特征**：核心转折点、关键行动、重要设定首次引入
- **示例**：
  - 主角觉醒升级系统 → P0
  - 车队得知上沪沦陷 → P0
  - 决定升级二八大杠 → P0

#### P1-血肉（40-50%）

- **定义**：重要设定或细节，删除会损失信息但主线仍可理解
- **特征**：世界观规则、重要但非即时的信息、人物关系建立
- **示例**：
  - 序列超凡设定 → P1
  - 手弩威慑作用 → P1
  - 佳佳+强子计划抢车 → P1

#### P2-皮肤（20-30%）

- **定义**：氛围渲染、情感细节，浓缩时可删
- **特征**：环境描写、心理活动、对话的具体措辞
- **示例**：
  - "微微亮起的火光照亮了陈野的侧脸轮廓" → P2
  - 周围LSP的反应 → P2
  - 关于为何没有汽车的详细解释 → P2

---

### 维度5：其他标记

| 标签 | 说明 | 示例 |
|------|------|------|
| `情绪基调` | 段落情感氛围 | 紧张/绝望/希望/平静 |
| `首次信息` | 重要信息首次出现 | 标记为 `true` |
| `重复强调次数` | 重复强调的实际次数 | 3次 |

---

## 数据结构

### ParagraphFunctionalTags

```python
{
    "paragraph_index": 1,
    "narrative_functions": ["故事推进", "核心故事设定（首次）"],
    "narrative_structures": ["钩子-悬念制造", "伏笔（明确）"],
    "character_tags": ["人物登场：陈野"],
    "priority": "P0-骨架",
    "priority_reason": "首次揭示世界观核心设定",
    "emotional_tone": "绝望",
    "is_first_occurrence": true,
    "repetition_count": 3,
    "condensation_advice": "保留：核心设定。删除：细节描写"
}
```

### FunctionalTagsLibrary

```python
{
    "chapter_number": 1,
    "total_paragraphs": 11,
    "paragraph_tags": [
        # ParagraphFunctionalTags 列表
    ],
    "priority_distribution": {
        "P0-骨架": 5,
        "P1-血肉": 4,
        "P2-皮肤": 2
    },
    "first_occurrence_count": 7,
    "metadata": {
        "processing_time": 50.9
    }
}
```

---

## 标注原则

### 1. 优先级判断要严格

- **P0-骨架应该只占20-30%**：真正不可删除的内容
- **P1-血肉占40-50%**：重要但可压缩
- **P2-皮肤占20-30%**：可直接删除

### 2. 叙事功能可多选

一个段落可以同时有多个功能（如：既推进故事，又塑造人物）

### 3. 首次信息很重要

如果是重要设定/道具/人物的首次出现，必须标记为 `true`

### 4. 重复强调要计数

如果段落内有明显重复（如："不要掉队！不要掉队！不要掉队！"），标注实际次数

### 5. 浓缩建议要具体

- 明确指出哪些内容必须保留、哪些可以删除
- 不要含糊其辞

---

## 实际应用

### 用途1：浓缩改编决策

```python
# 筛选P0-骨架段落（必须保留）
p0_paragraphs = [
    tag for tag in functional_tags.paragraph_tags 
    if tag.priority == "P0-骨架"
]

# 压缩P1-血肉段落（保留核心，删除细节）
p1_paragraphs = [
    tag for tag in functional_tags.paragraph_tags 
    if tag.priority == "P1-血肉"
]

# 删除P2-皮肤段落（可完全删除）
p2_paragraphs = [
    tag for tag in functional_tags.paragraph_tags 
    if tag.priority == "P2-皮肤"
]
```

### 用途2：伏笔追踪

```python
# 查找所有伏笔
foreshadowing = [
    tag for tag in functional_tags.paragraph_tags 
    if any("伏笔" in s for s in tag.narrative_structures)
]

# 检查是否有对应的回应伏笔
for foreshadow in foreshadowing:
    has_response = any(
        "回应伏笔" in s 
        for tag in functional_tags.paragraph_tags 
        for s in tag.narrative_structures
    )
```

### 用途3：首次信息保留率检查

```python
# 统计首次信息
first_occurrences = [
    tag for tag in functional_tags.paragraph_tags 
    if tag.is_first_occurrence
]

# 检查改编脚本是否保留了所有首次信息
coverage_rate = len(preserved_first_occurrences) / len(first_occurrences)
```

---

## 输出格式

### Markdown 格式

```markdown
## 段落1

**叙事功能**:
- 故事推进
- 核心故事设定（首次）

**叙事结构**:
- 钩子-悬念制造
- 伏笔（明确）

**角色与关系**:
- 人物登场：陈野

**浓缩优先级**: `P0-骨架`
**理由**: 首次揭示世界观核心设定

**情绪基调**: 绝望
**首次信息**: ✅ 是
**重复强调**: 3次

**浓缩建议**:
> 保留：电台广播内容、三条诡异规则
> 删除：杂音描写细节
```

---

## 性能指标

- **处理时间**: 约 50秒/章节（11段）
- **Token消耗**: 约 3K-5K input + 4K-6K output
- **准确度**: 依赖于LLM能力（Claude Sonnet 4.5推荐）

---

## 参考文档

- **方法论**: `archive/docs/NOVEL_SEGMENTATION_METHODOLOGY.md`
- **工具文档**: `docs/tools/novel_annotator.md`
- **Schema定义**: `src/core/schemas_novel.py`
- **Prompt模板**: `src/prompts/novel_annotation_pass3_functional_tags.yaml`

---

**最后更新**: 2026-02-10  
**实现状态**: ✅ 已完成并测试
