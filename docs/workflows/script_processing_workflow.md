# ScriptProcessingWorkflow - 脚本处理工作流

**文件**: `src/workflows/script_processing_workflow.py`  
**状态**: ✅ 已完成 (2026-02-10)  
**优先级**: P0（核心业务流程）

---

## 📋 概述

ScriptProcessingWorkflow 是从原始SRT文件到完整脚本分段数据的完整处理流程，为对齐分析提供Script端的结构化数据。

### 核心功能
- SRT导入与规范化
- 文本提取与智能修复
- Hook边界检测（ep01）
- Hook内容分析（可选）
- 脚本语义分段（ABC分类）
- 质量验证与报告生成

---

## 🎯 设计目标

1. **完整性**: 覆盖从SRT导入到质量验证的完整流程
2. **灵活性**: 支持有/无Novel参考两种模式
3. **智能性**: Hook自动检测与内容分析
4. **准确性**: Two-Pass分段 + ABC类型分类
5. **可靠性**: 完善的错误处理和质量门禁

---

## 🏗️ 工作流架构

```
SRT文件 (ep01.srt)
        ↓
Phase 1: SRT导入与规范化 (5-10秒)
        ├─ 编码检测与统一
        ├─ 时间轴格式验证
        └─ SRT结构修复
        ↓
Phase 2: 文本提取与智能修复 (30-60秒, LLM)
        ├─ 移除时间轴信息
        ├─ 智能添加标点符号
        ├─ 修正错别字和同音错字
        ├─ 实体标准化
        └─ 修复缺字问题
        ↓
Phase 3: Hook边界检测 (20-40秒, LLM, 仅ep01)
        ├─ 5特征判断
        ├─ 定位Body起点时间
        └─ 计算置信度
        ↓
Phase 4: Hook内容分析 (30-50秒, LLM, 可选)
        ├─ 分层提取(世界观/系统/道具/情节)
        ├─ 相似度计算
        └─ 推断来源(简介/章节/独立)
        ↓
Phase 5: 脚本语义分段 (60-120秒, Three-Pass LLM)
        ├─ Pass 1: 初步分段
        ├─ Pass 2: 校验修正
        └─ Pass 3: ABC类分类
        ↓
Phase 6: 质量验证 (5秒)
        ├─ 时间轴连续性检查
        ├─ 文本完整性验证
        ├─ 分段合理性检查
        └─ 生成质量报告
        ↓
输出: ScriptProcessingResult
```

---

## 📥 输入参数

### 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `srt_path` | str | SRT文件路径 |
| `project_name` | str | 项目名称 |
| `episode_name` | str | 集数名称（如 "ep01"） |

### 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `config` | ScriptProcessingConfig | 工作流配置（不提供则使用默认） |
| `novel_reference` | Optional[str] | Novel文本参考（用于实体标准化） |
| `novel_intro` | Optional[str] | Novel简介（用于Hook检测） |
| `novel_metadata` | Optional[Dict] | Novel元数据（用于Hook分析） |

---

## 📤 输出结果

### ScriptProcessingResult

```python
{
    "project_name": str,              # 项目名称
    "episode_name": str,              # 集数名称
    "success": bool,                  # 处理是否成功
    
    # Phase 结果
    "import_result": SrtImportResult,                   # Phase 1
    "extraction_result": SrtTextExtractionResult,       # Phase 2
    "hook_detection_result": HookDetectionResult,       # Phase 3（可选）
    "hook_analysis_result": HookAnalysisResult,         # Phase 4（可选）
    "segmentation_result": ScriptSegmentationResult,    # Phase 5
    "validation_report": ScriptValidationReport,        # Phase 6
    
    # 统计信息
    "processing_time": float,         # 总处理时间（秒）
    "llm_calls_count": int,          # LLM调用总次数
    "total_cost": float,             # 总成本（USD）
    "errors": List[ScriptProcessingError],  # 错误列表
    
    # 元数据
    "config_used": Dict,             # 使用的配置
    "processing_timestamp": datetime  # 处理时间戳
}
```

---

## ⚙️ 配置参数

### ScriptProcessingConfig

```python
config = ScriptProcessingConfig(
    # 功能开关
    enable_hook_detection=True,        # 是否启用Hook检测（仅ep01）
    enable_hook_analysis=False,        # 是否启用Hook内容分析
    enable_abc_classification=True,    # 是否启用ABC类分段
    
    # 重试与限流控制
    retry_on_error=True,               # API调用失败时是否自动重试
    max_retries=3,                     # 最大重试次数
    retry_delay=2.0,                   # 重试基础延迟（秒）
    request_delay=1.0,                 # 请求之间的延迟（秒）
    
    # LLM配置
    text_extraction_provider="deepseek",   # 文本提取LLM
    hook_detection_provider="deepseek",    # Hook检测LLM
    segmentation_provider="deepseek",      # 分段LLM
    
    # 错误处理
    continue_on_error=False,           # 失败时是否继续（通常为False）
    save_intermediate_results=True,    # 是否保存中间结果
    
    # 输出配置
    output_markdown_reports=True,      # 是否输出Markdown报告
    
    # 质量门禁
    min_quality_score=75               # 最低质量评分（0-100）
)
```

