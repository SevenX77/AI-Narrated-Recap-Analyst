# Heat-Driven Training Workflow (热度驱动训练工作流)

## 职责 (Responsibility)
`HeatDrivenTrainingWorkflow` (V2) 是一个闭环的自我优化系统。它利用已知的爆款项目（Ground Truth）作为训练数据，提取成功的叙事规则，并利用这些规则来评估和指导新内容的生成。

## 核心概念

- **Ground Truth (GT)**: 已知热度高、表现好的项目数据。
- **Rule Book (规则库)**: 从 GT 项目中提取的一组可量化的叙事规则（如"前3分钟必须出现Hook"）。
- **Heat Score (热度值)**: 用于量化项目表现的指标。

## 接口 (Interface)

### `run(mode: str, **kwargs)`

支持四种运行模式：
1. **extract**: 从 GT 项目提取规则。
2. **validate**: 验证规则库对热度的预测能力。
3. **evaluate**: 使用规则库评估新生成的内容。
4. **full**: 执行完整流程 (提取 -> 验证 -> 评估)。

## 实现逻辑 (Implementation Logic)

### 阶段 1: 规则提取 (Rule Extraction)
1. 加载项目索引，筛选 `is_ground_truth=True` 的项目。
2. 加载这些项目的详细数据（剧本、事件、Hook信息）。
3. 调用 `RuleExtractorAgent` (LLM) 分析高热度项目的共同特征。
4. 生成 `RuleBook` 并保存。

### 阶段 2: 规则验证 (Rule Validation)
1. 使用提取的 `RuleBook` 对 GT 项目进行打分。
2. 计算 "规则打分" 与 "实际热度" 之间的相关性 (Correlation)。
3. 如果相关性高，说明规则有效；否则生成优化建议。

### 阶段 3: 内容评估 (Content Evaluation)
1. 加载待评估项目的生成内容（如 `ep01_script.json`）。
2. 选择一个最相似的高热度 GT 项目作为参考锚点。
3. 调用 `ComparativeEvaluatorAgent` (LLM) 进行对比分析。
4. 输出评分、预测热度和修改建议。

## 依赖 (Dependencies)
- **Agents**:
  - `RuleExtractorAgent`
  - `RuleValidatorAgent`
  - `ComparativeEvaluatorAgent`
- **Schemas**: `src.core.schemas_feedback.*`
- **Managers**: `ProjectManager`, `ArtifactManager`

## 示例代码 (Code Example)

```python
from src.workflows.training_workflow_v2 import HeatDrivenTrainingWorkflow

workflow = HeatDrivenTrainingWorkflow()

# 运行完整流程
await workflow.run(
    mode="full",
    eval_project_id="PROJ_NEW_001"
)
```
