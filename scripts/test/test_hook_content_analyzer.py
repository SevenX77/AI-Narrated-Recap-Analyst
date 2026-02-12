"""
测试 HookContentAnalyzer 工具

验证Hook内容来源分析功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.hook_detector import HookDetector
from src.tools.hook_content_analyzer import HookContentAnalyzer
from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.script_segmenter import ScriptSegmenter
from src.tools.novel_metadata_extractor import NovelMetadataExtractor

def test_hook_content_analyzer():
    """测试HookContentAnalyzer"""
    print("=" * 60)
    print("测试 HookContentAnalyzer - Hook内容来源分析")
    print("=" * 60)
    
    # 配置
    project_name = "天命桃花_test"
    episode_name = "ep01"
    srt_path = "分析资料/有原小说/02_天命桃花/srt/ep01.srt"
    novel_path = "分析资料/有原小说/02_天命桃花/novel/读心术，小公主给满朝文武发对像.txt"
    
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
    
    # Step 3: 脚本分段
    print("\n[Step 3] 脚本分段...")
    segmenter = ScriptSegmenter(provider="deepseek")
    segmentation = segmenter.execute(
        processed_text=text_result.processed_text,
        srt_entries=srt_entries,
        project_name=project_name,
        episode_name=episode_name
    )
    print(f"✅ 分段完成: {segmentation.total_segments} 个段落")
    
    # Step 4: 提取Novel简介和元数据
    print("\n[Step 4] 提取Novel元数据...")
    metadata_extractor = NovelMetadataExtractor(provider="deepseek")
    novel_metadata = metadata_extractor.execute(novel_file=novel_path)
    print(f"✅ 元数据提取完成")
    print(f"   - 标题: {novel_metadata.title}")
    print(f"   - 简介: {len(novel_metadata.introduction)} 字符")
    
    # Step 5: 读取第一章预览
    print("\n[Step 5] 读取第一章预览...")
    with open(novel_path, 'r', encoding='utf-8') as f:
        content = f.read()
        chapter1_start = content.find("第一章")
        if chapter1_start == -1:
            chapter1_start = content.find("第1章")
        
        if chapter1_start != -1:
            chapter1_preview = content[chapter1_start:chapter1_start + 800]
        else:
            intro_end = len(novel_metadata.introduction)
            chapter1_preview = content[intro_end:intro_end + 800]
    
    # Step 6: Hook检测
    print("\n[Step 6] Hook边界检测...")
    detector = HookDetector(provider="deepseek")
    hook_result = detector.execute(
        script_segmentation=segmentation,
        novel_intro=novel_metadata.introduction,
        novel_chapter1_preview=chapter1_preview,
        check_count=10
    )
    
    print(f"✅ Hook检测完成: {'有Hook' if hook_result.has_hook else '无Hook'}")
    
    if not hook_result.has_hook:
        print("\n⚠️  未检测到Hook，跳过内容分析")
        return None
    
    # Step 7: Hook内容分析
    print(f"\n[Step 7] Hook内容来源分析...")
    
    # 提取Hook段落
    hook_segments = [
        segmentation.segments[i] 
        for i in hook_result.hook_segment_indices
    ]
    
    analyzer = HookContentAnalyzer(provider="deepseek")
    analysis_result = analyzer.execute(
        hook_segments=hook_segments,
        novel_intro=novel_metadata.introduction,
        novel_metadata=novel_metadata
    )
    
    print(f"\n{'='*60}")
    print(f"Hook内容分析结果")
    print(f"{'='*60}")
    print(f"来源类型: {analysis_result.source_type}")
    print(f"相似度: {analysis_result.similarity_score:.2%}")
    print(f"对齐策略: {analysis_result.alignment_strategy}")
    
    print(f"\nHook分层内容:")
    print(f"  - 世界观: {len(analysis_result.hook_layers.world_building)} 个")
    for item in analysis_result.hook_layers.world_building[:3]:
        print(f"    • {item}")
    
    print(f"  - 系统机制: {len(analysis_result.hook_layers.game_mechanics)} 个")
    for item in analysis_result.hook_layers.game_mechanics[:3]:
        print(f"    • {item}")
    
    print(f"  - 道具装备: {len(analysis_result.hook_layers.items_equipment)} 个")
    for item in analysis_result.hook_layers.items_equipment[:3]:
        print(f"    • {item}")
    
    print(f"  - 情节事件: {len(analysis_result.hook_layers.plot_events)} 个")
    for item in analysis_result.hook_layers.plot_events[:3]:
        print(f"    • {item}")
    
    print(f"\n简介分层内容:")
    print(f"  - 世界观: {len(analysis_result.intro_layers.world_building)} 个")
    print(f"  - 系统机制: {len(analysis_result.intro_layers.game_mechanics)} 个")
    print(f"  - 道具装备: {len(analysis_result.intro_layers.items_equipment)} 个")
    print(f"  - 情节事件: {len(analysis_result.intro_layers.plot_events)} 个")
    
    print(f"\n各层相似度:")
    for layer, score in analysis_result.layer_similarity.items():
        print(f"  - {layer}: {score:.2%}")
    
    print(f"\n处理信息:")
    print(f"  - 模型: {analysis_result.metadata.get('model_used')}")
    print(f"  - 耗时: {analysis_result.metadata.get('processing_time')}秒")
    
    return analysis_result


if __name__ == "__main__":
    try:
        result = test_hook_content_analyzer()
        print(f"\n{'='*60}")
        print("✅ Hook内容分析测试完成")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
