#!/usr/bin/env python3
"""
数据结构迁移脚本：从旧结构迁移到新结构

旧结构：
- raw/srt/
- processed/novel/
- processed/script/
- alignment/ (顶层)

新结构：
- raw/script/
- analyst/import/
- analyst/script_analysis/
- analyst/novel_analysis/
- analyst/alignment/

使用方法：
    python scripts/migrate_data_structure.py --project-id project_001 [--dry-run]
    python scripts/migrate_data_structure.py --all [--dry-run]
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import logger

class DataStructureMigrator:
    """数据结构迁移器"""
    
    def __init__(self, projects_dir: str, dry_run: bool = False):
        self.projects_dir = Path(projects_dir)
        self.dry_run = dry_run
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def migrate_project(self, project_id: str) -> bool:
        """迁移单个项目"""
        project_dir = self.projects_dir / project_id
        
        if not project_dir.exists():
            logger.error(f"Project directory not found: {project_dir}")
            self.error_count += 1
            return False
        
        logger.info(f"Migrating project: {project_id}")
        
        try:
            # 1. 迁移 raw/srt/ → raw/script/
            self._migrate_raw_srt(project_dir)
            
            # 2. 迁移 processed/ → analyst/
            self._migrate_processed(project_dir)
            
            # 3. 迁移 alignment/ → analyst/alignment/
            self._migrate_alignment(project_dir)
            
            self.migrated_count += 1
            logger.info(f"✅ Successfully migrated: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate {project_id}: {e}")
            self.error_count += 1
            return False
    
    def _migrate_raw_srt(self, project_dir: Path):
        """迁移 raw/srt/ → raw/script/"""
        old_srt_dir = project_dir / "raw" / "srt"
        new_script_dir = project_dir / "raw" / "script"
        
        if old_srt_dir.exists():
            if new_script_dir.exists():
                logger.warning(f"Target already exists: {new_script_dir}")
                return
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would rename: {old_srt_dir} → {new_script_dir}")
            else:
                old_srt_dir.rename(new_script_dir)
                logger.info(f"Renamed: raw/srt/ → raw/script/")
    
    def _migrate_processed(self, project_dir: Path):
        """迁移 processed/ → analyst/import/ 和 analyst/analysis/"""
        processed_dir = project_dir / "processed"
        analyst_dir = project_dir / "analyst"
        
        if not processed_dir.exists():
            logger.info("No processed/ directory found, skipping")
            return
        
        # 创建新目录结构
        if not self.dry_run:
            (analyst_dir / "import" / "novel").mkdir(parents=True, exist_ok=True)
            (analyst_dir / "import" / "script").mkdir(parents=True, exist_ok=True)
            (analyst_dir / "script_analysis" / "history").mkdir(parents=True, exist_ok=True)
            (analyst_dir / "novel_analysis" / "history").mkdir(parents=True, exist_ok=True)
        
        # 迁移 processed/novel/
        self._migrate_processed_novel(project_dir, processed_dir, analyst_dir)
        
        # 迁移 processed/script/
        self._migrate_processed_script(project_dir, processed_dir, analyst_dir)
        
        # 删除旧 processed/ 目录（如果为空）
        if not self.dry_run and processed_dir.exists():
            try:
                if not any(processed_dir.iterdir()):
                    processed_dir.rmdir()
                    logger.info("Removed empty processed/ directory")
            except OSError:
                logger.warning("processed/ directory not empty, keeping it")
    
    def _migrate_processed_novel(self, project_dir: Path, processed_dir: Path, analyst_dir: Path):
        """迁移小说处理数据"""
        novel_dir = processed_dir / "novel"
        if not novel_dir.exists():
            return
        
        # import 阶段文件
        import_files = ["metadata.json", "chapters.json", "intro.md", "novel-imported.md", "standardized.txt"]
        for filename in import_files:
            src = novel_dir / filename
            if src.exists():
                dst = analyst_dir / "import" / "novel" / filename
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would copy: {src.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
                else:
                    shutil.copy2(src, dst)
                    logger.info(f"Copied: {filename} to import/novel/")
        
        # segmented/ → novel_analysis/
        segmented_dir = novel_dir / "segmented"
        if segmented_dir.exists():
            for seg_file in segmented_dir.glob("*.json"):
                chapter_id = seg_file.stem  # e.g., "chapter_001"
                new_name = f"{chapter_id}_segmentation_latest.json"
                dst = analyst_dir / "novel_analysis" / new_name
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would copy: {seg_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
                else:
                    shutil.copy2(seg_file, dst)
                    logger.info(f"Migrated segmentation: {seg_file.name} → {new_name}")
        
        # annotated/ → novel_analysis/
        annotated_dir = novel_dir / "annotated"
        if annotated_dir.exists():
            for ann_file in annotated_dir.glob("*.json"):
                chapter_id = ann_file.stem
                new_name = f"{chapter_id}_annotation_latest.json"
                dst = analyst_dir / "novel_analysis" / new_name
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would copy: {ann_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
                else:
                    shutil.copy2(ann_file, dst)
                    logger.info(f"Migrated annotation: {ann_file.name} → {new_name}")
        
        # system_catalog.json
        system_catalog = novel_dir / "system_catalog.json"
        if system_catalog.exists():
            dst = analyst_dir / "novel_analysis" / "system_catalog_latest.json"
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would copy: {system_catalog.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
            else:
                shutil.copy2(system_catalog, dst)
                logger.info("Migrated system_catalog.json")
    
    def _migrate_processed_script(self, project_dir: Path, processed_dir: Path, analyst_dir: Path):
        """迁移脚本处理数据"""
        script_dir = processed_dir / "script"
        if not script_dir.exists():
            return
        
        # import 阶段文件
        import_files = ["episodes.json"]
        for filename in import_files:
            src = script_dir / filename
            if src.exists():
                dst = analyst_dir / "import" / "script" / filename
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would copy: {src.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
                else:
                    shutil.copy2(src, dst)
                    logger.info(f"Copied: {filename} to import/script/")
        
        # ep*-imported.md → import/script/
        for imported_file in script_dir.glob("ep*-imported.md"):
            dst = analyst_dir / "import" / "script" / imported_file.name
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would copy: {imported_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
            else:
                shutil.copy2(imported_file, dst)
                logger.info(f"Migrated: {imported_file.name}")
        
        # ep*-hook.json → script_analysis/
        for hook_file in script_dir.glob("ep*-hook.json"):
            ep_id = hook_file.stem.replace("-hook", "")  # e.g., "ep01"
            new_name = f"{ep_id}_hook_latest.json"
            dst = analyst_dir / "script_analysis" / new_name
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would copy: {hook_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
            else:
                shutil.copy2(hook_file, dst)
                logger.info(f"Migrated hook: {hook_file.name} → {new_name}")
        
        # segmented/*.json → script_analysis/
        segmented_dir = script_dir / "segmented"
        if segmented_dir.exists():
            for seg_file in segmented_dir.glob("*.json"):
                ep_id = seg_file.stem  # e.g., "ep01"
                new_name = f"{ep_id}_segmentation_latest.json"
                dst = analyst_dir / "script_analysis" / new_name
                
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would copy: {seg_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
                else:
                    shutil.copy2(seg_file, dst)
                    logger.info(f"Migrated segmentation: {seg_file.name} → {new_name}")
    
    def _migrate_alignment(self, project_dir: Path):
        """迁移 alignment/ → analyst/alignment/"""
        old_alignment_dir = project_dir / "alignment"
        new_alignment_dir = project_dir / "analyst" / "alignment"
        
        if not old_alignment_dir.exists():
            logger.info("No alignment/ directory found, skipping")
            return
        
        if not self.dry_run:
            new_alignment_dir.mkdir(parents=True, exist_ok=True)
            (new_alignment_dir / "history").mkdir(exist_ok=True)
        
        # 迁移所有对齐文件
        for alignment_file in old_alignment_dir.glob("*.json"):
            # 重命名为 *_alignment_latest.json
            if not alignment_file.name.endswith("_latest.json"):
                new_name = alignment_file.stem + "_alignment_latest.json"
            else:
                new_name = alignment_file.name
            
            dst = new_alignment_dir / new_name
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would copy: {alignment_file.relative_to(project_dir)} → {dst.relative_to(project_dir)}")
            else:
                shutil.copy2(alignment_file, dst)
                logger.info(f"Migrated alignment: {alignment_file.name} → {new_name}")
        
        # 删除旧 alignment/ 目录
        if not self.dry_run:
            try:
                if not any(old_alignment_dir.iterdir()):
                    old_alignment_dir.rmdir()
                    logger.info("Removed empty alignment/ directory")
            except OSError:
                logger.warning("alignment/ directory not empty, keeping it")
    
    def migrate_all(self) -> Dict[str, int]:
        """迁移所有项目"""
        if not self.projects_dir.exists():
            logger.error(f"Projects directory not found: {self.projects_dir}")
            return {"migrated": 0, "skipped": 0, "errors": 0}
        
        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                self.migrate_project(project_dir.name)
        
        return {
            "migrated": self.migrated_count,
            "skipped": self.skipped_count,
            "errors": self.error_count
        }
    
    def print_summary(self):
        """打印迁移摘要"""
        print("\n" + "="*50)
        print("Migration Summary")
        print("="*50)
        print(f"✅ Migrated: {self.migrated_count}")
        print(f"⏭️  Skipped:  {self.skipped_count}")
        print(f"❌ Errors:   {self.error_count}")
        print("="*50)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate project data structure from old to new format"
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Migrate specific project by ID"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all projects"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--projects-dir",
        type=str,
        default=str(PROJECT_ROOT / "data" / "projects"),
        help="Path to projects directory (default: data/projects)"
    )
    
    args = parser.parse_args()
    
    if not args.project_id and not args.all:
        parser.error("Either --project-id or --all must be specified")
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE - No changes will be made\n")
    
    migrator = DataStructureMigrator(args.projects_dir, dry_run=args.dry_run)
    
    if args.all:
        migrator.migrate_all()
    else:
        migrator.migrate_project(args.project_id)
    
    migrator.print_summary()


if __name__ == "__main__":
    main()
