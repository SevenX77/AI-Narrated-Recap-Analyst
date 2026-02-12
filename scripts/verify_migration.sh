#!/bin/bash
# 验证数据结构迁移是否完整

echo "============================================"
echo "数据结构迁移验证脚本"
echo "============================================"
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📍 项目根目录: $PROJECT_ROOT"
echo ""

# 检查文档中的旧路径引用
echo "🔍 检查文档中的旧路径引用..."
echo "-------------------------------------------"
echo "检查 'processed/' 引用（排除归档和迁移文档）:"
DOCS_PROCESSED=$(grep -r "processed/" docs/ --include="*.md" | grep -v "archive/" | grep -v "MIGRATION" | grep -v "processed_text" | grep -v "processed_files_count" || true)
if [ -z "$DOCS_PROCESSED" ]; then
    echo "✅ 无发现"
else
    echo "⚠️ 发现以下引用:"
    echo "$DOCS_PROCESSED"
fi
echo ""

echo "检查 'raw/srt' 引用（排除归档和迁移文档）:"
DOCS_SRT=$(grep -r "raw/srt" docs/ --include="*.md" | grep -v "archive/" | grep -v "MIGRATION" || true)
if [ -z "$DOCS_SRT" ]; then
    echo "✅ 无发现"
else
    echo "⚠️ 发现以下引用:"
    echo "$DOCS_SRT"
fi
echo ""

# 检查源代码中的旧路径引用
echo "🔍 检查源代码中的旧路径引用..."
echo "-------------------------------------------"
echo "检查 'processed/' 引用（排除注释）:"
SRC_PROCESSED=$(grep -r '"processed/' src/ --include="*.py" | grep -v ".pyc" | grep -v "# " | grep -v '"""' || true)
if [ -z "$SRC_PROCESSED" ]; then
    echo "✅ 无发现"
else
    echo "⚠️ 发现以下引用:"
    echo "$SRC_PROCESSED"
fi
echo ""

echo "检查 'raw/srt' 引用（排除注释）:"
SRC_SRT=$(grep -r '"raw/srt"' src/ --include="*.py" | grep -v ".pyc" | grep -v "# " | grep -v '"""' || true)
if [ -z "$SRC_SRT" ]; then
    echo "✅ 无发现"
else
    echo "⚠️ 发现以下引用:"
    echo "$SRC_SRT"
fi
echo ""

# 检查前端代码
echo "🔍 检查前端代码中的旧路径引用..."
echo "-------------------------------------------"
echo "检查 'files/processed' API路径:"
FRONTEND_PROCESSED=$(grep -r "files/processed" frontend-new/src/ --include="*.ts" --include="*.tsx" || true)
if [ -z "$FRONTEND_PROCESSED" ]; then
    echo "✅ 无发现"
else
    echo "⚠️ 发现以下引用:"
    echo "$FRONTEND_PROCESSED"
fi
echo ""

# 统计结果
echo "============================================"
echo "验证结果汇总"
echo "============================================"
TOTAL_ISSUES=0

if [ -n "$DOCS_PROCESSED" ]; then ((TOTAL_ISSUES++)); fi
if [ -n "$DOCS_SRT" ]; then ((TOTAL_ISSUES++)); fi
if [ -n "$SRC_PROCESSED" ]; then ((TOTAL_ISSUES++)); fi
if [ -n "$SRC_SRT" ]; then ((TOTAL_ISSUES++)); fi
if [ -n "$FRONTEND_PROCESSED" ]; then ((TOTAL_ISSUES++)); fi

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo "✅ 所有检查通过！未发现旧路径引用。"
    echo ""
    echo "📋 下一步建议:"
    echo "1. 备份现有数据: cp -r data/projects data/projects.backup.\$(date +%Y%m%d)"
    echo "2. 运行迁移脚本（测试）: python scripts/migrate_data_structure.py --all --dry-run"
    echo "3. 执行实际迁移: python scripts/migrate_data_structure.py --all"
    echo "4. 启动服务进行功能测试"
    exit 0
else
    echo "⚠️ 发现 $TOTAL_ISSUES 个问题，需要人工检查。"
    echo ""
    echo "📋 请检查上述标记的文件并确认是否需要修改。"
    exit 1
fi
