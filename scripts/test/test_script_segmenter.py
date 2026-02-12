"""
测试脚本：ScriptSegmenter - 脚本分段工具

测试目标：
1. 接收连续的脚本文本
2. 使用LLM按照叙事逻辑进行语义分段
3. 为每个段落匹配SRT时间戳
4. 生成Markdown格式输出
5. 返回正确的ScriptSegmentationResult

注意：此测试会串联使用所有三个Script处理工具
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.script_segmenter import ScriptSegmenter
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_script_segmenter():
    """测试ScriptSegmenter工具（完整流程）"""
    
    # ========== 测试配置 ==========
    test_srt_file = project_root / "archive/v2_data_20260208/projects/with_novel/末哥超凡公路/raw/ep01.srt"
    test_project_name = "末哥超凡公路_test"
    test_episode = "ep01"
    
    if not test_srt_file.exists():
        logger.error(f"Test SRT file not found: {test_srt_file}")
        return
    
    logger.info("=" * 80)
    logger.info("测试 ScriptSegmenter - 脚本分段工具（完整流程）")
    logger.info("=" * 80)
    
    # ========== Step 1: SrtImporter - 导入SRT ==========
    logger.info(f"\n{'=' * 80}")
    logger.info("Step 1: 导入SRT文件（SrtImporter）")
    
    importer = SrtImporter()
    import_result = importer.execute(
        source_file=test_srt_file,
        project_name=test_project_name,
        episode_name=test_episode,
        save_to_disk=False,
        include_entries=True
    )
    
    logger.info(f"✅ 导入成功：{import_result.entry_count} 条SRT条目")
    
    # ========== Step 2: SrtTextExtractor - 提取和处理文本 ==========
    logger.info(f"\n{'=' * 80}")
    logger.info("Step 2: 提取和处理文本（SrtTextExtractor）")
    
    extractor = SrtTextExtractor(use_llm=True)
    extraction_result = extractor.execute(
        srt_entries=import_result.entries,
        project_name=test_project_name,
        episode_name=test_episode,
        novel_reference=None  # 测试 without_novel 模式
    )
    
    logger.info(f"✅ 提取成功：{len(extraction_result.processed_text)} 字符")
    logger.info(f"   处理模式: {extraction_result.processing_mode}")
    
    # ========== Step 3: ScriptSegmenter - 语义分段 ==========
    logger.info(f"\n{'=' * 80}")
    logger.info("Step 3: 语义分段（ScriptSegmenter）")
    
    try:
        segmenter = ScriptSegmenter(provider="deepseek")
        logger.info(f"Tool: {segmenter.name}")
        logger.info(f"Description: {segmenter.description}")
        
        result = segmenter.execute(
            processed_text=extraction_result.processed_text,
            srt_entries=import_result.entries,
            project_name=test_project_name,
            episode_name=test_episode
        )
        
        logger.info(f"\n{'=' * 80}")
        logger.info("✅ 分段成功！")
        logger.info(f"{'=' * 80}")
        
        # ========== 输出结果 ==========
        logger.info("\n📊 分段结果：")
        logger.info(f"  - 总段落数: {result.total_segments}")
        logger.info(f"  - 平均每段句子数: {result.avg_sentence_count:.1f}")
        logger.info(f"  - 分段模式: {result.segmentation_mode}")
        logger.info(f"  - 输出文件: {result.output_file}")
        logger.info(f"  - 处理耗时: {result.processing_time:.2f} 秒")
        
        # ========== 段落示例 ==========
        logger.info(f"\n📝 段落示例（前5段）：")
        for i, seg in enumerate(result.segments[:5], 1):
            logger.info(f"\n  段落 {i}:")
            logger.info(f"    时间: {seg.start_time} - {seg.end_time}")
            logger.info(f"    句子数: {seg.sentence_count}")
            logger.info(f"    字符数: {seg.char_count}")
            logger.info(f"    内容: {seg.content[:80]}{'...' if len(seg.content) > 80 else ''}")
        
        # ========== 统计信息 ==========
        logger.info(f"\n{'=' * 80}")
        logger.info("📈 统计信息：")
        logger.info(f"  - 总段落数: {result.total_segments}")
        logger.info(f"  - 总字符数: {sum(seg.char_count for seg in result.segments)}")
        logger.info(f"  - 总句子数: {sum(seg.sentence_count for seg in result.segments)}")
        logger.info(f"  - 平均每段句子数: {result.avg_sentence_count:.1f}")
        logger.info(f"  - 平均每段字符数: {sum(seg.char_count for seg in result.segments) / result.total_segments:.1f}")
        
        # ========== 验证输出文件 ==========
        if result.output_file:
            output_path = Path(result.output_file)
            if output_path.exists():
                logger.info(f"\n✅ Markdown文件已生成: {output_path}")
                logger.info(f"   文件大小: {output_path.stat().st_size} bytes")
                
                # 显示前500字符
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                logger.info(f"\n📄 Markdown内容预览（前500字）：")
                logger.info("-" * 80)
                logger.info(content)
                logger.info("-" * 80)
            else:
                logger.warning(f"\n⚠️  输出文件不存在: {output_path}")
        else:
            logger.info("\n📌 注意：此版本不生成 Markdown 文件，只返回 JSON 数据")
        
        logger.info(f"\n{'=' * 80}")
        logger.info("🎉 测试完成！ScriptSegmenter 工作正常")
        logger.info(f"{'=' * 80}\n")
        
        return result
    
    except ValueError as e:
        logger.error(f"\n❌ 初始化失败: {e}")
        logger.info("提示: ScriptSegmenter 需要LLM支持，请确保API配置正确")
        raise
    
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    test_script_segmenter()
