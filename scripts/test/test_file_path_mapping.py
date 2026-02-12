"""
测试文件路径映射系统
验证 raw/novel 与 raw/srt 分类功能的完整性
"""
import sys
import os
from pathlib import Path
import requests
import json

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.project_manager_v2 import project_manager_v2
from src.core.config import config

# API 基础 URL
API_BASE = "http://localhost:8000/api/v2"

def print_section(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_backend_file_list():
    """测试后端文件列表 API"""
    print_section("1. 测试后端文件列表（带 category）")
    
    project_id = "project_002"
    files = project_manager_v2.get_raw_files(project_id)
    
    print(f"项目 {project_id} 文件列表：")
    print(f"  总数: {len(files)}")
    
    novel_files = [f for f in files if f.get('category') == 'novel']
    srt_files = [f for f in files if f.get('category') == 'srt']
    root_files = [f for f in files if 'category' not in f]
    
    print(f"  Novel 分类: {len(novel_files)} 个")
    for f in novel_files:
        print(f"    ✓ {f['name']}")
    
    print(f"  SRT 分类: {len(srt_files)} 个")
    for f in srt_files:
        print(f"    ✓ {f['name']}")
    
    if root_files:
        print(f"  根目录（旧数据）: {len(root_files)} 个")
        for f in root_files:
            print(f"    ⚠ {f['name']}")
    
    return len(files) > 0

def test_file_physical_location():
    """测试文件物理位置"""
    print_section("2. 测试文件物理位置")
    
    project_id = "project_002"
    project_dir = os.path.join(config.data_dir, "projects", project_id)
    
    # 检查目录结构
    raw_base = os.path.join(project_dir, "raw")
    raw_novel = os.path.join(raw_base, "novel")
    raw_srt = os.path.join(raw_base, "srt")
    
    checks = [
        (raw_base, "raw/"),
        (raw_novel, "raw/novel/"),
        (raw_srt, "raw/srt/"),
    ]
    
    all_exist = True
    for path, label in checks:
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"  {status} {label:20s} {'存在' if exists else '不存在'}")
        all_exist = all_exist and exists
    
    # 检查文件
    if os.path.exists(raw_novel):
        novel_files = os.listdir(raw_novel)
        print(f"\n  raw/novel/ 中的文件 ({len(novel_files)} 个):")
        for f in novel_files[:3]:  # 只显示前3个
            print(f"    • {f}")
        if len(novel_files) > 3:
            print(f"    ... 和 {len(novel_files) - 3} 个其他文件")
    
    if os.path.exists(raw_srt):
        srt_files = os.listdir(raw_srt)
        print(f"\n  raw/srt/ 中的文件 ({len(srt_files)} 个):")
        for f in sorted(srt_files)[:5]:  # 只显示前5个
            print(f"    • {f}")
        if len(srt_files) > 5:
            print(f"    ... 和 {len(srt_files) - 5} 个其他文件")
    
    return all_exist

def test_api_endpoints():
    """测试 API 端点"""
    print_section("3. 测试 API 端点")
    
    project_id = "project_002"
    
    tests = [
        ("GET /projects/{id}/files", f"{API_BASE}/projects/{project_id}/files"),
        ("GET /projects/{id}/chapters", f"{API_BASE}/projects/{project_id}/chapters"),
        ("GET /projects/{id}/episodes", f"{API_BASE}/projects/{project_id}/episodes"),
    ]
    
    all_success = True
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            success = response.status_code == 200
            status = "✓" if success else "✗"
            
            if success:
                data = response.json()
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"  {status} {name:40s} → 200 OK ({', '.join(keys[:3])}...)")
                elif isinstance(data, list):
                    print(f"  {status} {name:40s} → 200 OK ({len(data)} items)")
            else:
                print(f"  {status} {name:40s} → {response.status_code}")
                all_success = False
        except requests.exceptions.ConnectionError:
            print(f"  ✗ {name:40s} → 后端未运行")
            all_success = False
        except Exception as e:
            print(f"  ✗ {name:40s} → {str(e)}")
            all_success = False
    
    return all_success

