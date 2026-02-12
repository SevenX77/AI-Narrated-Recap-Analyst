# NovelSystemTracker - 章节系统元素追踪工具

## 职责 (Responsibility)

追踪每个事件中的系统元素变化（数量、状态、获得/消耗等），是小说分析工具链的 Phase 3。

**所属阶段**: 小说系统追踪（Phase 3）
**工具链位置**: NovelAnnotator → NovelSystemTracker

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    annotated_chapter: AnnotatedChapter,
    system_catalog: SystemCatalog,
    **kwargs
) -> SystemTrackingResult
```

### 输入参数

| 参数 | 类型 | 说明 |
|-----|------|------|
| `annotated_chapter` | `AnnotatedChapter` | 章节标注结果（来自 NovelAnnotator） |
| `system_catalog` | `SystemCatalog` | 系统目录（来自 NovelSystemAnalyzer） |

### 输出结果

**类型**: `SystemTrackingResult`

**结构**:
```python
SystemTrackingResult(
    chapter_number: int,              # 章节号
    total_events: int,                # 事件总数
    events_with_changes: int,         # 有系统变化的事件数
    tracking_entries: List[SystemTrackingEntry],  # 追踪记录列表
    metadata: Dict[str, Any]          # 元数据
)
```

**SystemTrackingEntry 结构**:
```python
SystemTrackingEntry(
    event_id: str,                    # 事件ID（9位数字+1位字母）
    event_summary: str,               # 事件摘要
    has_system_changes: bool,         # 是否有系统变化
    system_changes: List[SystemChange]  # 系统变化列表
)
```

**SystemChange 结构**:
```python
SystemChange(
    element_name: str,                # 元素名称
    category_id: str,                 # 类别ID（SC001, SC002...）
    change_type: str,                 # 变化类型（获得/消耗/升级/遭遇/状态变化）
    change_description: str,          # 变化描述
    quantity_change: Optional[str],   # 数量变化（+10, -5等）
    quantity_before: Optional[str],   # 变化前存量
    quantity_after: Optional[str]     # 变化后存量
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **准备输入数据**
   - 格式化系统目录摘要（前15个元素）
   - 格式化事件详情（摘要+段落内容前300字）

2. **LLM系统追踪**
   - 调用 `novel_system_tracking` prompt
   - 输入：章节号 + 系统目录摘要 + 事件详情
   - 输出：Markdown格式的追踪结果
   - Temperature: 0.2
   - Max tokens: 2000

3. **解析追踪结果**
   - 匹配事件块：`## 事件1：[事件ID] - [事件摘要]`
   - 匹配系统变化标志：`**系统变化**：有/无`
   - 匹配变化详情：
     - `**元素**：[名称]（[类别ID] - [类别名]）`
     - `**变化类型**：获得/消耗/升级/遭遇/状态变化`
     - `**变化描述**：[描述]`
     - `**数量变化**：[+/-数字]`（可选）
     - `**变化前存量**：[数字]`（可选）
     - `**变化后存量**：[数字]`（可选）

4. **构建结果**
   - 统计有变化的事件数
   - 计算处理时间
   - 生成元数据

### 设计理念

- **轻量级LLM调用**：输入控制在 3K tokens 以内
- **结构化输出**：易于生成表格和可视化
- **完整追踪**：同时记录数量和状态变化

### 性能特征

- **Token消耗**：约 2K-3K input + 1K-2K output
- **处理时间**：约 5-10秒/章节
- **准确度**：依赖于事件标注质量和系统目录准确性

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `AnnotatedChapter` - 章节标注结果
- `SystemCatalog` - 系统目录
- `SystemChange` - 系统变化
- `SystemTrackingEntry` - 追踪记录
- `SystemTrackingResult` - 追踪结果

### Tool 依赖

**前置工具**:
- `NovelAnnotator` - 提供章节标注结果
- `NovelSystemAnalyzer` - 提供系统目录

**后续工具**:
- 可用于生成系统变化报表
- 可用于追踪资源流向

### Prompt 依赖

**Prompt 文件**: `src/prompts/novel_system_tracking.yaml`

**配置项**:
- `system` - 系统提示词
- `user_template` - 用户提示词模板

### LLM 依赖

**Provider**: Claude (默认)
**Model**: 由 `get_model_name(provider)` 决定
**配置**: 通过 `src/core/llm_client_manager` 管理

## 代码示例 (Usage Example)

```python
from src.tools.novel_system_tracker import NovelSystemTracker
from src.core.schemas_novel import AnnotatedChapter, SystemCatalog

# 初始化工具
tracker = NovelSystemTracker(provider="claude")

# 准备输入
annotated_chapter = AnnotatedChapter(...)  # 来自 NovelAnnotator
system_catalog = SystemCatalog(...)        # 来自 NovelSystemAnalyzer

# 执行追踪
result = tracker.execute(
    annotated_chapter=annotated_chapter,
    system_catalog=system_catalog
)

# 访问结果
print(f"追踪完成：{result.events_with_changes}/{result.total_events} 个事件有系统变化")

# 遍历追踪记录
for entry in result.tracking_entries:
    if entry.has_system_changes:
        print(f"事件 {entry.event_id}：{entry.event_summary}")
        for change in entry.system_changes:
            print(f"  - {change.element_name}: {change.change_type}")
            print(f"    描述：{change.change_description}")
            if change.quantity_change:
                print(f"    数量变化：{change.quantity_change}")
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "chapter_number": 1,
  "total_events": 5,
  "events_with_changes": 2,
  "tracking_entries": [
    {
      "event_id": "000100001B",
      "event_summary": "陈野获得轻型枪械",
      "has_system_changes": true,
      "system_changes": [
        {
          "element_name": "轻型枪械",
          "category_id": "SC002",
          "change_type": "获得",
          "change_description": "从仓库中找到一把手枪",
          "quantity_change": "+1",
          "quantity_before": "0",
          "quantity_after": "1"
        }
      ]
    }
  ],
  "metadata": {
    "processing_time": 8.5,
    "model_used": "claude-sonnet-4.5",
    "provider": "claude"
  }
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **解析失败**：LLM输出格式不符合预期
   - 记录警告日志
   - 跳过该条记录
   - 继续处理剩余记录

2. **元素未找到**：变化中的元素不在系统目录中
   - 使用 `SC999` 作为默认类别ID
   - 记录警告日志

3. **数量格式错误**：数量变化无法解析
   - 设置为 `None`
   - 保留变化描述

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 解析失败、元素未找到
- `DEBUG`: 详细的解析过程

## 性能优化 (Performance)

### Token 优化

1. **系统目录摘要**：每个类别只显示前15个元素
2. **事件内容预览**：每个事件只显示前300字
3. **输出长度限制**：Max tokens 设为 2000

### 处理速度

- **单章节**：5-10秒
- **批量处理**：建议使用并行处理（多线程/异步）

## 扩展性 (Extensibility)

### 支持的变化类型

当前支持：
- `获得` - 获取新资源/道具
- `消耗` - 消耗资源/道具
- `升级` - 等级/技能提升
- `遭遇` - 遇到敌人/怪物
- `状态变化` - 状态改变（中毒/增益等）

### 扩展新类型

在 `src/prompts/novel_system_tracking.yaml` 中添加新的变化类型定义。

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
