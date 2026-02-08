# Claude Sonnet 4.5 Thinking 模型配置指南

## 📋 配置概述

本指南将帮助您配置 Claude Sonnet 4.5 Thinking 模型，实现 DeepSeek 和 Claude 之间的灵活切换。

## 🔧 配置步骤

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件，添加以下内容：

```bash
# ============================================================================
# LLM Provider Configuration
# ============================================================================
# 当前使用的 LLM 提供商: deepseek | claude
# 修改此值可以在不同 LLM 之间切换
LLM_PROVIDER=deepseek

# ============================================================================
# DeepSeek Configuration (Default)
# ============================================================================
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat

# ============================================================================
# Claude Configuration (API易中转)
# ============================================================================
CLAUDE_API_KEY=sk-K8IJLx3fdq22F81rxvQpAmaGyC4ceoy1yrZ8mwZs17PDW7nq
CLAUDE_BASE_URL=https://vip.apiyi.com/v1
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929

# Claude Thinking Mode (Extended Thinking) 参数
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=1.0

# ============================================================================
# Application Configuration
# ============================================================================
LOG_LEVEL=INFO
```

### 2. 配置说明

#### LLM Provider 选择

- **DeepSeek (默认)**: `LLM_PROVIDER=deepseek`
- **Claude**: `LLM_PROVIDER=claude`

#### Claude 配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `CLAUDE_API_KEY` | `sk-K8IJLx3fdq...` | OneChats 中转服务提供的密钥 |
| `CLAUDE_BASE_URL` | 见下方说明 | OneChats 中转服务地址（两种计费模式） |
| `CLAUDE_MODEL_NAME` | `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 模型标识 |
| `CLAUDE_MAX_TOKENS` | `4096` | 最大输出 token 数 |
| `CLAUDE_TEMPERATURE` | `1.0` | 温度参数（控制创造性） |

#### OneChats 计费模式选择

OneChats 提供两种计费模式：

| 模式 | Base URL | 适用场景 | 说明 |
|------|----------|---------|------|
| **次数模式** | `https://api.onechats.top` | 短任务、简单问答 | 按调用次数计费，成本固定 |
| **额度模式** | `https://chatapi.onechats.top` | 长文本、章节分析 | 按 token 使用量计费，灵活计费 |

**如何选择？**
- 运行对比测试：`python scripts/compare_claude_billing_modes.py`
- 脚本会自动测试两种模式，给出成本对比和使用建议

### 3. 测试配置

运行测试脚本验证配置：

```bash
# 1. 首先确保已安装 anthropic SDK
pip install anthropic

# 2. 运行测试脚本
python scripts/test_claude_api.py
```

测试脚本将执行以下检查：
- ✅ 基础连接测试
- ✅ Thinking 模式推理测试
- ✅ 项目配置集成测试
- ✅ 费用估算

### 4. 在代码中使用

配置完成后，系统会根据 `LLM_PROVIDER` 自动选择对应的 LLM：

```python
from src.core.config import config

# 自动根据 LLM_PROVIDER 使用对应配置
print(f"当前使用: {config.llm.provider}")
print(f"模型: {config.llm.model_name}")
print(f"API Key: {config.llm.api_key[:20]}...")

# 获取完整配置
provider_config = config.llm.get_provider_config()
```

### 5. 切换 LLM Provider

只需修改 `.env` 文件中的 `LLM_PROVIDER` 值：

```bash
# 使用 Claude
LLM_PROVIDER=claude

# 使用 DeepSeek
LLM_PROVIDER=deepseek
```

修改后重启程序即可生效。

## 💰 费用信息

### Claude Sonnet 4.5 定价

- **输入**: $3 / 百万 tokens
- **输出**: $15 / 百万 tokens

### 费用估算示例

| 任务类型 | 输入 tokens | 输出 tokens | 费用 (USD) | 费用 (CNY) |
|---------|-------------|-------------|-----------|-----------|
| 简单问答 | 50 | 100 | $0.0017 | ¥0.012 |
| 章节分析 | 2000 | 1000 | $0.021 | ¥0.15 |
| 深度推理 | 5000 | 3000 | $0.060 | ¥0.43 |

💡 **建议**: 先用测试脚本进行小规模测试，评估实际费用后再决定是否大规模使用。

## 🔍 API易中转服务说明

### 优势

- ✅ 国内直连，无需翻墙
- ✅ 支持人民币支付
- ✅ 稳定可靠的中转服务
- ✅ 与官方 API 完全兼容

### 参考资源

- [API易 Claude 配置教程](https://help.apiyi.com/apiyi-claude-code-setup-tutorial.html)
- [Claude API 完全指南](https://help.apiyi.com/claude-4-5-sonnet-api-complete-guide.html)
- [Anthropic 官方文档](https://docs.anthropic.com/)

## 🔧 高级配置

### Extended Thinking 模式

Claude Sonnet 4.5 支持扩展思维模式，适用于需要深度推理的任务。

参考官方文档配置：
- [Extended Thinking Documentation](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)

### 自定义参数

在 `.env` 中可以自定义以下参数：

```bash
# 控制输出长度
CLAUDE_MAX_TOKENS=8192

# 控制创造性（0.0-2.0）
CLAUDE_TEMPERATURE=0.7
```

## 📝 最佳实践

1. **开发阶段**: 使用 DeepSeek（成本更低）
2. **质量要求高**: 切换到 Claude（推理能力更强）
3. **费用控制**: 合理设置 `CLAUDE_MAX_TOKENS`
4. **定期测试**: 使用测试脚本监控 API 状态

## ❓ 故障排查

### 问题 1: 连接失败

**现象**: `Connection Error` 或 `API Key Invalid`

**解决方案**:
1. 检查 `.env` 文件是否存在于项目根目录
2. 确认 `CLAUDE_API_KEY` 正确无误
3. 验证 `CLAUDE_BASE_URL` 是否可访问

### 问题 2: 模型名称错误

**现象**: `Model not found` 错误

**解决方案**:
1. 确认 `CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929`
2. 如果 API易 更新了模型名称，请相应修改

### 问题 3: 费用异常高

**现象**: Token 消耗超出预期

**解决方案**:
1. 降低 `CLAUDE_MAX_TOKENS` 值
2. 优化提示词，减少不必要的输入
3. 使用测试脚本评估单次调用成本

## 📞 技术支持

- **项目 Issues**: 在 GitHub 提交 issue
- **API易支持**: 访问 [API易帮助中心](https://help.apiyi.com/)
- **Claude 官方**: [Anthropic Support](https://support.anthropic.com/)

---

*Last Updated: 2026-02-08*