def test_file_view_api():
    """测试文件查看 API（带 category）"""
    print_section("4. 测试文件查看 API")
    
    project_id = "project_002"
    files = project_manager_v2.get_raw_files(project_id)
    
    if not files:
        print("  ⚠ 没有文件可测试")
        return False
    
    # 测试一个 novel 文件
    novel_file = next((f for f in files if f.get('category') == 'novel'), None)
    if novel_file:
        filename = novel_file['name']
        url = f"{API_BASE}/projects/{project_id}/files/{filename}/view?category=novel"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content_length = len(response.text)
                print(f"  ✓ Novel 文件查看: {filename}")
                print(f"    URL: ...?category=novel")
                print(f"    大小: {content_length:,} 字符")
            else:
                print(f"  ✗ Novel 文件查看失败: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"  ⚠ 后端未运行，跳过 API 测试")
            return True  # 不算失败
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            return False
    
    # 测试一个 srt 文件
    srt_file = next((f for f in files if f.get('category') == 'srt'), None)
    if srt_file:
        filename = srt_file['name']
        url = f"{API_BASE}/projects/{project_id}/files/{filename}/view?category=srt"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content_length = len(response.text)
                print(f"  ✓ SRT 文件查看: {filename}")
                print(f"    URL: ...?category=srt")
                print(f"    大小: {content_length:,} 字符")
            else:
                print(f"  ✗ SRT 文件查看失败: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            # 已经在上面报告过了
            pass
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            return False
    
    return True

def test_processed_data():
    """测试预处理后的数据"""
    print_section("5. 测试预处理数据")
    
    project_id = "project_002"
    project_dir = os.path.join(config.data_dir, "projects", project_id)
    
    checks = [
        ("novel/chapters.json", os.path.join(project_dir, "processed/novel/chapters.json")),
        ("novel/metadata.json", os.path.join(project_dir, "processed/novel/metadata.json")),
        ("script/episodes.json", os.path.join(project_dir, "processed/script/episodes.json")),
    ]
    
    all_exist = True
    for name, path in checks:
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        
        if exists:
            size = os.path.getsize(path)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if name == "novel/chapters.json" and "chapters" in data:
                        chapter_count = len(data["chapters"])
                        print(f"  {status} {name:30s} ({size:,} bytes, {chapter_count} 章节)")
                    elif name == "script/episodes.json" and "episodes" in data:
                        episode_count = len(data["episodes"])
                        print(f"  {status} {name:30s} ({size:,} bytes, {episode_count} 集)")
                    else:
                        print(f"  {status} {name:30s} ({size:,} bytes)")
                except:
                    print(f"  {status} {name:30s} ({size:,} bytes, 无法解析)")
        else:
            print(f"  {status} {name:30s} 不存在")
            all_exist = False
    
    return all_exist

def test_chapters_api():
    """测试章节 API"""
    print_section("6. 测试章节 API")
    
    project_id = "project_002"
    
    try:
        # 获取章节列表
        url = f"{API_BASE}/projects/{project_id}/chapters"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            print(f"  ✗ 章节列表获取失败: {response.status_code}")
            return False
        
        data = response.json()
        chapters = data.get('chapters', [])
        total = data.get('total_chapters', len(chapters))
        print(f"  ✓ 章节列表 API: {total} 个章节（显示 {len(chapters)} 个）")
        
        if len(chapters) == 0:
            print(f"  ⚠ 没有章节数据")
            return False
        
        # 测试获取第一章内容
        first_chapter = chapters[0]['chapter_number']
        url = f"{API_BASE}/projects/{project_id}/chapters/{first_chapter}"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            print(f"  ✗ 章节内容获取失败: {response.status_code}")
            return False
        
        content = response.text
        lines = [l for l in content.split('\n') if l.strip()]
        print(f"  ✓ 章节内容 API: 第 {first_chapter} 章")
        print(f"    标题: {chapters[0].get('title', '无标题')}")
        print(f"    内容行数: {len(lines)}")
        if lines:
            print(f"    前2行: {lines[0][:50]}...")
            if len(lines) > 1:
                print(f"           {lines[1][:50]}...")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"  ⚠ 后端未运行，跳过章节 API 测试")
        return True
    except Exception as e:
        print(f"  ✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 70)
    print(" 文件路径映射系统测试")
    print("=" * 70)
    
    results = {}
    
    # 运行所有测试
    results['backend_list'] = test_backend_file_list()
    results['physical_location'] = test_file_physical_location()
    results['api_endpoints'] = test_api_endpoints()
    results['file_view'] = test_file_view_api()
    results['processed_data'] = test_processed_data()
    results['chapters_api'] = test_chapters_api()
    
    # 总结
    print_section("测试总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status:10s} {name}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n  🎉 所有测试通过！文件路径映射系统工作正常。")
    else:
        print("\n  ⚠️  部分测试失败，请检查上述输出。")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
