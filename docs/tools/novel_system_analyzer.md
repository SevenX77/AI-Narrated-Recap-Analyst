# NovelSystemAnalyzer - 小说系统元素分析工具

## 职责 (Responsibility)

分析小说前N章内容，识别核心系统元素并智能归类，生成系统目录（SystemCatalog）。是小说分析工具链的 Phase 1。

**所属阶段**: 小说系统分析（Phase 1）
**工具链位置**: 工具链起点 → NovelSystemAnalyzer → NovelSystemDetector

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    novel_path: str,
    novel_name: str = "",
    max_chapters: int = 50,
    use_chapter_detector: bool = True,
    **kwargs
) -> SystemCatalog
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `novel_path` | `str` | 必填 | 小说文件路径（data/projects/xxx/raw/novel.txt） |
| `novel_name` | `str` | `""` | 小说名称 |
| `max_chapters` | `int` | `50` | 最大分析章节数 |
| `use_chapter_detector` | `bool` | `True` | 是否使用章节检测器 |

### 输出结果

**类型**: `SystemCatalog`

**结构**:
```python
SystemCatalog(
    novel_type: str,                          # 小说类型
    novel_name: str,                          # 小说名称
    analyzed_chapters: str,                   # 分析的章节范围（如 "1-50"）
    categories: List[SystemCategory],         # 系统类别列表
    metadata: Dict[str, Any]                  # 元数据
)
```

**SystemCategory 结构**:
```python
SystemCategory(
    category_id: str,          # 类别ID（SC001, SC002...）
    category_name: str,        # 类别名称
    category_desc: str,        # 类别描述
    importance: str,           # 重要程度（critical/important/minor）
    elements: List[str],       # 元素列表
    tracking_strategy: str     # 追踪策略（quantity/state_change/ownership/encounter）
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **读取小说内容**
   - 从指定路径读取小说文件
   - 检查文件是否存在

2. **提取章节摘要**
   - **策略A（use_chapter_detector=True）**：
     - 使用 `NovelChapterDetector` 检测章节边界
     - 每章提取前800字
   - **策略B（use_chapter_detector=False）**：
     - 使用正则表达式匹配章节标题
     - 每章提取前30行

3. **LLM系统分析**
   - 调用 `novel_system_analysis` prompt
   - 输入：小说名称 + 总章节数 + 章节摘要
   - 输出：Markdown格式的系统目录
   - Temperature: 0.3
   - Max tokens: 4000

4. **解析LLM输出**
   - 提取小说类型（从 `## 小说类型` 段落）
   - 提取系统类别（匹配 `### SC001 - [类别名称]`）
   - 提取字段：
     - `**重要程度**：critical/important/minor`
     - `**追踪策略**：quantity/state_change/ownership/encounter`
     - `**类别描述**：[描述]`
     - `**元素列表**：- [元素1]\n- [元素2]`

5. **构建系统目录**
   - 创建 `SystemCatalog` 对象
   - 计算元数据（总元素数、类别数）

### 设计理念

- **使用章节摘要而非完整内容**：降低 Token 成本
- **参考系统类型模板**：灵活适应创新设定
- **关注剧情推进相关元素**：避免无关信息

### 性能特征

- **Token消耗**：约 10K-20K input + 2K-4K output
- **处理时间**：约 20-30秒（50章）
- **准确度**：依赖于章节摘要质量和LLM能力

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `SystemCategory` - 系统类别
- `SystemCatalog` - 系统目录

### Tool 依赖

**前置工具**:
- `NovelChapterDetector` - （可选）用于准确检测章节边界

**后续工具**:
- `NovelSystemDetector` - 使用此工具生成的初始目录

### Prompt 依赖

**Prompt 文件**: `src/prompts/novel_system_analysis.yaml`

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

**Prompt 模板**:
```yaml
system: |
  你是小说系统元素分析专家...

user_template: |
  小说名称：{novel_name}
  分析章节：前{total_chapters}章

  {chapters_summary}
```

### LLM 依赖

**Provider**: Claude (默认)
**Model**: 由 `get_model_name(provider)` 决定
**配置**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_system_analyzer import NovelSystemAnalyzer

# 初始化工具
analyzer = NovelSystemAnalyzer(provider="claude")

