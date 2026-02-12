# LLM管理器集成指南

## 🎯 集成目标

将`LLMCallManager`集成到`NovelProcessingWorkflow`，实现：
1. 统一的限流控制
2. 自动重试机制
3. 多模型配置支持
4. 并发智能管理

---

## 📝 集成步骤

### Step 1: 更新Workflow初始化

```python
from src.core.llm_rate_limiter import get_llm_manager

class NovelProcessingWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        
        # 初始化工具
        self.novel_importer = NovelImporter()
        # ... 其他工具
        
        # 初始化LLM调用管理器
        self.llm_manager = get_llm_manager()
        
        logger.info(f"✅ {self.name} 初始化完成")
```

### Step 2: 替换分段调用

**原代码** (`_segment_single_chapter`):
```python
# 使用自定义重试逻辑
if workflow_config.retry_on_error:
    seg_output = await self._retry_with_backoff(
        self.novel_segmenter.execute,
        chapter_content=chapter_content,
        chapter_number=chapter.number,
        chapter_title=chapter.title,
        provider=workflow_config.segmentation_provider,
        max_retries=workflow_config.max_retries,
        base_delay=workflow_config.retry_delay
    )
else:
    seg_output = self.novel_segmenter.execute(...)

# 手动延迟
if workflow_config.request_delay > 0:
    await asyncio.sleep(workflow_config.request_delay)
```

**优化后**:
```python
# 使用LLM管理器（自动限流+重试+延迟）
seg_output = await self.llm_manager.call_with_rate_limit(
    func=self.novel_segmenter.execute,
    provider=workflow_config.segmentation_provider,  # "deepseek"
    model="deepseek-chat",  # 或从config获取
    estimated_tokens=self._estimate_tokens(chapter_content),
    chapter_content=chapter_content,
    chapter_number=chapter.number,
    chapter_title=chapter.title,
    provider=workflow_config.segmentation_provider
)
```

### Step 3: 替换标注调用

**原代码** (`_annotate_single_chapter`):
```python
if workflow_config.retry_on_error:
    result = await self._retry_with_backoff(...)
else:
    result = self.novel_annotator.execute(...)

if workflow_config.request_delay > 0:
    await asyncio.sleep(workflow_config.request_delay)
```

**优化后**:
```python
result = await self.llm_manager.call_with_rate_limit(
    func=self.novel_annotator.execute,
    provider=workflow_config.annotation_provider,
    model="deepseek-chat",
    estimated_tokens=self._estimate_tokens_for_annotation(segmentation_result),
    segmentation_result=segmentation_result,
    enable_functional_tags=workflow_config.enable_functional_tags,
    provider=workflow_config.annotation_provider
)
```

### Step 4: 添加Token估算方法

```python
def _estimate_tokens(self, text: str) -> int:
    """
    估算文本的token数量
    
    中文: 1字 ≈ 1.5 tokens
    英文: 1词 ≈ 1.3 tokens
    """
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    other_chars = len(text) - chinese_chars
    
    # 保守估算（包含输出tokens）
    input_tokens = int(chinese_chars * 1.5 + other_chars * 0.3)
    output_tokens = int(input_tokens * 0.2)  # 假设输出是输入的20%
    
    return input_tokens + output_tokens

def _estimate_tokens_for_annotation(self, seg_result: ParagraphSegmentationResult) -> int:
    """估算标注任务的token数量"""
    total_chars = sum(len(p.content) for p in seg_result.paragraphs)
    return self._estimate_tokens("x" * total_chars)
```

### Step 5: 删除旧的重试逻辑

现在可以删除`_retry_with_backoff`方法，因为LLM管理器已提供统一的重试功能。

```python
# ❌ 删除这个方法
async def _retry_with_backoff(self, func, *args, max_retries=3, base_delay=2.0, **kwargs):
    ...
```

### Step 6: 简化Config

现在这些配置项可以移除（由LLM管理器统一管理）：

```python
# ❌ 可以移除（可选）
class NovelProcessingConfig:
    retry_on_error: bool = True
    max_retries: int = 3
    retry_delay: float = 2.0
    request_delay: float = 1.5
```

保留这些配置也可以，作为override选项。

---

## 🔄 完整代码示例

### 修改后的`_segment_single_chapter`

```python
async def _segment_single_chapter(
    self,
    chapter: ChapterInfo,
    novel_content: str,
    workflow_config: NovelProcessingConfig
) -> ParagraphSegmentationResult:
    """分段单个章节（使用LLM管理器）"""
    logger.info(f"   处理章节 {chapter.number}: {chapter.title}")
    
    # 提取章节内容
    lines = novel_content.split('\n')
    end_line = chapter.end_line if chapter.end_line is not None else len(lines)
    chapter_content = '\n'.join(lines[chapter.start_line:end_line])
    
    # 使用LLM管理器调用（自动限流+重试）
    seg_output = await self.llm_manager.call_with_rate_limit(
        func=self.novel_segmenter.execute,
        provider=workflow_config.segmentation_provider,
        model="deepseek-chat",  # 或从config获取
        estimated_tokens=self._estimate_tokens(chapter_content),
        chapter_content=chapter_content,
        chapter_number=chapter.number,
        chapter_title=chapter.title,
        provider=workflow_config.segmentation_provider
    )
    
    return seg_output.json_result
```

