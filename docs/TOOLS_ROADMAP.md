# 工具开发路线图

## 设计原则
1. **工具优先**: 先把单个工具做扎实，再考虑workflow
2. **职责单一**: 每个工具只做一件事
3. **测试驱动**: 每个工具都要有验证方法
4. **文档同步**: 代码即文档，文档即规范
5. **渐进构建**: Phase by Phase，不急于求成

---

## Phase I: 素材标准化处理

### 目标
将原始文件（novel.txt, SRT）转换为统一的结构化格式，为后续分析打好基础。

### 1.1 Novel处理工具

#### `NovelImporter` - 小说导入工具
**职责**: 读取并规范化小说文件
- 读取novel.txt文件
- 编码检测与统一（UTF-8）
- 换行符规范化
- 去除BOM标记
- 基础格式验证

**输入**: `raw/novel.txt`  
**输出**: 规范化的文本字符串  
**依赖**: 无

---

#### `NovelMetadataExtractor` - 小说元数据提取工具
**职责**: 提取小说的基本信息
- 提取标题
- 提取作者
- 提取标签/分类
- 提取简介（含LLM智能过滤）
- 识别章节分隔符模式

**输入**: 规范化的小说文本  
**输出**: `NovelMetadata` schema  
**依赖**: `NovelImporter`

---

#### `NovelChapterDetector` - 章节检测工具
**职责**: 检测章节边界
- 识别章节标题模式（第X章、ChapterX等）
- 定位章节起始位置
- 生成章节索引
- 验证章节连续性

**输入**: 规范化的小说文本  
**输出**: `List[ChapterInfo]` - 章节索引列表  
**依赖**: `NovelImporter`

---

#### `NovelSegmenter` - 小说分段工具
**职责**: 将小说按自然段落分段
- 按段落分割（保持\n\n边界）
- 识别对话段落
- 识别描写段落
- 识别叙事段落
- 保持语义完整性

**输入**: 规范化的小说文本  
**输出**: `List[Paragraph]` - 分段后的段落列表  
**依赖**: `NovelImporter`

---

#### `NovelChapterSplitter` - 章节拆分工具
**职责**: 将小说拆分为独立的章节文件
- 根据章节索引拆分
- 生成chpt_0000.txt（简介）
- 生成chpt_0001-0010.txt（第1-10章）
- 维护章节映射关系

**输入**: 规范化的小说文本 + 章节索引  
**输出**: 多个章节文件  
**依赖**: `NovelImporter`, `NovelChapterDetector`

---

### 1.2 Script处理工具

#### `SrtImporter` - SRT导入工具
**职责**: 读取并规范化SRT文件
- 读取SRT文件
- 编码检测与统一
- 解析SRT格式（序号、时间轴、文本）
- 验证时间轴格式
- 修复常见格式错误

**输入**: `raw/ep01.srt`  
**输出**: `List[SrtEntry]` - SRT条目列表  
**依赖**: 无

---

#### `SrtTextExtractor` - SRT文本提取工具
**职责**: 从SRT中提取纯文本
- 移除时间轴信息
- 合并碎片化文本
- 还原完整句子
- 保留时间戳映射关系

**输入**: `List[SrtEntry]`  
**输出**: 纯文本 + 时间戳映射  
**依赖**: `SrtImporter`

---

#### `ScriptSegmenter` - 脚本分段工具
**职责**: 将脚本按语义分段
- 按句子边界分段
- 识别对话片段
- 识别旁白片段
- 保持时间戳关联

**输入**: 纯文本 + 时间戳映射  
**输出**: `List[ScriptSegment]` - 脚本段落列表  
**依赖**: `SrtTextExtractor`

---

### 1.3 验证工具

#### `NovelValidator` - 小说验证工具
**职责**: 验证小说处理质量
- 检查编码正确性
- 检查章节完整性
- 检查段落合理性
- 生成质量报告

**输入**: 处理后的小说数据  
**输出**: 验证报告  
**依赖**: 所有Novel工具

---

#### `ScriptValidator` - 脚本验证工具
**职责**: 验证脚本处理质量
- 检查时间轴连续性
- 检查文本完整性
- 检查分段合理性
- 生成质量报告

**输入**: 处理后的脚本数据  
**输出**: 验证报告  
**依赖**: 所有Script工具

---

## Phase II: 内容分析与对齐

### 目标
在Phase I基础上，分析novel和script的语义，建立对应关系。

### 2.1 Hook检测工具

#### `HookDetector` - Hook检测工具
**职责**: 检测ep01是否存在Hook及其边界
- 分析前90秒内容
- 判断是否为Hook
- 定位Body起点时间
- 计算置信度

**输入**: ep01的脚本段落  
**输出**: `HookDetectionResult`  
**依赖**: `ScriptSegmenter`

---

#### `HookContentAnalyzer` - Hook内容分析工具
**职责**: 分析Hook的内容来源
- 提取Hook的关键信息
- 对比Novel简介
- 计算相似度
- 推断来源（简介/章节/独立）

