"""
Project Migration Workflow
项目迁移与数据处理工作流
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from src.core.interfaces import BaseWorkflow
from src.core.config import config
from src.tools.novel_processor import NovelSegmentationTool
from src.tools.novel_chapter_processor import NovelChapterProcessor, MetadataExtractor
from src.tools.introduction_validator import IntroductionValidator
from src.tools.srt_processor import SrtScriptProcessor

logger = logging.getLogger(__name__)


class ProjectMigrationWorkflow(BaseWorkflow):
    """
    项目迁移工作流
    
    功能：
    1. 从 分析资料/ 迁移项目到标准化的 data/projects/ 结构
    2. 重构目录：with_novel / without_novel
    3. 处理小说文本：分段、格式化
    4. 处理字幕文件：编码规范化
    5. 更新 project_index.json
    6. 生成迁移报告
    """
    
    name = "project_migration"
    
    # 项目映射配置
    PROJECT_MAPPING = {
        "with_novel": {
            "末哥超凡公路": {
                "old_id": "PROJ_002",
                "source": "分析资料/有原小说/01_末哥超凡公路",
                "purpose": "alignment_writer_training",
                "is_ground_truth": True,
                "is_explosive": False
            },
            "天命桃花": {
                "old_id": "PROJ_004",
                "source": "分析资料/有原小说/02_天命桃花",
                "purpose": "alignment_writer_training",
                "is_ground_truth": False,
                "is_explosive": False
            },
            "永夜悔恨录": {
                "old_id": "PROJ_003",
                "source": "分析资料/有原小说/03_永夜悔恨录",
                "purpose": "alignment_writer_training",
                "is_ground_truth": False,
                "is_explosive": False
            }
        },
        "without_novel": {
            "超前崛起": {
                "old_id": "PROJ_001",
                "source": "分析资料/没有原小说/04_超前崛起",
                "purpose": "script_analysis_hit_pattern",
                "is_ground_truth": False,
                "is_explosive": False
            },
            "末世寒潮": {
                "old_id": "PROJ_005",
                "source": "分析资料/没有原小说/05_末世寒潮",
                "purpose": "script_analysis_hit_pattern",
                "is_ground_truth": False,
                "is_explosive": False
            }
        }
    }
    
    def __init__(self, use_llm: bool = True, dry_run: bool = False):
        """
        Args:
            use_llm: 是否在小说处理中使用 LLM 辅助
            dry_run: 是否为试运行（不实际写入文件）
        """
        super().__init__()
        self.use_llm = use_llm
        self.dry_run = dry_run
        self.novel_tool = NovelSegmentationTool(use_llm=use_llm)
        self.chapter_processor = NovelChapterProcessor(chapters_per_file=10)
        self.metadata_extractor = MetadataExtractor(use_llm=True)  # 启用LLM智能过滤
        self.intro_validator = IntroductionValidator()  # LLM验证器
        self.srt_processor = SrtScriptProcessor(use_llm=use_llm)  # SRT处理器
        
        self.base_dir = Path(config.base_dir)
        self.data_dir = Path(config.data_dir)
        self.source_dir = Path(config.analysis_source_dir)
        
        self.migration_report = {
            "start_time": None,
            "end_time": None,
            "projects_migrated": 0,
            "files_processed": {
                "novels": 0,
                "srt_files": 0,
                "srt_scripts_processed": 0,
                "total_size_mb": 0
            },
            "novel_processing": {},
            "errors": []
        }
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        执行迁移工作流
        
        Returns:
            迁移报告
        """
        logger.info(f"Starting migration workflow (use_llm={self.use_llm}, dry_run={self.dry_run})")
        self.migration_report["start_time"] = datetime.now().isoformat()
        
        try:
            # 步骤 1: 验证源目录
            self._validate_sources()
            
            # 步骤 2: 迁移 with_novel 项目
            for project_name, project_info in self.PROJECT_MAPPING["with_novel"].items():
                await self._migrate_with_novel(project_name, project_info)
            
            # 步骤 3: 迁移 without_novel 项目
            for project_name, project_info in self.PROJECT_MAPPING["without_novel"].items():
                await self._migrate_without_novel(project_name, project_info)
            
            # 步骤 4: 更新 project_index.json
            self._update_project_index()
            
            # 步骤 5: 生成报告
            self._finalize_report()
            
            logger.info(f"Migration completed: {self.migration_report['projects_migrated']} projects")
            return self.migration_report
        
        except Exception as e:
            logger.error(f"Migration workflow failed: {e}", exc_info=True)
            self.migration_report["errors"].append({
                "stage": "workflow",
                "error": str(e)
            })
            raise
    
    def _validate_sources(self):
        """验证源目录存在"""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
        
        logger.info(f"Source directory validated: {self.source_dir}")
    
    async def _migrate_with_novel(self, project_name: str, project_info: Dict[str, Any]):
        """
        迁移有小说的项目
        
        Args:
            project_name: 项目名称（中文）
            project_info: 项目配置信息
        """
        logger.info(f"Migrating with_novel project: {project_name}")
        
        try:
            # 1. 创建目标目录
            target_dir = self.data_dir / "projects" / "with_novel" / project_name
            raw_dir = target_dir / "raw"
            novel_dir = target_dir / "novel"  # 新增：处理后的小说目录
            script_dir = target_dir / "script"  # 新增：处理后的脚本目录
            
            if not self.dry_run:
                raw_dir.mkdir(parents=True, exist_ok=True)
                novel_dir.mkdir(parents=True, exist_ok=True)  # 新增
                script_dir.mkdir(parents=True, exist_ok=True)  # 新增
                (target_dir / "alignment").mkdir(exist_ok=True)
                (target_dir / "analysis").mkdir(exist_ok=True)
                (target_dir / "ground_truth").mkdir(exist_ok=True)
            
            # 2. 处理小说文件
            source_path = self.base_dir / project_info["source"]
            novel_source = source_path / "novel"
            
            # 查找小说文件
            novel_files = list(novel_source.glob("*.txt"))
            if not novel_files:
                logger.warning(f"No novel file found for {project_name}")
                return
            
            novel_file = novel_files[0]  # 取第一个 .txt 文件
            logger.info(f"Processing novel: {novel_file.name}")
            
            # 读取原始小说
            with open(novel_file, "r", encoding="utf-8") as f:
                original_text = f.read()
            
            file_size_mb = len(original_text.encode("utf-8")) / (1024 * 1024)
            
            if not self.dry_run:
                # 保存原始文件到 raw/
                raw_novel_path = raw_dir / "novel.txt"
                with open(raw_novel_path, "w", encoding="utf-8") as f:
                    f.write(original_text)
                logger.info(f"Saved raw novel: {raw_novel_path}")
                
                # 处理分段
                logger.info(f"Starting novel segmentation for {project_name}")
                result = self.novel_tool.execute(original_text, preserve_metadata=True)
                processed_text = result.paragraphs[0]
                
                # 先提取元数据（包含智能过滤的简介）
                logger.info(f"Extracting metadata for {project_name}")
                extracted_metadata = self.metadata_extractor.execute(original_text)
                filtered_introduction = extracted_metadata["novel"]["introduction"]
                
                # 验证过滤质量（混合策略验证）
                logger.info(f"Validating introduction quality for {project_name}")
                original_intro = self._extract_original_introduction(original_text)
                validation_result = self.intro_validator.execute(
                    original_introduction=original_intro,
                    filtered_introduction=filtered_introduction,
                    novel_title=extracted_metadata["novel"].get("title", project_name)
                )
                
                # 使用验证后的简介（可能已修复critical问题）
                final_introduction = validation_result.filtered_introduction
                
                # 记录验证结果
                validation_summary = {
                    "is_valid": validation_result.is_valid,
                    "quality_score": validation_result.quality_score,
                    "issues_count": len(validation_result.issues),
                    "critical_issues": sum(1 for i in validation_result.issues if i.severity == "critical"),
                    "rule_suggestions": validation_result.rule_suggestions
                }
                logger.info(f"Validation result: {validation_result}")
                
                # 章节处理：拆分为 chpt_0000.txt, chpt_0001-0010.txt, ...
                logger.info(f"Starting chapter processing for {project_name}")
                chapter_report = self.chapter_processor.execute(
                    processed_text, 
                    novel_dir,
                    introduction_override=final_introduction  # 使用验证后的简介
                )
                logger.info(f"Created {len(chapter_report['chapter_files'])} chapter files")
                
                # 更新迁移报告
                self.migration_report["novel_processing"][project_name] = {
                    **result.stats,
                    "chapters": chapter_report,
                    "validation": validation_summary  # 添加验证结果
                }
            
            self.migration_report["files_processed"]["novels"] += 1
            self.migration_report["files_processed"]["total_size_mb"] += file_size_mb
            
            # 3. 复制 SRT 文件到 raw/
            srt_source = source_path / "srt"
            if srt_source.exists():
                srt_count = await self._copy_srt_files(srt_source, raw_dir)
                self.migration_report["files_processed"]["srt_files"] += srt_count
                
                # 4. 处理 SRT 文件 -> script/
                if not self.dry_run:
                    logger.info(f"Processing SRT files for {project_name}")
                    
                    # 读取前3章小说作为参考
                    novel_reference = self._load_novel_reference(novel_dir, chapters=3)
                    
                    # 处理每个SRT文件
                    srt_files = sorted(raw_dir.glob("*.srt"))
                    for srt_file in srt_files:
                        try:
                            logger.info(f"Processing {srt_file.name}")
                            srt_report = self.srt_processor.execute(
                                srt_file_path=srt_file,
                                output_dir=script_dir,
                                novel_reference=novel_reference,
                                episode_name=srt_file.stem
                            )
                            self.migration_report["files_processed"]["srt_scripts_processed"] += 1
                            logger.info(f"Processed {srt_file.name} -> {srt_report['output_file']}")
                        except Exception as e:
                            logger.error(f"Failed to process SRT {srt_file.name}: {e}", exc_info=True)
                            self.migration_report["errors"].append({
                                "project": project_name,
                                "file": srt_file.name,
                                "error": str(e)
                            })
            
            # 4. 创建元数据文件
            if not self.dry_run:
                metadata = {
                    "project_name": project_name,
                    "old_project_id": project_info["old_id"],
                    "category": "with_novel",
                    "source_path": str(source_path),
                    "migrated_at": datetime.now().isoformat(),
                    "raw_novel_file": novel_file.name,
                    **extracted_metadata  # 包含 novel: {title, author, tags, introduction}
                }
                
                # 添加章节文件信息
                if "novel" in metadata:
                    metadata["novel"]["chapters"] = {
                        "total": chapter_report["total_chapters"],
                        "files": {
                            filename: f"第{i*10+1}-{min((i+1)*10, chapter_report['total_chapters'])}章"
                            for i, filename in enumerate(chapter_report["chapter_files"])
                        }
                    }
                    # 添加简介文件
                    metadata["novel"]["chapters"]["files"]["chpt_0000.txt"] = "简介"
                
                metadata_path = target_dir / "metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.migration_report["projects_migrated"] += 1
            logger.info(f"Successfully migrated {project_name}")
        
        except Exception as e:
            logger.error(f"Failed to migrate {project_name}: {e}", exc_info=True)
            self.migration_report["errors"].append({
                "project": project_name,
                "error": str(e)
            })
    
    async def _migrate_without_novel(self, project_name: str, project_info: Dict[str, Any]):
        """
        迁移没有小说的项目
        
        Args:
            project_name: 项目名称
            project_info: 项目配置
        """
        logger.info(f"Migrating without_novel project: {project_name}")
        
        try:
            # 1. 创建目标目录
            target_dir = self.data_dir / "projects" / "without_novel" / project_name
            raw_dir = target_dir / "raw"
            script_dir = target_dir / "script"  # 新增：处理后的脚本目录
            
            if not self.dry_run:
                raw_dir.mkdir(parents=True, exist_ok=True)
                script_dir.mkdir(parents=True, exist_ok=True)  # 新增
                (target_dir / "analysis").mkdir(exist_ok=True)
                (target_dir / "ground_truth").mkdir(exist_ok=True)
            
            # 2. 复制 SRT 文件到 raw/
            source_path = self.base_dir / project_info["source"]
            srt_source = source_path / "srt"
            
            if srt_source.exists():
                srt_count = await self._copy_srt_files(srt_source, raw_dir)
                self.migration_report["files_processed"]["srt_files"] += srt_count
                
                # 3. 处理 SRT 文件 -> script/（无小说参考模式）
                if not self.dry_run:
                    logger.info(f"Processing SRT files for {project_name} (without novel reference)")
                    
                    # 处理每个SRT文件（无小说参考）
                    srt_files = sorted(raw_dir.glob("*.srt"))
                    for srt_file in srt_files:
                        try:
                            logger.info(f"Processing {srt_file.name}")
                            srt_report = self.srt_processor.execute(
                                srt_file_path=srt_file,
                                output_dir=script_dir,
                                novel_reference=None,  # 无小说参考
                                episode_name=srt_file.stem
                            )
                            self.migration_report["files_processed"]["srt_scripts_processed"] += 1
                            logger.info(f"Processed {srt_file.name} -> {srt_report['output_file']}")
                        except Exception as e:
                            logger.error(f"Failed to process SRT {srt_file.name}: {e}", exc_info=True)
                            self.migration_report["errors"].append({
                                "project": project_name,
                                "file": srt_file.name,
                                "error": str(e)
                            })
            else:
                logger.warning(f"No SRT directory found for {project_name}")
            
            # 3. 创建元数据
            if not self.dry_run:
                metadata = {
                    "project_name": project_name,
                    "old_project_id": project_info["old_id"],
                    "category": "without_novel",
                    "source_path": str(source_path),
                    "migrated_at": datetime.now().isoformat()
                }
                
                metadata_path = target_dir / "metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.migration_report["projects_migrated"] += 1
            logger.info(f"Successfully migrated {project_name}")
        
        except Exception as e:
            logger.error(f"Failed to migrate {project_name}: {e}", exc_info=True)
            self.migration_report["errors"].append({
                "project": project_name,
                "error": str(e)
            })
    
    async def _copy_srt_files(self, source_dir: Path, target_dir: Path) -> int:
        """
        复制并处理 SRT 文件
        
        Args:
            source_dir: SRT 源目录
            target_dir: 目标目录
        
        Returns:
            复制的文件数量
        """
        srt_files = sorted(source_dir.glob("*.srt"))
        
        for srt_file in srt_files:
            if not self.dry_run:
                # 读取原始内容
                with open(srt_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # 规范化编码和换行符
                content = content.replace("\r\n", "\n")
                
                # 写入目标
                target_path = target_dir / srt_file.name
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logger.info(f"Copied SRT: {srt_file.name}")
        
        return len(srt_files)
    
    def _update_project_index(self):
        """更新 project_index.json"""
        logger.info("Updating project_index.json")
        
        index_path = self.data_dir / "project_index.json"
        
        # 读取旧的索引（如果存在）
        old_index = {}
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                old_index = json.load(f)
        
        # 构建新索引
        new_index = {
            "version": "2.0",
            "updated_at": datetime.now().isoformat(),
            "projects": {
                "with_novel": {},
                "without_novel": {}
            },
            "migration_history": {
                "v1_to_v2": {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "archived_to": "data/projects_archive_20260205",
                    "reason": "重构项目结构，分离有无原小说项目，实现小说自然分段处理"
                }
            }
        }
        
        # 填充项目信息
        for category in ["with_novel", "without_novel"]:
            for project_name, project_info in self.PROJECT_MAPPING[category].items():
                old_id = project_info["old_id"]
                
                # 从旧索引获取信息
                old_project_data = {}
                if "projects" in old_index and old_id in old_index["projects"]:
                    old_project_data = old_index["projects"][old_id]
                
                # 获取 episodes 列表
                episodes = self._get_episodes(project_name, category)
                
                new_index["projects"][category][project_name] = {
                    "id": old_id,
                    "name": project_name,
                    "category": category,
                    "purpose": project_info["purpose"],
                    "source_path": str(self.base_dir / project_info["source"]),
                    "created_at": old_project_data.get("created_at", datetime.now().isoformat()),
                    "migrated_at": datetime.now().isoformat(),
                    "status": "migrated",
                    "is_ground_truth": project_info["is_ground_truth"],
                    "is_explosive": project_info["is_explosive"],
                    "heat_score": old_project_data.get("heat_score"),
                    "episodes": episodes,
                    "notes": old_project_data.get("notes", "")
                }
                
                # 添加小说处理信息
                if category == "with_novel" and project_name in self.migration_report["novel_processing"]:
                    new_index["projects"][category][project_name]["novel_processing"] = {
                        "method": "rule_llm_hybrid" if self.use_llm else "rule_only",
                        "processed_at": datetime.now().isoformat(),
                        "stats": self.migration_report["novel_processing"][project_name]
                    }
        
        # 保留元数据定义
        if "heat_score_definition" in old_index:
            new_index["heat_score_definition"] = old_index["heat_score_definition"]
        if "is_explosive_definition" in old_index:
            new_index["is_explosive_definition"] = old_index["is_explosive_definition"]
        
        # 写入新索引
        if not self.dry_run:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(new_index, f, ensure_ascii=False, indent=2)
            logger.info(f"Updated project_index.json")
    
    def _load_novel_reference(self, novel_dir: Path, chapters: int = 3) -> str:
        """
        加载小说参考文本（用于SRT处理）
        
        Args:
            novel_dir: 小说目录（包含chpt_*.txt文件）
            chapters: 加载前N章作为参考（默认3章）
        
        Returns:
            合并的小说参考文本
        """
        try:
            # 读取简介
            intro_file = novel_dir / "chpt_0000.txt"
            reference_parts = []
            
            if intro_file.exists():
                with open(intro_file, 'r', encoding='utf-8') as f:
                    reference_parts.append(f.read())
            
            # 读取前N章
            chapter_files = sorted(novel_dir.glob("chpt_*.txt"))
            loaded = 0
            
            for chapter_file in chapter_files:
                if chapter_file.name == "chpt_0000.txt":
                    continue  # 跳过简介
                
                if loaded >= chapters:
                    break
                
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 限制每章的长度（避免context过长）
                    if len(content) > 3000:
                        content = content[:3000] + "..."
                    reference_parts.append(content)
                    loaded += 1
            
            reference_text = "\n\n".join(reference_parts)
            logger.info(f"Loaded novel reference: {len(reference_text)} chars from {loaded} chapters")
            return reference_text
        
        except Exception as e:
            logger.warning(f"Failed to load novel reference: {e}")
            return ""
    
    def _extract_original_introduction(self, novel_text: str) -> str:
        """提取原始简介（包含元信息）"""
        lines = novel_text.split('\n')
        intro_lines = []
        in_introduction = False
        
        for line in lines:
            if line.strip() == '简介:':
                in_introduction = True
                continue
            
            if '========' in line or line.startswith('==='):
                if in_introduction:
                    break
                continue
            
            if in_introduction and line.strip():
                intro_lines.append(line.strip())
        
        return '\n'.join(intro_lines)
    
    def _get_episodes(self, project_name: str, category: str) -> List[str]:
        """获取项目的集数列表"""
        project_dir = self.data_dir / "projects" / category / project_name / "raw"
        
        if not project_dir.exists():
            return []
        
        srt_files = sorted(project_dir.glob("ep*.srt"))
        episodes = [f.stem for f in srt_files]  # ep01, ep02, ...
        
        return episodes
    
    def _finalize_report(self):
        """完成报告"""
        self.migration_report["end_time"] = datetime.now().isoformat()
        
        # 保存报告
        if not self.dry_run:
            report_path = self.data_dir / "migration_report_20260205.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(self.migration_report, f, ensure_ascii=False, indent=2)
            logger.info(f"Migration report saved: {report_path}")


async def main():
    """主函数：执行迁移"""
    import asyncio
    
    # 创建工作流
    workflow = ProjectMigrationWorkflow(use_llm=True, dry_run=False)
    
    # 执行迁移
    report = await workflow.run()
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 迁移完成摘要")
    print("="*60)
    print(f"✅ 项目迁移数量: {report['projects_migrated']}")
    print(f"📖 小说文件处理: {report['files_processed']['novels']}")
    print(f"📝 字幕文件复制: {report['files_processed']['srt_files']}")
    print(f"💾 总数据大小: {report['files_processed']['total_size_mb']:.2f} MB")
    
    if report["errors"]:
        print(f"\n⚠️  错误数量: {len(report['errors'])}")
        for error in report["errors"]:
            print(f"  - {error}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
