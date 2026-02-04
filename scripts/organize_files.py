#!/usr/bin/env python3
"""
文件整理脚本
将alignment目录中的版本文件整理到history目录
"""

import os
import shutil
import glob
from pathlib import Path

def organize_alignment_files(base_dir: str):
    """
    整理alignment目录中的文件
    
    策略：
    1. 主目录只保留 *_latest.json 文件
    2. 所有版本文件（*_v*.json）移动到 history/ 目录
    3. _backup 目录保持不变
    """
    print("📦 开始整理文件...")
    print("=" * 60)
    
    alignment_dir = os.path.join(base_dir, "data/projects/PROJ_002/alignment")
    history_dir = os.path.join(alignment_dir, "history")
    
    # 1. 创建 history 目录
    os.makedirs(history_dir, exist_ok=True)
    print(f"✅ 创建目录: {history_dir}")
    
    # 2. 查找所有版本文件（_v* 格式）
    pattern = os.path.join(alignment_dir, "*_v*.json")
    version_files = glob.glob(pattern)
    
    moved_count = 0
    skipped_count = 0
    
    print(f"\n📋 找到 {len(version_files)} 个版本文件")
    print("\n正在移动文件...")
    
    for file_path in version_files:
        # 只处理主目录中的文件，不处理子目录
        if os.path.dirname(file_path) == alignment_dir:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(history_dir, filename)
            
            try:
                shutil.move(file_path, dest_path)
                moved_count += 1
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")
                skipped_count += 1
        else:
            skipped_count += 1
    
    # 3. 显示结果
    print("\n" + "=" * 60)
    print("📊 整理结果:")
    print(f"  ✅ 成功移动: {moved_count} 个文件")
    if skipped_count > 0:
        print(f"  ⏭  跳过: {skipped_count} 个文件")
    
    # 4. 显示最终结构
    print("\n" + "=" * 60)
    print("📁 整理后的目录结构:\n")
    
    print("主目录 (alignment/):")
    main_files = [f for f in os.listdir(alignment_dir) 
                  if f.endswith('.json') and os.path.isfile(os.path.join(alignment_dir, f))]
    for f in sorted(main_files):
        size = os.path.getsize(os.path.join(alignment_dir, f))
        print(f"  • {f} ({size//1024}KB)")
    
    print(f"\nhistory/ 目录:")
    history_files = [f for f in os.listdir(history_dir) 
                     if f.endswith('.json')]
    print(f"  共 {len(history_files)} 个版本文件")
    
    # 按类型分组统计
    file_types = {}
    for f in history_files:
        prefix = f.rsplit('_v', 1)[0]
        file_types[prefix] = file_types.get(prefix, 0) + 1
    
    for prefix, count in sorted(file_types.items()):
        print(f"  • {prefix}: {count} 个版本")
    
    print("\n✨ 整理完成！")

if __name__ == "__main__":
    import sys
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    try:
        organize_alignment_files(base_dir)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
