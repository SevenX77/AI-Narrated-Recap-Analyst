import os
import argparse
import json
import shutil
import asyncio
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.agents.deepseek_writer import DeepSeekWriter
from src.workflows.ingestion_workflow import IngestionWorkflow
from src.workflows.training_workflow import TrainingWorkflow
from src.utils.logger import op_logger, logger
from src.core.project_manager import project_manager
from src.core.artifact_manager import artifact_manager

def run_production_pipeline(project_id):
    logger.info(f"🚀 启动生产流程: {project_id}")
    
    # 1. Initialize Project (Ensure paths exist)
    if not project_manager.initialize_project(project_id):
        logger.error(f"Failed to initialize project {project_id}")
        return

    paths = project_manager.get_project_paths(project_id)
    
    # 2. Load Novel Content
    novel_path = os.path.join(paths['raw'], "novel.txt")
    if not os.path.exists(novel_path):
        logger.error(f"Novel file not found at {novel_path}")
        return

    logger.info("1. 读取小说内容...")
    with open(novel_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # In production, we might process chunk by chunk. 
    # For now, let's take the first 15k chars as a demo "Episode 1"
    chunk = content[:15000]
    
    client = get_llm_client()
    analyst = DeepSeekAnalyst(client)
    writer = DeepSeekWriter(client)
    
    logger.info("2. 执行深度分析 (Analyst)...")
    analysis = analyst.analyze(chunk, previous_context="小说开篇")
    
    # Save analysis using ArtifactManager
    analysis_path = artifact_manager.save_artifact(
        analysis.model_dump(), 
        "ep01_analysis", 
        project_id, 
        paths['analysis']
    )
    logger.info(f"   - 分析结果已保存: {analysis_path}")
    
    logger.info("3. 生成解说文案 (Writer)...")
    script = writer.generate_script(analysis, style="first_person")
    
    # Save script using ArtifactManager (to production/scripts)
    scripts_dir = os.path.join(paths['root'], "production", "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    script_path = artifact_manager.save_artifact(
        script.model_dump(),
        "ep01_script",
        project_id,
        scripts_dir
    )
    logger.info(f"   - 解说稿已保存: {script_path}")
    
    # Log operation
    op_logger.log_operation(
        project_id=project_id,
        action="Generate Script (Production)",
        output_files=[analysis_path, script_path],
        details=f"Generated EP01 script"
    )

    logger.info("\n✅ 生产流程完成！")

def run_ingestion_pipeline(project_id):
    logger.info(f"📥 启动数据摄入与对齐流程: {project_id}")
    
    workflow = IngestionWorkflow(project_id)
    asyncio.run(workflow.run())

def run_training_pipeline(project_id):
    logger.info(f"🧪 启动训练/验证流程: {project_id}")
    
    workflow = TrainingWorkflow(project_id)
    asyncio.run(workflow.run())

def main():
    parser = argparse.ArgumentParser(description="AI Narrated Recap Analyst CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingestion Command
    ingest_parser = subparsers.add_parser("ingest", help="Run data ingestion and alignment workflow")
    ingest_parser.add_argument("--id", required=True, help="Project ID (e.g. PROJ_001)")
    
    # Production Command
    prod_parser = subparsers.add_parser("generate", help="Generate recap script from novel")
    prod_parser.add_argument("--id", required=True, help="Project ID (e.g. PROJ_001)")
    
    # Training Command
    train_parser = subparsers.add_parser("train", help="Run alignment training/verification")
    train_parser.add_argument("--id", required=True, help="Project ID (e.g. PROJ_001)")
    
    # List Projects Command
    list_parser = subparsers.add_parser("list", help="List available projects")

    args = parser.parse_args()
    
    if args.command == "ingest":
        run_ingestion_pipeline(args.id)
    elif args.command == "generate":
        run_production_pipeline(args.id)
    elif args.command == "train":
        run_training_pipeline(args.id)
    elif args.command == "list":
        projects = project_manager.list_projects()
        print(f"{'ID':<10} {'Name':<30} {'Status':<15}")
        print("-" * 60)
        for p in projects:
            print(f"{p['id']:<10} {p['name']:<30} {p.get('status', 'unknown'):<15}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
