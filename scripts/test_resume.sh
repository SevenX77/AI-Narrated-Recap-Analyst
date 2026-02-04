#!/bin/bash
# 断点续传功能测试脚本

echo "🧪 断点续传功能测试"
echo "===================="
echo ""

# 第一次运行
echo "第1步：首次运行（10秒后自动中断）"
echo "-----------------------------------"
timeout 10 python3 main.py ingest --id PROJ_002 2>&1 | head -30
echo ""
echo "✅ 第一次运行已中断"
echo ""

# 检查生成的文件
echo "第2步：检查已生成的文件"
echo "-----------------------------------"
ls -lh data/projects/PROJ_002/alignment/*_latest.json 2>/dev/null || echo "暂无文件生成"
echo ""

# 第二次运行（续传）
echo "第3步：重新运行（应该自动续传）"
echo "-----------------------------------"
echo "请观察是否出现 '♻️ 发现已存在的结果，跳过处理'"
echo ""
python3 main.py ingest --id PROJ_002

