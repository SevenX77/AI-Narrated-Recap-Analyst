#!/usr/bin/env python3
"""
批量保存女频新书榜数据的脚本
"""

import json
from pathlib import Path

# 待保存的榜单数据队列
rankings_to_save = []

def save_ranking(data):
    """保存单个榜单数据"""
    ranking_name = data['ranking_name']
    output_file = Path(f"data/fanqie/rankings/{ranking_name}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存: {output_file.name}")
    return output_file

def get_progress():
    """统计进度"""
    ranking_dir = Path("data/fanqie/rankings")
    female_new_files = [f for f in ranking_dir.glob("女频新书榜-*.json") if "_test" not in f.name]
    
    total = len(female_new_files)
    percentage = (total / 18) * 100
    remaining = 18 - total
    
    print(f"\n📊 女频新书榜进度: {total}/18 ({percentage:.1f}%)")
    print(f"⚡ 剩余 {remaining} 个榜单")
    
    return total, remaining

if __name__ == "__main__":
    print("批量保存女频新书榜数据...")
    get_progress()
