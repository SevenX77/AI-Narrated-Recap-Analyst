import os
import argparse
import json
import shutil
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.agents.deepseek_writer import DeepSeekWriter
from src.workflows.training_workflow import TrainingWorkflow

def setup_novel_workspace(novel_name):
    base_dir = f"output/novels/{novel_name}"
    os.makedirs(f"{base_dir}/raw", exist_ok=True)
    os.makedirs(f"{base_dir}/analysis", exist_ok=True)
    os.makedirs(f"{base_dir}/scripts", exist_ok=True)
    os.makedirs(f"{base_dir}/evaluation", exist_ok=True)
    return base_dir

def run_production_pipeline(novel_path, novel_name):
    print(f"🚀 启动生产流程: {novel_name}")
    workspace = setup_novel_workspace(novel_name)
    
    # Copy novel to workspace
    dest_path = f"{workspace}/raw/novel.txt"
    shutil.copy(novel_path, dest_path)
    
    client = get_llm_client()
    analyst = DeepSeekAnalyst(client)
    writer = DeepSeekWriter(client)
    
    print("1. 读取小说内容...")
    with open(dest_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # In production, we might process chunk by chunk. 
    # For now, let's take the first 15k chars as a demo "Episode 1"
    chunk = content[:15000]
    
    print("2. 执行深度分析 (Analyst)...")
    analysis = analyst.analyze(chunk, previous_context="小说开篇")
    
    # Save analysis
    analysis_path = f"{workspace}/analysis/ep01_analysis.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"   - 分析结果已保存: {analysis_path}")
    
    print("3. 生成解说文案 (Writer)...")
    script = writer.generate_script(analysis, style="first_person")
    
    # Save script
    script_path = f"{workspace}/scripts/ep01_script.json"
    with open(script_path, 'w', encoding='utf-8') as f:
        json.dump(script.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"   - 解说稿已保存: {script_path}")
    
    print("\n✅ 生产流程完成！")

def run_training_pipeline(novel_path, srt_folder, novel_name):
    print(f"🧪 启动训练/验证流程: {novel_name}")
    workspace = setup_novel_workspace(novel_name)
    
    workflow = TrainingWorkflow(novel_path, srt_folder, workspace)
    workflow.run()

def main():
    parser = argparse.ArgumentParser(description="AI Narrated Recap Analyst CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Production Command
    prod_parser = subparsers.add_parser("generate", help="Generate recap script from novel")
    prod_parser.add_argument("--novel", required=True, help="Path to novel text file")
    prod_parser.add_argument("--name", required=True, help="Project name (e.g. 'my_novel')")
    
    # Training Command
    train_parser = subparsers.add_parser("train", help="Run alignment training/verification")
    train_parser.add_argument("--novel", required=True, help="Path to novel text file")
    train_parser.add_argument("--srt", required=True, help="Path to folder containing SRT files")
    train_parser.add_argument("--name", required=True, help="Project name")

    args = parser.parse_args()
    
    if args.command == "generate":
        run_production_pipeline(args.novel, args.name)
    elif args.command == "train":
        run_training_pipeline(args.novel, args.srt, args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
