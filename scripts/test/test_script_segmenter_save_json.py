"""
测试脚本：ScriptSegmenter - 保存 JSON 输出
运行 ScriptSegmenter 并保存 JSON 结果
"""

import sys
import json
from pathlib import Path
from datetime import datetime

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


def main():
    """运行测试并保存 JSON"""
    
    # 测试配置
    test_srt_file = project_root / "archive/v2_data_20260208/projects/with_novel/末哥超凡公路/raw/ep01.srt"
    test_project_name = "末哥超凡公路_test"
    test_episode = "ep01"
    
    # 输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / f"output/temp/script_segmenter_test_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Step 1: 导入SRT
    logger.info("Step 1: Importing SRT")
    importer = SrtImporter()
    import_result = importer.execute(
        source_file=test_srt_file,
        project_name=test_project_name,
        episode_name=test_episode,
        save_to_disk=False,
        include_entries=True
    )
    
    # Step 2: 提取文本
    logger.info("Step 2: Extracting text")
    extractor = SrtTextExtractor(use_llm=True)
    extraction_result = extractor.execute(
        srt_entries=import_result.entries,
        project_name=test_project_name,
        episode_name=test_episode,
        novel_reference=None
    )
    
    # Step 3: 分段
    logger.info("Step 3: Segmentation")
    segmenter = ScriptSegmenter(provider="deepseek")
    result = segmenter.execute(
        processed_text=extraction_result.processed_text,
        srt_entries=import_result.entries,
        project_name=test_project_name,
        episode_name=test_episode
    )
    
    # 保存 JSON
    json_output = output_dir / f"{test_episode}_segmentation.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ JSON saved: {json_output}")
    
    # 生成 Markdown 摘要
    summary_output = output_dir / f"{test_episode}_summary.md"
    with open(summary_output, 'w', encoding='utf-8') as f:
        f.write(f"# ScriptSegmenter 测试报告\n\n")
        f.write(f"**集数**: {test_episode}\n")
        f.write(f"**测试时间**: {timestamp}\n")
        f.write(f"**分段模式**: {result.segmentation_mode}\n\n")
        
        f.write(f"## 统计信息\n\n")
        f.write(f"- **总段落数**: {result.total_segments}\n")
        f.write(f"- **平均每段句子数**: {result.avg_sentence_count:.1f}\n")
        f.write(f"- **处理耗时**: {result.processing_time:.2f} 秒\n\n")
        
        f.write(f"## ❌ 无 A/B/C 分类\n\n")
        f.write(f"✅ **确认：当前版本不包含 A/B/C 类型分类**\n\n")
        
        f.write(f"## 段落列表\n\n")
        for seg in result.segments:
            f.write(f"### 段落 {seg.index}\n\n")
            f.write(f"- **时间**: `{seg.start_time}` - `{seg.end_time}`\n")
            f.write(f"- **句子数**: {seg.sentence_count}\n")
            f.write(f"- **字符数**: {seg.char_count}\n")
            f.write(f"- **内容**:\n\n")
            f.write(f"```\n{seg.content[:200]}{'...' if len(seg.content) > 200 else ''}\n```\n\n")
    
    logger.info(f"✅ Summary saved: {summary_output}")
    
    # 打印统计
    print(f"\n{'='*80}")
    print(f"✅ 测试完成！")
    print(f"{'='*80}")
    print(f"总段落数: {result.total_segments}")
    print(f"平均句子数: {result.avg_sentence_count:.1f}")
    print(f"处理耗时: {result.processing_time:.2f}s")
    print(f"\n输出文件:")
    print(f"  - JSON: {json_output}")
    print(f"  - Summary: {summary_output}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
