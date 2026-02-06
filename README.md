# AI-Narrated Recap Analyst (AI 爆款解说生成器)

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

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

## 🚀 核心特性

### 1. 动态章节提取 (Adaptive Chapter Extraction)
- **智能预估**: 根据SRT数量自动计算初始提取章节数
- **质量驱动**: 实时评估对齐质量（置信度、覆盖率、连续性）
- **自适应策略**: 根据评估结果动态决定是否继续提取
- **安全缓冲**: 防止遗漏更好的匹配

### 2. 并发优化 (Concurrent Processing)
- **异步LLM调用**: 支持多章节/多chunk并发提取
- **智能限流**: Semaphore控制并发数，避免API rate limit
- **性能提升**: 理论加速10倍（10并发时）

### 3. 质量评估系统 (Quality Evaluation)
- **多维度评分**:
  - 平均置信度 (40%)
  - 整体覆盖率 (40%)
  - 章节连续性 (20%)
- **合格标准**: 综合得分 ≥ 70分
- **详细报告**: 每集覆盖情况、匹配章节范围

## 📖 使用指南

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置API Key
```bash
export DEEPSEEK_API_KEY="your_api_key"
# 或编辑 .env 文件
```

### 运行工作流

#### 1. 数据摄入与对齐 (Ingestion Workflow)
```bash
# 使用动态章节提取
python main.py ingest --id PROJ_002

# 强制指定章节数
python main.py ingest --id PROJ_002 --max-chapters 50
```

#### 2. 生产流程 (Production)
```bash
python main.py generate --id PROJ_002
```

### 配置调整

编辑 `src/core/config.py`:
```python
@dataclass
class IngestionConfig:
    initial_chapter_multiplier: int = 2  # 初始章节倍数
    batch_size: int = 10  # 每批提取数
    safety_buffer_chapters: int = 10  # 安全缓冲
    quality_threshold: float = 70.0  # 合格分数
    max_concurrent_requests: int = 10  # 最大并发
    enable_concurrent: bool = True  # 启用并发
```

## 📊 质量报告示例

```
📊 最终对齐质量报告
============================================================
   综合得分: 75.50/100
   平均置信度: 82.30%
   整体覆盖率: 85.20%
   章节连续性: 92.00%
   是否合格: ✅ 是

   各集覆盖情况:
     - ep01: 18/20 (90.0%) [第1章 - 第8章]
     - ep02: 17/20 (85.0%) [第8章 - 第15章]
     - ep03: 15/18 (83.3%) [第15章 - 第22章]
============================================================
```

## 📚 文档索引

### 核心文档
- **项目结构**: `docs/PROJECT_STRUCTURE.md` - 项目文件组织与说明
- **开发标准**: `docs/DEV_STANDARDS.md` - 代码规范与最佳实践
- **架构文档**: `docs/architecture/logic_flows.md` - 系统架构与数据流

### 功能优化文档
- **摄入优化部署**: `docs/maintenance/ingestion_optimization_deployment.md` - 动态章节提取部署指南
- **摄入优化进度**: `docs/maintenance/ingestion_optimization_progress.md` - 功能开发进度与使用说明

### 示例代码
- **使用示例**: `scripts/examples/` - 实际使用示例脚本
