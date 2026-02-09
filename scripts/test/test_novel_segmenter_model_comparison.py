#!/usr/bin/env python3
"""
NovelSegmenter 模型对比测试
测试三个模型的Two-Pass分段效果：
- Claude Sonnet 4.5
- DeepSeek V3.2 (deepseek-chat)
- DeepSeek V3.2 Thinking (deepseek-reasoner)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts
from src.tools.novel_importer import NovelImporter
from src.tools.novel_chapter_detector import NovelChapterDetector
from scripts.test.test_helpers import TestOutputManager
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_twopass_with_model(chapter_content, model_config, output_dir):
    """
    使用指定模型运行Two-Pass分段
    
    Args:
        chapter_content: 章节内容
        model_config: {"provider": "claude/deepseek", "model": "model_name", "name": "显示名称"}
        output_dir: 输出目录
    
    Returns:
        dict: {"pass1_count": int, "pass2_count": int, "pass1_time": float, "pass2_time": float, "success": bool}
    """
    provider = model_config["provider"]
    model_name = model_config["model"]
    display_name = model_config["name"]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"  测试模型: {display_name}")
    logger.info(f"  Provider: {provider}, Model: {model_name}")
    logger.info(f"{'='*60}")
    
    try:
        # 获取LLM客户端
        llm_client = get_llm_client(provider)
        
        # Pass 1: 初步分段
        logger.info("Pass 1: 初步分段...")
        prompt_pass1 = load_prompts("novel_chapter_segmentation_pass1")
        
        user_prompt_pass1 = prompt_pass1["user_template"].format(
            chapter_content=chapter_content,
            chapter_number=1
        )
        
        start_time = time.time()
        response_pass1 = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt_pass1["system"]},
                {"role": "user", "content": user_prompt_pass1}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass1_time = time.time() - start_time
        
        pass1_result = response_pass1.choices[0].message.content.strip()
        pass1_count = len(re.findall(r'^\- \*\*段落\d+', pass1_result, re.MULTILINE))
        
        logger.info(f"Pass 1完成: {pass1_count}个段落, 耗时: {pass1_time:.2f}秒")
        
        # 保存Pass 1结果
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "第1章分段结果_Pass1.md").write_text(pass1_result, encoding='utf-8')
        
        # Pass 2: 校验修正
        logger.info("Pass 2: 校验修正...")
        prompt_pass2 = load_prompts("novel_chapter_segmentation_pass2")
        
        user_prompt_pass2 = prompt_pass2["user_template"].format(
            chapter_content=chapter_content,
            pass1_result=pass1_result,
            chapter_number=1
        )
        
        start_time = time.time()
        response_pass2 = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": prompt_pass2["system"]},
                {"role": "user", "content": user_prompt_pass2}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass2_time = time.time() - start_time
        
        pass2_result = response_pass2.choices[0].message.content.strip()
        
        # 判断是否修正
        if "✅ 分段正确，无需修改" in pass2_result or "分段正确" in pass2_result:
            pass2_count = pass1_count
            modified = False
        else:
            pass2_count = len(re.findall(r'^\- \*\*段落\d+', pass2_result, re.MULTILINE))
            modified = True
        
        logger.info(f"Pass 2完成: {pass2_count}个段落, 耗时: {pass2_time:.2f}秒")
        if modified:
            logger.info(f"  修正: {abs(pass2_count - pass1_count)}个段落")
        else:
            logger.info(f"  无需修正")
        
        # 保存Pass 2结果
        (output_dir / "第1章分段结果_Pass2_修正.md").write_text(pass2_result, encoding='utf-8')
        
        return {
            "pass1_count": pass1_count,
            "pass2_count": pass2_count,
            "pass1_time": pass1_time,
            "pass2_time": pass2_time,
            "total_time": pass1_time + pass2_time,
            "modified": modified,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return {
            "pass1_count": 0,
            "pass2_count": 0,
            "pass1_time": 0,
            "pass2_time": 0,
            "total_time": 0,
            "modified": False,
            "success": False,
            "error": str(e)
        }


def main():
    """主测试流程"""
    
    logger.info("\n" + "="*60)
    logger.info("  NovelSegmenter 模型对比测试")
    logger.info("="*60 + "\n")
    
    # 1. 准备测试数据
    test_novel_path = Path("分析资料/有原小说/01_末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt")
    project_name = "末哥超凡公路_model_comparison_test"
    
    # 导入小说
    importer = NovelImporter()
    import_result = importer.execute(
        source_file=test_novel_path,
        project_name=project_name
    )
    logger.info(f"Test novel imported to: {import_result.saved_path}")
    
    # 获取第1章内容
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
    
    # 2. 定义测试模型
    models = [
        {
            "provider": "claude",
            "model": get_model_name("claude"),
            "name": "Claude Sonnet 4.5"
        },
        {
            "provider": "deepseek",
            "model": get_model_name("deepseek", model_type="v32"),
            "name": "DeepSeek V3.2 (deepseek-chat)"
        },
        {
            "provider": "deepseek",
            "model": get_model_name("deepseek", model_type="v32-thinking"),
            "name": "DeepSeek V3.2 Thinking (deepseek-reasoner)"
        }
    ]
    
    # 3. 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = Path("output/temp") / timestamp / "model_comparison"
    
    # 4. 运行所有模型测试
    results = {}
    
    for model_config in models:
        model_name = model_config["name"]
        output_dir = base_output_dir / model_name.replace(" ", "_").replace("(", "").replace(")", "")
        
        result = run_twopass_with_model(chapter_content, model_config, output_dir)
        results[model_name] = result
    
    # 5. 输出对比结果（终端输出，不创建文件）
    print("\n" + "="*80)
    print("  📊 模型对比测试结果")
    print("="*80 + "\n")
    
    print("┌────────────────────────────────┬─────────┬─────────┬───────────┬────────┐")
    print("│ 模型                           │ Pass 1  │ Pass 2  │ 总耗时    │ 状态   │")
    print("├────────────────────────────────┼─────────┼─────────┼───────────┼────────┤")
    
    for model_name, result in results.items():
        if result["success"]:
            status = "✅" if result["pass2_count"] == 11 else "⚠️"
            modified_mark = "*" if result["modified"] else ""
            print(f"│ {model_name:<30} │ {result['pass1_count']:>5}个 │ {result['pass2_count']:>5}个{modified_mark} │ {result['total_time']:>7.2f}秒 │ {status:^6} │")
        else:
            print(f"│ {model_name:<30} │   失败  │   失败  │     -     │   ❌   │")
    
    print("└────────────────────────────────┴─────────┴─────────┴───────────┴────────┘")
    
    print("\n说明：")
    print("  * 表示Pass 2有修正")
    print("  ✅ 表示Pass 2结果为11个段落（匹配标准）")
    print("  ⚠️ 表示Pass 2结果不是11个段落")
    
    # 输出失败原因
    for model_name, result in results.items():
        if not result["success"]:
            print(f"\n❌ {model_name} 失败原因:")
            print(f"  {result.get('error', 'Unknown error')}")
    
    print(f"\n📁 输出目录: {base_output_dir}")
    print(f"\n💡 查看详细结果:")
    for model_name, result in results.items():
        if result["success"]:
            model_dir = model_name.replace(" ", "_").replace("(", "").replace(")", "")
            print(f"  {model_name}:")
            print(f"    cat '{base_output_dir / model_dir / '第1章分段结果_Pass1.md'}'")
            print(f"    cat '{base_output_dir / model_dir / '第1章分段结果_Pass2_修正.md'}'")
    
    print("\n" + "="*80 + "\n")
    
    # 6. 清理测试数据
    import shutil
    test_project_dir = Path("data/projects") / project_name
    if test_project_dir.exists():
        shutil.rmtree(test_project_dir)
        logger.info(f"Test project cleaned up: {test_project_dir}")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
