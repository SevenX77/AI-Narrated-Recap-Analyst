# 爆款标记功能更新说明

## 📋 更新概述

**更新时间**: 2026-02-03  
**功能**: 增加 `is_explosive` 爆款标记字段，作为热度值的辅助验证指标

---

## 🎯 功能说明

### 背景

热度值（`heat_score`）是基于单日观看时长的指标，但有些剧集在热度榜上持续多天，综合市场影响力更大，这类项目应该获得更高的可信度。

### 解决方案

增加人为判断的 `is_explosive` 标记，作为 `heat_score` 的补充验证：

- **主要依据**: `heat_score`（必填，0-10分）
- **辅助验证**: `is_explosive`（选填，true/false）
- **权重加成**: 标记为爆款的项目在规则提取时获得10-15%的置信度加成

---

## 📊 判断标准

### is_explosive = true 的条件

满足以下任意2项或以上：

1. **持续性**: 在热度榜上连续3天以上进入前10
2. **稳定性**: 多日热度值稳定在高位（如连续保持≥7分）
3. **影响力**: 引发大量讨论、二创、模仿等市场效应

### 示例

```json
{
  "PROJ_002": {
    "heat_score": 9.5,
    "is_explosive": true,
    "notes": "热度榜持续5天保持前3，引发大量二创"
  },
  "PROJ_003": {
    "heat_score": 8.2,
    "is_explosive": false,
    "notes": "单日冲上第1，但第二天就跌出前10"
  }
}
```

---

## 🔧 技术实现

### 1. 数据结构更新

**project_index.json**:
```json
{
  "projects": {
    "PROJ_XXX": {
      "heat_score": 9.5,
      "is_explosive": true,
      "notes": "说明依据"
    }
  },
  "is_explosive_definition": {
    "description": "爆款标记，人为判断的辅助指标",
    "weight_bonus": "约10-15%置信度加成"
  }
}
```

### 2. 规则提取逻辑

**RuleExtractorAgent** (`src/agents/rule_extractor.py`):

```python
def extract_rules_from_projects(
    self,
    projects_data: Dict[str, Dict[str, Any]],
    heat_scores: Dict[str, float],
    explosive_flags: Optional[Dict[str, bool]] = None  # 新增参数
) -> RuleBook:
```

**处理逻辑**:
1. 在项目摘要中标注爆款项目：`🔥 [已验证爆款]`
2. 提高爆款项目特征的权重和置信度
3. 在RuleBook的metadata中记录爆款项目列表

### 3. Prompt优化

**rule_extraction.yaml**:
```yaml
【说明】
- is_explosive: 爆款标记（true表示在热度榜持续多天，已验证为真正的爆款）
- confidence_level: 标记为爆款的项目具有更高的可信度

【任务】
**爆款标记的影响**：对于 is_explosive=true 的项目，其特征应该获得更高的权重和置信度（建议在原权重基础上+10-15%）
```

### 4. Workflow集成

**training_workflow_v2.py**:
- 自动从 `project_index.json` 读取 `is_explosive` 标记
- 在日志中显示爆款项目：`✅ PROJ_002: 热度=9.5 🔥`
- 传递给 RuleExtractorAgent

---

## 📖 使用指南

### 填写步骤

1. **确定热度值**（必填）
   ```json
   "heat_score": 9.5
   ```

2. **判断是否爆款**（选填）
   - 如果在热度榜持续多天 → `"is_explosive": true`
   - 如果仅单日表现好 → `"is_explosive": false`

3. **添加说明**（推荐）
   ```json
   "notes": "热度榜持续5天，引发大量讨论"
   ```

### 示例场景

**场景1: 持续爆款**
```json
{
  "name": "末哥超凡公路",
  "heat_score": 9.5,
  "is_explosive": true,
  "notes": "热度榜第1位持续5天，完播率85%，评论超10万"
}
```
→ 规则提取时权重最高，可信度最高

**场景2: 单日爆发**
```json
{
  "name": "某剧",
  "heat_score": 9.0,
  "is_explosive": false,
  "notes": "首播当日冲上第1，次日跌至第15"
}
```
→ 规则提取时按标准权重，热度值依然很高

**场景3: 持续中热**
```json
{
  "name": "某剧",
  "heat_score": 6.5,
  "is_explosive": true,
  "notes": "虽然单日热度不高，但在榜上稳定持续10天"
}
```
→ 规则提取时获得加成，适合提取"稳定性"特征

---

## ⚠️ 注意事项

### 1. 主次关系
- **主要依据**: `heat_score`（数值基准）
- **辅助参考**: `is_explosive`（可信度加成）
- 不能用 `is_explosive=true` 弥补低 `heat_score`

### 2. 谨慎标记
- 只标记明确验证过的爆款
- 避免误标导致规则偏差
- 宁缺毋滥

### 3. 组合策略

| heat_score | is_explosive | 适用场景 |
|-----------|--------------|---------|
| 9-10 | true | 💎 最佳样本：提取核心规则 |
| 9-10 | false | ⭐ 优秀样本：提取爆发力规则 |
| 7-8 | true | 🎯 稳定样本：提取持续性规则 |
| 7-8 | false | 📊 良好样本：常规参考 |
| <7 | true | ⚡ 特殊样本：提取细分规则 |
| <7 | false | 📝 一般样本：对比参考 |

---

## 📁 更新文件列表

- ✅ `data/project_index.json` - 增加字段定义
- ✅ `src/agents/rule_extractor.py` - 支持爆款标记
- ✅ `src/workflows/training_workflow_v2.py` - 读取并传递标记
- ✅ `src/prompts/rule_extraction.yaml` - 优化prompt
- ✅ `docs/HEAT_DRIVEN_TRAINING_SYSTEM.md` - 更新文档
- ✅ `docs/maintenance/EXPLOSIVE_FLAG_UPDATE.md` - 本文档

---

## 🔮 未来扩展

1. **自动判断**: 基于多日热度数据自动标记
2. **分级标记**: explosive_level (1-3级)
3. **持续时间**: explosive_days (持续天数)
4. **影响力指标**: engagement_score (评论/点赞/转发)

---

*Last Updated: 2026-02-03*
