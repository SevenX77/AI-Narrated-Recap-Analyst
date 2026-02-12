# HookContentAnalyzer

## 职责 (Responsibility)

**单一职责**: 分析Hook的内容来源，判断其与Novel简介的相似度，为对齐流程提供策略建议。

HookContentAnalyzer通过分层提取和比对，分析Hook是来源于Novel简介、某个章节，还是独立创作。分析结果用于指导后续的对齐策略选择。

---

## 接口 (Interface)

### 输入 (Input)

```python
def execute(
    hook_segments: List[ScriptSegment],  # Hook段落列表
    novel_intro: str,                    # Novel简介
    novel_metadata: NovelMetadata = None # Novel元数据（可选）
) -> HookAnalysisResult
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `hook_segments` | `List[ScriptSegment]` | ✅ | Hook段落列表（由HookDetector识别） |
| `novel_intro` | `str` | ✅ | Novel简介文本 |
| `novel_metadata` | `NovelMetadata` | ❌ | Novel元数据，辅助分析（当前版本未使用） |

### 输出 (Output)

```python
class HookAnalysisResult(BaseModel):
    source_type: str                     # 来源类型: "简介"/"章节"/"独立创作"
    similarity_score: float              # 总体相似度 (0.0-1.0)
    matched_chapter: Optional[int]       # 匹配的章节号（暂不支持）
    
    # 分层内容
    hook_layers: LayeredContent          # Hook的4层内容
    intro_layers: LayeredContent         # 简介的4层内容
    layer_similarity: Dict[str, float]   # 各层相似度
    
    # 对齐建议
    alignment_strategy: str              # 对齐策略: direct_intro/chapter_based/skip
    
    metadata: Dict[str, Any]             # 元数据
```

**LayeredContent结构**:
```python
class LayeredContent(BaseModel):
    world_building: List[str]    # 第1层: 世界观/背景设定
    game_mechanics: List[str]    # 第2层: 游戏机制/系统规则
    items_equipment: List[str]   # 第3层: 物品/装备
    plot_events: List[str]       # 第4层: 剧情事件
```

**示例输出**:
```python
HookAnalysisResult(
    source_type="简介",
    similarity_score=0.78,
    matched_chapter=None,
    
    hook_layers=LayeredContent(
        world_building=["末世爆发", "诡异入侵"],
        game_mechanics=["生存系统", "升级机制"],
        items_equipment=["二八大杠", "弩箭"],
        plot_events=["江城逃亡", "车队组建"]
    ),
    
    intro_layers=LayeredContent(
        world_building=["末世爆发", "全球诡异"],
        game_mechanics=["生存系统", "物资升级"],
        items_equipment=["二八大杠"],
        plot_events=["江城逃亡"]
    ),
    
    layer_similarity={
        "world_building": 0.67,
        "game_mechanics": 0.80,
        "items_equipment": 0.50,
        "plot_events": 0.50
    },
    
    alignment_strategy="direct_intro",
    
    metadata={
        "processing_time": 3.5,
        "hook_segment_count": 3
    }
)
```

---

## 实现逻辑 (Implementation)

### 分析流程

```
Hook文本 ──┐
          ├──> LLM分层提取 ──> Hook4层内容
          │
简介文本 ──┘──> LLM分层提取 ──> 简介4层内容
                                    │
                                    ├──> Jaccard相似度计算 ──> 各层相似度
                                    │
                                    ├──> 总体相似度 ──> 来源类型推断
                                    │
                                    └──> 对齐策略建议
```

### 1. 提取Hook分层内容

**输入**: Hook段落文本（拼接）

**LLM任务**: 提取4层内容
- 第1层: 世界观/背景设定
- 第2层: 游戏机制/系统规则
- 第3层: 物品/装备
- 第4层: 剧情事件

**输出**: `LayeredContent` 对象

### 2. 提取简介分层内容

与Hook相同的方式，提取简介的4层内容。

### 3. 计算各层相似度

使用 **Jaccard相似度**:

```
相似度 = |交集| / |并集|
       = |Hook层 ∩ 简介层| / |Hook层 ∪ 简介层|
```

**示例计算**:
```python
Hook世界观 = {"末世爆发", "诡异入侵", "人类禁区"}
简介世界观 = {"末世爆发", "全球诡异", "人类禁区"}

