#!/bin/bash
# Claude Sonnet 4.5 快速配置脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "========================================"
echo "Claude Sonnet 4.5 快速配置向导"
echo "========================================"
echo ""

# 检查 .env 文件是否存在
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  .env 文件已存在"
    read -p "是否覆盖现有配置？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 已取消配置"
        exit 1
    fi
    echo "📝 将覆盖现有 .env 文件..."
fi

# 创建 .env 文件
echo "📝 创建 .env 文件..."

cat > "$ENV_FILE" << 'EOF'
# ============================================================================
# LLM Provider Configuration
# ============================================================================
# 当前使用的 LLM 提供商: deepseek | claude
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
EOF

echo "✅ .env 文件创建成功！"
echo ""
echo "📋 配置信息："
echo "   - DeepSeek: 默认启用（需配置 DEEPSEEK_API_KEY）"
echo "   - Claude: 已预配置 API Key"
echo ""
echo "🔄 切换到 Claude："
echo "   在 .env 中设置: LLM_PROVIDER=claude"
echo ""
echo "🧪 测试 Claude 配置："
echo "   pip install anthropic"
echo "   python scripts/test_claude_api.py"
echo ""
echo "📖 详细文档："
echo "   docs/CLAUDE_SETUP_GUIDE.md"
echo ""
echo "========================================"
echo "✅ 配置完成！"
echo "========================================"
