# NovelProcessingWorkflow 技术文档

## 概览

**NovelProcessingWorkflow** 是完整的小说处理工作流，负责将原始小说文件转换为结构化的分析数据，包括分段、标注、系统分析和质量验证。

## 职责

从原始小说文件到完整的章节分析数据，建立结构化的小说知识库。

## 接口定义

### 输入

```python
async def run(
    novel_path: str,              # 小说文件路径
    project_name: str,             # 项目名称
    config: Optional[NovelProcessingConfig] = None,  # 工作流配置
    resume_from_step: Optional[int] = None  # 断点续传（1-8）
) -> NovelProcessingResult
```

### 输出

```python
class NovelProcessingResult(BaseModel):
    project_name: str
    import_result: Optional[NovelImportResult]
    metadata: Optional[NovelMetadata]
    chapters: List[ChapterInfo]
    segmentation_results: Dict[int, ParagraphSegmentationResult]
    annotation_results: Dict[int, AnnotatedChapter]
    system_catalog: Optional[SystemCatalog]
    system_updates: Dict[int, SystemUpdateResult]
    system_tracking: Dict[int, SystemTrackingResult]
    validation_report: Optional[NovelValidationReport]
    processing_stats: Dict[str, Any]
    processing_time: float
    llm_calls_count: int
    total_cost: float
    errors: List[ChapterProcessingError]
```

## 实现逻辑

### Step 1: 小说导入与规范化
- 工具：`NovelImporter`
- 逻辑：读取原始小说，检测编码，统一格式，保存到项目目录
- 输出：`NovelImportResult` + Markdown报告

### Step 2: 提取小说元数据
- 工具：`NovelMetadataExtractor`
- 逻辑：提取标题、作者、标签、简介
- LLM调用：1次（DeepSeek v3.2）
- 输出：`NovelMetadata` + Markdown报告

### Step 3: 检测章节边界
- 工具：`NovelChapterDetector`
- 逻辑：识别章节标题，定位行号，应用章节范围过滤
- 输出：`List[ChapterInfo]` + Markdown报告

### Step 4: 章节并行分段（核心）
- 工具：`NovelSegmenter` (Two-Pass)
- 并行策略：同时处理3-5个章节
- 逻辑：
  1. 并行处理多个章节
  2. 每章执行 Pass 1（初步分段）+ Pass 2（校验修正）
  3. 输出行号范围，代码提取内容
- LLM调用：2次/章（Claude Sonnet 4.5）
- 输出：`Dict[int, ParagraphSegmentationResult]` + Markdown报告

### Step 5: 章节并行标注（核心）
- 工具：`NovelAnnotator` (Three-Pass)
- 并行策略：同时处理3-5个章节
- 逻辑：
  1. Pass 1：事件聚合 + 时间线分析
  2. Pass 2：设定关联 + 累积知识库
  3. Pass 3（可选）：功能性标签标注
- LLM调用：2-3次/章（Claude Sonnet 4.5）
- 输出：`Dict[int, AnnotatedChapter]` + Markdown报告

### Step 6: 全书系统元素分析（可选）
- 工具：`NovelSystemAnalyzer`
- 逻辑：分析前50章，识别系统类型，归类元素，定义追踪策略
- LLM调用：1次（Claude Sonnet 4.5）
- 输出：`SystemCatalog` + Markdown报告（与Step 7合并）

### Step 7: 章节系统元素检测与追踪（可选）
- 工具：`NovelSystemDetector` + `NovelSystemTracker`
- 并行策略：同时处理5-10个章节
- 逻辑：
  1. Detector：检测C类段落中的新系统元素
  2. Tracker：追踪事件中的系统元素变化
- LLM调用：2次/章（Claude Sonnet 4.5）
- 输出：`Dict[int, SystemUpdateResult]` + `Dict[int, SystemTrackingResult]` + Markdown报告

### Step 8: 质量验证
- 工具：`NovelValidator`
- 逻辑：验证编码、章节、分段、标注的合理性，生成质量评分
- 输出：`NovelValidationReport` + Markdown报告

## LLM管理器集成 (LLM Manager Integration)

### 概述

自2026年2月起，Workflow已集成 **LLMCallManager**，提供统一的LLM调用管理，包括：
- ✅ 自动限流（QPM/TPM/并发控制）
- ✅ 智能重试（指数退避 + 限流检测）
- ✅ 使用统计（请求数/Token数追踪）
- ✅ 模型信息记录（每个结果记录使用的模型）

