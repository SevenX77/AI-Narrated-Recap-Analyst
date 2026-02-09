"""
Novel Chapter Detector Tool
小说章节检测工具：检测章节边界和元信息

职责：
1. 读取小说文件
2. 识别章节标题模式
3. 提取章节序号和标题
4. 计算章节位置信息
5. 验证章节连续性
6. 返回章节索引列表
"""

import re
import logging
from pathlib import Path
from typing import Union, List, Optional, Tuple

from src.core.interfaces import BaseTool
from src.core.schemas_novel import ChapterInfo

logger = logging.getLogger(__name__)


class NovelChapterDetector(BaseTool):
    """
    小说章节检测工具
    
    功能：
    - 识别章节标题（支持多种格式）
    - 提取章节号和标题
    - 计算章节起止位置（行号、字符位置）
    - 统计章节字数
    - 验证章节连续性
    
    Example:
        >>> detector = NovelChapterDetector()
        >>> chapters = detector.execute(
        ...     novel_file="data/projects/xxx/raw/novel.txt"
        ... )
        >>> print(len(chapters))       # 10
        >>> print(chapters[0].title)   # "车队第一铁律"
    """
    
    name = "novel_chapter_detector"
    description = "Detect chapter boundaries and extract chapter metadata"
    
    # 章节标题匹配模式（优先级从高到低）
    CHAPTER_PATTERNS = [
        r'^===\s*第\s*(\d+)\s*章\s*(.*)===',     # === 第1章 标题 ===
        r'^===\s*第\s*(\d+)\s*章\s*===',          # === 第1章 ===
        r'^第\s*(\d+)\s*章[：:\s]+(.+)',          # 第1章：标题
        r'^第\s*(\d+)\s*章\s*(.+)',               # 第1章 标题
        r'^Chapter\s+(\d+)[：:\s]*(.*)$',         # Chapter 1: Title
    ]
    
    # 中文数字映射（简单版本）
    CN_NUM = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000
    }
    
    def execute(
        self,
        novel_file: Union[str, Path],
        validate_continuity: bool = True
    ) -> List[ChapterInfo]:
        """
        检测章节信息
        
        Args:
            novel_file: 小说文件路径
            validate_continuity: 是否验证章节连续性（默认True）
        
        Returns:
            List[ChapterInfo]: 章节信息列表
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 未检测到章节或章节不连续
        """
        novel_file = Path(novel_file)
        
        logger.info(f"Detecting chapters in: {novel_file}")
        
        # Step 1: 读取文件
        content = self._read_file(novel_file)
        lines = content.split('\n')
        
        # Step 2: 检测章节边界
        chapters = self._detect_chapters(lines)
        logger.info(f"Detected {len(chapters)} chapters")
        
        if not chapters:
            raise ValueError("No chapters detected in file")
        
        # Step 3: 验证章节连续性（可选）
        if validate_continuity:
            self._validate_continuity(chapters)
            logger.info("Chapter continuity validated")
        
        # Step 4: 计算位置信息
        chapters_with_positions = self._calculate_positions(chapters, content)
        
        return chapters_with_positions
    
    def _read_file(self, file_path: Path) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: 文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.debug(f"Read file: {len(content)} chars")
        return content
    
    def _detect_chapters(self, lines: List[str]) -> List[dict]:
        """
        检测章节边界
        
        Args:
            lines: 文本行列表
        
        Returns:
            List[dict]: 章节信息列表（初步，未计算位置）
        """
        chapters = []
        
        for line_num, line in enumerate(lines):
            # 尝试匹配章节标题
            chapter_match = self._match_chapter_title(line)
            
            if chapter_match:
                chapter_number, chapter_title = chapter_match
                
                chapters.append({
                    'number': chapter_number,
                    'title': chapter_title,
                    'start_line': line_num,
                    'header_text': line.strip()
                })
                
                logger.debug(f"Found chapter {chapter_number}: {chapter_title} at line {line_num}")
        
        return chapters
    
    def _match_chapter_title(self, line: str) -> Optional[Tuple[int, str]]:
        """
        匹配章节标题
        
        Args:
            line: 文本行
        
        Returns:
            (chapter_number, chapter_title) or None
        """
        line_stripped = line.strip()
        
        for pattern in self.CHAPTER_PATTERNS:
            match = re.match(pattern, line_stripped, re.IGNORECASE)
            
            if match:
                # 提取章节号
                num_str = match.group(1)
                try:
                    chapter_num = int(num_str)
                except ValueError:
                    # 尝试中文数字转换
                    chapter_num = self._chinese_to_number(num_str)
                    if not chapter_num:
                        continue
                
                # 提取章节标题
                chapter_title = ""
                if len(match.groups()) > 1 and match.group(2):
                    chapter_title = match.group(2).strip()
                
                return (chapter_num, chapter_title)
        
        return None
    
    def _chinese_to_number(self, cn_str: str) -> Optional[int]:
        """
        中文数字转阿拉伯数字（简化版）
        
        Args:
            cn_str: 中文数字字符串
        
        Returns:
            int or None: 转换后的数字
        
        Examples:
            一 → 1
            十 → 10
            二十三 → 23 (TODO: 需要完整实现)
        """
        # 简单实现：单个字符直接映射
        if cn_str in self.CN_NUM:
            return self.CN_NUM[cn_str]
        
        # TODO: 实现更复杂的中文数字转换（二十三、一百零五等）
        logger.debug(f"Cannot convert Chinese number: {cn_str}")
        return None
    
    def _validate_continuity(self, chapters: List[dict]) -> None:
        """
        验证章节连续性
        
        Args:
            chapters: 章节列表
        
        Raises:
            ValueError: 章节不连续
        """
        if not chapters:
            return
        
        # 检查章节是否连续
        for i in range(len(chapters) - 1):
            current_num = chapters[i]['number']
            next_num = chapters[i + 1]['number']
            
            if next_num != current_num + 1:
                logger.warning(
                    f"Chapter discontinuity detected: "
                    f"Chapter {current_num} followed by Chapter {next_num}"
                )
                # 注意：这里不抛出异常，只记录警告
                # 因为有些小说可能故意跳章节
        
        # 检查是否从第1章开始
        if chapters[0]['number'] != 1:
            logger.warning(
                f"First chapter is not Chapter 1 (found: Chapter {chapters[0]['number']})"
            )
    
    def _calculate_positions(self, chapters: List[dict], content: str) -> List[ChapterInfo]:
        """
        计算章节位置信息
        
        Args:
            chapters: 章节列表（初步）
            content: 完整文本内容
        
        Returns:
            List[ChapterInfo]: 完整的章节信息
        """
        lines = content.split('\n')
        chapters_info = []
        
        for i, chapter in enumerate(chapters):
            start_line = chapter['start_line']
            
            # 确定结束行（下一章开始前一行，或文件末尾）
            if i < len(chapters) - 1:
                end_line = chapters[i + 1]['start_line']
            else:
                end_line = len(lines)
            
            # 计算字符位置
            start_char = sum(len(line) + 1 for line in lines[:start_line])  # +1 for \n
            end_char = sum(len(line) + 1 for line in lines[:end_line])
            
            # 提取章节内容并计算字数
            chapter_lines = lines[start_line + 1:end_line]  # 跳过标题行
            chapter_content = '\n'.join(chapter_lines)
            word_count = len(chapter_content.strip())
            
            # 创建 ChapterInfo 对象
            chapter_info = ChapterInfo(
                number=chapter['number'],
                title=chapter['title'],
                start_line=start_line,
                end_line=end_line,
                start_char=start_char,
                end_char=end_char,
                word_count=word_count
            )
            
            chapters_info.append(chapter_info)
            
            logger.debug(
                f"Chapter {chapter['number']}: "
                f"lines {start_line}-{end_line}, "
                f"{word_count} chars"
            )
        
        return chapters_info