---

## 📊 Phase 详细说明

### Phase 1: SRT导入与规范化

**工具**: SrtImporter  
**耗时**: 5-10秒  
**成本**: 无LLM调用  

**功能**:
1. 编码检测与统一（UTF-8）
2. 时间轴格式验证（HH:MM:SS,mmm）
3. SRT结构修复（序号、空行）

**输出**: `SrtImportResult`
- 保存路径
- 条目数量（entry_count）
- 总时长（total_duration）
- 编码信息（encoding）
- 规范化操作列表

**质量检查**:
- 时间轴连续性（无跳跃 > 5秒）
- 编码正确性（无乱码字符）

---

### Phase 2: 文本提取与智能修复

**工具**: SrtTextExtractor  
**耗时**: 30-60秒  
**成本**: $0.02-0.04 USD  
**LLM**: DeepSeek v3.2  

**功能**:
1. 移除时间轴信息
2. 智能添加标点符号
3. 修正错别字和同音错字
4. 实体标准化（有/无Novel参考）
5. 修复缺字问题

**输出**: `SrtTextExtractionResult`
- 处理后文本（processed_text）
- 原始文本（raw_text）
- 实体标准化信息
- 修正统计

**质量检查**:
- 文本覆盖率 ≥ 95%
- 无明显乱码或缺字

---

### Phase 3: Hook边界检测

**工具**: HookDetector  
**耗时**: 20-40秒  
**成本**: $0.01-0.03 USD  
**LLM**: DeepSeek v3.2 或 Claude  

**执行条件**:
- `enable_hook_detection = True`
- `episode_name = "ep01"`（仅第一集）

**5特征判断**:
1. 独立语义段落
2. 非具象的当下描述（总结/预告）
3. Hook后连贯性增强
4. Hook后可在Novel开头匹配
5. Hook与简介相似度高

**输出**: `HookDetectionResult`
- 是否有Hook（has_hook）
- Hook结束时间（hook_end_time）
- Body起点时间（body_start_time）
- 置信度（confidence: 0-1）
- 判断理由（reasoning）

**质量检查**:
- 置信度 ≥ 0.8（高置信度）
- 0.6-0.8（中等，警告）
- < 0.6（低，建议人工审核）

---

### Phase 4: Hook内容分析

**工具**: HookContentAnalyzer  
**耗时**: 30-50秒  
**成本**: $0.02-0.04 USD  
**LLM**: DeepSeek v3.2  

**执行条件**:
- `enable_hook_analysis = True`
- 检测到Hook（has_hook = True）
- 提供Novel简介和元数据

**分层提取**（4层）:
1. 世界观设定（World Building）
2. 系统机制（Game Mechanics）
3. 道具装备（Items/Equipment）
4. 情节事件（Plot Events）

**输出**: `HookAnalysisResult`
- 来源类型（简介/章节/独立创作）
- 相似度（similarity_score: 0-1）
- 分层内容（hook_layers, intro_layers）
- 分层相似度（layer_similarity）
- 建议策略（alignment_strategy）

**跳过条件**:
- 无Novel参考（纯Script项目）
- 未检测到Hook

---

### Phase 5: 脚本语义分段

**工具**: ScriptSegmenter  
**耗时**: 60-120秒  
**成本**: $0.06-0.09 USD  
**LLM**: DeepSeek v3.2（Three-Pass）  

**Three-Pass策略**:
1. **Pass 1**: 初步分段（场景转换/情节转折/对话切换）
2. **Pass 2**: 校验修正（检查合理性，修正过度/欠分段）
3. **Pass 3**: ABC类分类
   - A类-设定（Setting）：旁白讲解世界观、规则说明
   - B类-事件（Event）：对话、动作、场景推进
   - C类-系统（System）：系统提示音、数据面板显示

**输出**: `ScriptSegmentationResult`
- 段落列表（segments）
  - 段落内容（content）
  - 类型标签（category: A/B/C）
  - 时间戳范围（start_time, end_time）
  - 句子数量（sentence_count）
- 总段落数（total_segments）
- 平均句子数（avg_sentence_count）

**质量检查**:
- 段落数量：5-20段/集（合理范围）
- ABC类型分布：A: 5-15%, B: 80-95%, C: 0-5%
- 时间戳匹配准确性：100%

---

### Phase 6: 质量验证

