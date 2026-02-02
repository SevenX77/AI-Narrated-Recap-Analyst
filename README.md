# AI-Narrated Recap Analyst (AI 爆款解说生成器)

## 项目愿景
本项目旨在构建一个**全自动化的爆款短视频解说生成系统**。
我们的目标不仅仅是“转换文本”，而是**复刻并超越**人类金牌解说员的创作能力，通过严谨的工程架构和数据反馈机制，稳定产出具有高完播率、高互动率的解说视频文案与分镜。

## 核心痛点与解决方案

### 1. 解决 AI 长文本“崩坏”问题
**痛点**：传统 LLM 在处理长篇小说时，容易遗忘前文设定、丢失剧情框架、忽略爆款节奏规则。
**方案**：**结构化状态机 (Structured State Machine)**
- **Chunking Strategy**: 不直接处理全文，而是基于语义切片。
- **Memory Bus (记忆总线)**: 独立维护“世界观”、“主角状态”、“当前冲突”等元数据，随剧情推进动态更新，确保 AI 永远“记得”当前上下文。
- **Critic-Refine Loop**: 引入“审稿人”Agent，基于硬性规则（如黄金三秒、情绪钩子）对生成内容进行多轮打磨。

### 2. 构建自动进化的反馈系统 (Self-Evolving System)
**痛点**：Prompt 工程难以量化效果，缺乏基于真实数据的优化闭环。
**方案**：**DSPy-like Optimization & Data Flywheel**
- **Ground Truth Training**: 利用现有的“小说原文 -> 爆款解说稿”配对数据，自动反向优化 Prompt 策略和小模型参数。
- **Real-world Feedback**: 接入视频投放数据（完播率、点赞等），将高表现样本自动回流至训练集，持续进化生成策略。

## 系统架构概览

### Phase 1: Narrative Agent (文案生成)
- **Input**: 小说原文
- **Process**: 
    1. **剧情提取**: 识别爽点、冲突、关键转折。
    2. **策略映射**: 匹配爆款解说模板（如倒叙开场、情绪递进）。
    3. **文案生成**: 结合记忆总线生成口语化文案。
- **Output**: 爆款解说稿

### Phase 2: Visual Director (分镜生成)
- **Input**: 解说稿
- **Process**: 
    1. **KV 映射**: 将抽象文案转化为具象画面描述。
    2. **一致性控制**: 确保角色形象和场景风格的连续性。
- **Output**: 包含 Image Prompt 的分镜脚本

### Phase 3: Feedback Engine (反馈引擎)
- **Input**: 历史案例、人工修正记录、投放数据
- **Process**: 自动评估生成质量，动态调整 Agent 的 System Prompt 和 Few-Shot Examples。
