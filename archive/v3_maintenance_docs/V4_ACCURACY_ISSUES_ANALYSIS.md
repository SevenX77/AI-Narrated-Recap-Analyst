# V4.0 准确性问题深度分析与解决方案

**发现日期**: 2026-02-05  
**严重级别**: 🔴 高（影响核心对齐准确性）  
**涉及模块**: `layered_alignment_engine.py`, `layered_extraction.yaml`

---

## 📋 问题汇总

| 问题ID | 问题描述 | 严重度 | 根本原因 | 状态 |
|--------|---------|--------|----------|------|
| ACC-001 | 关键语义丢失（铁律） | 🔴 高 | LLM提取不完整 + Prompt不够明确 | 待修复 |
| ACC-002 | 相似度评分过低 | 🟡 中 | 算法过于简单（字符集Jaccard） | 待优化 |
| ACC-003 | items_equipment为0 | 🔴 高 | Prompt Key不匹配（Bug） | **可立即修复** |
| ACC-004 | 缺乏优化机制 | 🟢 低 | 未实现自反馈系统 | 规划中 |

---

## 问题1：关键语义丢失（铁律提取不完整）

### 📊 案例详情

**原文**（ep01.srt，时间00:00:40）：
```srt
31
00:00:40,500 --> 00:00:42,433
所有人都得谨记两条铁路第一

32
00:00:42,433 --> 00:00:43,100
不要掉队

33
00:00:43,100 --> 00:00:44,466
第二尽可能储备物资

34
00:00:44,466 --> 00:00:46,200
而第一条永远高于第二条
```

**小说原文**（novel.txt，第1章）：
```
在这个车队的人，必须谨记两条铁律！
第一条：不要掉队！不要掉队！不要掉队！！！
第二条：尽可能多的储备物资！！！
第一条铁律优于第二条。
```

**Script提取结果**：
```json
{
  "node_id": "world_building_script_4",
  "content": "尽可能储备物资",  // ❌ 只有第二条！
  "summary": "尽可能储备物资"
}

// ❌ 缺失：
// - "不要掉队"（第一条，最重要！）
// - 优先级关系（"第一条永远高于第二条"）
```

**Novel提取结果**：
```json
{
  "node_id": "world_building_novel_4",
  "content": "车队铁律：不要掉队，尽可能多储备物资",  // ✅ 完整
  "summary": "车队铁律：不要掉队，尽可能多储备物资"
}
```

**对齐结果**：
```json
{
  "similarity": 0.4117,  // ❌ 相似度低（因为Script不完整）
  "confidence": "medium"
}
```

### 🔍 根本原因分析

#### 原因1：Prompt指导不够明确

**当前Prompt**（`extract_world_building`）：
```yaml
【提取原则】
1. 只提取"设定性"信息，不提取具体事件
2. 合并重复的设定
3. 提取关键规则和限制  ← 有提及，但不够强调
4. 忽略角色的主观感受
```

**问题**：
- ❌ 没有强调"规则的完整性"
- ❌ 没有强调"优先级关系"
- ❌ 没有强调"多条规则应该合并"

#### 原因2：LLM可能分别提取了但未显示

让我们检查所有Script world_building节点：

```python
# 实际提取的Script world_building节点
1. [world_building_script_1] "诡异降临，城市成为人类禁区"
2. [world_building_script_4] "尽可能储备物资"
3. [world_building_script_22] "序列超凡者可对抗诡异"

# 总共22个Script节点，但只有3个被对齐
# "不要掉队"可能在未对齐的19个节点中
```

#### 原因3：对齐阈值过滤

```python
# layered_alignment_engine.py:385
if best_match and best_score > 0.3:  # 阈值
    alignments.append(...)
```

如果"不要掉队"被单独提取为一个节点，但与Novel的"车队铁律：不要掉队，尽可能多储备物资"相似度<0.3，则会被过滤掉。

### ✅ 解决方案