交集 = {"末世爆发", "人类禁区"}  # 2个
并集 = {"末世爆发", "诡异入侵", "人类禁区", "全球诡异"}  # 4个

相似度 = 2 / 4 = 0.50
```

### 4. 计算总体相似度

**方法**: 4层相似度的平均值

```
总体相似度 = Σ(各层相似度) / 4
```

### 5. 推断来源类型

| 相似度范围 | 来源类型 | 说明 |
|-----------|---------|------|
| ≥ 0.7 | 简介 | Hook主要来自简介 |
| 0.4 - 0.7 | 章节 | Hook可能来自某个章节 |
| < 0.4 | 独立创作 | Hook为UP主独立创作 |

### 6. 推荐对齐策略

| 来源类型 | 相似度 | 对齐策略 | 说明 |
|---------|-------|---------|------|
| 简介 | ≥ 0.7 | `direct_intro` | 直接与简介对齐，跳过Hook |
| 章节 | 0.4-0.7 | `chapter_based` | 基于章节内容对齐 |
| 独立创作 | < 0.4 | `skip` | 跳过Hook，从Body开始对齐 |

---

## 依赖关系 (Dependencies)

### Schema

- **输入Schema**:
  - `ScriptSegment` - Script段落
  - `NovelMetadata` - Novel元数据（可选）

- **输出Schema**:
  - `HookAnalysisResult` - 分析结果
  - `LayeredContent` - 分层内容

### Tools

- **前置工具**: `HookDetector`
  - 必须先识别Hook段落，才能分析内容

- **后置工具**: `NovelScriptAligner`
  - 根据分析结果选择对齐策略

### 外部依赖

- **Prompt**: `src/prompts/hook_content_analysis.yaml`
- **LLM**: DeepSeek v3.2 或 Claude Sonnet
- **LLM调用次数**: 2次（Hook分层 + 简介分层）

---

## 数据模型 (Data Models)

### LayeredContent (4层内容)

```python
class LayeredContent(BaseModel):
    world_building: List[str] = []     # 第1层: 世界观（如"末世", "诡异"）
    game_mechanics: List[str] = []     # 第2层: 游戏机制（如"系统", "升级"）
    items_equipment: List[str] = []    # 第3层: 物品装备（如"弩箭", "自行车"）
    plot_events: List[str] = []        # 第4层: 剧情事件（如"逃亡", "组队"）
```

### HookAnalysisResult

详见"接口-输出"部分。

**元数据字段**:
```python
metadata = {
    "processing_time": float,        # 处理时间（秒）
    "model_used": str,               # 使用的LLM模型
    "provider": str,                 # LLM提供商
    "hook_segment_count": int        # Hook段落数量
}
```

---

## 使用示例 (Usage Example)

### 完整流程

```python
from src.tools.hook_detector import HookDetector
from src.tools.hook_content_analyzer import HookContentAnalyzer

# 1. 先检测Hook边界
detector = HookDetector(provider="deepseek")
hook_result = detector.execute(
    script_segmentation=script_seg,
    novel_intro=novel_intro,
    novel_chapter1_preview=chapter1_preview
)

# 2. 如果有Hook，分析内容来源
if hook_result.has_hook:
    # 提取Hook段落
    hook_segments = [
        script_seg.segments[i] 
        for i in hook_result.hook_segment_indices
    ]
    
    # 分析Hook内容
    analyzer = HookContentAnalyzer(provider="deepseek")
    analysis_result = analyzer.execute(
        hook_segments=hook_segments,
        novel_intro=novel_intro
    )
    
    # 3. 根据分析结果选择对齐策略
    print(f"来源类型: {analysis_result.source_type}")
    print(f"相似度: {analysis_result.similarity_score:.2%}")
    print(f"建议策略: {analysis_result.alignment_strategy}")
    
    if analysis_result.alignment_strategy == "direct_intro":
        print("→ 直接与简介对齐，跳过Hook部分")
    elif analysis_result.alignment_strategy == "chapter_based":
        print("→ 需要基于章节内容对齐")
    else:
        print("→ 跳过Hook，从Body开始对齐")
