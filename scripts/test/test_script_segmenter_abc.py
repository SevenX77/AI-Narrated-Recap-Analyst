"""
测试 ScriptSegmenter v2 - ABC分类

验证双Pass分段 + ABC分类功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.script_segmenter import ScriptSegmenter

def test_script_segmenter_abc():
    """测试ScriptSegmenter v2 - ABC分类"""
    print("=" * 60)
    print("测试 ScriptSegmenter v2 - ABC分类")
    print("=" * 60)
    
    # 配置
    project_name = "天命桃花_test"
    episode_name = "ep01"
    srt_path = "分析资料/有原小说/02_天命桃花/srt/ep01.srt"
    
    # Step 1: 导入SRT
    print("\n[Step 1] 导入SRT...")
    srt_importer = SrtImporter()
    srt_result = srt_importer.execute(
        source_file=srt_path,
        project_name=project_name,
        episode_name=episode_name
    )
    srt_entries = srt_result.entries if srt_result.entries else []
    print(f"✅ 导入完成: {len(srt_entries)} 条字幕")
    
    # Step 2: 提取文本
    print("\n[Step 2] 提取脚本文本...")
    text_extractor = SrtTextExtractor(provider="deepseek")
    text_result = text_extractor.execute(
        srt_entries=srt_entries,
        novel_reference=None,
        project_name=project_name,
        episode_name=episode_name
    )
    print(f"✅ 提取完成: {len(text_result.processed_text)} 字符")
    
    # Step 3: 脚本分段 + ABC分类
    print("\n[Step 3] 脚本分段 + ABC分类...")
    segmenter = ScriptSegmenter(provider="deepseek")
    
    segmentation = segmenter.execute(
        processed_text=text_result.processed_text,
        srt_entries=srt_entries,
        project_name=project_name,
        episode_name=episode_name
    )
    
    print(f"\n{'='*60}")
    print(f"分段结果")
    print(f"{'='*60}")
    print(f"总段落数: {segmentation.total_segments}")
    print(f"平均句数: {segmentation.avg_sentence_count:.1f}")
    print(f"处理时长: {segmentation.processing_time:.2f}秒")
    
    # 统计各分类数量
    category_counts = {"A": 0, "B": 0, "C": 0, None: 0}
    for seg in segmentation.segments:
        category_counts[seg.category] = category_counts.get(seg.category, 0) + 1
    
    print(f"\nABC分类统计:")
    print(f"  - A类（Setting）: {category_counts.get('A', 0)} 段")
    print(f"  - B类（Event）: {category_counts.get('B', 0)} 段")
    print(f"  - C类（System）: {category_counts.get('C', 0)} 段")
    
    print(f"\n前5个段落:")
    for seg in segmentation.segments[:5]:
        category_name = {
            "A": "Setting",
            "B": "Event",
            "C": "System"
        }.get(seg.category, "Unknown")
        
        print(f"\n  段落{seg.index} [{seg.category}-{category_name}]")
        print(f"  时间: {seg.start_time} - {seg.end_time}")
        print(f"  内容: {seg.content[:60]}...")
    
    print(f"\n输出文件: {segmentation.output_file}")
    
    return segmentation


if __name__ == "__main__":
    try:
        result = test_script_segmenter_abc()
        print(f"\n{'='*60}")
        print("✅ ScriptSegmenter v2 测试完成")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
