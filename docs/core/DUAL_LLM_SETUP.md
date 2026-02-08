# 双 LLM Provider 配置指南

## 概述

本项目支持同时使用 **Claude** 和 **DeepSeek** 两个 LLM Provider，实现功能分工：

- **Claude**: 用于复杂任务（小说分段分析、深度理解）
- **DeepSeek**: 用于简单任务（元数据提取、格式处理）

## 架构设计

### LLMClientManager

位置：`src/core/llm_client_manager.py`

核心功能：
1. 统一管理多个 LLM Provider 的客户端实例
2. 单例模式：同一 Provider 复用客户端实例
3. 使用统计：自动记录调用次数和 Token 消耗

### 使用方式

```python
from src.core.llm_client_manager import get_llm_client, get_model_name

# 获取 Claude 客户端
claude_client = get_llm_client("claude")
claude_model = get_model_name("claude")

# 获取 DeepSeek 客户端
deepseek_client = get_llm_client("deepseek")
deepseek_model = get_model_name("deepseek")

# 调用 LLM
response = claude_client.chat.completions.create(
    model=claude_model,
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 环境配置

### .env 文件配置

```bash
# ============================================
# Claude 配置
# ============================================
CLAUDE_API_KEY=sk-K8IJLx3fdq22F81rxvQpAmaGyC4ceoy1yrZ8mwZs17PDW7nq
CLAUDE_BASE_URL=https://chatapi.onechats.ai/v1/
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=1.0

# ============================================
# DeepSeek 配置
# ============================================
DEEPSEEK_API_KEY=sk-你的API密钥  # 需要重新获取
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat

# DeepSeek R1 推理模型
DEEPSEEK_R1_MODEL_NAME=deepseek-reasoner
```

### 获取 DeepSeek API Key

**⚠️ 重要提示**：项目中原有的 DeepSeek API Key 已失效，需要重新获取。

**步骤**：

1. 访问 DeepSeek 官网：https://platform.deepseek.com/api_keys
2. 注册/登录账号
3. 点击"创建 API Key"
4. 复制生成的 API Key（格式：`sk-xxx`，只显示一次）
5. 在 `.env` 文件中配置：
   ```bash
   DEEPSEEK_API_KEY=sk-你复制的密钥
   ```

**注意**：
- API Key 只在创建时显示一次，务必立即保存
- 如果丢失，需要删除旧密钥并创建新密钥

## 工具分工策略

### 已更新的工具

#### 1. NovelMetadataExtractor
- **默认 Provider**: DeepSeek
- **原因**: 元数据提取是简单任务，DeepSeek 性价比高
- **使用**:
  ```python
  # 默认使用 DeepSeek
  extractor = NovelMetadataExtractor()
  
  # 可选指定 Claude
  extractor = NovelMetadataExtractor(provider="claude")
  ```

#### 2. NovelSegmenter
- **默认 Provider**: Claude
- **原因**: 小说分段分析需要高质量理解
- **使用**:
  ```python
  # 默认使用 Claude
  segmenter = NovelSegmenter()
  
  # 可选指定 DeepSeek
  segmenter = NovelSegmenter(provider="deepseek")
  ```

### 其他工具

未更新的工具仍使用全局配置 `config.llm.api_key` 和 `config.llm.base_url`，会根据 `LLM_PROVIDER` 环境变量选择 Provider。

## 测试验证

### 运行测试脚本

```bash
python scripts/test/test_dual_llm_providers.py
```

**测试内容**：
1. ✅ LLMClientManager 客户端创建
2. ✅ Claude API 连接测试
3. ❌ DeepSeek API 连接测试（需要有效的 API Key）
4. ✅ 使用统计功能

**当前测试结果**：
```
✅ 客户端创建: 通过
✅ Claude API: 通过
❌ DeepSeek API: 失败 (API Key 无效)
```

### 成本对比

#### Claude（OneChats 代理）
- 优点：高质量输出，上下文理解强
- 成本：相对较高
- 适用：复杂分析、创意生成

#### DeepSeek
- 优点：价格便宜，速度快
- 成本：约为 Claude 的 1/10
- 适用：简单处理、格式化、规则提取

#### DeepSeek R1（推理模型）
- 优点：逻辑推理能力强，返回推理过程
- 成本：与 DeepSeek Chat 相近
- 适用：规则提取、因果分析、复杂推理

## 使用建议

### 任务分级

| 任务类型 | 推荐 Provider | 说明 |
|---------|--------------|------|
| 元数据提取 | DeepSeek | 简单的结构化提取 |
| 格式转换 | DeepSeek | 文本格式处理 |
| 小说分段 | Claude | 需要深度理解叙事结构 |
| 改编分析 | Claude | 需要对比和创意评估 |
| 规则提取 | DeepSeek R1 | 逻辑推理任务 |
| 质量评估 | Claude | 主观判断和综合评价 |

### 成本优化策略

1. **优先使用 DeepSeek**：除非任务明确需要高质量输出
2. **批量处理**：相同任务批量调用，减少网络开销
3. **缓存结果**：避免重复调用相同内容
4. **监控使用**：定期查看 `LLMClientManager.get_usage_stats()` 统计

## 下一步扩展

### 未来可能添加的功能

1. **自动回退机制**：DeepSeek 失败时自动切换到 Claude
2. **成本预算控制**：设置每日/每月 Token 上限
3. **质量评估**：对比两个模型的输出质量
4. **A/B 测试工具**：同时调用两个模型，选择最优结果

## 故障排查

### DeepSeek API Key 无效

**症状**：
```
Error code: 401 - Authentication Fails
```

**解决**：
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 访问 https://platform.deepseek.com/api_keys 创建新密钥
3. 更新 `.env` 文件后重启应用

### Claude API 连接失败

**症状**：
```
Connection error or timeout
```

**解决**：
1. 检查网络连接
2. 确认 `CLAUDE_BASE_URL` 是否正确
3. 测试 OneChats 代理是否可用

### 客户端创建失败

**症状**：
```
ValueError: API Key not configured
```

**解决**：
1. 确认 `.env` 文件存在于项目根目录
2. 检查环境变量是否正确加载
3. 重新加载环境变量：`from dotenv import load_dotenv; load_dotenv()`

---

**最后更新**: 2026-02-09  
**负责模块**: Core / LLMClientManager