```

### 查看分层内容

```python
# 查看Hook的分层内容
print("Hook分层内容:")
print(f"  世界观: {analysis_result.hook_layers.world_building}")
print(f"  游戏机制: {analysis_result.hook_layers.game_mechanics}")
print(f"  物品装备: {analysis_result.hook_layers.items_equipment}")
print(f"  剧情事件: {analysis_result.hook_layers.plot_events}")

# 查看各层相似度
print("\n各层相似度:")
for layer, score in analysis_result.layer_similarity.items():
    print(f"  {layer}: {score:.2%}")
```

---

## 分层提取标准 (Layering Standards)

### 第1层: 世界观/背景设定

**定义**: 故事发生的世界、时代、背景

**示例**:
- ✅ "末世爆发"、"诡异入侵"、"人类禁区"
- ✅ "修仙世界"、"灵气复苏"、"异界穿越"
- ❌ "主角获得系统"（这是剧情事件）
- ❌ "弩箭"（这是物品）

### 第2层: 游戏机制/系统规则

**定义**: 系统性的规则、机制、设定

**示例**:
- ✅ "生存系统"、"升级机制"、"商城功能"
- ✅ "修炼境界"、"功法等级"、"丹药炼制"
- ❌ "江城逃亡"（这是剧情事件）
- ❌ "末世背景"（这是世界观）

### 第3层: 物品/装备

**定义**: 具体的物品、装备、道具

**示例**:
- ✅ "二八大杠"、"弩箭"、"干粮"
- ✅ "飞剑"、"储物戒"、"丹药"
- ❌ "升级系统"（这是游戏机制）
- ❌ "获得装备"（这是剧情事件）

### 第4层: 剧情事件

**定义**: 具体发生的事件、行动、情节

**示例**:
- ✅ "江城逃亡"、"车队组建"、"击杀丧尸"
- ✅ "拜师学艺"、"闯入秘境"、"击败对手"
- ❌ "末世爆发"（这是世界观）
- ❌ "弩箭"（这是物品）

---

## 性能指标 (Performance)

- **LLM调用**: 2次（Hook分层 + 简介分层）
- **执行时间**: 3-8秒（取决于LLM响应）
- **相似度计算**: 本地计算，<1ms
- **准确率**: ~80%（基于人工标注测试集）

---

## 注意事项 (Notes)

1. **分层质量**: 依赖LLM的理解能力
   - 建议使用Claude（分层更准确）
   - DeepSeek也可用，但可能需要review

2. **相似度阈值**: 
   - `≥ 0.7`: 高相似度，可信度高
   - `0.4-0.7`: 中等相似度，建议人工review
   - `< 0.4`: 低相似度，通常为独立创作

3. **Jaccard局限性**: 
   - 无法处理语义相近但用词不同的情况
   - 如"末世"和"末日"会被视为不同元素
   - 未来可考虑使用语义相似度

4. **章节匹配**: 
   - 当前版本不支持具体章节匹配
   - `matched_chapter` 字段保留，但始终为 `None`
   - 未来版本可能支持

---

## 常见问题 (FAQ)

### Q1: 如何提高分层准确性？

**方法**:
1. 使用Claude模型（理解能力更强）
2. 确保Hook和简介文本完整
3. 如果分层明显错误，可以review Prompt
4. 记录bad case，改进Prompt

### Q2: 相似度为0是否正常？

**情况**:
- 如果Hook是独立创作，相似度接近0很正常
- 如果Hook明显来自简介但相似度为0，说明分层失败
- 建议查看 `hook_layers` 和 `intro_layers`，判断提取是否准确

### Q3: 如何处理中等相似度（0.4-0.7）？

**建议**:
1. 查看 `layer_similarity`，找出哪层相似度高
2. 如果 `world_building` 和 `game_mechanics` 相似度高，倾向于"简介"
3. 如果 `plot_events` 相似度高，倾向于"章节"
4. 不确定时，建议人工review

---

## 相关文档 (Related Docs)

- [HookDetector](./hook_detector.md) - Hook边界检测
- [NovelScriptAligner](./novel_script_aligner.md) - 对齐工具（使用分析结果）
- [ScriptProcessingWorkflow](../workflows/script_processing_workflow.md) - 完整流程

---

**最后更新**: 2026-02-10  
**维护者**: AI Assistant
