# NovelMetadataExtractor - 小说元数据提取工具

## 职责 (Responsibility)

提取小说标题、作者、标签、简介等元数据，支持 LLM 智能过滤简介内容（移除营销文案、标签等元信息）。

**所属阶段**: 小说元数据提取（Phase 0）
**工具链位置**: NovelImporter → NovelMetadataExtractor → 小说分析

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    novel_file: Union[str, Path],
    use_llm: bool = None
) -> NovelMetadata
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `novel_file` | `str \| Path` | 必填 | 小说文件路径 |
| `use_llm` | `bool` | `None` | 是否使用LLM过滤简介（None则使用初始化时的设置） |

### 输出结果

**类型**: `NovelMetadata`

**结构**:
```python
NovelMetadata(
    title: str,               # 小说标题
    author: str,              # 作者
    tags: List[str],          # 标签列表
    introduction: str,        # 简介（已过滤）
    chapter_count: Optional[int] = None  # 章节数（需要 NovelChapterDetector 填充）
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **读取文件**
   - 使用 UTF-8 编码读取

2. **提取基本信息**
   - 匹配 `Title: xxx`
   - 匹配 `Author: xxx`

3. **提取原始简介**
   - 从 `简介:` 标记开始
   - 到分隔符（`====`）或章节标题（`=== 第`）结束

4. **从简介中提取标签**
   - 匹配 `【标签1+标签2+标签3】` 格式
   - 只在简介前5行查找
   - 按 `+` 分割标签
   - 过滤过长内容（最大20字符）

5. **智能过滤简介**
   - **策略A（LLM模式）**：
     - 使用 LLM 智能过滤
     - 移除：标签、书名变体、营销文案、作者注释
     - 保留：世界观、主角设定、核心冲突、悬念
   - **策略B（规则模式）**：
     - 移除包含 `【】` 的标签行
     - 移除"又有书名"行
     - 移除营销关键词行（推荐票、月票、打赏等）

6. **验证结果**
   - 检查必填字段（标题、作者）
   - 检查简介非空

### LLM 智能过滤

**Prompt**: `introduction_extraction`

**输入**:
- 原始简介文本

**输出**:
- 过滤后的简介（纯文本）

**处理**:
- Temperature: 0.1
- Max tokens: 1000
- 清理可能的 markdown 格式

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `NovelMetadata` - 元数据结果

### 外部库依赖

**可选依赖**:
- `openai` - LLM功能（推荐）
  - 如果不可用，使用规则降级策略

### Prompt 依赖

**Prompt 文件**: `src/prompts/introduction_extraction.yaml`

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板
- `settings` - LLM配置（model, temperature, max_tokens）

### LLM 依赖

**Provider**: DeepSeek (默认)
**Model**: 由 `get_model_name(provider)` 决定
**Configuration**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_metadata_extractor import NovelMetadataExtractor

# 初始化工具（启用LLM）
extractor = NovelMetadataExtractor(use_llm=True, provider="deepseek")

# 提取元数据
metadata = extractor.execute(
    novel_file="data/projects/超凡公路/raw/novel.txt"
)

# 访问结果
print(f"标题：{metadata.title}")
print(f"作者：{metadata.author}")
print(f"标签：{', '.join(metadata.tags)}")
print(f"简介：{metadata.introduction[:100]}...")

# 不使用LLM（规则过滤）
extractor_rule = NovelMetadataExtractor(use_llm=False)
metadata_rule = extractor_rule.execute(
    novel_file="data/projects/超凡公路/raw/novel.txt"
)
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "title": "超凡公路",
  "author": "末哥",
  "tags": [
    "末世",
    "升级流",
    "系统",
    "爽文"
  ],
  "introduction": "末日降临，全球诡异爆发。陈野驾驶着破旧的轻卡，带领幸存者车队在超凡公路上求生...",
  "chapter_count": null
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **文件不存在**
   - 抛出 `FileNotFoundError`
   - 提示文件路径

2. **标题未找到**
   - 抛出 `ValueError`
   - 提示检查文件格式

3. **作者未找到**
   - 抛出 `ValueError`
   - 提示检查文件格式

4. **简介未找到**
   - 抛出 `ValueError`
   - 提示检查 `简介:` 标记

5. **简介过滤后为空**
   - 抛出 `ValueError`
   - 提示检查简介内容

6. **LLM调用失败**
   - 自动降级到规则过滤
   - 记录警告日志

### 日志级别

- `INFO`: 处理进度、过滤方式
- `WARNING`: LLM调用失败、降级策略
- `DEBUG`: 标签提取、过滤详情

## 文件格式要求 (File Format)

### 标准格式

```
Title: 超凡公路
Author: 末哥

简介:
【末世+升级流+系统+爽文】

末日降临，全球诡异爆发。
陈野驾驶着破旧的轻卡，带领幸存者车队在超凡公路上求生...

又有书名：《末日超凡公路》

============================
=== 第1章 车队第一铁律 ===
============================
```

### 必填字段

- `Title:` 行
- `Author:` 行
- `简介:` 标记
- 分隔符（`====` 或 `=== 第`）

### 可选字段

- 标签（`【标签1+标签2】`）
- 书名变体（`又有书名：xxx`）

## LLM vs 规则过滤对比

### LLM过滤（推荐）

**优点**:
- 智能识别元信息
- 保留核心剧情描述
- 处理复杂格式

**缺点**:
- 需要LLM调用（成本）
- 处理时间稍长（1-2秒）

### 规则过滤（降级）

**优点**:
- 无需LLM调用
- 处理速度快
- 无额外成本

**缺点**:
- 只能移除明显的元信息
- 可能误删有效内容
- 无法处理复杂格式

### 过滤示例

**原始简介**:
```
【末世+升级流+系统+爽文】

末日降临，全球诡异爆发。
陈野驾驶着破旧的轻卡，带领幸存者车队在超凡公路上求生...

又有书名：《末日超凡公路》

本书特点：节奏快、剧情爽、更新稳定！
求推荐票、月票、打赏！
```

**LLM过滤后**:
```
末日降临，全球诡异爆发。
陈野驾驶着破旧的轻卡，带领幸存者车队在超凡公路上求生...
```

**规则过滤后**:
```
末日降临，全球诡异爆发。
陈野驾驶着破旧的轻卡，带领幸存者车队在超凡公路上求生...
```

## 性能特征 (Performance)

### 处理速度

- **规则过滤**：<1秒
- **LLM过滤**：1-2秒

### Token 消耗（LLM模式）

- **Input**: 约 500-1000 tokens（简介长度）
- **Output**: 约 200-500 tokens
- **成本**: 约 $0.001-0.002 USD/次

## 注意事项 (Notes)

### 初始化参数

- `use_llm=True`: 启用LLM智能过滤（推荐）
- `provider="deepseek"`: 使用 DeepSeek（成本低）
- `provider="claude"`: 使用 Claude（质量高）

### LLM降级策略

如果 LLM 调用失败：
1. 记录警告日志
2. 自动降级到规则过滤
3. 返回规则过滤结果

### 标签提取位置

- 只在简介前5行查找标签
- 避免提取正文中的 `【】` 内容
- 过滤过长内容（>20字符）

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
