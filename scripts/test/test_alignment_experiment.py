"""
实验：Novel-Script 句子级语义对齐
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.novel_segmenter import NovelSegmenter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def segment_novel_first_chapter():
    """分段小说第一章"""
    logger.info("=" * 80)
    logger.info("Step 1: 分段小说第一章")
    logger.info("=" * 80)
    
    # 读取小说
    novel_file = project_root / "data/projects/末哥超凡公路_output_test/raw/novel.txt"
    with open(novel_file, 'r', encoding='utf-8') as f:
        novel_content = f.read()
    
    # 提取第一章
    chapter_start = novel_content.find("=== 第1章")
    chapter_end = novel_content.find("=== 第2章")
    
    if chapter_start == -1:
        raise ValueError("找不到第一章")
    
    if chapter_end == -1:
        chapter_content = novel_content[chapter_start:]
    else:
        chapter_content = novel_content[chapter_start:chapter_end]
    
    # 去掉章节标题行
    lines = chapter_content.split('\n')
    chapter_content = '\n'.join(lines[1:])  # 跳过 "=== 第1章 ==="
    
    logger.info(f"第一章长度: {len(chapter_content)} 字符")
    
    # 分段
    segmenter = NovelSegmenter(provider="claude")
    result = segmenter.execute(
        chapter_content=chapter_content,
        chapter_number=1
    )
    
    logger.info(f"✅ 分段完成：{result.total_paragraphs} 个段落")
    logger.info(f"类型分布: {result.metadata['type_distribution']}")
    
    return result


def read_script():
    """读取Script数据"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: 读取Script数据")
    logger.info("=" * 80)
    
    script_file = project_root / "output/temp/script_segmenter_test_20260209_105546/ep01_segmentation.json"
    
    with open(script_file, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
    
    logger.info(f"✅ Script段落数: {script_data['total_segments']}")
    
    return script_data


def split_script_sentences(script_data):
    """拆分Script段落为句子"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 3: 拆分Script为句子")
    logger.info("=" * 80)
    
    import re
    
    all_sentences = []
    
    for segment in script_data['segments']:
        content = segment['content']
        
        # 按中文句子结束符拆分
        sentences = re.split(r'([。！？])', content)
        
        # 将标点符号合并回句子
        segment_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                if sentence.strip():
                    segment_sentences.append(sentence.strip())
        
        # 处理最后可能剩余的文本
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            segment_sentences.append(sentences[-1].strip())
        
        for sent in segment_sentences:
            all_sentences.append({
                "segment_index": segment['index'],
                "sentence": sent,
                "start_time": segment['start_time'],
                "end_time": segment['end_time']
            })
    
    logger.info(f"✅ 拆分完成：共 {len(all_sentences)} 个句子")
    
    return all_sentences


def align_sentences(novel_paragraphs, script_sentences):
    """对齐Novel段落和Script句子（实验版：只对齐前5个句子）"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 4: 语义对齐（实验：前5个句子）")
    logger.info("=" * 80)
    
    from src.core.llm_client_manager import get_llm_client, get_model_name
    
    client = get_llm_client("claude")
    model = get_model_name("claude")
    
    # 只对齐前5个句子作为实验
    test_sentences = script_sentences[:5]
    
    alignments = []
    
    for idx, sent_data in enumerate(test_sentences, 1):
        sentence = sent_data['sentence']
        
        logger.info(f"\n--- 对齐句子 {idx}/5 ---")
        logger.info(f"Script句子: {sentence[:50]}...")
        
        # 构建Prompt
        novel_text = "\n\n".join([
            f"【段落{p.index}（{p.type}类）】\n{p.content[:200]}..."
            for p in novel_paragraphs[:15]  # 只取前15段作为候选
        ])
        
        prompt = f"""你是专业的文本对齐分析师。

**任务**：找出Script句子在Novel中的对应内容。

**Script句子**：
{sentence}

**Novel候选段落**（前15段）：
{novel_text}

**要求**：
1. 找出与Script句子语义相关的Novel段落（可能多个）
2. 判断对应关系类型：
   - exact: 几乎一模一样
   - paraphrase: 改写
   - summarize: 总结压缩
   - expand: 扩写
   - none: 无对应（原创）

**输出格式**（JSON）：
```json
{{
  "matches": [
    {{
      "paragraph_index": 1,
      "paragraph_type": "B",
      "match_type": "paraphrase",
      "confidence": 0.95,
      "explanation": "简要说明对应关系"
    }}
  ]
}}
```

如果没有对应，返回空数组。
"""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是文本对齐分析专家，输出JSON格式结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 提取JSON
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(result_text)
            
            alignments.append({
                "sentence": sentence,
                "segment_index": sent_data['segment_index'],
                "time": f"{sent_data['start_time']}-{sent_data['end_time']}",
                "novel_matches": result.get('matches', [])
            })
            
            # 显示结果
            if result.get('matches'):
                for match in result['matches']:
                    logger.info(f"  → 匹配段落{match['paragraph_index']}（{match.get('paragraph_type', '?')}类）")
                    logger.info(f"     类型: {match['match_type']}, 置信度: {match.get('confidence', 0)}")
                    logger.info(f"     说明: {match.get('explanation', '')}")
            else:
                logger.info("  → 无匹配（可能是原创）")
        
        except Exception as e:
            logger.error(f"对齐失败: {e}")
            alignments.append({
                "sentence": sentence,
                "segment_index": sent_data['segment_index'],
                "error": str(e)
            })
    
    return alignments


