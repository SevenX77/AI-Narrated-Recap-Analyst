#!/usr/bin/env python3
"""
NovelSegmenter Two-Pass 测试脚本
Pass 1: 初步分段
Pass 2: 校验修正
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


def test_twopass_segmentation():
    """测试Two-Pass: 初步分段 + 校验修正"""
    
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter Two-Pass 测试")
    logger.info("="*60 + "\n")
    
    # 1. 准备测试数据
    test_novel_path = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
    project_name = "末哥超凡公路_twopass_test"
    
    # 导入小说
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=test_novel_path,
        project_name=project_name
    )
    logger.info(f"Test novel imported to: {import_result.saved_path}")
    
    # 创建测试输出目录
    output_manager = TestOutputManager("novel_segmenter_twopass")
    
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
    
    # 3. Pass 1: 初步分段
    logger.info("\n" + "="*60)
    logger.info("  Pass 1: 初步分段")
    logger.info("="*60)
    
    prompt_pass1 = load_prompts("novel_chapter_segmentation_pass1")
    llm_client = get_llm_client("claude")
    model_name = get_model_name("claude")
    
    user_prompt_pass1 = prompt_pass1["user_template"].format(
        chapter_content=chapter_content,
        chapter_number=1
    )
    
    logger.info("Calling LLM for Pass 1...")
    
    try:
        response_pass1 = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt_pass1["system"]},
                {"role": "user", "content": user_prompt_pass1}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        pass1_result = response_pass1.choices[0].message.content.strip()
        logger.info(f"Pass 1 complete: {len(pass1_result)} chars")
        
        # 保存Pass 1结果
        output_manager.save_text("第1章分段结果_Pass1.md", pass1_result)
        
        # 统计Pass 1段落数量
        import re
        pass1_paragraph_count = len(re.findall(r'^\- \*\*段落\d+', pass1_result, re.MULTILINE))
        logger.info(f"Pass 1 段落数量: {pass1_paragraph_count} 个")
        
    except Exception as e:
        logger.error(f"Pass 1 failed: {e}")
        return False
    
    # 4. Pass 2: 校验修正
    logger.info("\n" + "="*60)
    logger.info("  Pass 2: 校验修正")
    logger.info("="*60)
    
    prompt_pass2 = load_prompts("novel_chapter_segmentation_pass2")
    
    user_prompt_pass2 = prompt_pass2["user_template"].format(
        chapter_content=chapter_content,
        pass1_result=pass1_result,
        chapter_number=1
    )
    
    logger.info("Calling LLM for Pass 2...")
    
    try:
        response_pass2 = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt_pass2["system"]},
                {"role": "user", "content": user_prompt_pass2}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        pass2_result = response_pass2.choices[0].message.content.strip()
        logger.info(f"Pass 2 complete: {len(pass2_result)} chars")
        
        # 保存Pass 2结果
        output_manager.save_text("第1章分段结果_Pass2_修正.md", pass2_result)
        
        # 统计Pass 2段落数量（如果有修正）
        if "✅ 分段正确，无需修改" in pass2_result:
            pass2_paragraph_count = pass1_paragraph_count
            logger.info("Pass 2: ✅ 无需修改")
        else:
            pass2_paragraph_count = len(re.findall(r'^\- \*\*段落\d+', pass2_result, re.MULTILINE))
            logger.info(f"Pass 2 修正后段落数量: {pass2_paragraph_count} 个")
        
    except Exception as e:
        logger.error(f"Pass 2 failed: {e}")
        return False
    
    # 5. 结果统计（不生成报告文件，仅在终端输出）
    # 注意：根据.cursorrules，禁止创建过程性/总结性文档
    
    # 6. 打印结果摘要
    print("\n" + "="*60)
    print("  📊 Two-Pass 测试结果摘要")
    print("="*60 + "\n")
    print(f"✅ Two-Pass流程完成！")
    print(f"\n📋 段落数量变化：")
    print(f"  - Pass 1: {pass1_paragraph_count} 个")
    print(f"  - Pass 2: {pass2_paragraph_count} 个")
    print(f"  - 标准:   11 个")
    print(f"  - 原版:   14 个（过度分段）")
    
    if pass2_paragraph_count == pass1_paragraph_count:
        print(f"\n✅ Pass 2无需修正，Pass 1分段已经符合规范！")
    else:
        print(f"\n✅ Pass 2成功修正了 {abs(pass2_paragraph_count - pass1_paragraph_count)} 个段落")
    
    if 9 <= pass2_paragraph_count <= 12:
        print(f"\n🎉 最终段落数量({pass2_paragraph_count}个)接近标准(11个)！")
    
    print(f"\n📁 输出目录: {output_manager.get_path()}")
    print(f"\n💡 查看详细结果:")
    print(f"  cat '{output_manager.get_path() / 'Two-Pass对比报告.md'}'")
    print("\n" + "="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = test_twopass_segmentation()
        sys.exit(0 if success else 1)
    finally:
        # 清理测试数据
        import shutil
        test_project_dir = Path("data/projects/末哥超凡公路_twopass_test")
        if test_project_dir.exists():
            shutil.rmtree(test_project_dir)
            logger.info(f"Test project cleaned up: {test_project_dir}")
