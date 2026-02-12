# LLM并发调用管理系统

## 📋 概述

统一的LLM调用管理系统，提供：
- ✅ 多提供商限流规则管理
- ✅ 自动限流检测与等待
- ✅ 智能重试策略（指数退避）
- ✅ 并发控制
- ✅ 使用统计追踪
- ✅ 自动测试工具

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────┐
│          LLMCallManager（全局单例）          │
├─────────────────────────────────────────────┤
│  - 配置管理（加载/保存/更新）                │
│  - 限流器管理（每个模型一个限流器）          │
│  - 统一调用接口（带限流+重试）               │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼──────┐ ┌─────▼──────┐
│ RateLimiter │ │ RetryLogic │
├─────────────┤ ├────────────┤
│ - QPM限制   │ │ - 指数退避  │
│ - QPD限制   │ │ - 错误识别  │
│ - TPM限制   │ │ - 智能延迟  │
│ - 并发控制   │ └────────────┘
└─────────────┘
```

---

## 🔧 核心组件

### 1. `LLMRateLimitConfig`
**限流配置模型**

```python
@dataclass
class LLMRateLimitConfig:
    provider: str  # 提供商（anthropic, deepseek, openai）
    model: str  # 模型名称
    
    # 限流规则
    requests_per_minute: Optional[int] = None  # QPM
    requests_per_day: Optional[int] = None  # QPD
    tokens_per_minute: Optional[int] = None  # TPM
    tokens_per_day: Optional[int] = None  # TPD
    
    # 并发控制
    max_concurrent: int = 1
    
    # 重试策略
    max_retries: int = 3
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    
    # 测试状态
    is_tested: bool = False
    last_test_date: Optional[str] = None
    test_notes: str = ""
```

### 2. `RateLimiter`
**限流器（滑动窗口算法）**

功能：
- 跟踪时间窗口内的请求数和token数
- 确保不超过QPM/QPD/TPM/TPD限制
- 并发数控制
- 自动清理过期记录

核心方法：
```python
async def acquire(estimated_tokens: int) -> bool:
    """请求执行权限"""
    # 检查是否超过限制
    # 如果未超过，记录并返回True
    # 如果超过，返回False

async def release():
    """释放执行权限"""
```

### 3. `LLMCallManager`
**调用管理器（全局单例）**

功能：
- 配置管理（加载/保存/更新）
- 为每个模型创建限流器
- 提供统一的调用接口
- 自动重试与错误处理

核心方法：
```python
async def call_with_rate_limit(
    func: Callable,
    provider: str,
    model: str,
    estimated_tokens: int = 1000,
    *args, **kwargs
) -> Any:
    """带限流控制的LLM调用"""
    # 1. 获取配置和限流器
    # 2. 等待获取执行权限（阻塞式）
    # 3. 执行函数（带重试）
    # 4. 释放执行权限
```

---

## 📦 预定义配置

### Anthropic Claude
```python
{
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "requests_per_minute": 50,  # 待测试验证
    "tokens_per_minute": 40000,  # 待测试验证
    "max_concurrent": 3,
    "max_retries": 3,
    "base_retry_delay": 2.0
}
```

### DeepSeek
```python
{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "requests_per_minute": 60,  # 待测试验证
    "max_concurrent": 2,
    "max_retries": 3,
    "base_retry_delay": 3.0
}
```

### OpenAI GPT-4
```python
{
    "provider": "openai",
    "model": "gpt-4",
    "requests_per_minute": 500,  # 付费账户
    "requests_per_day": 10000,
    "tokens_per_minute": 10000,
    "max_concurrent": 5
}
```

### Conservative（保守配置）
用于未测试的模型：
```python
{
    "requests_per_minute": 10,
    "max_concurrent": 1,
    "max_retries": 5,
    "base_retry_delay": 5.0
}
```

---

## 🚀 使用方法

### 1. 基本使用

```python
from src.core.llm_rate_limiter import get_llm_manager

# 获取全局管理器
manager = get_llm_manager()

# 定义你的API调用函数
def my_llm_call():
    # 实际的LLM调用逻辑
    return client.messages.create(...)

