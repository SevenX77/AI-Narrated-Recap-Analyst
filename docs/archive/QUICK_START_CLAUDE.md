# Claude Sonnet 4.5 快速开始指南

> **您的 Claude API Key**: `sk-K8IJLx3fdq22F81rxvQpAmaGyC4ceoy1yrZ8mwZs17PDW7nq`

## 🚀 四步快速配置

### 步骤 1: 运行自动配置脚本

```bash
# 在项目根目录执行
chmod +x scripts/setup_claude.sh
./scripts/setup_claude.sh
```

脚本会自动创建 `.env` 文件并填入您的 API Key。

### 步骤 2: 安装 Claude SDK

```bash
pip install anthropic
```

### 步骤 3: 对比测试两种计费模式 ⭐ 重要

```bash
python scripts/compare_claude_billing_modes.py
```

**OneChats 提供两种计费模式**：
- **次数模式** (`https://api.onechats.top`) - 按调用次数计费
- **额度模式** (`https://chatapi.onechats.top`) - 按 token 使用量计费

对比脚本会：
- ✅ 测试不同规模的任务（简单问答、短文本、章节分析等）
- ✅ 计算两种模式的实际成本
- ✅ 给出针对章节分析的最优建议

### 步骤 4: 基础功能测试

```bash
python scripts/test_claude_api.py
```

测试脚本会验证：
- ✅ API 连接状态
- ✅ Thinking 模式推理能力
- ✅ 费用估算

## 🔄 切换配置

### 切换 LLM Provider

编辑 `.env` 文件，修改：

```bash
LLM_PROVIDER=claude
```

### 切换计费模式

在 `.env` 文件中修改 `CLAUDE_BASE_URL`：

```bash
# 使用次数模式（按调用次数计费）
CLAUDE_BASE_URL=https://api.onechats.top

# 或使用额度模式（按 token 计费）
CLAUDE_BASE_URL=https://chatapi.onechats.top
```

修改后重启程序即可生效。

## 💰 计费模式对比

### 两种模式说明

| 计费模式 | 计费方式 | 适用场景 |
|---------|---------|---------|
| 次数模式 | 固定每次调用成本 | 短任务、简单问答、成本可预测 |
| 额度模式 | 按 token 使用量计费 | 长文本、章节分析、灵活计费 |

### 费用参考（基于对比测试结果）

运行 `python scripts/compare_claude_billing_modes.py` 获取您的实际使用场景的成本对比！

**典型场景预估**：
- 简单问答（~100 tokens）
- 章节分析（~2000 tokens）  
- 深度推理（~4000 tokens）

**建议**：先运行对比测试，根据实际结果选择最优模式！

## 📖 更多信息

- **详细配置**: [CLAUDE_SETUP_GUIDE.md](./CLAUDE_SETUP_GUIDE.md)
- **项目文档**: [README.md](../README.md)

---

## ✅ 配置清单

本次配置已完成：

1. ✅ 更新 `src/core/config.py` - 多 LLM 提供商支持
2. ✅ 创建 `docs/CLAUDE_SETUP_GUIDE.md` - 完整配置文档
3. ✅ 创建 `scripts/test_claude_api.py` - API 测试脚本
4. ✅ 创建 `scripts/compare_claude_billing_modes.py` - 计费模式对比测试 ⭐ NEW
5. ✅ 创建 `scripts/setup_claude.sh` - 自动配置脚本
6. ✅ 更新 `README.md` - 添加配置说明
7. ✅ 配置 OneChats 双计费模式支持

**下一步**: 运行对比测试 → `python scripts/compare_claude_billing_modes.py`

---

*Last Updated: 2026-02-08*