def main():
    """主函数"""
    
    # Step 1: 分段Novel
    novel_result = segment_novel_first_chapter()
    
    # Step 2: 读取Script
    script_data = read_script()
    
    # Step 3: 拆分Script为句子
    script_sentences = split_script_sentences(script_data)
    
    # Step 4: 对齐
    alignments = align_sentences(novel_result.paragraphs, script_sentences)
    
    # Step 5: 保存结果
    logger.info("\n" + "=" * 80)
    logger.info("Step 5: 保存结果")
    logger.info("=" * 80)
    
    output_dir = project_root / "output/temp/alignment_experiment"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存对齐结果
    alignment_file = output_dir / "alignment_result.json"
    with open(alignment_file, 'w', encoding='utf-8') as f:
        json.dump(alignments, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 对齐结果已保存: {alignment_file}")
    
    # 生成可读报告
    report_file = output_dir / "alignment_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Novel-Script 对齐实验报告\n\n")
        f.write(f"**实验时间**: 2026-02-09\n")
        f.write(f"**Novel段落数**: {novel_result.total_paragraphs}\n")
        f.write(f"**Script句子数**: {len(script_sentences)} (测试前5个)\n\n")
        
        f.write("## 对齐结果\n\n")
        
        for i, alignment in enumerate(alignments, 1):
            f.write(f"### 句子 {i}\n\n")
            f.write(f"**Script**: {alignment['sentence']}\n\n")
            
            if 'error' in alignment:
                f.write(f"❌ 错误: {alignment['error']}\n\n")
            elif alignment.get('novel_matches'):
                f.write(f"**匹配结果**:\n\n")
                for match in alignment['novel_matches']:
                    f.write(f"- 段落{match['paragraph_index']}（{match.get('paragraph_type', '?')}类）\n")
                    f.write(f"  - 类型: `{match['match_type']}`\n")
                    f.write(f"  - 置信度: {match.get('confidence', 0)}\n")
                    f.write(f"  - 说明: {match.get('explanation', '')}\n")
                f.write("\n")
            else:
                f.write("❌ 无匹配（可能是原创内容）\n\n")
    
    logger.info(f"✅ 报告已保存: {report_file}")
    
    print(f"\n{'='*80}")
    print("✅ 实验完成！")
    print(f"{'='*80}")
    print(f"对齐结果: {alignment_file}")
    print(f"可读报告: {report_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