#### 方案1：优化Prompt（立即实施）

```yaml
extract_world_building:
  system: |
    【提取原则】
    1. 只提取"设定性"信息，不提取具体事件
    2. ⭐ 保持规则的完整性：
       - 如果规则有多条，必须全部提取
       - 记录规则间的优先级关系
       - 例如："铁律1：xxx，铁律2：yyy，铁律1优先于铁律2"
    3. 合并重复的设定（如"诡异无法被杀死"多次出现，只记录一次）
    4. ⭐ 对于重要规则（铁律、禁忌、核心规则），必须一字不漏地提取
    5. 忽略角色的主观感受
    
    【重要规则识别】
    标志词：铁律、禁忌、规则、不要XX、必须XX、第一条、第二条、优先于
```

#### 方案2：实现二次验证（中期实施）

```python
async def _verify_critical_rules(
    self,
    extracted_nodes: List[PlotNode],
    original_text: str
) -> List[PlotNode]:
    """
    验证关键规则是否被完整提取
    
    检测标志词：
    - "铁律"、"禁忌"、"规则"
    - "第一条"、"第二条"
    - "优先于"、"高于"
    
    如果检测到这些词，但节点中没有完整体现，
    触发二次提取prompt
    """
    pass
```

#### 方案3：降低对齐阈值（短期实施）

```python
# 对于world_building层，降低阈值
if layer == "world_building":
    threshold = 0.2  # 降低到0.2
else:
    threshold = 0.3
```

---

## 问题2：相似度评分过低（算法过于简单）

### 📊 案例详情

**Text1**: `诡异降临，城市成为人类禁区`  
**Text2**: `全球诡异爆发，城市成为人类禁区`

**人类感知相似度**: ~90% （核心意思完全一致）  
**算法计算相似度**: **0.6471** （仅基于字符重叠）

### 🔍 算法分析

**当前算法**：字符集Jaccard相似度
```python
def _calculate_simple_similarity(self, text1: str, text2: str) -> float:
    set1 = set(text1)  # {'诡', '异', '降', '临', ...}
    set2 = set(text2)  # {'全', '球', '诡', '异', '爆', '发', ...}
    
    intersection = set1 & set2  # 共同字符：11个
    union = set1 | set2          # 全部字符：17个
    
    return len(intersection) / len(union)  # 11/17 = 0.6471
```

**问题**：
1. ❌ **忽略语义**："降临" vs "爆发" - 意思相同，字符不同
2. ❌ **忽略顺序**：字符顺序不影响结果
3. ❌ **惩罚差异**："全球"增加2个字符 → 分数下降
4. ❌ **无词权重**：所有字符权重相同（"诡异"和"，"权重一样）

### 📉 更多案例

| Text1 | Text2 | 人类感知 | 算法得分 | 差距 |
|-------|-------|----------|----------|------|
| 诡异降临，城市成为人类禁区 | 全球诡异爆发，城市成为人类禁区 | 90% | 64.7% | ↓25.3% |
| 尽可能储备物资 | 车队铁律：不要掉队，尽可能多储备物资 | 40% | 41.2% | ✅ 接近 |
| 序列超凡者可对抗诡异 | 诡异无法被杀死，只有序列超凡能对付 | 85% | 35% | ↓50% |

**结论**：
- ✅ 短文本、差异大时，算法还可以
- ❌ 长文本、语义相近但用词不同时，算法失效

### ✅ 解决方案

#### 方案1：词级Jaccard（立即实施）✅