**工具**: ScriptValidator  
**耗时**: 5秒  
**成本**: 无LLM调用  

**检查项目**:
1. **时间轴连续性**
   - 检查时间跳跃（> 5秒）
   - 检查时间重叠
2. **文本完整性**
   - SRT覆盖率（> 95%）
   - 内容还原度
3. **分段合理性**
   - 分段数量（5-20段/集）
   - 时间戳匹配准确性（100%）
   - 段落长度分布

**输出**: `ScriptValidationReport`
- 质量评分（quality_score: 0-100）
- 是否通过（is_valid）
- 检查结果（timeline_check, text_check, segmentation_check）
- 问题列表（issues）
- 改进建议（recommendations）

**质量标准**:
- ≥ 85分：优秀（通过）
- 70-85分：良好（通过，有警告）
- 60-70分：及格（建议人工审核）
- < 60分：不合格（建议停止）

---

## 💰 成本与性能

### 单集处理成本

**估算值**（基于DeepSeek v3.2）：

| Phase | LLM调用 | 成本（USD） | 耗时 |
|-------|---------|-------------|------|
| Phase 1 | 0 | $0.00 | 5-10秒 |
| Phase 2 | 1-3 | $0.02-0.04 | 30-60秒 |
| Phase 3 | 2-4 | $0.03-0.06 | 20-40秒 |
| Phase 4 | 1-2 | $0.02-0.04 | 30-50秒 |
| Phase 5 | 3-5 | $0.06-0.12 | 60-120秒 |
| Phase 6 | 0 | $0.00 | 5秒 |
| **总计（含Hook）** | **7-15** | **$0.18-0.40** | **2.5-5分钟** |
| **总计（无Hook）** | **4-8** | **$0.08-0.16** | **1.5-3分钟** |

**实测数据**（末哥超凡公路，2026-02-10）：

| 集数 | 条目数 | LLM调用 | 成本（USD） | 耗时 | 说明 |
|------|--------|---------|-------------|------|------|
| ep01 | 357 | 7 | $0.19 | 4.5分钟 | 含Hook检测 |
| ep02 | 146 | 11 | $0.29 | 2.7分钟 | 无Hook |
| ep03 | 108 | 15 | $0.40 | 2.4分钟 | 无Hook |
| **平均** | **204** | **11** | **$0.29** | **3.2分钟** | - |

**注意**：
- 实际成本受文本长度、API重试次数、网络状况影响
- LLM调用次数包含重试和fallback机制
- 使用Claude成本约为DeepSeek的3-5倍

### 批量处理成本（10集）

**估算值**：

| 场景 | 成本 | 说明 |
|------|------|------|
| ep01（含Hook） | $0.18-0.40 | Hook检测+分析 |
| ep02-10（无Hook） | $0.08-0.16 × 9 = $0.72-1.44 | 标准处理 |
| **总计** | **$0.90-1.84** | 10集 |

**实测估算**（基于末哥超凡公路）：

| 场景 | 成本 | 说明 |
|------|------|------|
| ep01（含Hook） | ~$0.19 | 357条SRT |
| ep02-10（无Hook） | ~$0.29 × 9 = $2.61 | 平均150-200条SRT |
| **总计** | **~$2.80** | 10集（约5000条SRT） |

**优化建议**：
- 批量处理可节省10-15%成本（减少API握手开销）
- 使用缓存机制可避免重复处理
- 合理设置`max_retries`避免不必要的重试

---

## 🔧 使用示例

### 基本使用

```python
from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig

# 初始化工作流
workflow = ScriptProcessingWorkflow()

# 执行处理
result = await workflow.run(
    srt_path="data/projects/天命桃花_test/raw/ep01.srt",
    project_name="天命桃花_test",
    episode_name="ep01",
    config=ScriptProcessingConfig(
        enable_hook_detection=True,
        min_quality_score=75
    )
)

# 检查结果
if result.success:
    print(f"处理成功！质量评分: {result.validation_report.quality_score:.0f}/100")
else:
    print(f"处理失败: {result.errors}")
```

### 有Novel参考的处理

```python
# 提供Novel参考数据
result = await workflow.run(
    srt_path="data/projects/天命桃花_test/raw/ep01.srt",
    project_name="天命桃花_test",
    episode_name="ep01",
    novel_reference=novel_text,      # Novel文本（用于实体标准化）
    novel_intro=novel_intro,         # Novel简介（用于Hook检测）
    novel_metadata=novel_metadata,   # Novel元数据（用于Hook分析）
    config=ScriptProcessingConfig(
        enable_hook_analysis=True     # 启用Hook分析
    )
)
```

### 最小配置（ep02-10）

