"""
Test Helper Utilities
测试辅助工具：统一管理测试输出和临时文件

用于测试阶段输出中间结果供人工检查，生产环境不使用。
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TestOutputManager:
    """
    测试输出管理器
    
    统一管理测试脚本的临时文件输出，方便人工检查工具处理结果。
    所有输出文件存放在 output/temp/<timestamp>/<tool_name>/ 目录下。
    
    Features:
    - 自动创建时间戳目录
    - 创建符号链接指向最新结果（output/temp/latest）
    - 提供文本和JSON保存方法
    - 自动记录日志
    
    Example:
        >>> output = TestOutputManager("novel_importer")
        >>> output.save_text("normalized.txt", "规范化后的文本...")
        >>> output.save_json("metadata.json", {"encoding": "GBK"})
        >>> print(output.get_path())  # output/temp/20260208_143025/novel_importer
    """
    
    def __init__(self, tool_name: str, base_dir: Optional[Path] = None):
        """
        初始化测试输出管理器
        
        Args:
            tool_name: 工具名称（如 "01_novel_importer"）
            base_dir: 输出基础目录（默认：output/temp）
        """
        self.tool_name = tool_name
        
        # 创建时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if base_dir is None:
            # 默认使用项目根目录下的 output/temp
            base_dir = Path(__file__).parent.parent.parent / "output" / "temp"
        
        self.output_dir = base_dir / timestamp / tool_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建或更新符号链接指向最新结果
        latest_link = base_dir / "latest"
        try:
            if latest_link.exists() or latest_link.is_symlink():
                latest_link.unlink()
            latest_link.symlink_to(timestamp, target_is_directory=True)
            logger.debug(f"Created symlink: {latest_link} -> {timestamp}")
        except OSError as e:
            logger.warning(f"Failed to create symlink: {e}")
        
        logger.info(f"Test output directory created: {self.output_dir}")
    
    def save_text(self, filename: str, content: str, log: bool = True) -> Path:
        """
        保存文本文件
        
        Args:
            filename: 文件名（如 "normalized_text.txt"）
            content: 文本内容
            log: 是否打印日志
        
        Returns:
            Path: 保存的文件路径
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if log:
            logger.info(f"Saved text file: {filepath}")
            print(f"   💾 已保存: {filepath}")
        
        return filepath
    
    def save_json(self, filename: str, data: Dict[str, Any], log: bool = True) -> Path:
        """
        保存JSON文件
        
        Args:
            filename: 文件名（如 "metadata.json"）
            data: JSON数据（字典）
            log: 是否打印日志
        
        Returns:
            Path: 保存的文件路径
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if log:
            logger.info(f"Saved JSON file: {filepath}")
            print(f"   💾 已保存: {filepath}")
        
        return filepath
    
    def save_lines(self, filename: str, lines: list, log: bool = True) -> Path:
        """
        保存行列表为文本文件
        
        Args:
            filename: 文件名
            lines: 行列表
            log: 是否打印日志
        
        Returns:
            Path: 保存的文件路径
        """
        content = '\n'.join(str(line) for line in lines)
        return self.save_text(filename, content, log=log)
    
    def get_path(self) -> Path:
        """
        获取输出目录路径
        
        Returns:
            Path: 输出目录路径
        """
        return self.output_dir
    
    def print_summary(self, stats: Dict[str, Any]) -> None:
        """
        打印测试摘要
        
        Args:
            stats: 统计信息字典
        """
        print("\n" + "="*60)
        print(f"📊 测试摘要 - {self.tool_name}")
        print("="*60)
        
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\n📁 输出目录: {self.output_dir}")
        print(f"💡 快速查看: ls {self.output_dir}")
        print("="*60 + "\n")


def print_section(title: str, char: str = "=") -> None:
    """
    打印分节标题
    
    Args:
        title: 标题文本
        char: 分隔符字符
    """
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(f"{char * 60}\n")


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
    
    Returns:
        str: 格式化的大小（如 "1.5MB"）
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"
