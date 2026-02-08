"""
测试重构后的处理脚本 - 只处理第1章
"""

import sys
import json
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.novel_chapter_processor import MetadataExtractor, NovelChapterProcessor
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.core.artifact_manager import ArtifactManager
from src.core.config import LLMConfig


def main():
    """主流程 - 只测试第1章"""
    print("="*80)
    print("测试重构后的处理脚本（第1章）")
    print("="*80)
    
    # 配置路径
    project_root = Path(__file__).parent.parent
    project_dir = project_root / "data/projects/with_novel/末哥超凡公路"
    raw_novel = project_dir / "raw/novel.txt"
    novel_dir = project_dir / "novel"
    analysis_dir = novel_dir / "functional_analysis"
    
    # 确保目录存在
    novel_dir.mkdir(exist_ok=True)
    analysis_dir.mkdir(exist_ok=True)
    
    # 读取原始小说
    print(f"\n📖 读取小说: {raw_novel}")
    with open(raw_novel, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    # Step 1: 使用 MetadataExtractor 提取简介
    print("\n" + "="*80)
    print("Step 1: 提取简介（使用 MetadataExtractor）")
    print("="*80)
    
    extractor = MetadataExtractor(use_llm=True)
    metadata = extractor.execute(novel_text)
    
    print(f"✅ 简介提取完成:")
    print(f"   作者: {metadata['novel']['author']}")
    print(f"   标签: {', '.join(metadata['novel']['tags'])}")
    print(f"   简介长度: {len(metadata['novel']['introduction'])} 字符")
    print(f"   简介预览: {metadata['novel']['introduction'][:100]}...")
    
    # 检查是否包含"又有书名"
    if "又有书名" in metadata['novel']['introduction']:
        print("   ❌ 简介仍包含'又有书名'")
    else:
        print("   ✅ 简介已清理")
    
    # Step 2: 读取已存在的第1章文件
    print("\n" + "="*80)
    print("Step 2: 读取第1章")
    print("="*80)
    
    chapter_file = novel_dir / "chpt_0001.md"
    if not chapter_file.exists():
        print(f"❌ 第1章文件不存在: {chapter_file}")
        return
    
    with open(chapter_file, 'r', encoding='utf-8') as f:
        chapter_content = f.read()
    
    print(f"✅ 第1章已读取: {len(chapter_content)} 字符")
    
    # Step 3: 使用 NovelChapterAnalyzer（内置V3->R1 fallback）
    print("\n" + "="*80)
    print("Step 3: 功能分析（使用 NovelChapterAnalyzer + 内置Fallback机制）")
    print("="*80)
    
    llm_config = LLMConfig()
    print(f"   主模型: {llm_config.primary_model}")
    print(f"   备用模型: {llm_config.fallback_model}")
    print(f"   Fallback启用: {llm_config.enable_fallback}")
    
    analyzer = NovelChapterAnalyzer()
    
    try:
        # 提取章节号和标题
        import re
        title_match = re.search(r'# 第(\d+)章 - (.+)', chapter_content)
        chapter_number = int(title_match.group(1)) if title_match else 1
        chapter_title = title_match.group(2).strip() if title_match else "未知标题"
        
        print(f"   章节: 第{chapter_number}章 - {chapter_title}")
        
        analysis = analyzer.execute(
            chapter_content=chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_title
        )
        
        # 转换为字典（analysis 是 Pydantic 对象）
        # 使用 mode='json' 自动处理 datetime 等特殊类型
        analysis_dict = analysis.model_dump(mode='json')
        
        print(f"✅ 第1章分析完成:")
        print(f"   功能段数: {len(analysis_dict['segments'])}")
        print(f"   第1段字数: {len(analysis_dict['segments'][0]['content'])} 字符")
        print(f"   第1段功能: {analysis_dict['segments'][0]['tags']['narrative_function']}")
        print(f"   第1段优先级: {analysis_dict['segments'][0]['tags']['priority']}")
        
        # Step 4: 使用 ArtifactManager 保存
        print("\n" + "="*80)
        print("Step 4: 保存结果（使用 ArtifactManager）")
        print("="*80)
        
        artifact_type = "chpt_0001_functional_analysis"
        versioned_path = ArtifactManager.save_artifact(
            content=analysis_dict,
            artifact_type=artifact_type,
            project_id="末哥超凡公路",
            base_dir=str(analysis_dir),
            extension="json"
        )
        
        print(f"✅ 已保存版本化文件: {Path(versioned_path).name}")
        
        # 验证 _latest.json 和 history/ 结构
        latest_file = analysis_dir / f"{artifact_type}_latest.json"
        history_dir = analysis_dir / "history"
        
        print("\n📂 验证版本管理:")
        print(f"   _latest.json 存在: {latest_file.exists()}")
        print(f"   history/ 目录存在: {history_dir.exists()}")
        
        if history_dir.exists():
            history_files = list(history_dir.glob(f"{artifact_type}_v*.json"))
            print(f"   history/ 中的版本数: {len(history_files)}")
            for hf in history_files:
                print(f"      - {hf.name}")
        
        # 检查主目录中是否还有旧版本文件
        root_versions = list(analysis_dir.glob(f"{artifact_type}_v*.json"))
        if root_versions:
            print(f"   ⚠️  主目录中仍有版本文件: {len(root_versions)} 个")
            for rv in root_versions:
                print(f"      - {rv.name}")
        else:
            print(f"   ✅ 主目录只有 _latest.json")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)


if __name__ == "__main__":
    main()
