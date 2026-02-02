import os
import json
import glob
import re
from typing import List, Dict
from dotenv import load_dotenv
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client, NarrativeEvent

load_dotenv()

def read_file_content(filepath, limit_chars=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if limit_chars:
        return content[:limit_chars]
    return content

def parse_novel_chapters(text: str) -> List[Dict]:
    """
    Split novel into chapters.
    """
    pattern = r"(第[0-9零一二三四五六七八九十百]+章\s+[^\n]+)"
    parts = re.split(pattern, text)
    
    chapters = []
    
    # Handle preamble
    if parts and not re.match(pattern, parts[0]):
        chapters.append({"id": "序章/前言", "content": parts[0].strip()})
        parts = parts[1:]
        
    for i in range(0, len(parts), 2):
        if i+1 < len(parts):
            title = parts[i].strip()
            content = parts[i+1].strip()
            chapters.append({"id": title, "content": content})
            
    return chapters

def parse_srt_groups(text: str, group_size=10) -> List[Dict]:
    """
    Parse SRT and group lines.
    """
    blocks = text.strip().split('\n\n')
    grouped_chunks = []
    current_group_text = []
    start_time = ""
    
    for i, block in enumerate(blocks):
        lines = block.split('\n')
        if len(lines) >= 3:
            if not start_time:
                start_time = lines[1].split(' --> ')[0]
            
            text_lines = " ".join(lines[2:])
            current_group_text.append(text_lines)
            
            if (i + 1) % group_size == 0:
                grouped_chunks.append({
                    "time": start_time,
                    "content": " ".join(current_group_text)
                })
                current_group_text = []
                start_time = ""
                
    if current_group_text:
        grouped_chunks.append({
            "time": start_time,
            "content": " ".join(current_group_text)
        })
        
    return grouped_chunks

def batch_verify_alignment():
    print("正在初始化 Agent...")
    client = get_llm_client()
    agent = DeepSeekAnalyst(client)
    
    novel_path = "分析资料/末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    srt_dir = "分析资料/末哥超凡公路/srt"
    
    print(f"读取小说: {novel_path}")
    # Read first 50k chars (approx 15-20 chapters) to cover first few episodes
    novel_text = read_file_content(novel_path, limit_chars=60000) 
    chapters = parse_novel_chapters(novel_text)
    print(f"解析到 {len(chapters)} 个章节")
    
    # Pre-extract events for all chapters (Cache this in real app)
    novel_cache_file = "novel_events_cache.json"
    novel_events_db = []
    
    if os.path.exists(novel_cache_file):
        print(f"发现小说事件缓存，正在加载: {novel_cache_file}")
        with open(novel_cache_file, "r", encoding="utf-8") as f:
            novel_events_db = json.load(f)
            # Convert dicts back to NarrativeEvent objects if needed, 
            # but our agent.align_script_with_novel handles dicts gracefully now.
    else:
        print("\n正在提取小说章节事件 (SVO)...")
        for i, chap in enumerate(chapters):
            print(f"  [{i+1}/{len(chapters)}] 处理 {chap['id']} ...")
            events = agent.extract_events(chap['content'], chap['id'])
            # Convert NarrativeEvent objects to dicts for JSON serialization
            events_data = [e.model_dump() for e in events]
            novel_events_db.append({"id": chap['id'], "events": events_data})
        
        # Save cache
        with open(novel_cache_file, "w", encoding="utf-8") as f:
            json.dump(novel_events_db, f, ensure_ascii=False, indent=2)
        print(f"小说事件已缓存至: {novel_cache_file}")
        
    # Process each SRT file
    srt_files = sorted(glob.glob(os.path.join(srt_dir, "*.srt")))
    
    # Load existing report if available to resume
    full_report = {}
    report_file = "batch_alignment_report.json"
    if os.path.exists(report_file):
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                full_report = json.load(f)
            print(f"已加载现有进度: {list(full_report.keys())}")
        except:
            pass
    
    for srt_path in srt_files:
        filename = os.path.basename(srt_path)
        if filename in full_report:
            print(f"\n跳过已处理文件: {filename}")
            continue

        print(f"\n正在处理解说文件: {filename}")
        
        srt_text = read_file_content(srt_path)
        srt_chunks = parse_srt_groups(srt_text, group_size=12) # ~40s chunks
        
        print(f"  - 分割为 {len(srt_chunks)} 个切片，开始提取事件...")
        srt_events_data = []
        for chunk in srt_chunks:
            events = agent.extract_events(chunk['content'], f"{filename} {chunk['time']}")
            srt_events_data.append({"time": chunk['time'], "events": events})
            
        print("  - 执行逻辑对齐...")
        alignment_results = agent.align_script_with_novel(novel_events_db, srt_events_data)
        
        # Calculate coverage stats
        matched_count = sum(1 for item in alignment_results if item.matched_novel_chapter != "None")
        coverage = matched_count / len(alignment_results) if alignment_results else 0
        
        # Extract chapter range
        matched_chapters = [item.matched_novel_chapter for item in alignment_results if item.matched_novel_chapter != "None"]
        chapter_range = "无匹配"
        if matched_chapters:
            # Simple unique list preserving order
            unique_chaps = []
            for c in matched_chapters:
                if c not in unique_chaps:
                    unique_chaps.append(c)
            chapter_range = f"{unique_chaps[0]} -> {unique_chaps[-1]}"

        print(f"  - 匹配覆盖率: {coverage:.1%}")
        print(f"  - 对应章节流: {chapter_range}")
        
        full_report[filename] = {
            "coverage": coverage,
            "chapter_range": chapter_range,
            "details": [item.model_dump() for item in alignment_results]
        }
        
        # Save progress after each file
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)
        print(f"  - 进度已保存 ({filename})")
        
    print("\n" + "="*60)
    print("批量验证完成！报告已保存至 batch_alignment_report.json")
    print("="*60)

if __name__ == "__main__":
    batch_verify_alignment()
