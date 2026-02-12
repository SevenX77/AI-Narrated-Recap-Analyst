"""
实验：Script句子 与 Novel Annotation（事件+设定）对齐
"""

import sys
import json
import re
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.llm_client_manager import get_llm_client, get_model_name
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_novel_annotation():
    """加载Novel的事件+设定标注数据"""
    logger.info("=" * 80)
    logger.info("Step 1: 加载Novel Annotation数据")
    logger.info("=" * 80)
    
    annotation_file = project_root / "output/temp/novel_annotation_test_20260209_195255/chpt_0001_annotation.json"
    
    with open(annotation_file, 'r', encoding='utf-8') as f:
        annotation = json.load(f)
    
    events = annotation['event_timeline']['events']
    settings = annotation['setting_library']['settings']
    
    logger.info(f"✅ 加载完成")
    logger.info(f"   事件数: {len(events)}")
    logger.info(f"   设定数: {len(settings)}")
    
    return events, settings


def load_script_sentences():
    """加载Script句子（前半部分，已标注）"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: 加载Script数据")
    logger.info("=" * 80)
    
    script_file = project_root / "data/projects/末哥超凡公路_test/script/ep01.md"
    
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取已标注的部分（前半部分，到分界线为止）
    parts = content.split("————————————————")
    annotated_part = parts[0]
    
    # 按时间段分割
    segments = re.split(r'## \[(.+?)\]', annotated_part)
    
    script_items = []
    
    for i in range(1, len(segments), 2):
        if i + 1 < len(segments):
            time_range = segments[i].strip()
            content_block = segments[i + 1].strip()
            
            # 按 [对应...] 标记分割成多个句子
            # 找到所有 [对应...] 标记的位置
            annotation_pattern = r'\[对应(.+?)\]'
            annotations = list(re.finditer(annotation_pattern, content_block))
            
            if not annotations:
                # 没有标注的块，跳过
                continue
            
            # 处理每个标注的句子
            for idx, match in enumerate(annotations):
                annotation = match.group(1)
                start_pos = match.end()
                
                # 确定句子的结束位置（下一个标注的开始，或内容块结束）
                if idx + 1 < len(annotations):
                    end_pos = annotations[idx + 1].start()
                    # 找到前一个句子的实际开始位置
                    if idx == 0:
                        sentence_start = 0
                    else:
                        sentence_start = annotations[idx - 1].end()
                    sentence = content_block[sentence_start:match.start()].strip()
                else:
                    # 最后一个标注
                    if idx == 0:
                        sentence_start = 0
                    else:
                        sentence_start = annotations[idx - 1].end()
                    sentence = content_block[sentence_start:match.start()].strip()
                
                if sentence:
                    script_items.append({
                        "time_range": time_range,
                        "content": sentence,
                        "manual_annotation": annotation
                    })
    
    logger.info(f"✅ 加载完成：{len(script_items)} 个Script片段（已标注）")
    
    return script_items


def align_with_llm(script_items, events, settings):
    """使用LLM对齐Script片段与Novel事件/设定"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 3: LLM对齐分析")
    logger.info("=" * 80)
    
    client = get_llm_client("claude")
    model = get_model_name("claude")
    
    # 准备Novel事件和设定的文本
    events_text = "\n\n".join([
        f"【事件{e['event_id']}】{e['event_summary']}\n"
        f"类型: {e['event_type']}类\n"
        f"包含段落: {e['paragraph_indices']}\n"
        f"时间: {e['time']}\n"
        f"地点: {e['location']}"
        for e in events
    ])
    
    settings_text = "\n\n".join([
        f"【设定{s['setting_id']}】{s['setting_title']}\n"
        f"内容: {s['setting_summary']}\n"
        f"段落: {s['paragraph_index']}"
        for s in settings
    ])
    
    alignments = []
    
    for idx, item in enumerate(script_items, 1):
        logger.info(f"\n--- 对齐片段 {idx}/{len(script_items)} ---")
        logger.info(f"Script: {item['content'][:80]}...")
        logger.info(f"手动标注: {item['manual_annotation']}")
        
        prompt = f"""你是专业的文本对齐分析师。

**任务**：找出Script片段对应的Novel事件和设定。

**Script片段**：
{item['content']}

**Novel事件列表**：
{events_text}

**Novel设定列表**：
{settings_text}

**要求**：
1. 找出与Script片段相关的Novel事件（可能多个）
2. 找出Script片段中提到的Novel设定（可能多个）
3. 判断对应关系：
   - exact: 几乎原文
   - paraphrase: 改写
   - summarize: 总结压缩
   - expand: 扩写
   - skip: 跳过了某些事件/设定

**输出格式**（JSON）：
```json
{{
  "matched_events": [
    {{
      "event_id": "000100001B",
      "match_type": "summarize",
      "confidence": 0.9,
      "explanation": "Script压缩了事件1的内容"
    }}
  ],
  "matched_settings": [
    {{
      "setting_id": "S00010001",
      "match_type": "paraphrase",
      "confidence": 0.95,
      "explanation": "Script改写了设定1"
    }}
  ],
  "skipped_content": [
    {{
      "type": "setting",
      "id": "S00010003",
      "reason": "Script完全跳过了序列超凡设定"
    }}
  ]
}}
```
"""
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是文本对齐分析专家，输出JSON格式结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 提取JSON
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = json.loads(result_text)
            
            alignments.append({
                "script_index": idx,
                "script_content": item['content'][:100] + "...",
                "time_range": item['time_range'],
                "manual_annotation": item['manual_annotation'],
                "llm_alignment": result
            })
            
            # 显示结果
            logger.info(f"  匹配事件: {[e['event_id'] for e in result.get('matched_events', [])]}")
            logger.info(f"  匹配设定: {[s['setting_id'] for s in result.get('matched_settings', [])]}")
            if result.get('skipped_content'):
                logger.info(f"  跳过内容: {len(result['skipped_content'])} 项")
        
        except Exception as e:
            logger.error(f"对齐失败: {e}")
            alignments.append({
                "script_index": idx,
                "error": str(e)
            })
    
    return alignments