### 集成位置

LLM管理器在以下步骤中使用：

| 步骤 | 工具 | LLM调用方式 |
|-----|------|-----------|
| Step 2 | NovelMetadataExtractor | 通过 `llm_manager.call_with_rate_limit()` |
| Step 4 | NovelSegmenter | 通过 `llm_manager.call_with_rate_limit()` |
| Step 5 | NovelAnnotator | 通过 `llm_manager.call_with_rate_limit()` |
| Step 6 | NovelSystemAnalyzer | 通过 `llm_manager.call_with_rate_limit()` |
| Step 7 | NovelSystemDetector/Tracker | 通过 `llm_manager.call_with_rate_limit()` |

### 使用示例

```python
# Workflow初始化时创建manager
from src.core.llm_rate_limiter import get_llm_manager
self.llm_manager = get_llm_manager()

# 调用工具时使用限流
seg_output = await self.llm_manager.call_with_rate_limit(
    func=self.novel_segmenter.execute,
    provider="claude",                           # 使用的provider
    model="claude-sonnet-4-5-20250929",         # 使用的模型
    estimated_tokens=self._estimate_tokens(content),  # 估算token数
    chapter_content=chapter_content,
    chapter_number=chapter.number
)
```

### 模型信息记录

每个工具的输出结果都会在 `metadata` 字段中记录使用的模型：

```python
# 分段结果中的模型记录
ParagraphSegmentationResult(
    metadata={
        "model_used": "claude-sonnet-4-5-20250929",
        "processing_time": 12.5,
        ...
    }
)

# 标注结果中的模型记录
AnnotatedChapter(
    metadata={
        "model_used": "claude-sonnet-4-5-20250929",
        "pass1_time": 8.2,
        "pass2_time": 6.3,
        ...
    }
)
```

### 配置文件

LLM限流配置位于 `data/llm_configs.json`：

```json
{
  "claude_claude_sonnet_4_5_20250929": {
    "provider": "claude",
    "model": "claude-sonnet-4-5-20250929",
    "requests_per_minute": 30,
    "max_concurrent": 2,
    "max_retries": 3,
    "base_retry_delay": 3.0
  }
}
```

### 相关文档

- [LLM限流系统设计](../core/LLM_RATE_LIMIT_SYSTEM.md)
- [LLM集成指南](../core/LLM_INTEGRATION_GUIDE.md)
- [LLM系统完整文档](../core/LLM_SYSTEM_COMPLETE.md)

---

## 依赖关系

### Schema
- `NovelProcessingConfig` (配置)
- `NovelProcessingResult` (输出)
- `ChapterProcessingError` (错误记录)
- 以及所有工具的输入输出Schema

### Tools
- `NovelImporter`
- `NovelMetadataExtractor`
- `NovelChapterDetector`
- `NovelSegmenter`
- `NovelAnnotator`
- `NovelSystemAnalyzer`
- `NovelSystemDetector`
- `NovelSystemTracker`
- `NovelValidator`

### Core Components
- **`LLMCallManager`** - LLM调用管理器（限流、重试、统计）
- **`RateLimiter`** - 滑动窗口限流器
- **`LLMRateLimitConfig`** - 限流配置

### Config
- 使用 `data/projects/` 作为项目根目录
- 支持断点续传（中间结果保存在 `processing/` 目录）
- LLM配置文件：`data/llm_configs.json`

## 核心特性

### 1. 并行处理
- 章节级别并行处理（Step 4, 5, 7）
- 可配置并发数（默认3个章节）
- 使用 `asyncio.gather()` 实现

### 2. 错误处理
- 三级容错：工具重试 → 章节降级 → 流程恢复
- `continue_on_error` 配置：单章失败时是否继续

### 3. 中间结果持久化
```
data/projects/{project_name}/processing/
├── step1_import.json
├── step2_metadata.json
├── step3_chapters.json
├── step4_segmentation/
│   ├── chapter_001.json
│   ├── chapter_002.json
│   └── ...
├── step5_annotation/
│   └── ...
├── step6_system_catalog.json
├── step7_system_tracking/
│   └── ...
├── step8_validation_report.json
├── reports/  (Markdown报告)
│   ├── step1_import_report.md
│   ├── step2_metadata_report.md
│   ├── step3_chapters_report.md
│   ├── step4_segmentation_report.md
│   ├── step5_annotation_report.md
│   ├── step67_system_report.md
│   └── step8_validation_report.md
└── final_result.json
```