```python
# ep02-10不需要Hook检测
result = await workflow.run(
    srt_path="data/projects/天命桃花_test/raw/ep02.srt",
    project_name="天命桃花_test",
    episode_name="ep02",
    config=ScriptProcessingConfig(
        enable_hook_detection=False,   # 禁用Hook检测
        enable_hook_analysis=False,    # 禁用Hook分析
        min_quality_score=70           # 更宽松的质量要求
    )
)
```

---

## 🧪 测试

### 测试脚本

**位置**: `scripts/test/test_script_processing_workflow.py`

### 运行测试

```bash
# 完整测试（包含Hook检测）
python scripts/test/test_script_processing_workflow.py

# 或直接运行async测试
python -m asyncio scripts.test.test_script_processing_workflow
```

### 测试覆盖

1. **完整流程测试**（ep01）
   - 所有Phase执行
   - Hook检测与分析
   - 质量验证

2. **最小配置测试**（ep02）
   - 不包含Hook检测
   - 标准分段流程

3. **边界测试**
   - 无Novel参考
   - 无Hook的脚本
   - 异常格式SRT

---

## ⚠️ 注意事项

### 1. Hook检测仅限ep01

Hook检测只在第一集（ep01）执行，原因：
- Hook通常只在第一集出现
- 避免不必要的LLM调用成本
- 提高后续集数的处理速度

如需在其他集数检测Hook，可手动设置：
```python
config.enable_hook_detection = True  # 强制启用
```

### 2. Hook分析需要Novel参考

Hook内容分析需要提供：
- `novel_intro`: Novel简介
- `novel_metadata`: Novel元数据

如果没有Novel数据，建议禁用：
```python
config.enable_hook_analysis = False
```

### 3. 质量门禁阈值

默认最低质量评分为75分（严格标准），可根据实际情况调整：
- 实验性项目：60-70分
- 生产项目：75-85分
- 高质量要求：85-90分

### 4. LLM Provider选择

- **DeepSeek v3.2**：速度快，成本低，适合大批量处理
- **Claude Sonnet 4.5**：质量高，理解强，适合复杂场景

建议配置：
- 文本提取：DeepSeek（格式处理）
- Hook检测：DeepSeek或Claude（视复杂度）
- 脚本分段：DeepSeek（标准流程）

### 5. 错误处理与Fallback机制

**自动降级策略**：
- Phase 2（文本提取）：LLM超时 → 降级到rule_based处理
- Phase 5（脚本分段）：LLM失败 → 重试机制（最多3次）
- 网络问题：自动重试，间隔2秒

**实测案例**（2026-02-10）：
```
Phase 2: LLM entity extraction failed: Request timed out.
→ 自动降级到rule_based处理
→ 工作流继续执行，最终成功
```

**配置重试策略**：
```python
config = ScriptProcessingConfig(
    retry_on_error=True,    # 启用自动重试
    max_retries=3,          # 最多重试3次
    retry_delay=2.0,        # 重试间隔2秒
    continue_on_error=False # 失败时不继续（推荐）
)
```

### 6. 异步执行机制

**实现细节**：
- 使用`asyncio.to_thread()`在线程池中运行同步工具
- 避免阻塞事件循环
- 支持并发处理多个集数

**技术说明**：
```python
# 所有LLM调用都通过asyncio.to_thread()包装
extraction_result = await asyncio.to_thread(
    self.text_extractor.execute,
    ...
)
```

这确保了长时间的LLM API调用不会阻塞workflow的执行。

---

## 📈 性能优化建议

### 1. 批量处理

对于多集处理，建议使用BatchProcessingWorkflow（未来实现）：
```python
# 未来版本
batch_workflow = BatchProcessingWorkflow()
results = await batch_workflow.run(
    srt_paths=["ep01.srt", "ep02.srt", ...],
    project_name="天命桃花_test"
)
```

### 2. 并发控制

当前workflow为串行处理，如需并发：
- 使用`asyncio.gather`并行处理多集
- 注意API限流（建议并发数 ≤ 2）

### 3. 成本控制

- 禁用不必要的功能（Hook分析）
- 使用DeepSeek而非Claude（降低70%成本）
- 批量调用优化

---

## 🔗 相关文档

- [ROADMAP.md](ROADMAP.md) - Workflow开发路线图
- [novel_processing_workflow.md](novel_processing_workflow.md) - Novel处理工作流
- [tools/script_segmenter.md](../tools/script_segmenter.md) - 脚本分段工具
- [tools/hook_detector.md](../tools/hook_detector.md) - Hook检测工具

---

**最后更新**: 2026-02-10  
**状态**: ✅ 已完成并通过生产环境测试  
**测试数据**: 末哥超凡公路 ep01-ep03（实测成功率100%）  
**下一步**: 
- 开发`AlignmentWorkflow`（P0优先级）
- 开发`BatchProcessingWorkflow`优化批量处理
- 持续收集成本和性能数据优化估算
