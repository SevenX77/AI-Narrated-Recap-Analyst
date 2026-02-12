"""
Novel Helper Functions
小说处理辅助函数集合

提供常用的小说处理工具函数，如章节内容提取等。
"""

import logging
from pathlib import Path
from typing import Union

from src.core.schemas_novel import ChapterInfo

logger = logging.getLogger(__name__)


def extract_chapter_content(
    novel_file: Union[str, Path],
    chapter_info: ChapterInfo,
    include_title: bool = False
) -> str:
    """
    从小说文件中提取指定章节的内容
    
    Args:
        novel_file: 小说文件路径
        chapter_info: 章节信息（来自NovelChapterDetector）
        include_title: 是否包含章节标题行（默认False）
    
    Returns:
        str: 章节文本内容
    
    Example:
        >>> from src.tools.novel_chapter_detector import NovelChapterDetector
        >>> detector = NovelChapterDetector()
        >>> chapters = detector.execute("data/projects/xxx/raw/novel.txt")
        >>> content = extract_chapter_content(
        ...     "data/projects/xxx/raw/novel.txt",
        ...     chapters[0]
        ... )
        >>> print(len(content))  # 章节字数
    """
    novel_file = Path(novel_file)
    
    if not novel_file.exists():
        raise FileNotFoundError(f"Novel file not found: {novel_file}")
    
    logger.debug(f"Extracting chapter {chapter_info.number} from {novel_file}")
    
    # 读取完整文本
    full_text = novel_file.read_text(encoding='utf-8')
    
    # 根据字符位置提取章节内容
    chapter_content = full_text[chapter_info.start_char:chapter_info.end_char]
    
    if not include_title:
        # 移除章节标题行
        lines = chapter_content.split('\n')
        
        # 检查第一行是否是章节标题
        if lines and _is_chapter_title(lines[0], chapter_info.number):
            chapter_content = '\n'.join(lines[1:]).strip()
            logger.debug(f"Removed chapter title line: {lines[0][:50]}...")
    
    logger.debug(f"Extracted chapter content: {len(chapter_content)} chars")
    
    return chapter_content


def _is_chapter_title(line: str, chapter_number: int) -> bool:
    """
    判断一行是否是章节标题
    
    Args:
        line: 文本行
        chapter_number: 期望的章节号
    
    Returns:
        bool: 是否为章节标题
    """
    line_stripped = line.strip()
    
    # 常见章节标题格式
    patterns = [
        f"=== 第{chapter_number}章",
        f"=== 第 {chapter_number} 章",
        f"第{chapter_number}章",
        f"第 {chapter_number} 章",
        f"Chapter {chapter_number}",
        f"Chapter{chapter_number}",
    ]
    
    for pattern in patterns:
        if pattern in line_stripped:
            return True
    
    return False


def get_chapter_by_number(
    novel_file: Union[str, Path],
    chapter_number: int,
    chapters: list = None
) -> tuple:
    """
    根据章节号获取章节信息和内容
    
    Args:
        novel_file: 小说文件路径
        chapter_number: 章节序号
        chapters: 章节列表（可选，如果不提供则自动检测）
    
    Returns:
        tuple: (ChapterInfo, content: str)
    
    Raises:
        ValueError: 章节不存在
    
    Example:
        >>> info, content = get_chapter_by_number(
        ...     "data/projects/xxx/raw/novel.txt",
        ...     chapter_number=1
        ... )
        >>> print(info.title)  # "车队第一铁律"
    """
    novel_file = Path(novel_file)
    
    # 如果没有提供章节列表，自动检测
    if chapters is None:
        from src.tools.novel_chapter_detector import NovelChapterDetector
        detector = NovelChapterDetector()
        chapters = detector.execute(novel_file=novel_file)
    
    # 查找指定章节
    target_chapter = None
    for chapter in chapters:
        if chapter.number == chapter_number:
            target_chapter = chapter
            break
    
    if not target_chapter:
        raise ValueError(
            f"Chapter {chapter_number} not found in {novel_file}. "
            f"Available chapters: {[c.number for c in chapters]}"
        )
    
    # 提取章节内容
    content = extract_chapter_content(
        novel_file=novel_file,
        chapter_info=target_chapter,
        include_title=False
    )
    
    return target_chapter, content