---

## ⚙️ 配置文件管理

### 配置文件位置
```
data/llm_configs.json
```

### 配置文件格式

```json
{
  "anthropic_claude": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "requests_per_minute": 50,
    "tokens_per_minute": 40000,
    "max_concurrent": 3,
    "max_retries": 3,
    "base_retry_delay": 2.0,
    "is_tested": false,
    "last_test_date": null,
    "test_notes": "默认配置，待测试验证"
  },
  "deepseek_chat": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "requests_per_minute": 60,
    "max_concurrent": 2,
    "max_retries": 3,
    "base_retry_delay": 3.0,
    "is_tested": false,
    "test_notes": "默认配置，待测试验证"
  }
}
```

### 手动编辑配置

可以直接编辑`data/llm_configs.json`，下次运行时会自动加载。

---

## 🧪 测试与验证

### 1. 运行集成演示

```bash
python3 scripts/test/test_llm_manager_integration.py
```

输出示例：
```
✅ 请求1: Response to: Test prompt 1...
✅ 请求2: Response to: Test prompt 2...
🚫 检测到API限流
⚠️ 执行失败（第1/4次尝试）: Error code: 403
⏳ 等待4.0秒后重试...
✅ 请求3: Response to: Test prompt 3...

📊 成功率: 10/10
```

### 2. 测试实际API限流

需要创建实际的API调用函数：

```python
# 在scripts/test/test_llm_rate_limits.py中实现

def test_deepseek_actual():
    """测试DeepSeek实际限流"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=50
    )
    
    return response

# 运行测试
tester = LLMRateLimitTester()
result = await tester.test_provider(
    provider="deepseek",
    model="deepseek-chat",
    test_func=test_deepseek_actual,
    test_duration=120,  # 测试2分钟
    ramp_up_delay=3.0
)
```

### 3. 查看测试结果

测试完成后会生成：
- `data/llm_configs.json` - 更新后的配置
- `data/llm_rate_limit_test_results.json` - 测试结果记录

---

## 📈 不同模型的策略

### DeepSeek（当前主力）
```python
{
    "requests_per_minute": 30,  # 保守估计
    "max_concurrent": 1,  # 串行化
    "base_retry_delay": 3.0,  # 较长延迟
    "test_notes": "经验值：QPM>30会频繁触发限流"
}
```

### Claude（Anthropic）
```python
{
    "requests_per_minute": 50,  # 付费账户
    "tokens_per_minute": 40000,
    "max_concurrent": 3,
    "base_retry_delay": 2.0
}
```

### GPT-4（OpenAI）
```python
{
    "requests_per_minute": 500,  # 付费账户
    "tokens_per_minute": 10000,
    "max_concurrent": 5,
    "base_retry_delay": 1.0
}
```

---

## 💡 使用建议

### 1. 首次使用新模型

```bash
# 1. 运行测试工具
python3 scripts/test/test_llm_rate_limits.py

# 2. 选择"测试单个提供商"
# 3. 输入实际的API调用函数
# 4. 等待测试完成
# 5. 根据建议更新配置
```

### 2. 监控使用情况

在workflow结束时输出统计：

```python
# 在run方法最后
stats = self.llm_manager.get_all_stats()
logger.info(f"📊 LLM调用统计: {json.dumps(stats, indent=2)}")
```

### 3. 调优策略

| 观察到的现象 | 调整建议 |
|------------|---------|
| 频繁触发限流 | 降低QPM或max_concurrent |
| 处理速度太慢 | 提高QPM或max_concurrent |
| 成功率>99% | 可以更激进配置 |
| 成功率<90% | 需要更保守配置 |

---

## 🔧 高级功能

### 1. 自定义限流策略

```python
# 创建自定义配置
custom_config = LLMRateLimitConfig(
    provider="my_provider",
    model="my_model",
    requests_per_minute=20,
    max_concurrent=1,
    max_retries=5,
    base_retry_delay=5.0,
    rate_limit_errors=["403", "429", "quota_exceeded"]
)

# 添加到管理器
manager = get_llm_manager()
manager.configs["my_provider_my_model"] = custom_config
manager.limiters["my_provider_my_model"] = RateLimiter(custom_config)
manager._save_configs()
```

### 2. 实时调整配置

```python
# 运行时动态调整
manager.update_config(
    "deepseek_chat",
    requests_per_minute=40,  # 降低QPM
    max_concurrent=1  # 串行化
)
```

### 3. 多账户支持

```python
# 为同一模型配置多个账户
configs = {
    "deepseek_account1": LLMRateLimitConfig(
        provider="deepseek",
        model="deepseek-chat",
        requests_per_minute=60,
        ...
    ),
    "deepseek_account2": LLMRateLimitConfig(
        provider="deepseek",
        model="deepseek-chat",
        requests_per_minute=60,
        ...
    )
}

# 轮询使用
account = f"deepseek_account{(i % 2) + 1}"
result = await manager.call_with_rate_limit(
    func=...,
    provider="deepseek",
    model=account,
    ...
)
```