```python
import jieba

def _calculate_word_similarity(self, text1: str, text2: str) -> float:
    """基于分词的Jaccard相似度"""
    words1 = set(jieba.lcut(text1))
    words2 = set(jieba.lcut(text2))
    
    intersection = words1 & words2
    union = words1 | words2
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

# 测试效果：
# "诡异降临，城市成为人类禁区" vs "全球诡异爆发，城市成为人类禁区"
# 分词: ['诡异', '降临', '城市', '成为', '人类', '禁区']
#    vs ['全球', '诡异', '爆发', '城市', '成为', '人类', '禁区']
# 交集: ['诡异', '城市', '成为', '人类', '禁区'] = 5
# 并集: ['全球', '诡异', '降临', '爆发', '城市', '成为', '人类', '禁区'] = 8
# 得分: 5/8 = 0.625  （还是不理想，但比0.647略好）
```

#### 方案2：Embedding相似度（中期实施）⭐

```python
from sentence_transformers import SentenceTransformer

class LayeredAlignmentEngine:
    def __init__(self, ...):
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    def _calculate_embedding_similarity(self, text1: str, text2: str) -> float:
        """基于Embedding的余弦相似度"""
        emb1 = self.embedding_model.encode(text1)
        emb2 = self.embedding_model.encode(text2)
        
        # 余弦相似度
        from scipy.spatial.distance import cosine
        return 1 - cosine(emb1, emb2)

# 预期效果：
# "诡异降临，城市成为人类禁区" vs "全球诡异爆发，城市成为人类禁区"
# 得分: ~0.92  ✅ 符合人类感知！
```

#### 方案3：LLM语义判断（长期实施）⭐⭐

```python
async def _calculate_llm_similarity(self, text1: str, text2: str) -> float:
    """使用LLM判断语义相似度"""
    prompt = f"""
    比较以下两段文本的语义相似度，返回0-1之间的分数。
    
    文本1：{text1}
    文本2：{text2}
    
    评分标准：
    - 1.0：意思完全一致
    - 0.8-0.9：核心意思相同，细节略有差异
    - 0.6-0.7：部分相关
    - 0.3-0.5：有关联但主题不同
    - 0.0-0.2：无关
    
    只返回数字分数。
    """
    
    response = await self.llm_client.chat.completions.create(...)
    return float(response.choices[0].message.content)
```

#### 方案4：混合策略（推荐）⭐⭐⭐

```python
def _calculate_hybrid_similarity(self, text1: str, text2: str) -> float:
    """混合相似度计算"""
    # 1. 快速字符级过滤（<0.2直接排除）
    char_sim = self._calculate_simple_similarity(text1, text2)
    if char_sim < 0.2:
        return char_sim
    
    # 2. 词级Jaccard（主要）
    word_sim = self._calculate_word_similarity(text1, text2)
    
    # 3. 如果词级>0.5，用Embedding精确计算
    if word_sim > 0.5:
        emb_sim = self._calculate_embedding_similarity(text1, text2)
        return emb_sim
    
    return word_sim
```

---

## 问题3：items_equipment为0（Prompt Key不匹配）

### 🐛 Bug详情

**代码**（layered_alignment_engine.py:256）：
```python
for layer, prompt_key in [
    ("world_building", "extract_world_building"),
    ("game_mechanics", "extract_game_mechanics"),
    ("items_equipment", "extract_items_equipment"),  # ❌ 错误！
    ("plot_events", "extract_plot_events")
]:
```

**YAML**（layered_extraction.yaml:201）：
```yaml
extract_items:  # ✅ 正确的key名
  system: |
    你是一个道具追踪专家...
```

**结果**：
```python
layer_prompts = self.prompts.get("extract_items_equipment", {})
# 返回: {}  ← 找不到key！

if not layer_prompts:
    logger.warning(f"未找到prompt: extract_items_equipment，跳过")
    return []  # ❌ 返回空列表
```

### ✅ 修复方案（立即实施）

```python
# layered_alignment_engine.py:256
for layer, prompt_key in [
    ("world_building", "extract_world_building"),
    ("game_mechanics", "extract_game_mechanics"),
    ("items_equipment", "extract_items"),  # ✅ 修复
    ("plot_events", "extract_plot_events")
]:
```

