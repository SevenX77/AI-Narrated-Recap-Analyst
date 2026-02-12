"""
测试自动预处理流程
"""
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.project_manager_v2 import project_manager_v2
from src.workflows.preprocess_service import preprocess_service
from src.core.config import config

def test_auto_preprocess():
    """测试完整的自动预处理流程"""
    
    print("=" * 60)
    print("测试自动预处理流程")
    print("=" * 60)
    
    # Step 1: 创建测试项目
    print("\n[Step 1] 创建测试项目...")
    project = project_manager_v2.create_project(
        name="测试项目_自动预处理",
        description="测试自动预处理功能"
    )
    print(f"✅ 项目已创建: {project.id}")
    print(f"   - 名称: {project.name}")
    print(f"   - 状态: {project.status}")
    print(f"   - has_novel: {project.sources.has_novel}")
    print(f"   - has_script: {project.sources.has_script}")
    
    # Step 2: 模拟上传文件（创建测试文件）
    print("\n[Step 2] 模拟上传测试文件...")
    project_dir = os.path.join(config.data_dir, "projects", project.id)
    raw_dir = os.path.join(project_dir, "raw")
    
    # 创建测试 novel.txt（符合格式要求）
    novel_content = """Title: 测试小说
Author: 测试作者
【玄幻】【冒险】

Introduction:
这是一本测试小说，用于验证自动预处理流程。主角将展开一段精彩的冒险旅程。

=== 第1章 测试章节 ===

这是测试小说内容。主角来到了一个陌生的世界，他必须适应这里的一切。

第一段剧情发展。主角遇到了第一个挑战。

第二段剧情发展。主角开始学习新的技能。

第三段剧情发展。主角结识了第一个朋友。

=== 第2章 另一个测试章节 ===

第二章的内容。主角的冒险继续深入。

剧情逐渐展开，矛盾开始显现。

主角面临新的选择和挑战。
"""
    novel_path = os.path.join(raw_dir, "novel.txt")
    with open(novel_path, 'w', encoding='utf-8') as f:
        f.write(novel_content)
    print(f"✅ 已创建测试 novel.txt")
    
    # 创建测试 ep01.srt（至少10条）
    srt_content = """1
00:00:00,000 --> 00:00:05,000
这是第一句话

2
00:00:05,000 --> 00:00:10,000
这是第二句话

3
00:00:10,000 --> 00:00:15,000
主角来到了一个陌生的地方

4
00:00:15,000 --> 00:00:20,000
他必须适应这里的一切

5
00:00:20,000 --> 00:00:25,000
第一个挑战很快就出现了

6
00:00:25,000 --> 00:00:30,000
但是主角没有退缩

7
00:00:30,000 --> 00:00:35,000
他开始学习新的技能

8
00:00:35,000 --> 00:00:40,000
并结识了第一个朋友

9
00:00:40,000 --> 00:00:45,000
冒险的故事正式开始

10
00:00:45,000 --> 00:00:50,000
精彩的旅程即将展开
"""
    srt_path = os.path.join(raw_dir, "ep01.srt")
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    print(f"✅ 已创建测试 ep01.srt")
    
    # Step 3: 更新源文件信息
    print("\n[Step 3] 更新项目源文件信息...")
    project_manager_v2.update_sources_from_filesystem(project.id)
    
    # 重新获取项目
    project = project_manager_v2.get_project(project.id)
    print(f"✅ 源文件信息已更新:")
    print(f"   - has_novel: {project.sources.has_novel}")
    print(f"   - has_script: {project.sources.has_script}")
    print(f"   - 项目状态: {project.status}")
    
    # Step 4: 执行预处理
    print("\n[Step 4] 执行自动预处理...")
    result = preprocess_service.preprocess_project(project.id)
    
    print(f"\n预处理结果:")
    print(f"   - 成功: {result['success']}")
    print(f"   - Novel处理: {result['novel_processed']}")
    print(f"   - Script集数: {result['script_episodes_processed']}")
    if result['errors']:
        print(f"   - 错误: {result['errors']}")
    
    # Step 5: 验证处理结果
    print("\n[Step 5] 验证处理结果...")
    
    # 检查章节
    chapters = project_manager_v2.get_chapters(project.id)
    print(f"✅ 章节数: {len(chapters)}")
    if chapters:
        print(f"   - 第一章: {chapters[0].get('title', 'N/A')}")
    
    # 检查集数
    episodes = project_manager_v2.get_episodes(project.id)
    print(f"✅ 集数: {len(episodes)}")
    if episodes:
        print(f"   - 第一集: {episodes[0].get('episode_name', 'N/A')}")
    
    # 检查工作流阶段
    project = project_manager_v2.get_project(project.id)
    print(f"\n工作流阶段状态:")
    print(f"   - 预处理阶段: {project.workflow_stages.preprocess.status}")
    
    # Step 6: 检查生成的文件
    print("\n[Step 6] 检查生成的文件...")
    processed_novel_dir = os.path.join(project_dir, "processed/novel")
    processed_script_dir = os.path.join(project_dir, "processed/script")
    
    novel_files = os.listdir(processed_novel_dir) if os.path.exists(processed_novel_dir) else []
    script_files = os.listdir(processed_script_dir) if os.path.exists(processed_script_dir) else []
    
    print(f"✅ Novel 处理后文件: {novel_files}")
    print(f"✅ Script 处理后文件: {script_files}")
    
    # Step 7: 显示元数据
    if 'metadata.json' in novel_files:
        metadata_path = os.path.join(processed_novel_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"\n小说元数据:")
        print(f"   - 标题: {metadata.get('title', 'N/A')}")
        print(f"   - 作者: {metadata.get('author', 'N/A')}")
        print(f"   - 字数: {metadata.get('word_count', 0)}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    
    return project.id


if __name__ == "__main__":
    try:
        project_id = test_auto_preprocess()
        print(f"\n测试项目ID: {project_id}")
        print("可以使用以下命令查看项目目录:")
        print(f"  tree data/projects/{project_id}")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
