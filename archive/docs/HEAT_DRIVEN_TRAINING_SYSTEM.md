# 热度驱动训练系统 (Heat-Driven Training System)

## 📋 系统概述

热度驱动训练系统是一个基于真实市场数据的内容质量评估框架，通过分析多个不同热度的Ground Truth项目，提取爆款规则并用于评估新生成的内容。

### 核心理念

```
真实热度数据 → 提取爆款规则 → 验证规则有效性 → 评估新内容 → 预测潜在热度
```

### 三大优势

1. **数据驱动**：基于真实播放数据，不是主观判断
2. **可解释性**：每个评分都有具体的GT对比示例
3. **可预测性**：能预测新内容的潜在市场表现

---

## 🏗️ 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                  项目索引 (project_index.json)          │
│  - 存储各项目的热度值 (heat_score: 0-10)               │
│  - 标记Ground Truth项目 (is_ground_truth: true)         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           阶段1: 规则提取 (Rule Extraction)             │
│  Agent: RuleExtractorAgent                              │
│  输入: 多个GT项目 + 热度值                              │
│  输出: RuleBook (爆款规则库)                            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           阶段2: 规则验证 (Rule Validation)             │
│  Agent: RuleValidatorAgent                              │
│  输入: RuleBook + GT项目数据                            │
│  输出: ValidationResult (相关性分析)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│         阶段3: 内容评估 (Content Evaluation)            │
│  Agent: ComparativeEvaluatorAgent                       │
│  输入: Generated内容 + RuleBook + GT参考                │
│  输出: ComparativeFeedback (详细评估报告)               │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型

### 1. 热度值与爆款标记

在 `project_index.json` 中定义：

```json
{
  "heat_score_definition": {
    "description": "热度评分，代表项目的真实市场表现（单日观看时长相关）",
    "scale": "0-10分",
    "reference": {
      "9-10": "超高热度：单日表现极佳",
      "7-8": "高热：单日表现优秀",
      "5-6": "中等：单日表现一般",
      "3-4": "低热：单日表现较差",
      "0-2": "冷门：单日表现很差"
    },
    "usage": "用于规则优化和质量预测的主要基准数据"
  },
  "is_explosive_definition": {
    "description": "爆款标记，人为判断的辅助指标",
    "criteria": [
      "在热度榜上持续多天（如连续3天以上进入前10）",
      "多日热度值稳定在高位（如连续保持7分以上）",
      "综合市场影响力大（如引发讨论、二创等）"
    ],
    "usage": "作为热度值的补充验证，增加规则提取的可信度。主要判断依据仍是heat_score，is_explosive只是辅助参考",
    "weight_bonus": "标记为爆款的项目在规则提取时会获得额外的置信度加成（约10-15%）"
  }
}
```

**使用逻辑**：
- `heat_score`（必填）：主要判断依据，基于单日观看时长
- `is_explosive`（选填）：辅助验证，基于多日持续表现
- 两者结合使用：heat_score提供数值基准，is_explosive提供可信度加成

### 2. 规则库结构 (RuleBook)

```python
{
  "version": "v1.0",
  "extracted_from_projects": ["PROJ_002", "PROJ_003"],
  "project_heat_scores": {
    "PROJ_002": 9.5,
    "PROJ_003": 6.0
  },
  "hook_rules": [
    {
      "rule_id": "HOOK_001",
      "dimension": "information_density",
      "rule_text": "信息密度≥1.15个关键点/秒",
      "weight": 9,
      "threshold": {"min": 1.15, "optimal": 1.3},
      "evidence": {
        "PROJ_002": {"value": 1.2, "heat_score": 9.5},
        "PROJ_003": {"value": 0.8, "heat_score": 6.0}
      }
    }
  ],
  "ep01_rules": [...],
  "ep02_plus_rules": [...],
  "duration_patterns": {...},
  "heat_prediction_accuracy": 0.95
}
```

### 3. 评估报告结构 (ComparativeFeedback)

```python
{
  "total_score": 78.5,
  "predicted_heat_score": 7.2,
  "gt_project_id": "PROJ_002",
  "gt_heat_score": 9.5,
  "score_gap": -13.5,
  
  "dimension_scores": [
    {
      "dimension": "hook_strength",
      "score": 30,
      "max_score": 40,
      "violations": [
        {
          "rule_id": "HOOK_001",
          "severity": "major",
          "deduction": 8,
          "comparison": {
            "ground_truth_example": "【00:00-00:03】诡异末日爆发的那天...",
            "generated_example": "【00:00-00:03】这是一个关于末日的故事",
            "issue": "缺少具体场景和冲击力",
            "suggestion": "改为具体场景描述"
          }
        }
      ]
    }
  ],
  
  "similarity_metrics": {
    "length_ratio": 1.15,
    "pacing_similarity": 0.76,
    "keyword_overlap": 0.68
  },
  
  "recommendation": "improve"
}
```

---

## 🚀 使用指南

### 步骤1: 准备Ground Truth数据

编辑 `data/project_index.json`，为GT项目添加热度值和爆款标记：

```json
{
  "projects": {
    "PROJ_002": {
      "name": "末哥超凡公路",
      "heat_score": 9.5,
      "is_ground_truth": true,
      "is_explosive": true,
      "notes": "爆款案例，在热度榜持续5天，用于规则提取"
    },
    "PROJ_001": {
      "name": "超前崛起",
      "heat_score": 6.0,
      "is_ground_truth": true,
      "is_explosive": false,
      "notes": "中等热度，单日表现良好但未持续"
    }
  }
}
```

**填写说明**：
- `heat_score`（必填）：填入真实的单日热度值（0-10分）
- `is_ground_truth`（必填）：是否作为训练数据（true/false）
- `is_explosive`（选填）：是否为已验证的爆款
  - true：在热度榜持续多天 + 多日稳定高位 + 市场影响力大
  - false：仅单日表现好，或热度未持续
