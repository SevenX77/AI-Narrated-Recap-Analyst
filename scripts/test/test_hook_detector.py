"""
测试 HookDetector 工具

验证Hook边界检测功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.hook_detector import HookDetector
from src.tools.srt_importer import SrtImporter
from src.tools.srt_text_extractor import SrtTextExtractor
from src.tools.script_segmenter import ScriptSegmenter
from src.tools.novel_metadata_extractor import NovelMetadataExtractor

def test_hook_detector():
    """测试HookDetector"""
    print("=" * 60)
    print("测试 HookDetector - Hook边界检测")
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
    
    # Step 4: 提取Novel简介
    print("\n[Step 4] 提取Novel简介...")
    metadata_extractor = NovelMetadataExtractor(provider="deepseek")
    novel_metadata = metadata_extractor.execute(novel_file=novel_path)
    print(f"✅ 简介提取完成: {len(novel_metadata.introduction)} 字符")
    
    # Step 5: 读取第一章预览
    print("\n[Step 5] 读取第一章预览...")
    with open(novel_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 简单提取：找到第一章，取前800字
        chapter1_start = content.find("第一章")
        if chapter1_start == -1:
            chapter1_start = content.find("第1章")
        
        if chapter1_start != -1:
            chapter1_preview = content[chapter1_start:chapter1_start + 800]
        else:
            # 如果找不到章节标题，取简介后的800字
            intro_end = len(novel_metadata.introduction)
            chapter1_preview = content[intro_end:intro_end + 800]
    
    print(f"✅ 第一章预览: {len(chapter1_preview)} 字符")
    
    # Step 6: Hook检测
    print("\n[Step 6] Hook边界检测...")
    detector = HookDetector(provider="deepseek")
    
    result = detector.execute(
        script_segmentation=segmentation,
        novel_intro=novel_metadata.introduction,
        novel_chapter1_preview=chapter1_preview,
        check_count=10
    )
    
    print(f"\n{'='*60}")
    print(f"Hook检测结果")
    print(f"{'='*60}")
    print(f"是否存在Hook: {'✅ 是' if result.has_hook else '❌ 否'}")
    print(f"置信度: {result.confidence:.2%}")
    
    if result.has_hook:
        print(f"\nHook信息:")
        print(f"  - 结束时间: {result.hook_end_time}")
        print(f"  - Hook时长: {result.metadata.get('hook_duration', 0):.1f}秒")
        print(f"  - Hook段落: {len(result.hook_segment_indices)} 段")
        print(f"  - Body起点: {result.body_start_time}")
        print(f"  - Body段落: {len(result.body_segment_indices)} 段")
    
    print(f"\n推理:")
    print(f"  {result.reasoning}")
    
    print(f"\n处理信息:")
    print(f"  - 模型: {result.metadata.get('model_used')}")
    print(f"  - 耗时: {result.metadata.get('processing_time')}秒")
    
    return result


if __name__ == "__main__":
    try:
        result = test_hook_detector()
        print(f"\n{'='*60}")
        print("✅ HookDetector 测试完成")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
