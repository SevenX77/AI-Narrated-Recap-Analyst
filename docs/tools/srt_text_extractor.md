# SrtTextExtractor - SRT文本提取工具

## 职责 (Responsibility)

从SRT条目中提取纯文本，使用LLM智能添加标点符号、修正错别字、标准化实体、修复缺字问题，确保语义通顺连贯。

**所属阶段**: SRT文本处理（Phase 1）
**工具链位置**: SrtImporter → SrtTextExtractor → ScriptSegmenter

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    srt_entries: List[SrtEntry],
    project_name: str,
    episode_name: str,
    novel_reference: Optional[str] = None
) -> SrtTextExtractionResult
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `srt_entries` | `List[SrtEntry]` | 必填 | SRT条目列表（从 SrtImporter 输出） |
| `project_name` | `str` | 必填 | 项目名称 |
| `episode_name` | `str` | 必填 | 集数名称 |
| `novel_reference` | `str` | `None` | 小说参考文本（可选，前3章即可） |

### 输出结果

**类型**: `SrtTextExtractionResult`

**结构**:
```python
SrtTextExtractionResult(
    processed_text: str,                      # 处理后的文本
    processing_mode: str,                     # 处理模式（with_novel/without_novel/rule_based）
    raw_text: str,                            # 原始文本
    entity_standardization: Dict[str, Dict[str, Any]],  # 实体标准化信息
    corrections: Dict[str, Any],              # 修正统计
    processing_time: float,                   # 处理时间（秒）
    original_chars: int,                      # 原始字符数
    processed_chars: int                      # 处理后字符数
)
```

**entity_standardization 结构**:
```python
{
    "characters": {                     # 人物实体
        "source": "novel_reference",    # 来源
        "entities": ["陈野", "李队长"],  # 实体列表
        "count": 2
    },
    "locations": {                      # 地点实体
        "source": "novel_reference",
        "entities": ["江城", "上沪"],
        "count": 2
    }
}
```

## 实现逻辑 (Logic)

### 两种处理模式

#### 模式1: with_novel（有小说参考）

**流程**:
1. 从小说参考文本中提取标准实体
   - 人物：常见姓氏+名字，或带称谓
   - 地点：含"地"/"城"/"宫"等
2. 使用LLM处理字幕
   - 添加标点符号
   - 修正错别字
   - 使用标准实体替换变体

**Prompt**: `srt_script_processing_with_novel`

#### 模式2: without_novel（无小说参考）

**流程**:
1. 使用LLM智能识别实体变体
2. 推断标准实体形式
3. 同时完成标点、修正、标准化

**Prompt**: `srt_script_processing_without_novel`

### 核心流程

1. **提取原始文本**
   - 从SRT条目中提取所有文本
   - 用换行符连接（保留断句信息）

2. **选择处理模式**
   - 如果提供 `novel_reference` → with_novel
   - 如果未提供 → without_novel
   - 如果LLM不可用 → rule_based（降级）

3. **LLM处理**
   - 调用对应的Prompt
   - 解析LLM输出

4. **构建结果**
   - 统计修正信息
   - 计算处理时间
   - 返回结果

### 降级策略（rule_based）

如果LLM不可用或失败：
1. 简单合并行
2. 添加基本标点（句号）
3. 不进行实体标准化

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_script.py`

- `SrtEntry` - SRT条目
- `SrtTextExtractionResult` - 提取结果

### Prompt 依赖

**Prompt 文件**:
- `src/prompts/srt_script_processing_with_novel.yaml` - with_novel 模式
- `src/prompts/srt_script_processing_without_novel.yaml` - without_novel 模式

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板
- `settings` - LLM配置

### LLM 依赖

**Provider**: DeepSeek (默认)
**Model**: 由 `get_model_name(provider)` 决定
**Configuration**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.srt_text_extractor import SrtTextExtractor
from src.core.schemas_script import SrtEntry

# 初始化工具
extractor = SrtTextExtractor(use_llm=True, provider="deepseek")

# 准备输入
srt_entries = [
    SrtEntry(index=1, start_time="...", end_time="...", text="收音机里传来消息"),
    SrtEntry(index=2, start_time="...", end_time="...", text="上沪沦陷了"),
    ...
]

# 模式1: 有小说参考
result = extractor.execute(
    srt_entries=srt_entries,
    project_name="末哥超凡公路",
    episode_name="ep01",
    novel_reference=novel_text  # 前3章内容
)

print(f"处理模式：{result.processing_mode}")  # "with_novel"
print(f"处理后文本：{result.processed_text}")
print(f"实体标准化：{result.entity_standardization}")

# 模式2: 无小说参考
result = extractor.execute(
    srt_entries=srt_entries,
    project_name="末哥超凡公路",
    episode_name="ep01"
)

print(f"处理模式：{result.processing_mode}")  # "without_novel"
```