# 使用管理器调用（自动限流+重试）
result = await manager.call_with_rate_limit(
    func=my_llm_call,
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    estimated_tokens=1000  # 预估token使用量
)
```

### 2. 在Workflow中使用

**原代码**（直接调用）：
```python
seg_output = self.novel_segmenter.execute(
    chapter_content=chapter_content,
    chapter_number=chapter.number,
    chapter_title=chapter.title
)
```

**优化后**（使用管理器）：
```python
from src.core.llm_rate_limiter import get_llm_manager

manager = get_llm_manager()

seg_output = await manager.call_with_rate_limit(
    func=self.novel_segmenter.execute,
    provider="deepseek",  # 从config获取
    model="deepseek-chat",
    estimated_tokens=2000,  # 根据章节长度估算
    chapter_content=chapter_content,
    chapter_number=chapter.number,
    chapter_title=chapter.title
)
```

### 3. 查看统计信息

```python
# 获取所有限流器的统计信息
stats = manager.get_all_stats()

for model, stat in stats.items():
    print(f"{model}:")
    print(f"  当前并发: {stat['current_concurrent']}")
    print(f"  最近1分钟请求: {stat['requests_last_minute']}")
    print(f"  最近1天请求: {stat['requests_last_day']}")
    print(f"  最近1分钟tokens: {stat['tokens_last_minute']}")
```

### 4. 更新配置

```python
# 根据测试结果更新配置
manager.update_config(
    "anthropic_claude",
    requests_per_minute=80,  # 更新QPM
    is_tested=True,
    last_test_date="2026-02-10",
    test_notes="测试验证：QPM=80可稳定运行"
)
```

---

## 🧪 限流规则测试

### 测试工具使用

```bash
# 运行交互式测试工具
python3 scripts/test/test_llm_rate_limits.py
```

### 测试流程

1. **选择测试模式**
   - 快速测试（使用mock数据）
   - 单个提供商测试（需要实际API）
   - 查看当前配置

2. **自动测试逻辑**
   - 逐渐加快请求频率
   - 直到触发限流
   - 记录成功/失败次数
   - 计算估算的QPM
   - 给出建议配置

3. **测试结果**
   ```json
   {
     "provider": "anthropic",
     "model": "claude-3-5-sonnet-20241022",
     "test_date": "2026-02-10T12:00:00",
     "successful_requests": 45,
     "rate_limited_requests": 5,
     "estimated_qpm": 48,
     "suggested_qpm": 38,
     "notes": "触发5次限流，建议QPM设置为38"
   }
   ```

4. **更新配置**
   - 工具会自动询问是否更新配置
   - 更新后的配置持久化到`data/llm_configs.json`

### 实际API测试（示例）

```python
# 创建实际的API调用函数
def test_anthropic():
    from anthropic import Anthropic
    client = Anthropic(api_key="...")
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hi"}]
    )
    return response

# 测试
tester = LLMRateLimitTester()
result = await tester.test_provider(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    test_func=test_anthropic,
    test_duration=60,  # 测试60秒
    ramp_up_delay=2.0  # 初始延迟2秒
)

# 更新配置
tester.update_configs_from_test()
```

---

## 📊 测试结果管理

### 测试记录格式

```json
{
  "anthropic_claude": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "test_date": "2026-02-10T12:00:00",
    "test_duration_seconds": 60,
    "total_requests": 50,
    "successful_requests": 45,
    "rate_limited_requests": 5,
    "other_errors": 0,
    "estimated_qpm": 48,
    "suggested_qpm": 38,
    "notes": "触发5次限流，建议QPM=38"
  }
}
```

### 测试结果文件

- **配置文件**: `data/llm_configs.json`
- **测试结果**: `data/llm_rate_limit_test_results.json`

---

## 🔄 集成到现有Workflow

### Step 1: 导入管理器

```python
from src.core.llm_rate_limiter import get_llm_manager

class NovelProcessingWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__()
        # ...其他初始化
        
        # 初始化LLM调用管理器
        self.llm_manager = get_llm_manager()