---

## 🚀 实战案例

### 案例1: 处理100章小说

**原方案**（无管理器）:
- 配置: 并发=3, 无重试
- 结果: 频繁触发限流，成功率40%
- 耗时: 10分钟

**优化方案**（使用管理器）:
```python
config = NovelProcessingConfig(
    max_concurrent_chapters=2,  # Workflow层并发
    # LLM管理器会进一步控制实际并发
)

# LLM配置（自动加载）
llm_config = {
    "requests_per_minute": 30,
    "max_concurrent": 1,  # LLM层并发
    "max_retries": 3
}
```

- 结果: 自动重试，成功率95%+
- 耗时: 15-20分钟

### 案例2: 混合使用多个模型

```python
# 分段使用DeepSeek（便宜）
seg_output = await self.llm_manager.call_with_rate_limit(
    func=self.novel_segmenter.execute,
    provider="deepseek",
    model="deepseek-chat",
    ...
)

# 标注使用Claude（质量高）
ann_output = await self.llm_manager.call_with_rate_limit(
    func=self.novel_annotator.execute,
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    ...
)

# 管理器会为每个模型独立管理限流
```

---

## 📊 监控与统计

### 实时监控

```python
# 每处理10章输出一次统计
if len(result.segmentation_results) % 10 == 0:
    stats = self.llm_manager.get_all_stats()
    logger.info(f"📊 当前LLM使用情况:")
    for model, stat in stats.items():
        logger.info(f"  {model}:")
        logger.info(f"    并发: {stat['current_concurrent']}")
        logger.info(f"    最近1分钟请求: {stat['requests_last_minute']}")
```

### 最终报告

```python
# 在workflow结束时生成LLM使用报告
def _generate_llm_usage_report(self, processing_dir: str):
    """生成LLM使用报告"""
    stats = self.llm_manager.get_all_stats()
    
    report = f"""# LLM使用统计报告

## 各模型使用情况

"""
    for model, stat in stats.items():
        report += f"""### {model}
- 当前并发: {stat['current_concurrent']}
- 最近1分钟请求: {stat['requests_last_minute']}
- 最近1天请求: {stat['requests_last_day']}
- 最近1分钟tokens: {stat['tokens_last_minute']}

"""
    
    filepath = Path(processing_dir) / "reports" / "llm_usage_report.md"
    filepath.write_text(report, encoding='utf-8')
```

---

## ⚙️ 配置文件示例

### 生产环境配置

```json
{
  "deepseek_chat": {
    "provider": "deepseek",
    "model": "deepseek-chat",
    "requests_per_minute": 30,
    "max_concurrent": 1,
    "max_retries": 3,
    "base_retry_delay": 3.0,
    "max_retry_delay": 30.0,
    "rate_limit_errors": ["403", "429", "rate limit"],
    "is_tested": true,
    "last_test_date": "2026-02-10",
    "test_notes": "实际测试：QPM>30触发限流，建议QPM=30"
  }
}
```

### 测试环境配置

```json
{
  "deepseek_chat": {
    "requests_per_minute": 10,
    "max_concurrent": 1,
    "max_retries": 5,
    "base_retry_delay": 5.0,
    "test_notes": "测试环境：极度保守配置"
  }
}
```

---

## 🎓 关键概念

### QPM vs max_concurrent

- **QPM (Queries Per Minute)**: 每分钟最大请求数（API提供商限制）
- **max_concurrent**: 最大并发数（同时进行的请求数）

**关系**：
```
实际QPM = min(配置QPM, max_concurrent * 60/平均响应时间)

例如：
- 配置QPM=60
- max_concurrent=3
- 平均响应时间=10秒
- 实际QPM = min(60, 3 * 60/10) = min(60, 18) = 18
```

**建议**：
- QPM设置为API限制的80%（留余量）
- max_concurrent根据平均响应时间调整

### 滑动窗口 vs 令牌桶

当前实现使用**滑动窗口算法**：
- 记录最近60秒的所有请求
- 计算窗口内请求数是否超过QPM
- 优点：精确
- 缺点：内存占用稍高

如果需要更高性能，可改用**令牌桶算法**。

---

## 🐛 常见问题

### Q1: 为什么设置了QPM=60，但实际只有20？

A: 检查以下因素：
1. `max_concurrent`是否太低？
2. 平均响应时间是否很长？
3. 是否有其他限制（TPM, QPD）？

### Q2: 如何知道当前配置是否合理？

A: 运行测试工具：
```bash
python3 scripts/test/test_llm_rate_limits.py
```

### Q3: 配置更新后不生效？

A: 需要重启进程，或调用：
```python
manager._load_configs()  # 重新加载配置
```

---

## 📚 相关文档

- `src/core/llm_rate_limiter.py` - 核心实现
- `scripts/test/test_llm_rate_limits.py` - 测试工具
- `scripts/test/test_llm_manager_integration.py` - 集成演示
- `docs/core/LLM_RATE_LIMIT_SYSTEM.md` - 系统文档

---

*最后更新: 2026-02-10*
*版本: 1.0.0*
