"""
测试NovelSystemAnalyzer工具

测试目标：
1. 评估前50章分析的时间和token成本
2. 验证系统元素识别的准确性
3. 检查类别归类是否合理
"""

import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_system_analyzer import NovelSystemAnalyzer
from src.core.schemas_novel import SystemCatalog

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主测试流程"""
    logger.info("=== NovelSystemAnalyzer 测试开始 ===")
    
    # 1. 配置路径
    novel_path = project_root / "data/projects/末哥超凡公路_output_test/raw/novel.txt"
    novel_name = "超凡公路"
    
    if not novel_path.exists():
        logger.error(f"Novel file not found: {novel_path}")
        return
    
    # 2. 初始化工具
    logger.info("Initializing NovelSystemAnalyzer...")
    analyzer = NovelSystemAnalyzer(provider="claude")
    
    # 3. 成本估算
    logger.info("\n=== 成本估算 ===")
    cost_estimate = analyzer.estimate_cost(max_chapters=50, avg_chapter_length=3000)
    logger.info(f"分析章节数: {cost_estimate['max_chapters']}")
    logger.info(f"每章预览长度: {cost_estimate['preview_per_chapter']} 字符")
    logger.info(f"总输入字符数: {cost_estimate['total_input_chars']}")
    logger.info(f"估算输入tokens: {cost_estimate['estimated_input_tokens']}")
    logger.info(f"估算输出tokens: {cost_estimate['estimated_output_tokens']}")
    logger.info(f"估算成本: ${cost_estimate['estimated_cost_usd']} USD")
    logger.info(f"估算时间: {cost_estimate['estimated_time']}")
    
    # 显示成本估算后继续
    print("\n" + "="*60)
    print("成本估算已完成，继续执行分析...")
    print("="*60)
    
    # 4. 执行系统分析
    logger.info("\n=== 开始系统分析 ===")
    logger.info(f"Novel: {novel_path}")
    
    system_catalog = analyzer.execute(
        novel_path=str(novel_path),
        novel_name=novel_name,
        max_chapters=50,
        use_chapter_detector=True
    )
    
    # 5. 打印结果摘要
    logger.info("\n=== 系统分析结果 ===")
    logger.info(f"小说类型: {system_catalog.novel_type}")
    logger.info(f"类别总数: {len(system_catalog.categories)}")
    logger.info(f"元素总数: {system_catalog.metadata.get('total_elements', 0)}")
    logger.info(f"处理时间: {system_catalog.metadata.get('processing_time', 0)}s")
    
    logger.info("\n类别列表:")
    for cat in system_catalog.categories:
        logger.info(f"  [{cat.category_id}] {cat.category_name} ({cat.importance})")
        logger.info(f"    追踪策略: {cat.tracking_strategy}")
        logger.info(f"    元素数量: {len(cat.elements)}")
        logger.info(f"    元素示例: {', '.join(cat.elements[:5])}")
        if len(cat.elements) > 5:
            logger.info(f"    ... 还有 {len(cat.elements) - 5} 个元素")
        logger.info("")
    
    # 6. 保存结果
    output_dir = project_root / "output/temp/novel_system_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / "system_catalog.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(system_catalog.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"\nSaved system catalog: {json_path}")
    
    # 7. 生成Markdown报告
    md_path = output_dir / "system_catalog.md"
    md_content = generate_catalog_markdown(system_catalog)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    logger.info(f"Saved markdown report: {md_path}")
    
    logger.info("\n=== 测试完成 ===")


def generate_catalog_markdown(catalog: SystemCatalog) -> str:
    """生成系统目录Markdown报告"""
    lines = [
        f"# {catalog.novel_name} - 系统元素目录",
        "",
        f"**小说类型**: {catalog.novel_type}",
        f"**分析章节**: {catalog.analyzed_chapters}",
        f"**类别总数**: {len(catalog.categories)}",
        f"**元素总数**: {catalog.metadata.get('total_elements', 0)}",
        "",
        "---",
        ""
    ]
    
    for cat in catalog.categories:
        lines.append(f"## {cat.category_id} - {cat.category_name}")
        lines.append("")
        lines.append(f"**重要程度**: {cat.importance}")
        lines.append(f"**追踪策略**: {cat.tracking_strategy}")
        lines.append(f"**类别描述**: {cat.category_desc}")
        lines.append("")
        lines.append("**元素列表**:")
        for element in cat.elements:
            lines.append(f"- {element}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


if __name__ == "__main__":
    main()
