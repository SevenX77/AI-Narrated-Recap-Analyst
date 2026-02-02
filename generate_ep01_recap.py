import os
import json
from dotenv import load_dotenv
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.agents.deepseek_writer import DeepSeekWriter
from src.utils.text_processing import split_text_into_chunks

load_dotenv()

def read_file_content(filepath, limit_chars=None):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if limit_chars:
        return content[:limit_chars]
    return content

def generate_ep01_recap():
    print("正在初始化 Agents...")
    client = get_llm_client()
    analyst = DeepSeekAnalyst(client)
    writer = DeepSeekWriter(client)
    
    novel_path = "分析资料/末哥超凡公路/novel/序列公路求生：我在末日升级物资.txt"
    
    print(f"读取小说: {novel_path}")
    # 读取前 3 章内容 (约 10000 字) 作为 EP01 的素材
    # 根据之前的分析，EP01 覆盖了序章到第 3 章的内容
    novel_text = read_file_content(novel_path, limit_chars=12000) 
    
    print("正在分析小说内容 (Analyst Agent)...")
    # 我们将前 12000 字作为一个整体 chunk 传给 Analyst (或者分块处理，这里简化为单块)
    # 注意：实际生产中可能需要分块摘要，这里为了测试直接传
    # 如果内容太长，LLM 可能会截断，但 12k chars 对于 DeepSeek 应该还好 (约 6k tokens)
    analysis = analyst.analyze(novel_text, previous_context="这是小说的开篇。")
    
    print("\n【分析结果】:")
    print(f"梗概: {analysis.summary}")
    print(f"倒叙候选: {analysis.flashback_candidate}")
    print(f"主角: {analysis.protagonist_name}")
    
    print("\n正在生成解说稿 (Writer Agent)...")
    script = writer.generate_script(analysis, style="first_person")
    
    print("\n" + "="*50)
    print(f"生成标题: {script.title}")
    print(f"叙事策略: {script.narrative_strategy}")
    print("="*50)
    
    for i, seg in enumerate(script.segments):
        print(f"[{i+1}] ({seg.duration}s) {seg.text}")
        print(f"    画面: {seg.visual_cue}")
        print("-" * 30)
        
    # Save result
    output_file = "ep01_generated_script.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(script.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"\n解说稿已保存至 {output_file}")

if __name__ == "__main__":
    generate_ep01_recap()
