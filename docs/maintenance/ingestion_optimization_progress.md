# 动态章节提取与并发优化 - 实施进度

## ✅ 已完成 (Phase 1 & 2)

### 1. 质量评估系统

**文件**: `src/core/schemas.py`

新增数据模型：
- `EpisodeCoverage`: 单集覆盖情况
- `AlignmentQualityReport`: 对齐质量评估报告

**文件**: `src/modules/alignment/deepseek_alignment_engine.py`

新增方法：
- `evaluate_alignment_quality()`: 评估对齐质量
  - 计算平均置信度
  - 计算整体覆盖率
  - 计算章节连续性得分
  - 综合得分 = 置信度×0.4 + 覆盖率×0.4 + 连续性×0.2
  
- `_calculate_continuity()`: 计算章节连续性
  - 检测章节跳跃
  - 跳跃越大，得分越低

**质量标准**：
- 合格阈值: 70分
- 最小整体覆盖率: 80%
- 单集最小覆盖率: 60%

### 2. 配置系统

**文件**: `src/core/config.py`

新增 `IngestionConfig` 类：
```python
initial_chapter_multiplier: int = 2  # 初始章节数倍数
batch_size: int = 10  # 每批提取章节数
safety_buffer_chapters: int = 10  # 安全缓冲章节数
quality_threshold: float = 70.0  # 质量阈值
min_coverage_ratio: float = 0.8  # 最小覆盖率
min_episode_coverage: float = 0.6  # 单集最小覆盖率
max_concurrent_requests: int = 10  # 最大并发数
enable_concurrent: bool = True  # 是否启用并发
```

### 3. 动态章节提取工作流

**文件**: `src/workflows/ingestion_workflow_v2.py` (新文件)

核心功能：
- ✅ 根据SRT数量预估初始章节数
- ✅ 批量提取并评估对齐质量
- ✅ 动态决定是否继续提取
- ✅ 添加安全缓冲机制
- ✅ 详细的质量报告输出

**算法流程**：
1. 初始提取: SRT数量 × 2 倍章节
2. 对齐并评估质量
3. 如果覆盖率 < 80% 或单集 < 60%，继续提取10章
4. 如果质量合格，再提取10章作为安全缓冲
5. 输出详细质量报告

---

## 🚧 待完成 (Phase 3 & 4)

### Phase 3: 并发优化

#### 3.1 异步Analyst方法

**文件**: `src/agents/deepseek_analyst.py`

需要添加：
```python
async def extract_events_async(self, text: str, context_id: str = "") -> List[NarrativeEvent]:
    """异步版本的 extract_events"""
    # 使用 asyncio 包装同步LLM调用
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self.extract_events, text, context_id)
```

#### 3.2 并发提取逻辑

**文件**: `src/workflows/ingestion_workflow_v2.py`

修改 `_extract_chapters()` 方法：
```python
async def _extract_chapters(self, chapters: List[Tuple[str, str]]) -> List[Dict]:
    """并发提取章节事件"""
    semaphore = asyncio.Semaphore(self.cfg.max_concurrent_requests)
    
    async def extract_with_limit(title, content):
        async with semaphore:
            return await self.analyst.extract_events_async(content, title)
    
    tasks = [extract_with_limit(title, content) for title, content in chapters]
    results = await asyncio.gather(*tasks)
    
    novel_events = []
    for (title, _), events in zip(chapters, results):
        novel_events.append({
            "id": title,
            "events": [e.model_dump() for e in events]
        })
    
    return novel_events
```

修改 `_parse_all_srt_files()` 方法实现并发SRT解析。

### Phase 4: 文档更新

#### 4.1 更新架构文档

**文件**: `docs/architecture/logic_flows.md`

需要更新：
- Workflow 1 的详细流程
- 动态章节提取策略说明
- 质量评估标准
- 并发优化说明

#### 4.2 添加配置文档

创建 `docs/CONFIGURATION.md`：
- 所有配置项说明
- 质量阈值调优指南
- 并发参数建议

#### 4.3 更新 README

添加：
- 动态章节提取功能说明
- 使用示例
- 质量报告解读

### Phase 5: 测试与验证

- [ ] 运行 `python scripts/validate_standards.py`
- [ ] 测试动态章节提取流程
- [ ] 测试并发性能
- [ ] 验证质量评估准确性

---

## 📝 使用说明

### 当前可用功能

1. **质量评估**：
```python
from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine

aligner = DeepSeekAlignmentEngine(client)
quality_report = aligner.evaluate_alignment_quality(alignment_results, threshold=70.0)

print(f"综合得分: {quality_report.overall_score}")
print(f"是否合格: {quality_report.is_qualified}")
print(f"需要更多章节: {quality_report.needs_more_chapters}")
```

2. **动态章节提取** (需要替换原workflow文件):
```bash
# 备份原文件
mv src/workflows/ingestion_workflow.py src/workflows/ingestion_workflow_old.py

# 使用新版本
mv src/workflows/ingestion_workflow_v2.py src/workflows/ingestion_workflow.py

# 运行
python main.py ingest --id PROJ_002
```

### 配置调整

编辑 `src/core/config.py` 中的 `IngestionConfig`:
```python
@dataclass
class IngestionConfig:
    initial_chapter_multiplier: int = 3  # 改为3倍
    quality_threshold: float = 75.0  # 提高阈值
    # ...
```

---

## 🔍 下一步行动

1. **立即可做**：
   - 替换 workflow 文件测试动态提取
   - 调整配置参数观察效果
   
2. **需要开发**：
   - 实现异步方法（Phase 3.1）
   - 实现并发逻辑（Phase 3.2）
   
3. **需要完善**：
   - 更新文档（Phase 4）
   - 运行验证（Phase 5）

---

**最后更新**: 2026-02-03
**状态**: Phase 1-2 完成，Phase 3-5 待实施
