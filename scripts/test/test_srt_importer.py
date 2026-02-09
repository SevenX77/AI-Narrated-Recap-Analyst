"""
测试脚本：SrtImporter - SRT导入工具

测试目标：
1. 读取并解析SRT文件
2. 编码检测与统一
3. SRT格式验证
4. 保存到项目目录
5. 返回正确的SrtImportResult
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tools.srt_importer import SrtImporter
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_srt_importer():
    """测试SrtImporter工具"""
    
    # ========== 测试配置 ==========
    # 使用归档中的SRT文件作为测试数据
    test_srt_file = project_root / "archive/v2_data_20260208/projects/with_novel/末哥超凡公路/raw/ep01.srt"
    test_project_name = "末哥超凡公路_test"
    
    if not test_srt_file.exists():
        logger.error(f"Test SRT file not found: {test_srt_file}")
        logger.info("Please check the path or use another SRT file")
        return
    
    logger.info("=" * 80)
    logger.info("测试 SrtImporter - SRT导入工具")
    logger.info("=" * 80)
    
    # ========== 创建工具实例 ==========
    importer = SrtImporter()
    logger.info(f"Tool: {importer.name}")
    logger.info(f"Description: {importer.description}")
    
    # ========== 执行导入 ==========
    try:
        logger.info(f"\n{'=' * 80}")
        logger.info("开始导入SRT文件...")
        logger.info(f"Source: {test_srt_file}")
        logger.info(f"Project: {test_project_name}")
        
        result = importer.execute(
            source_file=test_srt_file,
            project_name=test_project_name,
            save_to_disk=True,
            include_entries=True
        )
        
        logger.info(f"\n{'=' * 80}")
        logger.info("✅ 导入成功！")
        logger.info(f"{'=' * 80}")
        
        # ========== 输出结果 ==========
        logger.info("\n📊 导入结果：")
        logger.info(f"  - 保存路径: {result.saved_path}")
        logger.info(f"  - 原始路径: {result.original_path}")
        logger.info(f"  - 项目名称: {result.project_name}")
        logger.info(f"  - 集数名称: {result.episode_name}")
        logger.info(f"  - 文件编码: {result.encoding}")
        logger.info(f"  - 条目数量: {result.entry_count}")
        logger.info(f"  - 总时长: {result.total_duration}")
        logger.info(f"  - 文件大小: {result.file_size} bytes ({result.file_size / 1024:.2f} KB)")
        logger.info(f"  - 规范化操作: {', '.join(result.normalization_applied)}")
        
        # ========== 验证条目 ==========
        if result.entries:
            logger.info(f"\n📝 SRT条目示例（前5条）：")
            for i, entry in enumerate(result.entries[:5], 1):
                logger.info(f"\n  条目 {i}:")
                logger.info(f"    序号: {entry.index}")
                logger.info(f"    时间: {entry.start_time} --> {entry.end_time}")
                logger.info(f"    文本: {entry.text[:50]}{'...' if len(entry.text) > 50 else ''}")
        
        # ========== 验证保存的文件 ==========
        saved_path = Path(result.saved_path)
        if saved_path.exists():
            logger.info(f"\n✅ 文件已保存到: {saved_path}")
            logger.info(f"   文件大小: {saved_path.stat().st_size} bytes")
        else:
            logger.warning(f"\n⚠️  保存的文件不存在: {saved_path}")
        
        # ========== 统计信息 ==========
        logger.info(f"\n{'=' * 80}")
        logger.info("📈 统计信息：")
        logger.info(f"  - 总条目数: {result.entry_count}")
        logger.info(f"  - 平均每条时长: 约 {_calculate_avg_duration(result.entries):.1f} 秒")
        logger.info(f"  - 总字符数: {sum(len(e.text) for e in result.entries) if result.entries else 0}")
        
        logger.info(f"\n{'=' * 80}")
        logger.info("🎉 测试完成！SrtImporter 工作正常")
        logger.info(f"{'=' * 80}\n")
        
        return result
    
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise


def _calculate_avg_duration(entries):
    """计算平均每条时长（秒）"""
    if not entries or len(entries) < 2:
        return 0.0
    
    def time_to_seconds(time_str):
        """将 HH:MM:SS,mmm 转换为秒"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split(',')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1])
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    
    total_duration = 0
    for entry in entries:
        start = time_to_seconds(entry.start_time)
        end = time_to_seconds(entry.end_time)
        total_duration += (end - start)
    
    return total_duration / len(entries)


if __name__ == "__main__":
    test_srt_importer()
