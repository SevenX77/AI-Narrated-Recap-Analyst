"""
测试脚本：SrtTextExtractor - SRT文本提取工具

测试目标：
1. 从SRT条目中提取文本
2. LLM智能添加标点符号
3. 实体标准化（有/无小说参考两种模式）
4. 错字缺字修复
5. 返回正确的SrtTextExtractionResult
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_srt_text_extractor():
    """测试SrtTextExtractor工具"""
    
    # ========== 测试配置 ==========
    test_srt_file = project_root / "archive/v2_data_20260208/projects/with_novel/末哥超凡公路/raw/ep01.srt"
    test_project_name = "末哥超凡公路_test"
    test_episode = "ep01"
    
    # 可选：小说参考文本（测试 with_novel 模式）
    test_novel_file = project_root / "data/projects/末哥超凡公路_test/raw/novel.txt"
    novel_reference = None
    if test_novel_file.exists():
        with open(test_novel_file, 'r', encoding='utf-8') as f:
            # 只读前5000字作为参考
            novel_reference = f.read(5000)
        logger.info(f"Loaded novel reference: {len(novel_reference)} chars")
    else:
        logger.info("No novel reference found, will test without_novel mode")
    
    if not test_srt_file.exists():
        logger.error(f"Test SRT file not found: {test_srt_file}")
        return
    
    logger.info("=" * 80)
    logger.info("测试 SrtTextExtractor - SRT文本提取工具")
    logger.info("=" * 80)
    
    # ========== Step 1: 先使用 SrtImporter 导入SRT ==========
    logger.info(f"\n{'=' * 80}")
    logger.info("Step 1: 导入SRT文件（使用 SrtImporter）")
    
    importer = SrtImporter()
    import_result = importer.execute(
        source_file=test_srt_file,
        project_name=test_project_name,
        episode_name=test_episode,
        save_to_disk=False,  # 不保存，仅内存测试
        include_entries=True
    )
    
    logger.info(f"✅ 导入成功：{import_result.entry_count} 条SRT条目")
    
    # ========== Step 2: 使用 SrtTextExtractor 提取和处理文本 ==========
    logger.info(f"\n{'=' * 80}")
    logger.info("Step 2: 提取和处理文本（使用 SrtTextExtractor）")
    
    extractor = SrtTextExtractor(use_llm=True)
    logger.info(f"Tool: {extractor.name}")
    logger.info(f"Description: {extractor.description}")
    
    try:
        result = extractor.execute(
            srt_entries=import_result.entries,
            project_name=test_project_name,
            episode_name=test_episode,
            novel_reference=novel_reference
        )
        
        logger.info(f"\n{'=' * 80}")
        logger.info("✅ 提取成功！")
        logger.info(f"{'=' * 80}")
        
        # ========== 输出结果 ==========
        logger.info("\n📊 提取结果：")
        logger.info(f"  - 处理模式: {result.processing_mode}")
        logger.info(f"  - 原始字符数: {result.original_chars}")
        logger.info(f"  - 处理后字符数: {result.processed_chars}")
        logger.info(f"  - 字符变化: {result.processed_chars - result.original_chars:+d}")
        logger.info(f"  - 处理耗时: {result.processing_time:.2f} 秒")
        
        # ========== 修正统计 ==========
        logger.info(f"\n🔧 修正统计：")
        for correction_type, count in result.corrections.items():
            logger.info(f"  - {correction_type}: {count}")
        
        # ========== 实体标准化信息 ==========
        if result.entity_standardization:
            logger.info(f"\n🏷️  实体标准化信息：")
            if isinstance(result.entity_standardization, dict):
                for category, entities in result.entity_standardization.items():
                    if category == "source":
                        logger.info(f"  - 来源: {entities}")
                    elif isinstance(entities, dict):
                        logger.info(f"  - {category}: {len(entities)} 个实体")
                        # 显示前3个实体示例
                        for i, (name, info) in enumerate(list(entities.items())[:3], 1):
                            if isinstance(info, list):
                                logger.info(f"    {i}. {name}")
                            elif isinstance(info, dict):
                                logger.info(f"    {i}. {name}: {info.get('standard_form', name)}")
        
        # ========== 文本示例 ==========
        logger.info(f"\n📝 原始文本示例（前200字）：")
        logger.info(f"  {result.raw_text[:200]}...")
        
        logger.info(f"\n✨ 处理后文本示例（前300字）：")
        logger.info(f"  {result.processed_text[:300]}...")
        
        # ========== 保存处理后文本（可选）==========
        output_dir = project_root / f"output/temp/{test_project_name}/srt_text_extractor"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{test_episode}_processed.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.processed_text)
        logger.info(f"\n💾 处理后文本已保存到: {output_file}")
        
        # 保存原始文本对比
        raw_file = output_dir / f"{test_episode}_raw.txt"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(result.raw_text)
        logger.info(f"💾 原始文本已保存到: {raw_file}")
        
        logger.info(f"\n{'=' * 80}")
        logger.info("🎉 测试完成！SrtTextExtractor 工作正常")
        logger.info(f"{'=' * 80}\n")
        
        return result
    
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    test_srt_text_extractor()
