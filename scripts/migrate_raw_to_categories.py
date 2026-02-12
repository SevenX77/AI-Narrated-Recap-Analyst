"""
将现有项目的 raw 目录下的文件迁移到分类子目录（novel / srt）

使用方法：
    python3 scripts/migrate_raw_to_categories.py [--dry-run] [--project-id PROJECT_ID]

参数：
    --dry-run: 仅预览，不实际移动文件
    --project-id: 指定项目 ID，不指定则处理所有项目
"""
import sys
import os
import shutil
from pathlib import Path
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import config


def migrate_project_raw(project_id: str, dry_run: bool = False) -> dict:
    """迁移单个项目的 raw 文件到分类子目录"""
    project_dir = os.path.join(config.data_dir, "projects", project_id)
    raw_base = os.path.join(project_dir, "raw")
    
    if not os.path.exists(raw_base):
        return {"error": f"项目 {project_id} 的 raw 目录不存在"}
    
    result = {
        "project_id": project_id,
        "novel_files": [],
        "srt_files": [],
        "skipped": [],
        "errors": []
    }
    
    # 创建子目录
    raw_novel = os.path.join(raw_base, "novel")
    raw_srt = os.path.join(raw_base, "srt")
    
    if not dry_run:
        os.makedirs(raw_novel, exist_ok=True)
        os.makedirs(raw_srt, exist_ok=True)
    else:
        print(f"  [DRY-RUN] 将创建: {raw_novel}")
        print(f"  [DRY-RUN] 将创建: {raw_srt}")
    
    # 遍历 raw 目录下的文件（不包括子目录）
    for item in os.listdir(raw_base):
        item_path = os.path.join(raw_base, item)
        
        # 跳过目录（包括已存在的 novel / srt）
        if os.path.isdir(item_path):
            result["skipped"].append(f"{item} (目录)")
            continue
        
        ext = Path(item).suffix.lower()
        target_dir = None
        category = None
        
        # 根据扩展名决定目标目录
        if ext in ['.txt', '.md', '.pdf']:
            target_dir = raw_novel
            category = "novel"
        elif ext == '.srt':
            target_dir = raw_srt
            category = "srt"
        else:
            result["skipped"].append(f"{item} (未知类型: {ext})")
            continue
        
        target_path = os.path.join(target_dir, item)
        
        try:
            if dry_run:
                print(f"  [DRY-RUN] 将移动: {item} → {category}/")
                result[f"{category}_files"].append(item)
            else:
                shutil.move(item_path, target_path)
                print(f"  ✓ 已移动: {item} → {category}/")
                result[f"{category}_files"].append(item)
        except Exception as e:
            error_msg = f"{item}: {str(e)}"
            result["errors"].append(error_msg)
            print(f"  ✗ 错误: {error_msg}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="迁移 raw 文件到分类子目录")
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际移动')
    parser.add_argument('--project-id', type=str, help='指定项目 ID')
    args = parser.parse_args()
    
    print("=" * 70)
    print("raw 文件分类目录迁移工具")
    if args.dry_run:
        print("【预览模式】不会实际移动文件")
    print("=" * 70)
    
    projects_dir = os.path.join(config.data_dir, "projects")
    
    if not os.path.exists(projects_dir):
        print(f"错误：项目目录不存在: {projects_dir}")
        return
    
    # 确定要处理的项目列表
    if args.project_id:
        project_ids = [args.project_id]
    else:
        project_ids = [
            d for d in os.listdir(projects_dir)
            if os.path.isdir(os.path.join(projects_dir, d))
        ]
    
    if not project_ids:
        print("未找到任何项目")
        return
    
    print(f"\n发现 {len(project_ids)} 个项目: {', '.join(project_ids)}\n")
    
    all_results = []
    
    for project_id in project_ids:
        print(f"处理项目: {project_id}")
        result = migrate_project_raw(project_id, dry_run=args.dry_run)
        all_results.append(result)
        
        if "error" in result:
            print(f"  ✗ {result['error']}")
        else:
            print(f"  Novel 文件: {len(result['novel_files'])}")
            print(f"  SRT 文件: {len(result['srt_files'])}")
            print(f"  跳过: {len(result['skipped'])}")
            if result['errors']:
                print(f"  错误: {len(result['errors'])}")
        print()
    
    # 汇总统计
    print("=" * 70)
    print("迁移汇总")
    print("=" * 70)
    
    total_novel = sum(len(r.get('novel_files', [])) for r in all_results)
    total_srt = sum(len(r.get('srt_files', [])) for r in all_results)
    total_skipped = sum(len(r.get('skipped', [])) for r in all_results)
    total_errors = sum(len(r.get('errors', [])) for r in all_results)
    
    print(f"总计迁移:")
    print(f"  - Novel 文件: {total_novel}")
    print(f"  - SRT 文件: {total_srt}")
    print(f"  - 跳过: {total_skipped}")
    print(f"  - 错误: {total_errors}")
    
    if args.dry_run:
        print("\n提示：这是预览模式，未实际移动文件。")
        print("      移除 --dry-run 参数以执行实际迁移。")
    else:
        print("\n✓ 迁移完成！")
        print("\n建议：检查前端页面，确认文件按分类正确显示。")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