def main():
    """主函数"""
    
    # Step 1: 加载Novel Annotation
    events, settings = load_novel_annotation()
    
    # Step 2: 加载Script（已标注的前半部分）
    script_items = load_script_sentences()
    
    # Step 3: LLM对齐
    alignments = align_with_llm(script_items, events, settings)
    
    # Step 4: 保存结果
    logger.info("\n" + "=" * 80)
    logger.info("Step 4: 保存结果")
    logger.info("=" * 80)
    
    output_dir = project_root / "output/temp/alignment_with_annotation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON
    json_file = output_dir / "alignment_result.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(alignments, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ JSON已保存: {json_file}")
    
    # 生成可读报告
    report_file = output_dir / "alignment_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Novel Annotation ↔ Script 对齐分析报告\n\n")
        f.write(f"**实验时间**: 2026-02-09\n")
        f.write(f"**Novel事件数**: {len(events)}\n")
        f.write(f"**Novel设定数**: {len(settings)}\n")
        f.write(f"**Script片段数**: {len(script_items)} (前半部分)\n\n")
        
        f.write("## 对齐结果\n\n")
        
        for alignment in alignments:
            if 'error' in alignment:
                continue
            
            f.write(f"### Script片段 {alignment['script_index']}\n\n")
            f.write(f"**时间**: `{alignment['time_range']}`\n\n")
            f.write(f"**内容**: {alignment['script_content']}\n\n")
            f.write(f"**手动标注**: `{alignment['manual_annotation']}`\n\n")
            
            llm = alignment['llm_alignment']
            
            if llm.get('matched_events'):
                f.write(f"**匹配事件**:\n\n")
                for event in llm['matched_events']:
                    f.write(f"- `{event['event_id']}` ({event['match_type']}, 置信度: {event.get('confidence', 0)})\n")
                    f.write(f"  - {event.get('explanation', '')}\n")
                f.write("\n")
            
            if llm.get('matched_settings'):
                f.write(f"**匹配设定**:\n\n")
                for setting in llm['matched_settings']:
                    f.write(f"- `{setting['setting_id']}` ({setting['match_type']}, 置信度: {setting.get('confidence', 0)})\n")
                    f.write(f"  - {setting.get('explanation', '')}\n")
                f.write("\n")
            
            if llm.get('skipped_content'):
                f.write(f"**跳过内容**:\n\n")
                for skip in llm['skipped_content']:
                    f.write(f"- {skip['type']}: `{skip['id']}` - {skip.get('reason', '')}\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        # 统计分析
        f.write("## 统计分析\n\n")
        
        all_matched_events = set()
        all_matched_settings = set()
        
        for alignment in alignments:
            if 'llm_alignment' in alignment:
                for e in alignment['llm_alignment'].get('matched_events', []):
                    all_matched_events.add(e['event_id'])
                for s in alignment['llm_alignment'].get('matched_settings', []):
                    all_matched_settings.add(s['setting_id'])
        
        f.write(f"### 事件覆盖率\n\n")
        f.write(f"- 匹配的事件: {len(all_matched_events)} / {len(events)}\n")
        f.write(f"- 匹配率: {len(all_matched_events) / len(events) * 100:.1f}%\n\n")
        
        f.write(f"### 设定覆盖率\n\n")
        f.write(f"- 匹配的设定: {len(all_matched_settings)} / {len(settings)}\n")
        f.write(f"- 匹配率: {len(all_matched_settings) / len(settings) * 100:.1f}%\n\n")
    
    logger.info(f"✅ 报告已保存: {report_file}")
    
    print(f"\n{'='*80}")
    print("✅ 对齐分析完成！")
    print(f"{'='*80}")
    print(f"JSON: {json_file}")
    print(f"报告: {report_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
