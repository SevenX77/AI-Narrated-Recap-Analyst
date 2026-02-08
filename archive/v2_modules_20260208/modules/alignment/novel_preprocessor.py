"""
Novel预处理模块

用于提取Novel简介和章节索引
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class NovelPreprocessor:
    """
    Novel预处理器
    
    功能:
        1. 提取纯净简介（移除标签、书名等无关信息）
        2. 生成章节索引（章节标题 -> 行号范围）
    """
    
    # 章节标题匹配模式
    CHAPTER_PATTERNS = [
        r'^===?\s*第[0-9零一二三四五六七八九十百千]+章\s+.*?===?$',
        r'^第[0-9零一二三四五六七八九十百千]+章[：:\s]',
        r'^Chapter\s+\d+',
        r'^\[第[0-9]+章\]',
    ]
    
    # 简介中需要排除的行模式
    EXCLUDE_PATTERNS = [
        r'^\[封面:',                    # 封面链接
        r'^Title:',                    # 标题
        r'^Author:',                   # 作者
        r'^={3,}',                     # 分隔符
        r'^简介:$',                    # "简介:"标题行
        r'^\s*$',                      # 空行
        r'^【.*?】$',                  # 纯标签行（如【题材新颖+非无脑爽文】）
        r'又有书名[：:]',              # 书名行
        r'书名[：:]',                  # 书名行
    ]
    
    def __init__(self):
        self.chapter_regex = [re.compile(p, re.MULTILINE) for p in self.CHAPTER_PATTERNS]
        self.exclude_regex = [re.compile(p, re.IGNORECASE) for p in self.EXCLUDE_PATTERNS]
    
    def extract_introduction(self, novel_text: str) -> Tuple[str, int]:
        """
        提取纯净简介
        
        Args:
            novel_text: Novel完整文本
        
        Returns:
            (introduction_text, chapter_1_line_number)
            - introduction_text: 过滤后的纯净简介
            - chapter_1_line_number: 第1章的行号
        """
        lines = novel_text.split('\n')
        
        # Step 1: 定位第1章
        chapter_1_line = self._find_first_chapter(lines)
        
        if chapter_1_line == -1:
            logger.warning("未找到第1章标题，使用全文前100行作为简介区域")
            chapter_1_line = min(100, len(lines))
        
        logger.info(f"定位第1章: 行号 {chapter_1_line}")
        
        # Step 2: 提取简介候选区域（第1章之前）
        intro_lines = lines[:chapter_1_line]
        
        # Step 3: 过滤无关行
        filtered_lines = []
        for line in intro_lines:
            if not self._should_exclude_line(line):
                filtered_lines.append(line.strip())
        
        # Step 4: 合并为文本
        introduction = '\n'.join(filtered_lines)
        
        logger.info(f"简介提取完成: 原始{len(intro_lines)}行 → 过滤后{len(filtered_lines)}行")
        
        return introduction, chapter_1_line
    
    def build_chapter_index(self, novel_text: str, start_line: int = 0) -> List[Dict]:
        """
        构建章节索引
        
        Args:
            novel_text: Novel完整文本
            start_line: 开始扫描的行号（通常是第1章所在行）
        
        Returns:
            章节索引列表
            [
                {
                    "chapter_number": 1,
                    "chapter_title": "第1章 车队第一铁律",
                    "start_line": 24,
                    "end_line": 450,
                    "line_count": 426
                },
                ...
            ]
        """
        lines = novel_text.split('\n')
        chapters = []
        
        current_chapter = None
        
        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            
            # 检查是否是章节标题
            chapter_info = self._parse_chapter_title(line, i)
            
            if chapter_info:
                # 如果已有当前章节，先关闭它
                if current_chapter:
                    current_chapter['end_line'] = i - 1
                    current_chapter['line_count'] = current_chapter['end_line'] - current_chapter['start_line'] + 1
                    chapters.append(current_chapter)
                
                # 开始新章节
                current_chapter = chapter_info
        
        # 关闭最后一个章节
        if current_chapter:
            current_chapter['end_line'] = len(lines) - 1
            current_chapter['line_count'] = current_chapter['end_line'] - current_chapter['start_line'] + 1
            chapters.append(current_chapter)
        
        logger.info(f"章节索引构建完成: 共{len(chapters)}章")
        
        return chapters
    
    def _find_first_chapter(self, lines: List[str]) -> int:
        """定位第1章的行号"""
        for i, line in enumerate(lines):
            for regex in self.chapter_regex:
                if regex.search(line):
                    # 检查是否是第1章
                    if self._is_first_chapter(line):
                        return i
        return -1
    
    def _is_first_chapter(self, line: str) -> bool:
        """判断是否是第1章"""
        first_chapter_patterns = [
            r'第[1一]章',
            r'Chapter\s+1\b',
            r'\[第1章\]',
        ]
        for pattern in first_chapter_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _should_exclude_line(self, line: str) -> bool:
        """判断一行是否应该被排除"""
        line = line.strip()
        
        # 排除空行
        if not line:
            return True
        
        # 匹配排除模式
        for regex in self.exclude_regex:
            if regex.search(line):
                return True
        
        return False
    
    def _parse_chapter_title(self, line: str, line_number: int) -> Optional[Dict]:
        """
        解析章节标题
        
        Returns:
            {
                "chapter_number": 1,
                "chapter_title": "第1章 车队第一铁律",
                "start_line": 24
            }
            如果不是章节标题，返回None
        """
        for regex in self.chapter_regex:
            if regex.search(line):
                # 提取章节号
                chapter_num = self._extract_chapter_number(line)
                return {
                    "chapter_number": chapter_num,
                    "chapter_title": line,
                    "start_line": line_number
                }
        return None
    
    def _extract_chapter_number(self, title: str) -> int:
        """从章节标题中提取章节号"""
        # 尝试提取阿拉伯数字
        match = re.search(r'第(\d+)章', title)
        if match:
            return int(match.group(1))
        
        # 尝试提取中文数字
        chinese_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '零': 0
        }
        
        match = re.search(r'第([一二三四五六七八九十零百千]+)章', title)
        if match:
            chinese = match.group(1)
            # 简单处理：只处理一到十
            if chinese in chinese_nums:
                return chinese_nums[chinese]
            elif chinese == '十一':
                return 11
            elif chinese == '十二':
                return 12
            # 更复杂的中文数字转换可以后续扩展
        
        # 尝试Chapter格式
        match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # 默认返回0
        return 0


def preprocess_novel_file(
    novel_path: str,
    output_intro_path: str,
    output_index_path: str
) -> Dict:
    """
    预处理Novel文件的便捷函数
    
    Args:
        novel_path: Novel原始文件路径
        output_intro_path: 输出简介文件路径
        output_index_path: 输出章节索引文件路径
    
    Returns:
        处理结果摘要
    """
    import json
    
    logger.info(f"开始预处理Novel: {novel_path}")
    
    # 读取Novel文本
    with open(novel_path, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    # 初始化预处理器
    preprocessor = NovelPreprocessor()
    
    # 提取简介
    introduction, chapter_1_line = preprocessor.extract_introduction(novel_text)
    
    # 构建章节索引
    chapter_index = preprocessor.build_chapter_index(novel_text, chapter_1_line)
    
    # 保存简介
    Path(output_intro_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_intro_path, 'w', encoding='utf-8') as f:
        f.write(introduction)
    
    # 保存章节索引
    Path(output_index_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_index_path, 'w', encoding='utf-8') as f:
        json.dump(chapter_index, f, ensure_ascii=False, indent=2)
    
    result = {
        "novel_path": novel_path,
        "introduction_length": len(introduction),
        "chapter_1_line": chapter_1_line,
        "total_chapters": len(chapter_index),
        "output_intro": output_intro_path,
        "output_index": output_index_path
    }
    
    logger.info(f"✅ Novel预处理完成:")
    logger.info(f"   简介长度: {result['introduction_length']} 字符")
    logger.info(f"   总章节数: {result['total_chapters']}")
    logger.info(f"   输出文件: {output_intro_path}, {output_index_path}")
    
    return result