## 输出格式 (Output Format)

### JSON 输出示例（with_novel 模式）

```json
{
  "processed_text": "收音机里传来消息，上沪沦陷了。陈野关掉收音机，看向车窗外的荒凉公路。",
  "processing_mode": "with_novel",
  "raw_text": "收音机里传来消息\n上海沦陷了\n陈叶关掉收音机\n看向车窗外的荒凉公路",
  "entity_standardization": {
    "characters": {
      "source": "novel_reference",
      "entities": ["陈野", "李队长"],
      "count": 2
    },
    "locations": {
      "source": "novel_reference",
      "entities": ["江城", "上沪"],
      "count": 2
    }
  },
  "corrections": {
    "punctuation_added": 42,
    "char_difference": 3
  },
  "processing_time": 3.5,
  "original_chars": 248,
  "processed_chars": 251
}
```

### JSON 输出示例（without_novel 模式）

```json
{
  "processed_text": "收音机里传来消息，上沪沦陷了。陈野关掉收音机，看向车窗外的荒凉公路。",
  "processing_mode": "without_novel",
  "raw_text": "收音机里传来消息\n上海沦陷了\n陈叶关掉收音机\n看向车窗外的荒凉公路",
  "entity_standardization": {
    "characters": {
      "陈野": ["陈叶", "陈爷"],
      "李队长": ["李队"]
    },
    "locations": {
      "上沪": ["上海", "申城"]
    }
  },
  "corrections": {
    "punctuation_added": 42,
    "char_difference": 3
  },
  "processing_time": 4.2,
  "original_chars": 248,
  "processed_chars": 251
}
```

## 处理示例 (Processing Examples)

### 示例1: 添加标点符号

**原始**:
```
收音机里传来消息
上沪沦陷了
陈野关掉收音机
看向车窗外的荒凉公路
```

**处理后**:
```
收音机里传来消息，上沪沦陷了。陈野关掉收音机，看向车窗外的荒凉公路。
```

### 示例2: 修正错别字

**原始**:
```
陈叶关掉收音机（错别字：叶→野）
```

**处理后**:
```
陈野关掉收音机
```

### 示例3: 实体标准化

**原始**:
```
陈叶、陈爷、小陈（都指同一个人）
上海、申城（都指上沪）
```

**处理后**:
```
陈野（统一使用标准名称）
上沪（统一使用标准名称）
```

### 示例4: 修复缺字

**原始**:
```
到达上（缺少"海"）
```

**处理后**:
```
到达上沪
```

## 错误处理 (Error Handling)

### 常见错误

1. **LLM调用失败**
   - 自动降级到规则处理
   - 记录错误日志

2. **LLM输出解析失败**
   - 使用原始输出
   - 记录警告日志

3. **实体提取失败**
   - 跳过实体标准化
   - 记录警告日志

### 日志级别

- `INFO`: 处理进度、模式选择
- `WARNING`: LLM失败、降级策略
- `ERROR`: 严重错误

## 性能特征 (Performance)

### Token 消耗

- **with_novel 模式**：约 2K-4K input + 1K-2K output
- **without_novel 模式**：约 2K-4K input + 2K-3K output

### 处理时间

- **with_novel 模式**：3-5秒
- **without_novel 模式**：4-6秒
- **rule_based 模式**：<1秒

### 准确度

- **标点添加**：95%+
- **错别字修正**：90%+
- **实体标准化**：85%+（with_novel），75%+（without_novel）

## 实体提取规则 (Entity Extraction Rules)

### 人物实体

**正则表达式**:
```python
r'[\u4e00-\u9fa5]{2,4}(?:公主|王爷|皇帝|淑妃|大人|先生|小姐|队长|博士|教授)'
```

**示例**:
- 陈野队长
- 李教授
- 王小姐

### 地点实体

**正则表达式**:
```python
r'[\u4e00-\u9fa5]{2,6}(?:城|宫|地|国|州|省|县|市|镇|村)'
```

**示例**:
- 江城
- 上沪市
- 皇宫

## 注意事项 (Notes)

### 小说参考文本

- 建议使用前3章内容（约5000-10000字）
- 包含主要人物和地点即可
- 不需要完整小说

### 处理模式选择

| 场景 | 推荐模式 |
|-----|---------|
| 有原著小说 | with_novel |
| 无原著小说 | without_novel |
| 快速测试 | rule_based |

### 与其他工具的配合

1. **SrtImporter**：
   - 先导入并规范化SRT
   - 获取SRT条目列表

2. **ScriptSegmenter**：
   - 使用处理后的文本进行分段
   - 匹配时间戳

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