**输入**: Hook部分 + Novel简介  
**输出**: `HookAnalysisResult`  
**依赖**: `HookDetector`, `NovelMetadataExtractor`

---

### 2.2 语义分析工具

#### `NovelSemanticAnalyzer` - 小说语义分析工具
**职责**: 分析novel段落的语义信息
- 提取关键事件
- 识别角色
- 识别地点
- 识别时间
- 标注情感
- 标注节奏

**输入**: Novel段落列表  
**输出**: `List[NovelSemanticNode]`  
**依赖**: `NovelSegmenter`

---

#### `ScriptSemanticAnalyzer` - 脚本语义分析工具
**职责**: 分析script段落的语义信息
- 提取关键事件
- 识别角色
- 识别场景
- 标注情感
- 标注节奏

**输入**: Script段落列表  
**输出**: `List[ScriptSemanticNode]`  
**依赖**: `ScriptSegmenter`

---

### 2.3 对齐匹配工具

#### `SemanticMatcher` - 语义匹配工具
**职责**: 匹配novel和script的语义节点
- 计算节点相似度
- 识别对应关系
- 标注置信度
- 处理多对一、一对多情况

**输入**: NovelSemanticNodes + ScriptSemanticNodes  
**输出**: `List[AlignmentPair]`  
**依赖**: `NovelSemanticAnalyzer`, `ScriptSemanticAnalyzer`

---

#### `AlignmentValidator` - 对齐验证工具
**职责**: 验证对齐质量
- 检查覆盖率
- 检查连续性
- 检查合理性
- 生成质量报告

**输入**: 对齐结果  
**输出**: 质量评估报告  
**依赖**: `SemanticMatcher`

---

### 2.4 标签生成工具

#### `NovelTagger` - 小说标签生成工具
**职责**: 为novel段落生成标签
- 事件类型标签（冲突、转折、铺垫等）
- 功能标签（设定、剧情、情感等）
- 节奏标签（快/中/慢）
- 重要度标签（核心/次要/背景）

**输入**: NovelSemanticNodes  
**输出**: 带标签的Novel段落  
**依赖**: `NovelSemanticAnalyzer`

---

#### `ScriptTagger` - 脚本标签生成工具
**职责**: 为script段落生成标签
- 改编类型标签（直接/简化/扩展/创作）
- 内容类型标签（剧情/过渡/悬念）
- 节奏标签（快/中/慢）
- 重要度标签（核心/次要/衔接）

**输入**: ScriptSemanticNodes + 对齐结果  
**输出**: 带标签的Script段落  
**依赖**: `ScriptSemanticAnalyzer`, `SemanticMatcher`

---

## 工具优先级

### 🔥 P0 - 立即开始（Phase I 基础）
1. `NovelImporter`
2. `SrtImporter`
3. `NovelSegmenter`
4. `SrtTextExtractor`

### ⚡ P1 - 第二批（Phase I 完善）
5. `NovelMetadataExtractor`
6. `NovelChapterDetector`
7. `NovelChapterSplitter`
8. `ScriptSegmenter`

### 📊 P2 - 第三批（Phase I 验证）
9. `NovelValidator`
10. `ScriptValidator`

### 🎯 P3 - 第四批（Phase II Hook）
11. `HookDetector`
12. `HookContentAnalyzer`

### 🧠 P4 - 第五批（Phase II 语义）
13. `NovelSemanticAnalyzer`
14. `ScriptSemanticAnalyzer`
15. `SemanticMatcher`

### ✅ P5 - 第六批（Phase II 完善）
16. `AlignmentValidator`
17. `NovelTagger`
18. `ScriptTagger`

---

## 工具开发检查清单

每个工具开发时必须完成：

- [ ] **接口定义**: 继承`BaseTool`，定义清晰的`execute()`方法
- [ ] **Schema定义**: 在`src/core/schemas_*.py`中定义输入输出数据模型
- [ ] **文档**: 编写完整的docstring（Google Style）
- [ ] **测试脚本**: 在`scripts/test/`创建测试脚本
- [ ] **日志**: 使用`logging`模块，不用print
- [ ] **配置**: 不硬编码，使用`config`
- [ ] **错误处理**: 完善的异常处理和错误信息

---

## 当前状态

**已完成**: 0/18 工具  
**进行中**: 待开始  
**下一个**: `NovelImporter`

---

## 参考资源

**归档工具可参考**（但不要直接复制）:
- `archive/v2_tools_20260208/novel_processor.py`
- `archive/v2_tools_20260208/novel_segmentation_analyzer.py`
- `archive/v2_tools_20260208/srt_processor.py`

**归档文档可参考**:
- `docs/archive/NOVEL_SEGMENTATION_METHODOLOGY.md`
- `docs/archive/SRT_PROCESSING_QUICKSTART.md`

**开发规范**:
- `docs/DEV_STANDARDS.md`
- `.cursorrules`