- `notes`：说明热度来源和判断依据

### 步骤2: 运行规则提取

```python
from src.workflows.training_workflow_v2 import HeatDrivenTrainingWorkflow

workflow = HeatDrivenTrainingWorkflow()

# 提取规则
rulebook = await workflow.run(mode="extract")

# 输出: data/rule_books/rulebook_v1.0_latest.json
```

### 步骤3: 验证规则

```python
# 验证规则能否预测热度
validation_result = await workflow.run(mode="validate")

print(f"相关性: {validation_result.correlation}")
print(f"是否有效: {validation_result.is_valid}")

# 如果 correlation >= 0.85，规则验证通过
```

### 步骤4: 评估新内容

```python
# 评估新生成的内容
feedback = await workflow.run(
    mode="evaluate",
    project_id="PROJ_002"
)

print(f"得分: {feedback.total_score}/100")
print(f"预测热度: {feedback.predicted_heat_score}/10")
print(f"建议: {feedback.recommendation}")
```

### 步骤5: 完整流程

```python
# 一次性运行：提取→验证→评估
results = await workflow.run(
    mode="full",
    eval_project_id="PROJ_002"
)
```

---

## 📈 评分维度

### Hook类型（前30秒）

| 维度 | 权重 | 评判标准 |
|------|------|----------|
| Hook强度 | 40% | 前3秒冲击力、世界观展示、能力系统 |
| 信息密度 | 30% | 每秒关键信息点数量 |
| 节奏控制 | 20% | 句子时长、层层递进 |
| 时长控制 | 10% | 总时长、句长分布 |

### Ep01类型（第一集主体）

| 维度 | 权重 | 评判标准 |
|------|------|----------|
| 节奏控制 | 35% | 冲突点密集度、避免长描述 |
| 信息密度 | 30% | 高密度剧情推进 |
| 爽点频率 | 25% | 冲突/奖励/反转的密度 |
| 结尾悬念 | 10% | 引导下一集 |

### Ep02+类型（第二集及之后）

| 维度 | 权重 | 评判标准 |
|------|------|----------|
| 水时长技巧 | 30% | 次要人物、环境、心理描写 |
| 节奏控制 | 25% | 比Ep01慢20-30% |
| 连续性 | 25% | 与前集衔接、保持悬念 |
| 爽点维持 | 20% | 保留小爽点 |

---

## 🔄 规则优化循环

```
1. 提取规则（从多个GT项目）
   ↓
2. 验证规则（计算与热度的相关性）
   ↓
3. 相关性 >= 0.85？
   ├─ 是 → 规则有效，可用于评估
   └─ 否 → 调整权重/阈值，返回步骤2
```

### 优化策略

1. **维度重要性分析**
   - 如果某维度在所有爆款中都得高分 → 提高权重
   - 如果某维度在低热项目中也得高分 → 降低权重

2. **阈值调整**
   - 如果爆款项目都超过某阈值 → 提高阈值
   - 如果阈值过严导致爆款也不达标 → 降低阈值

3. **新规则发现**
   - 通过对比发现爆款的共同特征
   - 添加新规则并分配权重

---

## 📁 文件结构

```
src/
├── core/
│   └── schemas_feedback.py          # 热度驱动系统的数据模型
├── agents/
│   ├── rule_extractor.py            # 规则提取Agent
│   ├── rule_validator.py            # 规则验证Agent
│   └── comparative_evaluator.py     # 对比评估Agent
├── workflows/
│   └── training_workflow_v2.py      # 热度驱动训练工作流
└── prompts/
    ├── rule_extraction.yaml         # 规则提取Prompts
    ├── rule_validation.yaml         # 规则验证Prompts
    └── comparative_evaluation.yaml  # 对比评估Prompts

data/
├── project_index.json               # 项目索引（含热度值）
└── rule_books/                      # 规则库存储目录
    ├── rulebook_v1.0_latest.json
    └── validation_v1.0_*.json

scripts/examples/
└── test_heat_driven_training.py     # 测试脚本
```

---

## 🧪 测试

运行测试脚本：

```bash
cd /path/to/project
python scripts/examples/test_heat_driven_training.py
```

测试模式：
- `extract`: 仅测试规则提取
- `validate`: 测试规则提取+验证
- `evaluate`: 测试规则提取+内容评估
- `full`: 完整流程测试

---

## 💡 最佳实践

### 1. Ground Truth选择

- 至少需要2个不同热度的GT项目
- 建议包含：1个爆款（9+分）+ 1个中等（5-7分）
- 热度差距越大，规则区分度越高

**爆款标记使用建议**：
- 优先标记：热度榜持续3天以上 + 单日热度≥7分的项目
- 谨慎标记：避免误标，只标记明确验证过的爆款
- 权重加成：标记为爆款的项目在规则提取时会获得10-15%的置信度加成
- 主次关系：`is_explosive=true` 是加分项，不能弥补低 `heat_score`

### 2. 规则迭代

- 初次提取后必须验证
- 相关性<0.85时需要优化
- 随着更多GT项目加入，定期重新提取规则

### 3. 评估应用

- 新内容评估时选择热度最高的GT作为参考
- 关注"致命问题"（扣分>5）优先改进
- 预测热度<7分建议重写

---

## 🔮 未来扩展

1. **多维度热度**
   - 增加完播率、互动率等细分指标
   - 针对不同平台的热度标准

2. **自动优化**
   - 基于验证结果自动调整权重
   - 机器学习模型预测热度

3. **实时反馈**
   - 内容发布后的真实热度回流
   - 持续优化规则库

---

*Last Updated: 2026-02-03*
