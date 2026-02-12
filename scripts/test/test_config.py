"""
测试配置文件
统一管理测试脚本中的路径配置
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 测试项目根目录（遵循文档定义：测试数据放在 output/test_projects/）
TEST_PROJECTS_DIR = PROJECT_ROOT / "output" / "test_projects"

# 正式项目根目录（遵循文档定义）
DATA_PROJECTS_DIR = PROJECT_ROOT / "data" / "projects"

# 临时输出目录
TEMP_OUTPUT_DIR = PROJECT_ROOT / "output" / "temp"

# 分析资料目录（外部数据源）
ANALYSIS_SOURCE_DIR = PROJECT_ROOT / "分析资料"


def get_test_project_path(project_name: str) -> Path:
    """
    获取测试项目路径
    
    Args:
        project_name: 项目名称
    
    Returns:
        测试项目完整路径
    """
    return TEST_PROJECTS_DIR / project_name


def get_data_project_path(project_name: str) -> Path:
    """
    获取正式项目路径
    
    Args:
        project_name: 项目名称（如 PROJ_001）
    
    Returns:
        正式项目完整路径
    """
    return DATA_PROJECTS_DIR / project_name


# 常用测试文件路径
TEST_NOVEL_PATH = ANALYSIS_SOURCE_DIR / "有原小说" / "01_末哥超凡公路" / "novel" / "序列公路求生：我在末日升级物资.txt"
TEST_SCRIPT_PATH = ANALYSIS_SOURCE_DIR / "有原小说" / "01_末哥超凡公路" / "srt" / "ep01.srt"
