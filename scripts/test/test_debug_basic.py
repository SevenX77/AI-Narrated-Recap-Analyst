"""
最基础的调试测试
"""

import sys

print("=" * 80, flush=True)
print("开始测试", flush=True)
print("=" * 80, flush=True)

try:
    print("\nStep 1: 导入Path", flush=True)
    from pathlib import Path
    print("✅ Path导入成功", flush=True)
    
    print("\nStep 2: 设置project_root", flush=True)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    print(f"✅ project_root = {project_root}", flush=True)
    
    print("\nStep 3: 导入ScriptProcessingWorkflow", flush=True)
    from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
    print("✅ ScriptProcessingWorkflow导入成功", flush=True)
    
    print("\nStep 4: 导入ScriptProcessingConfig", flush=True)
    from src.core.schemas_script import ScriptProcessingConfig
    print("✅ ScriptProcessingConfig导入成功", flush=True)
    
    print("\nStep 5: 创建workflow实例", flush=True)
    workflow = ScriptProcessingWorkflow()
    print("✅ workflow创建成功", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("测试成功完成！", flush=True)
    print("=" * 80, flush=True)

except Exception as e:
    print(f"\n❌ 错误: {str(e)}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
