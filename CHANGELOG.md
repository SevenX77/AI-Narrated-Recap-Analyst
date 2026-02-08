# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project structure reset and cleanup
- Documentation structure aligned with code structure
- 18-tool development roadmap (Phase I: Material Processing, Phase II: Analysis & Alignment)
- **LLMClientManager**: 双 LLM Provider 统一管理 (Core Infrastructure)
  - ✅ 支持 Claude 和 DeepSeek 同时使用
  - ✅ 单例模式管理客户端实例（避免重复创建）
  - ✅ 自动使用统计（Token 消耗、调用次数、响应时间）
  - ✅ 工具级别灵活指定 Provider（代码层面配置，无需环境变量映射）
  - ✅ 功能分工策略：简单任务用 DeepSeek，复杂任务用 Claude
  - 📍 位置：`src/core/llm_client_manager.py`
  - 📚 文档：`docs/core/DUAL_LLM_SETUP.md`
  - 🧪 测试：`scripts/test/test_dual_llm_providers.py`
  - 💡 示例：`scripts/examples/example_dual_llm_usage.py`
- **NovelImporter** tool: 小说导入与规范化工具 (Phase I - P0 优先级)
  - ✅ 自动编码检测与转换（UTF-8, GBK, GB2312等）
  - ✅ 规范化换行符和BOM标记
  - ✅ **合并多余空行**（连续空行合并为单行，提升后续LLM分析质量）
  - ✅ **章节标题间添加空行**（便于区分章节，提升可读性）
  - ✅ 基础格式验证
  - ✅ **保存到项目标准位置** `data/projects/{project_name}/raw/novel.txt`
  - ✅ 完整的测试脚本和临时输出功能
  - ✅ 支持两种模式：完整导入（保存到磁盘）和内存处理（Workflow用）
- **schemas_novel.py**: 小说处理数据模型定义
  - `NovelImportResult`: 小说导入结果模型（包含保存路径和元数据）
  - `NormalizedNovelText`: 规范化文本数据模型（已废弃，使用 NovelImportResult）
  - `NovelMetadata`: 小说元数据模型
  - `ChapterInfo`: 章节信息模型
  - `Paragraph`: 段落模型
- **TestOutputManager**: 测试辅助工具，统一管理临时文件输出
- **NovelMetadataExtractor** tool: 小说元数据提取工具 (Phase I - P1 优先级)
  - ✅ 提取标题、作者信息
  - ✅ 智能标签提取（只从简介区域，避免误提取正文内容）
  - ✅ 简介智能过滤（LLM优先 + 规则降级）
    - 移除标签行、营销文案、书名变体
    - 保留世界观、主角设定、核心冲突
  - ✅ 完整的错误处理和日志记录
  - ✅ 完整的测试脚本（包含LLM vs 规则对比）
  - ✅ **支持双 LLM Provider**：默认使用 DeepSeek（简单任务，速度快）
- **NovelChapterDetector** tool: 小说章节检测工具 (Phase I - P1 优先级)
  - ✅ 识别章节标题边界（支持多种格式：第X章、Chapter X等）
  - ✅ 提取章节序号和标题
  - ✅ 计算章节位置信息（行号、字符位置）
  - ✅ 统计章节字数
  - ✅ 验证章节连续性（可选）
  - ✅ 完整的测试脚本（包含章节提取验证）
- **NovelSegmenter** tool: 小说叙事分段分析工具 (Phase I - P0 优先级)
  - ✅ 纯LLM驱动的叙事功能分段（非规则匹配）
  - ✅ **结构性分段策略**：只有世界观设定、叙事事件节点、核心转折才独立分段
  - ✅ **合并连续场景**：同一时空下的连续动作合并为一个段落（避免过度分段）
  - ✅ 识别段落类型（对话/叙述/描写/混合）
  - ✅ 标注叙事功能（开篇钩子、核心转折、世界观建立等）
  - ✅ 标注浓缩优先级（P0骨架/P1血肉/P2皮肤）
  - ✅ 生成Markdown格式的详细分析报告
  - ✅ 支持整章一次性分析
  - ✅ 完整的测试脚本（包含与标准分析对比）
  - ✅ **支持双 LLM Provider**：默认使用 Claude（复杂分析，质量优先）

### Changed
- Separated Fanqie novel crawler to independent project
- Archived V2 workflows, tools, agents, and modules
- Restructured docs/ directory to mirror src/ structure
- **LLM 配置架构重构**：从单一 Provider 切换到多 Provider 并存模式
  - 工具层面指定 Provider（`provider="claude"` 或 `provider="deepseek"`）
  - 移除对全局 `LLM_PROVIDER` 环境变量的强依赖
  - 统一通过 `LLMClientManager` 管理所有 LLM 调用

### Removed
- V2 ingestion and migration workflows (archived)
- V2 material processing tools (archived)
- V2 alignment and optimization modules (archived)

---

## Version History

**Note**: Detailed version history from V1.0 and V2.0 has been archived.  
See `archive/docs/v2_maintenance/` for historical records.

---

### 技术亮点
- **纯LLM驱动分段**: `NovelSegmenter` 不依赖规则匹配，完全由LLM理解叙事功能并分段
- **一次性处理**: 整章内容一次性输入LLM，保证语义完整性
- **Markdown输出**: 生成人类可读的分析报告，便于人工审查和调整
- **双 LLM Provider 架构**: 
  - 工具层面灵活选择 Claude（高质量）或 DeepSeek（高性价比）
  - 自动使用统计，优化成本控制
  - 功能分工策略：简单任务用 DeepSeek，复杂任务用 Claude
  - 测试显示 DeepSeek 响应速度是 Claude 的 2 倍（1.9s vs 4.1s）

---

*Last Updated: 2026-02-09*
