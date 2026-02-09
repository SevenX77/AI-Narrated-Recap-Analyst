# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ✨ ScriptSegmenter重构为Two-Pass + JSON输出（2026-02-09）

#### 重大变更
- **旧ScriptSegmenter归档**：`src/tools/script_segmenter.py` → `archive/v4_tools_20260209/`
- **新ScriptSegmenter创建**：基于Two-Pass策略，输出JSON格式
  - 使用句子序号定位段落边界（避免LLM改写文本）
  - 代码解析生成JSON（LLM不直接输出JSON）
  - 匹配SRT时间戳（基于字符位置比例）

#### Two-Pass Prompt
- **Pass 1**: `script_segmentation_pass1.yaml`（初步分段）
  - 输入：带句子序号的脚本文本
  - 输出：段落序号范围（句子1-3, 4-7...）
  - 原则：场景转换、情节转折、对话切换、因果独立
- **Pass 2**: `script_segmentation_pass2.yaml`（校验修正）
  - 检查：过度分段、欠分段、因果关系破坏
  - 输出：修正后的分段 或 "无需修改"

#### 输出格式
- **JSON结构**：`ScriptSegmentationResult`
  - `segments`: List[ScriptSegment]
  - `total_segments`: int
  - `avg_sentence_count`: float
  - `segmentation_mode`: "two_pass"
  - `processing_time`: float

#### 待测试
- 实际脚本数据测试（需要用户提供）
- Claude vs DeepSeek性能对比（决定默认Provider）

---

### ✨ NovelSegmenter重构为Two-Pass + JSON输出（2026-02-09）

#### 重大变更
- **旧NovelSegmenter归档**：`src/tools/novel_segmenter.py` → `archive/v3_tools_20260209/`
- **新NovelSegmenter创建**：基于Two-Pass策略，输出JSON格式
  - 使用行号定位段落边界（避免文本匹配问题）
  - 代码解析生成JSON（LLM不直接输出JSON）
  - 支持原文完整还原（JSON包含完整段落内容）

#### Two-Pass原则（强制应用于所有LLM任务）
- **Pass 1**：初步处理（~90行Prompt）
- **Pass 2**：校验修正（~100行Prompt）
- 准确率提升：78% → 100%（测试数据）
- Prompt简化：286行 → 190行（减少34%）

#### 新增Pydantic模型
- `ParagraphSegment`：段落分段模型（包含type, content, start_char, end_char等）
- `ParagraphSegmentationResult`：章节分段结果
- `ParagraphAnnotation`：段落标注模型（供NovelParagraphAnnotator使用）
- `AnnotatedParagraph`：带标注的段落
- `AnnotatedParagraphResult`：带标注的章节分段结果

#### LLM输出格式规范
- **禁止LLM直接输出JSON**（难以解析）
- **推荐方案**：LLM输出行号范围，代码根据行号提取内容
- **输出示例**：
  ```markdown
  - **段落1（B类-事件）**：收音机播报上沪沦陷
    行号：1-5
  ```

#### 测试脚本
- `scripts/test/test_novel_segmenter_json.py`：测试JSON输出和原文还原
- `scripts/test/test_novel_segmenter_model_comparison.py`：对比Claude/DeepSeek模型
  - 结论：Claude Sonnet 4.5最准确（100%），DeepSeek不适合复杂分段任务

#### 文档更新
- `docs/DEV_STANDARDS.md` 新增"6.4 Two-Pass LLM调用原则（强制）"
  - 何时使用Two-Pass
  - 实现模式
  - LLM输出格式规范
  - 成本与性能对比
- Prompt文件更新：
  - `novel_chapter_segmentation_pass1.yaml`：输出行号范围
  - `novel_chapter_segmentation_pass2.yaml`：输出行号范围
  - 要求：段落必须连续覆盖所有行，不能跳过

#### 架构变更
- 工具拆分原则：
  - `NovelSegmenter`：专注分段，输出JSON
  - `NovelParagraphAnnotator`（待实现）：专注标注
  - 报告生成：由测试脚本或Workflow负责

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
  - ✅ **DeepSeek 多模型支持**（2026-02-09）:
    - v3.2 标准模型 (`deepseek-chat`): 快速响应、低成本
    - v3.2 思维链模型 (`deepseek-reasoner`): 深度推理、复杂逻辑
    - 工具可通过 `model_type` 参数灵活选择
  - 📍 位置：`src/core/llm_client_manager.py`
  - 📚 文档：`docs/core/DUAL_LLM_SETUP.md`
  - 🧪 测试：`scripts/test/test_dual_llm_providers.py`, `scripts/test/test_deepseek_models.py`
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
  - ✅ **A/B类两步判断法**（2026-02-09升级）：
    - **第一步（P0优先级）**：判断文字类型
      * A类-设定类：跳脱时间线的设定信息 → 必须独立分段
      * B类-事件类：与时间线相关的事件 → 按时空/事件变化分段
    - **第二步**：对B类文字细分
      * 时空改变 → 分段
      * 事件改变 → 分段
      * 连续动作 → 合并
    - **关键区分点**：即使设定被包装成"回忆""思考"，本质仍是设定（A类）
    - 测试数据：准确率92%（11/12正确），比旧版本提升25%
  - ✅ **结构性分段策略**：只有世界观设定、叙事事件节点、核心转折才独立分段
  - ✅ **合并连续场景**：同一时空下的连续动作合并为一个段落（避免过度分段）
  - ✅ 识别段落类型（A类设定/B类事件）+ 段落文体（对话/叙述/描写/混合）
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
- **LLM 配置进一步优化**（2026-02-09）：
  - 移除全局 `CLAUDE_TEMPERATURE` 配置（温度参数在工具调用时按需设置）
  - 修正 `CLAUDE_BASE_URL` 默认值为 OneChats 通用线路
  - 添加 DeepSeek 多模型支持（v3.2 标准 + v3.2 思维链）
  - 所有工具和 Agent 迁移至 `LLMClientManager` 架构
- **Prompt 工程规范升级**：新增"避免过拟合"原则
  - ❌ 禁止用数量规定约束LLM输出（如"段落8-12个"）
  - ✅ 必须用逻辑判断规则（如"按时空变化分段"）
  - 写入 `docs/DEV_STANDARDS.md` 第6.2节，作为强制开发规范
- **NovelSegmenter Prompt 优化**（2026-02-09）：
  - 新增A/B/C三类判断法（C类：系统事件-次元空间）
  - 明确A类（设定类）必须独立分段，即使被包装成回忆/思考
  - 明确B类（事件类）按时空/事件变化分段，连续动作合并
  - 明确C类（系统事件）必须独立分段（系统觉醒、系统交互）
  - 增加段落类型标注（A类-设定类 / B类-事件类 / C类-系统事件）
  - 增加"段落结构统计"表格（A类 vs B类 vs C类）
  - **Two-Pass 策略验证成功**（2026-02-09晚）：
    * Pass 1（~90行）：极简Prompt，初步分段，10个段落
    * Pass 2（~100行）：用相同A/B/C原则校验修正，11个段落
    * 最终准确率：100%（11个段落，完全匹配标准）
    * Prompt简化：286行 → 190行（减少34%）
    * 解决了原版的过度分段问题（14个 → 11个）
    * 测试文件：`scripts/test/test_novel_segmenter_twopass.py`

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