```

### Step 2: 替换直接调用

**原方法**（在_segment_single_chapter中）：
```python
seg_output = self.novel_segmenter.execute(
    chapter_content=chapter_content,
    chapter_number=chapter.number,
    chapter_title=chapter.title,
    provider=workflow_config.segmentation_provider
)
```

**优化后**：
```python
seg_output = await self.llm_manager.call_with_rate_limit(
    func=self.novel_segmenter.execute,
    provider="deepseek",  # 或从config获取
    model="deepseek-chat",
    estimated_tokens=len(chapter_content) * 2,  # 根据内容长度估算
    chapter_content=chapter_content,
    chapter_number=chapter.number,
    chapter_title=chapter.title,
    provider=workflow_config.segmentation_provider
)
```

### Step 3: 移除旧的重试逻辑

现在重试逻辑由`LLMCallManager`统一管理，可以删除workflow中的`_retry_with_backoff`方法。

---

## 📈 性能优化建议

### 1. Token估算

准确的token估算可以提高TPM限流的准确性：

```python
def estimate_tokens(text: str) -> int:
    """估算文本的token数量"""
    # 简单估算：中文1字≈1.5tokens，英文1词≈1.3tokens
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    other_chars = len(text) - chinese_chars
    
    return int(chinese_chars * 1.5 + other_chars * 0.3)

# 使用
estimated_tokens = estimate_tokens(chapter_content)
```

### 2. 批量操作优化

对于批量操作，使用管理器会自动排队和限流：

```python
tasks = []
for chapter in chapters:
    task = self.llm_manager.call_with_rate_limit(
        func=self.novel_segmenter.execute,
        provider="deepseek",
        model="deepseek-chat",
        estimated_tokens=estimate_tokens(chapter.content),
        chapter_content=chapter.content,
        ...
    )
    tasks.append(task)

# 并发执行（管理器会自动限流）
results = await asyncio.gather(*tasks)
```

### 3. 配置调优

根据实际测试结果调整配置：

```python
# 保守配置（高成功率，低速度）
config = {
    "requests_per_minute": 30,
    "max_concurrent": 1,
    "base_retry_delay": 3.0
}

# 激进配置（高速度，可能触发限流）
config = {
    "requests_per_minute": 100,
    "max_concurrent": 5,
    "base_retry_delay": 1.0
}

# 均衡配置（推荐）
config = {
    "requests_per_minute": 50,
    "max_concurrent": 2-3,
    "base_retry_delay": 2.0
}
```

---

## 🐛 故障排查

### 问题1: 仍然频繁触发限流

**原因**：
- 配置的QPM过高
- 多个进程同时使用同一API key

**解决方案**：
1. 降低QPM配置
2. 增加请求延迟
3. 检查是否有其他进程在使用API

### 问题2: 处理速度太慢

**原因**：
- 配置过于保守
- 并发数太低

**解决方案**：
1. 运行测试工具，获取实际限流阈值
2. 根据测试结果调高QPM
3. 增加并发数

### 问题3: 配置未生效

**原因**：
- 配置文件路径错误
- 配置未保存

**解决方案**：
```python
# 检查配置
manager = get_llm_manager()
config = manager.get_config("anthropic", "claude-3-5-sonnet-20241022")
print(config)

# 手动保存配置
manager._save_configs()
```

---

## 📝 最佳实践

### 1. 测试新模型

每次使用新模型前，先运行测试：

```bash
python3 scripts/test/test_llm_rate_limits.py
```

### 2. 定期更新配置

API限流规则可能变化，建议：
- 每月重新测试一次
- 记录测试日期和结果
- 更新配置文件

### 3. 监控使用情况

定期检查统计信息：

```python
# 在workflow结束时输出统计
stats = self.llm_manager.get_all_stats()
logger.info(f"LLM调用统计: {stats}")
```

### 4. 错误日志分析

关注日志中的限流警告：

```
🚫 检测到API限流
⚠️ 执行失败（第1/4次尝试）: Error code: 403
⏳ 等待4.0秒后重试...
```

如果频繁出现，需要调整配置。

---

## 🎯 下一步计划

### 短期
- ✅ 完成核心系统实现
- ⏳ 测试所有预定义配置
- ⏳ 集成到NovelProcessingWorkflow

### 中期
- 自适应限流（根据成功率动态调整）
- 成本追踪与预算控制
- Web Dashboard可视化

### 长期
- 多账户负载均衡
- 分布式限流（多机器协同）
- 机器学习预测最优配置

---

*最后更新: 2026-02-10*
*版本: 1.0.0*
