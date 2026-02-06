"""
测试脚本：验证SRT字幕处理功能

测试场景：
1. 有小说参考的SRT处理（with_novel）
2. 无小说参考的SRT处理（without_novel）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.tools.srt_processor import SrtScriptProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_with_novel_reference():
    """测试：有小说参考的SRT处理"""
    print("\n" + "="*60)
    print("测试场景1：有小说参考的SRT处理")
    print("="*60)
    
    # 准备测试数据
    data_dir = project_root / "data" / "projects" / "with_novel" / "天命桃花"
    srt_file = data_dir / "raw" / "ep01.srt"
    novel_dir = data_dir / "novel"
    output_dir = data_dir / "script"
    
    # 检查文件是否存在
    if not srt_file.exists():
        print(f"❌ SRT文件不存在: {srt_file}")
        return False
    
    if not novel_dir.exists():
        print(f"❌ 小说目录不存在: {novel_dir}")
        return False
    
    # 读取小说参考
    novel_reference = ""
    try:
        intro_file = novel_dir / "chpt_0000.txt"
        if intro_file.exists():
            with open(intro_file, 'r', encoding='utf-8') as f:
                novel_reference = f.read()
        
        # 读取第一章
        chapter_files = sorted(novel_dir.glob("chpt_*.txt"))
        for chapter_file in chapter_files:
            if chapter_file.name != "chpt_0000.txt":
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    novel_reference += "\n\n" + content[:2000]
                break
        
        print(f"✅ 读取小说参考: {len(novel_reference)} 字符")
    except Exception as e:
        print(f"❌ 读取小说参考失败: {e}")
        return False
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 执行处理
    try:
        processor = SrtScriptProcessor(use_llm=True)
        report = processor.execute(
            srt_file_path=srt_file,
            output_dir=output_dir,
            novel_reference=novel_reference,
            episode_name="ep01"
        )
        
        print("\n📊 处理结果：")
        print(f"  输出文件: {report['output_file']}")
        print(f"  处理模式: {report['processing_mode']}")
        print(f"  原始字符数: {report['stats']['original_chars']}")
        print(f"  处理后字符数: {report['stats']['processed_chars']}")
        print(f"  段落数: {report['stats']['paragraphs']}")
        print(f"  SRT条目数: {report['stats']['srt_entries']}")
        print(f"  处理时间: {report['stats']['processing_time_seconds']}s")
        
        # 检查输出文件
        output_file = Path(report['output_file'])
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📄 输出文本预览（前500字）：")
                print("-" * 60)
                print(content[:500])
                print("-" * 60)
            print(f"✅ 测试通过！输出文件已生成")
            return True
        else:
            print(f"❌ 输出文件未生成")
            return False
    
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_novel_reference():
    """测试：无小说参考的SRT处理"""
    print("\n" + "="*60)
    print("测试场景2：无小说参考的SRT处理")
    print("="*60)
    
    # 准备测试数据
    data_dir = project_root / "data" / "projects" / "without_novel" / "超前崛起"
    srt_file = data_dir / "raw" / "ep01.srt"
    output_dir = data_dir / "script"
    
    # 检查文件是否存在
    if not srt_file.exists():
        print(f"❌ SRT文件不存在: {srt_file}")
        return False
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 执行处理
    try:
        processor = SrtScriptProcessor(use_llm=True)
        report = processor.execute(
            srt_file_path=srt_file,
            output_dir=output_dir,
            novel_reference=None,  # 无小说参考
            episode_name="ep01"
        )
        
        print("\n📊 处理结果：")
        print(f"  输出文件: {report['output_file']}")
        print(f"  处理模式: {report['processing_mode']}")
        print(f"  原始字符数: {report['stats']['original_chars']}")
        print(f"  处理后字符数: {report['stats']['processed_chars']}")
        print(f"  段落数: {report['stats']['paragraphs']}")
        print(f"  SRT条目数: {report['stats']['srt_entries']}")
        print(f"  处理时间: {report['stats']['processing_time_seconds']}s")
        
        # 显示实体标准化信息
        if report.get('entity_standardization'):
            print(f"\n🔍 实体标准化：")
            import json
            print(json.dumps(report['entity_standardization'], ensure_ascii=False, indent=2)[:500])
        
        # 检查输出文件
        output_file = Path(report['output_file'])
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📄 输出文本预览（前500字）：")
                print("-" * 60)
                print(content[:500])
                print("-" * 60)
            print(f"✅ 测试通过！输出文件已生成")
            return True
        else:
            print(f"❌ 输出文件未生成")
            return False
    
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("🧪 SRT字幕处理功能测试")
    print("="*70)
    
    results = []
    
    # 测试1：有小说参考
    result1 = test_with_novel_reference()
    results.append(("有小说参考模式", result1))
    
    # 测试2：无小说参考
    result2 = test_without_novel_reference()
    results.append(("无小说参考模式", result2))
    
    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查日志")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
