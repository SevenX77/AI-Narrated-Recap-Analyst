# Claude + OneChats 配置总结

## 🎯 关键结论

根据 OneChats 官方文档和实际测试，**Claude 模型只能使用额度模式**。

### 为什么不能用次数模式？

OneChats 文档明确指出：
- **次数模式**：仅支持 `gpt-4系列`、`gpt-4-32k系列`、`gpt-4-1106-preview`、`gpt-4o-all`
- **额度模式**：支持所有模型（包括 Claude）

## ✅ 正确配置

```bash
# .env 文件配置
CLAUDE_API_KEY=sk-K8IJLx3fdq22F81rxvQpAmaGyC4ceoy1yrZ8mwZs17PDW7nq
CLAUDE_BASE_URL=https://chatapi.onechats.top/v1/
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929
```

## 💰 实际测试成本（额度模式）

| 任务类型 | 输入 tokens | 输出 tokens | 费用 (USD) | 费用 (CNY) |
|---------|------------|------------|-----------|-----------|
| 简单问答 | 34 | 53 | $0.000897 | ¥0.0065 |
| 叙事分析 | 129 | 807 | $0.012492 | ¥0.0899 |

**章节分析预估**（1000字章节）：
- 输入：~800 tokens
- 输出：~1000 tokens
- 预估费用：~$0.02 (≈ ¥0.14)

## 🔧 使用方式

### Python 代码示例

```python
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# OneChats 使用 OpenAI 兼容的 API
client = OpenAI(
    api_key=os.getenv("CLAUDE_API_KEY"),
    base_url="https://chatapi.onechats.top/v1/"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "你的问题"}
    ]
)

print(response.choices[0].message.content)
```

### 注意事项

1. **使用 `openai` 库，不是 `anthropic` 库**
   - OneChats 提供 OpenAI 兼容的 API
   - 调用方式与 OpenAI API 完全一致

2. **URL 必须加 `/v1/` 后缀**
   - ✅ 正确：`https://chatapi.onechats.top/v1/`
   - ❌ 错误：`https://chatapi.onechats.top`

3. **Token 使用情况**
   - 通过 `response.usage.prompt_tokens` 获取输入 tokens
   - 通过 `response.usage.completion_tokens` 获取输出 tokens

## 📊 成本优化建议

对于章节分析场景（1000-3000字）：

1. **控制输出长度**
   - 设置合理的 `max_tokens` 值
   - 明确指定输出格式和长度要求

2. **批量处理**
   - 将多个小任务合并为一个请求
   - 减少 API 调用次数

3. **提示词优化**
   - 使用简洁明确的提示词
   - 避免不必要的上下文

## 🔗 相关资源

- OneChats 购买地址：https://shop.onechat.club
- API 监控：https://status.onechats.top
- 日志查询：https://query.onechats.top

---

**最后更新**: 2026-02-08
