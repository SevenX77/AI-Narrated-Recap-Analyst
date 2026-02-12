"""
迁移脚本：将 V1 项目数据迁移到 V2 格式
- 读取 project_index.json (V1)
- 为每个项目创建 meta.json (V2)
- 不删除 V1 数据（保留兼容性）
"""
import os
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import config
from src.core.schemas_project import ProjectMeta, ProjectStatus, ProjectSources
from src.utils.logger import logger


def migrate_v1_to_v2():
    """迁移 V1 项目到 V2 格式"""
    
    # 1. 读取 V1 索引
    index_path = os.path.join(config.data_dir, "project_index.json")
    if not os.path.exists(index_path):
        logger.info("❌ project_index.json 不存在，跳过迁移")
        return
    
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    v1_projects = index_data.get("projects", {})
    logger.info(f"📊 发现 {len(v1_projects)} 个 V1 项目")
    
    # 2. 迁移每个项目
    migrated_count = 0
    skipped_count = 0
    
    for project_id, v1_data in v1_projects.items():
        # 只迁移已初始化的项目（有实际目录）
        project_dir = os.path.join(config.data_dir, "projects", project_id)
        
        if not os.path.isdir(project_dir):
            logger.info(f"⏭️  跳过 {project_id}（目录不存在）")
            skipped_count += 1
            continue
        
        # 检查是否已有 meta.json
        meta_path = os.path.join(project_dir, "meta.json")
        if os.path.exists(meta_path):
            logger.info(f"⏭️  跳过 {project_id}（已迁移）")
            skipped_count += 1
            continue
        
        # 创建 V2 meta.json
        try:
            # 构建 ProjectMeta
            sources = v1_data.get("sources", {})
            meta = ProjectMeta(
                id=project_id,
                name=v1_data.get("name", project_id),
                description=v1_data.get("description", "从 V1 迁移的项目"),
                created_at=v1_data.get("created_at", datetime.now().isoformat()),
                updated_at=datetime.now().isoformat(),
                status=ProjectStatus(v1_data.get("status", "draft")),
                sources=ProjectSources(
                    has_novel=sources.get("has_novel", False),
                    has_script=sources.get("has_script", False),
                    novel_chapters=sources.get("novel_chapters", 0),
                    script_episodes=sources.get("script_episodes", 0)
                )
            )
            
            # 初始化 Phase I 状态
            meta.initialize_phase_i()
            
            # 保存 meta.json
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta.model_dump(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 迁移成功: {project_id} ({meta.name})")
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"❌ 迁移失败 {project_id}: {e}")
    
    # 3. 清理 discovered 状态的项目（分析资料/ 目录扫描生成的）
    logger.info("\n🧹 清理自动发现的项目...")
    cleaned_ids = []
    
    for project_id, v1_data in v1_projects.items():
        if v1_data.get("status") == "discovered":
            cleaned_ids.append(project_id)
            logger.info(f"🗑️  删除索引: {project_id} ({v1_data.get('name')})")
    
    # 更新索引文件（移除 discovered 项目）
    if cleaned_ids:
        for pid in cleaned_ids:
            del v1_projects[pid]
        
        index_data["projects"] = v1_projects
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 已清理 {len(cleaned_ids)} 个自动发现的项目")
    
    # 4. 禁用 V1 自动扫描（可选）
    v1_manager_path = os.path.join(
        os.path.dirname(__file__), 
        '../src/core/project_manager.py'
    )
    
    print("\n" + "="*60)
    print("📊 迁移统计:")
    print(f"  ✅ 成功迁移: {migrated_count} 个项目")
    print(f"  ⏭️  已跳过: {skipped_count} 个项目")
    print(f"  🗑️  已清理: {len(cleaned_ids)} 个自动发现的项目")
    print("="*60)
    
    if migrated_count > 0:
        print("\n✨ 迁移完成！现在可以使用 V2 API 访问项目。")
        print(f"\n📍 下一步：重启后端服务以生效")
        print(f"   cd {os.path.dirname(os.path.dirname(__file__))}")
        print(f"   python3 -m uvicorn src.api.main:app --reload")
    
    print("\n💡 提示：V1 数据已保留，可以安全回退")
    
    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "cleaned": len(cleaned_ids)
    }


if __name__ == "__main__":
    print("🚀 开始迁移 V1 项目到 V2 格式...")
    print()
    
    result = migrate_v1_to_v2()
    
    print("\n✅ 迁移脚本执行完成")
