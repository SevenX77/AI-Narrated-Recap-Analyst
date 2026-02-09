#!/usr/bin/env python3
"""
NovelSegmenter Pass 1 测试脚本
测试极简的纯分段逻辑
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts
from src.tools.novel_importer import NovelImporter
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from scripts.test.test_helpers import TestOutputManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pass1_segmentation():
    """测试Pass 1: 纯分段"""
    
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter Pass 1 测试")
    logger.info("="*60 + "\n")
    
    # 1. 准备测试数据
    test_novel_path = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
    project_name = "末哥超凡公路_pass1_test"
    
    # 导入小说
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=test_novel_path,
        project_name=project_name
    )
    logger.info(f"Test novel imported to: {import_result.saved_path}")
    
    # 创建测试输出目录
    output_manager = TestOutputManager("novel_segmenter_pass1")
    
    # 2. 获取第1章内容
    novel_file = Path(import_result.saved_path)
    chapter_detector = NovelChapterDetector()
    chapters = chapter_detector.execute(novel_file=novel_file)
    
    target_chapter_info = None
    for chapter_info in chapters:
        if chapter_info.number == 1:
            target_chapter_info = chapter_info
            break
    
    if not target_chapter_info:
        logger.error("Chapter 1 not found")
        return False
    
    full_text = novel_file.read_text(encoding='utf-8')
    chapter_content = full_text[target_chapter_info.start_char : target_chapter_info.end_char]
    
    # 移除章节标题行
    lines = chapter_content.split('\n')
    if lines and lines[0].strip().startswith(f"=== 第1章"):
        chapter_content = '\n'.join(lines[1:]).strip()
    
    logger.info(f"Chapter content: {len(chapter_content)} chars")
    
    # 3. 加载Pass 1 Prompt
    prompt_config = load_prompts("novel_chapter_segmentation_pass1")
    
    # 4. 获取小说元数据
    metadata_extractor = NovelMetadataExtractor(use_llm=False)
    novel_metadata = metadata_extractor.execute(novel_file=novel_file)
    
    # 5. 调用LLM进行Pass 1分段
    llm_client = get_llm_client("claude")
    model_name = get_model_name("claude")
    
    user_prompt = prompt_config["user_template"].format(
        chapter_content=chapter_content,
        chapter_number=1
    )
    
    logger.info("Calling LLM for Pass 1 segmentation...")
    logger.info(f"Model: {model_name}, Temperature: 0.3, Max Tokens: 4000")
    
    try:
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        segmentation_result = response.choices[0].message.content.strip()
        logger.info(f"LLM response: {len(segmentation_result)} chars")
        
        # 6. 保存结果
        output_manager.save_text("第1章分段结果_Pass1.md", segmentation_result)
        
        # 7. 统计段落数量
        import re
        paragraph_count = len(re.findall(r'^\- \*\*段落\d+', segmentation_result, re.MULTILINE))
        logger.info(f"\n📊 段落数量: {paragraph_count} 个")
        logger.info(f"📁 输出文件: {output_manager.get_path() / '第1章分段结果_Pass1.md'}")
        
        # 8. 对比分析
        print("\n" + "="*60)
        print("  📊 测试结果摘要")
        print("="*60 + "\n")
        print(f"✅ Pass 1 分段成功！")
        print(f"📋 段落数量: {paragraph_count} 个")
        print(f"📁 输出文件: {output_manager.get_path() / '第1章分段结果_Pass1.md'}")
        print(f"\n💡 标准分析: 11个段落")
        print(f"💡 之前的结果: 14个段落（过度分段）")
        print(f"💡 Pass 1结果: {paragraph_count}个段落")
        
        if paragraph_count <= 11:
            print(f"\n🎉 太好了！Pass 1的段落数量接近或优于标准分析！")
        elif paragraph_count <= 13:
            print(f"\n✅ 不错！Pass 1的段落数量比之前有所改善。")
        else:
            print(f"\n⚠️  Pass 1的段落数量仍然偏多，需要进一步优化。")
        
        print("\n" + "="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return False
    finally:
        # 清理测试数据
        import shutil
        test_project_dir = Path("data/projects") / project_name
        if test_project_dir.exists():
            shutil.rmtree(test_project_dir)
            logger.info(f"Test project directory cleaned up: {test_project_dir}")


if __name__ == "__main__":
    success = test_pass1_segmentation()
    sys.exit(0 if success else 1)
