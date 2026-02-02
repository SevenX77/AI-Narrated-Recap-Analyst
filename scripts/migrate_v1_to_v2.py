import os
import shutil
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.project_manager import project_manager
from src.core.config import config
from src.utils.logger import logger

def migrate():
    print("🚀 Starting Migration: V1 Output -> V2 Data Structure")
    
    # 1. Scan and Register Projects
    print("1. Scanning source directory...")
    project_manager._scan_and_update()
    projects = project_manager.list_projects()
    print(f"   Found {len(projects)} projects.")

    # 2. Initialize Structure & Ingest Data
    print("2. Initializing V2 structure...")
    for p in projects:
        pid = p['id']
        pname = p['name']
        print(f"   - Processing {pname} ({pid})...")
        if project_manager.initialize_project(pid):
            print(f"     ✅ Initialized & Ingested")
        else:
            print(f"     ❌ Failed")

    # 3. Clean up Old Output (Optional / Manual Confirmation)
    old_output = os.path.join(config.base_dir, "output", "novels")
    if os.path.exists(old_output):
        print("\n⚠️  Found old output directory: output/novels/")
        print("   It is recommended to archive or delete this manually after verifying the new data structure.")
        # We do not automatically delete to be safe
    
    print("\n✅ Migration Complete!")
    print(f"   New data location: {os.path.join(config.data_dir, 'projects')}")

if __name__ == "__main__":
    migrate()