# 执行分析
catalog = analyzer.execute(
    novel_path="data/projects/超凡公路/raw/novel.txt",
    novel_name="超凡公路",
    max_chapters=50,
    use_chapter_detector=True
)

# 访问结果
print(f"小说类型：{catalog.novel_type}")
print(f"系统类别数：{len(catalog.categories)}")
print(f"总元素数：{catalog.metadata['total_elements']}")

# 遍历类别
for category in catalog.categories:
    print(f"{category.category_id} - {category.category_name}")
    print(f"  重要程度：{category.importance}")
    print(f"  元素数量：{len(category.elements)}")
    print(f"  元素示例：{', '.join(category.elements[:5])}")
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "novel_type": "末世求生",
  "novel_name": "超凡公路",
  "analyzed_chapters": "1-50",
  "categories": [
    {
      "category_id": "SC001",
      "category_name": "生存资源",
      "category_desc": "角色赖以生存的基础资源",
      "importance": "critical",
      "elements": ["食物", "水", "燃料", "弹药", "医疗包"],
      "tracking_strategy": "quantity"
    },
    {
      "category_id": "SC002",
      "category_name": "装备道具",
      "category_desc": "角色装备的武器、护具、道具",
      "importance": "critical",
      "elements": ["轻型枪械", "防护服", "强化手套"],
      "tracking_strategy": "quantity"
    },
    {
      "category_id": "SC003",
      "category_name": "诡异生物",
      "category_desc": "威胁角色生存的怪物",
      "importance": "important",
      "elements": ["诡影", "腐蚀体", "巨型蜘蛛"],
      "tracking_strategy": "encounter"
    }
  ],
  "metadata": {
    "total_elements": 35,
    "category_count": 5,
    "processing_time": 25.3
  }
}
```

## 成本估算 (Cost Estimation)

### `estimate_cost()` 方法

```python
cost_info = analyzer.estimate_cost(
    max_chapters=50,
    avg_chapter_length=3000
)

print(cost_info)
# {
#     "max_chapters": 50,
#     "preview_per_chapter": 800,
#     "total_input_chars": 40000,
#     "estimated_input_tokens": 26667,
#     "estimated_output_tokens": 2000,
#     "estimated_cost_usd": 0.11,
#     "estimated_time": "20-30秒"
# }
```

### 价格参考（Claude Sonnet 4.5）

- Input: $3/M tokens
- Output: $15/M tokens
- **50章分析成本**: 约 $0.10-0.15 USD

## 错误处理 (Error Handling)

### 常见错误

1. **文件不存在**
   - 抛出 `FileNotFoundError`

2. **章节检测失败**
   - 自动降级到正则匹配模式
   - 记录警告日志

3. **LLM输出解析失败**
   - 返回空类别列表
   - 记录错误日志

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 章节检测失败、降级策略
- `DEBUG`: 详细的解析过程

## 性能优化 (Performance)

### Token 优化策略

1. **章节摘要压缩**
   - 每章仅保留前800字（约2-3段）
   - 跳过章节标题和空行

2. **批量处理**
   - 单次LLM调用分析所有章节
   - 避免多次调用的开销

3. **章节数量控制**
   - 默认分析前50章
   - 可根据小说长度调整

### 处理速度

- **50章分析**：20-30秒
- **100章分析**：40-60秒

## 注意事项 (Notes)

### 何时使用

- **项目初始化时**：分析小说类型和核心系统
- **系统目录不存在时**：生成初始系统目录
- **小说类型变化时**：重新分析

### 与 NovelSystemDetector 的关系

| 特性 | NovelSystemAnalyzer | NovelSystemDetector |
|-----|---------------------|---------------------|
| 运行时机 | 全书开始前 | 每章处理后 |
| 输入来源 | 原始小说文本（前50章） | 章节标注结果 + C类段落 |
| 输出结果 | 初始系统目录 | 新元素 + 更新目录 |
| Token消耗 | 高（10K-20K） | 低（2K-3K） |
| 运行次数 | 一次 | 每章一次 |

### 最佳实践

1. **首次分析**：使用前50章，确保覆盖主要系统元素
2. **后续更新**：使用 `NovelSystemDetector` 增量更新
3. **章节检测器**：建议开启 `use_chapter_detector=True`，提高准确度

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
