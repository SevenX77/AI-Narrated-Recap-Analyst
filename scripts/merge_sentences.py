#!/usr/bin/env python3
"""
合并sentences数组为原文字符串
将semantic_blocks中的sentences数组（每个sentence包含text字段）
合并成一个完整的原文字符串
"""

import json
import os
import shutil

def merge_sentences_in_block(block):
    """
    将semantic_block中的sentences数组合并为原文字符串
    在句子之间添加句号，提高LLM识别能力
    
    Args:
        block: semantic_block对象
        
    Returns:
        修改后的block
    """
    if 'sentences' in block and isinstance(block['sentences'], list):
        # 提取所有sentence的text
        text_parts = []
        for sentence in block['sentences']:
            if isinstance(sentence, dict) and 'text' in sentence:
                text = sentence['text'].strip()
                # 如果句子不为空，添加到列表
                if text:
                    text_parts.append(text)
            elif isinstance(sentence, str):
                text = sentence.strip()
                if text:
                    text_parts.append(text)
        
        # 用句号连接所有句子
        # 注意：只在句子之间添加句号，最后一句不加
        if text_parts:
            block['sentences'] = '。'.join(text_parts) + '。'
        else:
            block['sentences'] = ''
    
    return block

def process_events_file(file_path):
    """
    处理events文件，合并所有semantic_blocks中的sentences
    
    Args:
        file_path: events文件路径
    """
    print(f"\n处理文件: {file_path}")
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    # 统计
    total_blocks = 0
    modified_blocks = 0
    
    # 处理每个event
    for event in events:
        if 'semantic_blocks' in event:
            for block in event['semantic_blocks']:
                total_blocks += 1
                
                # 检查是否有sentences数组
                if 'sentences' in block and isinstance(block['sentences'], list):
                    original_count = len(block['sentences'])
                    merge_sentences_in_block(block)
                    modified_blocks += 1
    
    # 备份原文件
    backup_path = file_path.replace('.json', '_before_merge.json')
    shutil.copy2(file_path, backup_path)
    print(f"  ✓ 已备份原文件到: {backup_path}")
    
    # 保存修改后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ 处理完成:")
    print(f"    总Blocks数: {total_blocks}")
    print(f"    修改Blocks数: {modified_blocks}")
    
    return modified_blocks

def main():
    print("=" * 70)
    print("🔧 合并Sentences为原文字符串")
    print("=" * 70)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alignment_dir = os.path.join(base_dir, "data/projects/PROJ_002/alignment")
    
    # 需要处理的文件列表
    files_to_process = [
        # Script Events
        "ep01_script_events_v2_latest.json",
        "ep02_script_events_v2_latest.json",
        "ep03_script_events_v2_latest.json",
        "ep04_script_events_v2_latest.json",
        "ep05_script_events_v2_latest.json",
        # Novel Events
        "novel_events_v2_latest.json"
    ]
    
    total_modified = 0
    
    for filename in files_to_process:
        file_path = os.path.join(alignment_dir, filename)
        
        if os.path.exists(file_path):
            try:
                modified = process_events_file(file_path)
                total_modified += modified
            except Exception as e:
                print(f"  ✗ 错误: {e}")
        else:
            print(f"\n⏭  跳过 (文件不存在): {filename}")
    
    print("\n" + "=" * 70)
    print(f"✅ 完成！共修改 {total_modified} 个Semantic Blocks")
    print("=" * 70)
    
    # 显示示例
    print("\n📋 修改示例:")
    with open(os.path.join(alignment_dir, "ep01_script_events_v2_latest.json"), 'r') as f:
        events = json.load(f)
        if events and events[0]['semantic_blocks']:
            block = events[0]['semantic_blocks'][0]
            print(f"\nBlock: {block['theme']}")
            print(f"Sentences (修改后):")
            sentences_text = block.get('sentences', '')
            if isinstance(sentences_text, str):
                print(f"  类型: 字符串")
                print(f"  长度: {len(sentences_text)} 字符")
                print(f"  前100字符: {sentences_text[:100]}...")
            else:
                print(f"  类型: {type(sentences_text)}")

if __name__ == "__main__":
    main()
