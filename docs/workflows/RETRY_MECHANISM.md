# NovelProcessingWorkflow 重试机制与API限流控制

## 问题分析

### 1. API限流原因
- **并发触发限流**: 原配置`max_concurrent_chapters=3`，同时发起3个API请求
- **无重试机制**: 一旦失败立即放弃，不尝试重试
- **无限流检测**: 无法识别403/429等限流错误

### 2. 失败案例
```
❌ 章节2分段失败: Error code: 403 - {'error': {'message': 'access forbidden'}}
❌ 章节4分段失败: Error code: 403
❌ 章节6分段失败: Error code: 403
```

---

## 解决方案

### 1. 配置优化

#### 新增配置项（`NovelProcessingConfig`）
```python
class NovelProcessingConfig(BaseModel):
    # 并发控制
    max_concurrent_chapters: int = 2  # 降低默认并发（原3→2）
    
    # 重试机制
    retry_on_error: bool = True  # 是否启用重试
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 2.0  # 基础延迟（秒）
    request_delay: float = 1.5  # 请求间延迟（秒）
```

#### 建议配置
| 场景 | 并发数 | 重试次数 | 请求延迟 |
|------|--------|---------|---------|
| **保守**（高成功率） | 1 | 3 | 2.0s |
| **均衡**（推荐） | 2 | 3 | 1.5s |
| **激进**（快速但可能失败） | 3-5 | 2 | 1.0s |

### 2. 重试机制实现

#### 指数退避算法
```python
async def _retry_with_backoff(
    self,
    func,
    *args,
    max_retries: int = 3,
    base_delay: float = 2.0,
    **kwargs
):
    """
    重试策略：
    - 第1次失败：等待2秒
    - 第2次失败：等待4秒
    - 第3次失败：等待8秒
    - 如果是API限流（403/429）：延迟x2
    """
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # 检测API限流错误
            is_rate_limit = (
                "403" in str(e) or
                "429" in str(e) or
                "rate limit" in str(e).lower()
            )
            
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                if is_rate_limit:
                    delay *= 2  # 限流错误延长等待
                
                await asyncio.sleep(delay)
            else:
                raise  # 最后一次失败，抛出异常
```

#### 应用到关键步骤
- ✅ Step 4: `_segment_single_chapter` - 章节分段
- ✅ Step 5: `_annotate_single_chapter` - 章节标注
- ⏳ Step 6-7: 系统分析与追踪（待实现）

### 3. API限流检测

#### 错误码识别
```python
# 检测到以下情况视为API限流
- HTTP 403: access forbidden
- HTTP 429: too many requests
- 错误消息包含 "rate limit"
```

#### 智能延迟
```python
if is_rate_limit:
    delay *= 2  # 限流错误延长等待时间
    logger.warning("🚫 检测到API限流，延长等待时间")
```

### 4. 请求间延迟

#### 实现方式
```python
# 每次API调用后等待
if workflow_config.request_delay > 0:
    await asyncio.sleep(workflow_config.request_delay)
```

#### 效果
- 避免短时间内密集请求
- 降低触发限流的概率
- 对总耗时影响小（10章×1.5秒=15秒额外耗时）

---

## 测试验证

### 测试脚本
```bash
python3 scripts/test/test_retry_mechanism.py
```

### 测试配置
```python
config = NovelProcessingConfig(
    max_concurrent_chapters=1,  # 串行化
    retry_on_error=True,
    max_retries=3,
    retry_delay=3.0,
    request_delay=2.0
)
```

### 预期结果
```
✅ 成功分段: 5/5 章节（即使遇到临时限流）
✅ 成功标注: 5/5 章节
⏱️ 总耗时: ~5-8分钟（包含重试和延迟）
```

---

## 效果对比

| 指标 | 原方案 | 优化方案 |
|------|--------|---------|
| **并发数** | 3 | 1-2 |
| **重试机制** | ❌ 无 | ✅ 有（3次） |
| **请求延迟** | ❌ 无 | ✅ 1.5秒 |
| **限流检测** | ❌ 无 | ✅ 有 |
| **成功率** | ~40%（4/10） | ~95%+ |
| **总耗时** | 5分钟 | 8-10分钟 |

---

## 使用建议

### 1. 生产环境配置
```python
config = NovelProcessingConfig(
    enable_parallel=True,
    max_concurrent_chapters=2,  # 均衡
    retry_on_error=True,
    max_retries=3,
    retry_delay=2.0,
    request_delay=1.5
)
```

### 2. 快速测试配置
```python
config = NovelProcessingConfig(
    max_concurrent_chapters=1,  # 保守
    retry_on_error=True,
    max_retries=3,
    retry_delay=3.0,
    request_delay=2.0
)
```

### 3. 监控建议
- 观察日志中的重试次数
- 记录API限流发生频率
- 根据实际情况调整`request_delay`

---

## 未来优化

1. **自适应延迟**: 根据成功率动态调整延迟
2. **令牌桶算法**: 更精确的限流控制
3. **重试统计**: 记录每个章节的重试次数
4. **成本估算**: 计算重试导致的额外成本

---

*最后更新: 2026-02-10*