### 4. Markdown报告输出
- 每个关键步骤生成可读的Markdown报告
- 包含统计信息、详细列表、错误提示
- 保存在 `processing/reports/` 目录

### 5. 断点续传
- 支持 `resume_from_step` 参数从指定步骤恢复
- 自动加载中间结果

## 配置参数

```python
class NovelProcessingConfig(BaseModel):
    # 并行处理
    enable_parallel: bool = True
    max_concurrent_chapters: int = 3  # 建议3-5
    
    # 功能开关
    enable_functional_tags: bool = False  # 功能性标签（Pass 3）
    enable_system_analysis: bool = True    # 系统分析
    
    # 章节范围
    chapter_range: Optional[tuple] = None  # 如 (1, 10)
    
    # 错误处理
    continue_on_error: bool = True
    save_intermediate_results: bool = True
    
    # LLM配置
    segmentation_provider: str = "claude"
    annotation_provider: str = "claude"
    
    # 输出配置
    output_markdown_reports: bool = True
```

## 性能估算

### 时间成本（单本100章小说）
| 步骤 | 单章耗时 | 总耗时（串行） | 总耗时（并行3章） |
|-----|---------|--------------|----------------|
| Step 1-3 | - | ~10秒 | ~10秒 |
| Step 4 (分段) | ~20秒 | ~33分钟 | ~11分钟 |
| Step 5 (标注) | ~80秒 | ~133分钟 | ~45分钟 |
| Step 6 (系统) | - | ~30秒 | ~30秒 |
| Step 7 (追踪) | ~15秒 | ~25分钟 | ~8分钟 |
| Step 8 (验证) | - | ~20秒 | ~20秒 |
| **总计** | - | **~192分钟** | **~65分钟** |

**优化效果**：并行处理节约 **66%** 时间

### 经济成本（单本100章小说）
| 步骤 | 单章成本 | 总成本（100章） |
|-----|---------|---------------|
| Step 2 (元数据) | - | ~$0.01 |
| Step 4 (分段) | ~$0.05 | ~$5.00 |
| Step 5 (标注) | ~$0.08 | ~$8.00 |
| Step 6 (系统) | - | ~$0.15 |
| Step 7 (追踪) | ~$0.02 | ~$2.00 |
| **总计** | - | **~$15.16** |

## 使用示例

### 完整流程
```python
from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import NovelProcessingConfig

workflow = NovelProcessingWorkflow()
result = await workflow.run(
    novel_path="分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt",
    project_name="末哥超凡公路_test",
    config=NovelProcessingConfig(
        enable_parallel=True,
        max_concurrent_chapters=3,
        chapter_range=(1, 10),  # 只处理前10章
        enable_functional_tags=False,
        output_markdown_reports=True
    )
)

print(f"处理完成！耗时: {result.processing_time:.1f}秒")
print(f"LLM调用: {result.llm_calls_count}次")
print(f"总成本: ${result.total_cost:.4f}")
```

### 断点续传
```python
# 从Step 4恢复（假设Step 1-3已完成）
result = await workflow.run(
    novel_path="...",
    project_name="...",
    resume_from_step=4  # 从分段步骤开始
)
```

## 测试

### 测试脚本
```bash
# 完整流程测试（10章）
python scripts/test/test_novel_processing_workflow.py --mode full

# 部分流程测试（前3步）
python scripts/test/test_novel_processing_workflow.py --mode partial
```

### 验证结果
- 检查 `data/projects/{project_name}/processing/reports/` 中的Markdown报告
- 检查 `final_result.json` 中的统计信息
- 运行 `NovelValidator` 查看质量评分

## 注意事项

1. **Schema字段名匹配**：确保使用正确的属性名（如 `chapter.number` 而非 `chapter.chapter_number`）
2. **LLM Provider配置**：确保 `.env` 中配置了Claude API Key
3. **并发控制**：根据API限流调整 `max_concurrent_chapters`
4. **内存占用**：处理大型小说时注意内存使用
5. **成本控制**：使用 `chapter_range` 限制处理范围以控制成本

## 已知问题

1. ⚠️ Schema字段名不一致问题（开发中修复）
2. ⚠️ 部分工具返回类型需要对齐

## 版本历史

- **v1.0.0** (2026-02-10): 初始版本，实现完整8步流程

---

*最后更新: 2026-02-10*
