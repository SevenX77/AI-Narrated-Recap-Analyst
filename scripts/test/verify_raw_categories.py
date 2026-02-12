"""
验证 raw/novel 与 raw/srt 分类目录及列表/兼容逻辑
不依赖 LLM，仅检查 project_manager_v2 与目录结构。
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.project_manager_v2 import project_manager_v2
from src.core.config import config


def main():
    print("=" * 60)
    print("验证 raw 分类目录 (novel / srt) 修改")
    print("=" * 60)

    # 1. 新建项目，检查 raw/novel 与 raw/srt 是否存在
    print("\n[1] 创建新项目，检查目录结构...")
    project = project_manager_v2.create_project(
        name="验证raw分类_临时",
        description="验证脚本用"
    )
    project_dir = os.path.join(config.data_dir, "projects", project.id)
    raw_base = os.path.join(project_dir, "raw")
    raw_novel = os.path.join(raw_base, "novel")
    raw_srt = os.path.join(raw_base, "srt")
    assert os.path.isdir(raw_novel), "raw/novel 目录应存在"
    assert os.path.isdir(raw_srt), "raw/srt 目录应存在"
    print("  OK raw/novel 与 raw/srt 已创建")

    # 2. 在子目录中放文件，检查 get_raw_files 返回带 category
    print("\n[2] 在 raw/novel 与 raw/srt 中放置文件，检查列表...")
    with open(os.path.join(raw_novel, "test_novel.txt"), "w", encoding="utf-8") as f:
        f.write("test")
    with open(os.path.join(raw_srt, "ep01.srt"), "w", encoding="utf-8") as f:
        f.write("1\n00:00:00,000 --> 00:00:01,000\nline\n")
    files = project_manager_v2.get_raw_files(project.id)
    by_cat = {}
    for f in files:
        c = f.get("category", "root")
        by_cat.setdefault(c, []).append(f["name"])
    assert "novel" in by_cat and "test_novel.txt" in by_cat["novel"], "应有 category=novel 的 novel 文件"
    assert "srt" in by_cat and "ep01.srt" in by_cat["srt"], "应有 category=srt 的 srt 文件"
    print("  OK get_raw_files 返回带 category 的列表:", by_cat)

    # 3. 兼容：在根 raw 下放文件，检查无 category 且仍被列出
    print("\n[3] 兼容：根 raw 下文件无 category...")
    with open(os.path.join(raw_base, "legacy.txt"), "w", encoding="utf-8") as f:
        f.write("legacy")
    files2 = project_manager_v2.get_raw_files(project.id)
    legacy = [f for f in files2 if f["name"] == "legacy.txt"]
    assert len(legacy) == 1, "根目录 legacy.txt 应被列出"
    assert "category" not in legacy[0], "根目录文件不应带 category"
    print("  OK 根目录文件已列出且无 category")

    # 4. update_sources_from_filesystem 应正确识别 novel/srt 子目录
    print("\n[4] update_sources_from_filesystem 从 novel/srt 子目录识别...")
    project_manager_v2.update_sources_from_filesystem(project.id)
    meta = project_manager_v2.get_project(project.id)
    assert meta.sources.has_novel is True, "应有 has_novel"
    assert meta.sources.has_script is True, "应有 has_script"
    print("  OK has_novel=%s has_script=%s" % (meta.sources.has_novel, meta.sources.has_script))

    # 5. 清理：删除测试项目
    print("\n[5] 清理测试项目...")
    project_manager_v2.delete_project(project.id)
    print("  OK 已删除")

    print("\n" + "=" * 60)
    print("全部检查通过")
    print("=" * 60)


if __name__ == "__main__":
    main()
