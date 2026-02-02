import os
import json
import shutil
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.artifact_manager import artifact_manager
from src.core.project_manager import project_manager
from src.core.config import config

def migrate_artifacts():
    print("🚀 Starting Artifact Migration...")
    
    # Mapping: Old Folder Name -> Project ID
    # Based on user confirmation: doomsday_survival = 末哥超凡公路 = PROJ_002
    # doomsday_training is likely related to PROJ_002 as well
    project_map = {
        "doomsday_survival": "PROJ_002",
        "doomsday_training": "PROJ_002" 
    }
    
    old_novels_dir = os.path.join(config.output_dir, "novels")
    if not os.path.exists(old_novels_dir):
        print("No old novels directory found. Skipping.")
        return

    for old_name in os.listdir(old_novels_dir):
        old_path = os.path.join(old_novels_dir, old_name)
        if not os.path.isdir(old_path):
            continue
            
        target_pid = project_map.get(old_name)
        if not target_pid:
            print(f"⚠️  Skipping unknown folder: {old_name}")
            continue
            
        print(f"📦 Migrating {old_name} -> {target_pid}...")
        paths = project_manager.get_project_paths(target_pid)
        
        # 1. Migrate Analysis
        analysis_dir = os.path.join(old_path, "analysis")
        if os.path.exists(analysis_dir):
            for f in os.listdir(analysis_dir):
                if f.endswith(".json"):
                    src = os.path.join(analysis_dir, f)
                    with open(src, 'r', encoding='utf-8') as jf:
                        content = json.load(jf)
                    # Save as versioned artifact
                    artifact_manager.save_artifact(
                        content, 
                        f.replace(".json", ""), 
                        target_pid, 
                        paths['analysis']
                    )
                    print(f"   - Migrated analysis: {f}")

        # 2. Migrate Scripts (to production/scripts - create if needed)
        scripts_dir = os.path.join(old_path, "scripts")
        if os.path.exists(scripts_dir):
            target_scripts_dir = os.path.join(paths['root'], "production", "scripts")
            os.makedirs(target_scripts_dir, exist_ok=True)
            
            for f in os.listdir(scripts_dir):
                if f.endswith(".json"):
                    src = os.path.join(scripts_dir, f)
                    with open(src, 'r', encoding='utf-8') as jf:
                        content = json.load(jf)
                    artifact_manager.save_artifact(
                        content, 
                        f.replace(".json", ""), 
                        target_pid, 
                        target_scripts_dir
                    )
                    print(f"   - Migrated script: {f}")

        # 3. Migrate Reports/Methodology (from root of old folder)
        for f in os.listdir(old_path):
            if f == "feedback_report.json":
                src = os.path.join(old_path, f)
                with open(src, 'r', encoding='utf-8') as jf:
                    content = json.load(jf)
                # Save to a 'training' folder
                target_training_dir = os.path.join(paths['root'], "training", "reports")
                os.makedirs(target_training_dir, exist_ok=True)
                artifact_manager.save_artifact(content, "feedback_report", target_pid, target_training_dir)
                print(f"   - Migrated report: {f}")
                
            elif f == "methodology_v1.txt":
                src = os.path.join(old_path, f)
                with open(src, 'r', encoding='utf-8') as tf:
                    content = tf.read()
                target_training_dir = os.path.join(paths['root'], "training", "reports")
                os.makedirs(target_training_dir, exist_ok=True)
                artifact_manager.save_artifact(content, "methodology", target_pid, target_training_dir, extension="txt")
                print(f"   - Migrated methodology: {f}")

    print("\n✅ Migration complete.")

def clean_legacy():
    print("🧹 Cleaning up legacy folders...")
    legacy_dirs = [
        "novels",
        "analysis",
        "scripts",
        "logs"
    ]
    
    for d in legacy_dirs:
        path = os.path.join(config.output_dir, d)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"   - Deleted: {path}")
            
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    migrate_artifacts()
    clean_legacy()