**修复后预期效果**：
- ✅ 能正确提取道具信息（二八大杠、三轮车、手弩等）
- ✅ items_equipment层不再为0
- ✅ Overall Score提升（items_equipment权重10%）

---

## 问题4：缺乏优化机制（自反馈拟合系统）

### 🎯 目标

实现一个**自反馈的Prompt优化系统**，让对齐结果越来越准确。

### 💡 设计思路

利用现有的 **Heat-Driven Training System** 架构：

```
1. 用户标注 → 2. 计算Heat → 3. 优化Prompt → 4. 重新对齐 → 5. 评估改进
     ↑                                                              ↓
     └──────────────────────────── 反馈循环 ────────────────────────┘
```

### 📐 架构设计

#### 第1步：建立标注体系

```python
# src/core/schemas.py

class AlignmentAnnotation(BaseModel):
    """对齐标注"""
    project_id: str
    episode: str
    layer: str
    
    # 标注内容
    script_content: str
    novel_content: str
    is_correct_match: bool  # 是否正确匹配
    human_similarity: float  # 人类评估的相似度
    
    # 错误类型
    error_type: Optional[str] = None  # "missing", "incomplete", "wrong_match"
    correction: Optional[str] = None  # 正确答案
    
    # Heat计算
    heat_score: float = 0.0  # 问题严重程度
    
    timestamp: datetime = Field(default_factory=datetime.now)
```

#### 第2步：计算Heat（问题严重程度）

```python
# src/agents/alignment_evaluator.py

class AlignmentEvaluator:
    """对齐质量评估器"""
    
    def calculate_heat(self, annotation: AlignmentAnnotation) -> float:
        """
        计算Heat分数（0-100）
        
        Heat越高 = 问题越严重
        """
        heat = 0.0
        
        # 1. 是否错误匹配
        if not annotation.is_correct_match:
            heat += 50
        
        # 2. 相似度差距
        system_sim = annotation.system_similarity
        human_sim = annotation.human_similarity
        gap = abs(human_sim - system_sim)
        heat += gap * 50
        
        # 3. 错误类型严重性
        error_weights = {
            "missing": 40,  # 丢失关键信息（如铁律）
            "incomplete": 30,  # 提取不完整
            "wrong_match": 20,  # 错误匹配
        }
        heat += error_weights.get(annotation.error_type, 0)
        
        return min(heat, 100)
```

#### 第3步：Prompt自适应优化

```python
# src/agents/prompt_optimizer.py

class PromptOptimizer:
    """Prompt优化器"""
    
    async def optimize_prompt(
        self,
        layer: str,
        annotations: List[AlignmentAnnotation],
        current_prompt: str
    ) -> str:
        """
        基于标注数据优化Prompt
        
        策略：
        1. 聚合高Heat的错误案例
        2. 让LLM分析错误原因
        3. 生成新的Prompt指导
        """
        # 筛选高Heat案例（Heat>60）
        critical_errors = [a for a in annotations if a.heat_score > 60]
        
        # 构建优化Prompt
        optimization_prompt = f"""
        当前Prompt在提取{layer}层信息时存在以下问题：
        
        【错误案例】
        {self._format_error_cases(critical_errors)}
        
        【当前Prompt】
        {current_prompt}
        
        请分析错误原因，并优化Prompt的【提取原则】部分，
        确保：
        1. 明确指出要避免的错误
        2. 增加关键信息提取的强调
        3. 保持原有正确的部分
        
        只返回优化后的Prompt。
        """
        
        response = await self.llm_client.chat.completions.create(...)
        new_prompt = response.choices[0].message.content
        
        # 保存Prompt版本历史
        self._save_prompt_version(layer, new_prompt)
        
        return new_prompt
```

#### 第4步：A/B测试验证

