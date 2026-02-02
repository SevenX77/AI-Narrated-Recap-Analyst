import os
import sys
from dotenv import load_dotenv
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.utils.text_processing import split_text_into_chunks

load_dotenv()

def read_file_content(filepath, limit_chars=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if limit_chars:
        return content[:limit_chars]
    return content

def test_alignment_capability():
    print("正在初始化 Agent...")
    client = get_llm_client()
    agent = DeepSeekAnalyst(client)
    
    novel_path = "分析资料/末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    srt_path = "分析资料/末哥超凡公路/srt/ep01.srt"
    
    print(f"读取测试文件: {novel_path} & {srt_path}")
    # Read a small portion for testing
    novel_text = read_file_content(novel_path, limit_chars=2000) 
    srt_text = read_file_content(srt_path, limit_chars=1000) # First minute or so
    
    print("\n--- 测试 1: 事件提取 (Extract Events) ---")
    
    print("正在提取小说事件...")
    novel_events = agent.extract_events(novel_text, "第1章片段")
    print(f"提取到 {len(novel_events)} 个小说事件:")
    for e in novel_events[:3]:
        print(f"  - [{e.event_type}] {e.subject} {e.action} {e.outcome}")
        
    print("\n正在提取解说事件...")
    srt_events = agent.extract_events(srt_text, "解说开头")
    print(f"提取到 {len(srt_events)} 个解说事件:")
    for e in srt_events[:3]:
        print(f"  - [{e.event_type}] {e.subject} {e.action} {e.outcome}")
        
    print("\n--- 测试 2: 逻辑对齐 (Align) ---")
    
    novel_data = [{"id": "第1章片段", "events": novel_events}]
    srt_data = [{"time": "00:00:00", "events": srt_events}]
    
    print("正在执行对齐...")
    alignment_results = agent.align_script_with_novel(novel_data, srt_data)
    
    print(f"\n对齐结果 ({len(alignment_results)} 项):")
    for item in alignment_results:
        print(f"[{item.script_time}] {item.script_event}")
        print(f"  -> 对应: {item.matched_novel_chapter} | {item.matched_novel_event}")
        print(f"  -> 理由: {item.match_reason} (置信度: {item.confidence})")
        print("-" * 40)

if __name__ == "__main__":
    test_alignment_capability()