```python
# src/workflows/alignment_improvement_workflow.py

class AlignmentImprovementWorkflow:
    """对齐改进工作流"""
    
    async def run_ab_test(
        self,
        project_id: str,
        episode: str,
        old_prompt: str,
        new_prompt: str
    ) -> Dict:
        """
        A/B测试：对比新旧Prompt效果
        """
        # 1. 使用旧Prompt对齐
        old_result = await self.align_with_prompt(
            project_id, episode, old_prompt
        )
        
        # 2. 使用新Prompt对齐
        new_result = await self.align_with_prompt(
            project_id, episode, new_prompt
        )
        
        # 3. 对比指标
        comparison = {
            "old_overall_score": old_result.overall_score,
            "new_overall_score": new_result.overall_score,
            "improvement": new_result.overall_score - old_result.overall_score,
            
            "old_coverage": old_result.layer_scores,
            "new_coverage": new_result.layer_scores,
            
            "recommendation": "adopt_new" if new_result.overall_score > old_result.overall_score else "keep_old"
        }
        
        return comparison
```

#### 第5步：持续监控与迭代

```python
# 数据结构

prompt_optimization_history/
├── world_building/
│   ├── v1.0_baseline.yaml        # 初始版本
│   ├── v1.1_fix_铁律丢失.yaml     # 修复铁律提取
│   ├── v1.2_improve_完整性.yaml   # 改进完整性
│   └── metrics.json              # 每个版本的性能指标
├── game_mechanics/
├── items_equipment/
└── plot_events/
```

### 📊 评估指标

| 指标 | 定义 | 目标 |
|------|------|------|
| **Precision** | 正确匹配数 / 总匹配数 | >0.90 |
| **Recall** | 正确匹配数 / 应匹配数 | >0.85 |
| **F1 Score** | Precision和Recall的调和平均 | >0.87 |
| **Similarity Gap** | \|人类评分 - 系统评分\| | <0.10 |
| **Heat Reduction** | 问题严重程度下降率 | >30% per iteration |

---

## 🚀 实施路线图

### Phase 1：立即修复（本周）

- [x] 📊 完成问题诊断分析
- [ ] 🐛 修复 items_equipment Key不匹配
- [ ] 📝 优化 world_building Prompt（强调完整性）
- [ ] 🧪 测试修复效果（PROJ_002/ep01）

### Phase 2：算法优化（下周）

- [ ] 🔧 实现词级Jaccard相似度
- [ ] 🤖 集成Embedding模型
- [ ] 📈 A/B测试对比效果
- [ ] 📚 更新文档

### Phase 3：自反馈系统（2周内）

- [ ] 🏗️ 设计标注界面（简单CLI）
- [ ] 💾 建立标注数据库
- [ ] 🔥 实现Heat计算
- [ ] 🤖 实现Prompt自动优化
- [ ] 🧪 A/B测试框架

### Phase 4：全面优化（1个月）

- [ ] 🔄 完整反馈循环
- [ ] 📊 监控Dashboard
- [ ] 🎯 扩展到所有项目
- [ ] 📖 编写优化文档

---

## 📝 总结

### 核心问题

1. ✅ **Prompt不够精确** → 导致提取不完整
2. ✅ **相似度算法过于简单** → 导致评分不准
3. ✅ **Key配置错误** → 导致功能缺失
4. ✅ **缺乏优化机制** → 导致无法改进

### 最佳实践建议

1. **Prompt设计**：
   - ✅ 明确"完整性"要求
   - ✅ 提供正反例
   - ✅ 强调关键信息

2. **相似度计算**：
   - ✅ 混合策略（字符+词+Embedding）
   - ✅ 分层阈值（不同层不同标准）
   - ✅ 人工验证样本

3. **质量保证**：
   - ✅ 单元测试覆盖
   - ✅ 回归测试
   - ✅ 人工抽检

4. **持续改进**：
   - ✅ 建立标注体系
   - ✅ 实现自反馈
   - ✅ A/B测试验证

---

**文档状态**: ✅ 完成  
**下一步**: 执行 Phase 1 修复计划  
**更新时间**: 2026-02-05
