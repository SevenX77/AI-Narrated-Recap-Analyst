"""
Novel Chapter Processor
小说章节处理工具：提取简介、按章节拆分文件
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from src.core.interfaces import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class NovelMetadata:
    """小说元数据"""
    title: str
    author: str
    tags: List[str]
    introduction: str
    total_chapters: int


@dataclass
class ChapterGroup:
    """章节组"""
    filename: str  # chpt_0001-0010.md
    start_chapter: int
    end_chapter: int
    content: str
    chapter_titles: List[str]


class NovelChapterProcessor(BaseTool):
    """
    小说章节处理工具
    
    功能：
    1. 提取简介和元数据（标题、作者、标签）
    2. 按章节拆分小说（每10章一个文件）
    3. 生成 chpt_0000.md（简介）和 chpt_XXXX-YYYY.md（章节组）
    4. 使用Markdown格式，包含标题和段落标记
    """
    
    name = "novel_chapter_processor"
    description = "Process novel into introduction and chapter groups"
    
    # 章节匹配模式
    CHAPTER_PATTERNS = [
        r'^===\s*第\s*(\d+)\s*章\s*(.*)===',  # === 第1章 标题 ===
        r'^第\s*([零一二三四五六七八九十百千万\d]+)\s*章[：:\s]+(.*)',  # 第一章：标题
    ]
    
    # 中文数字转换
    CN_NUM = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000
    }
    
    def __init__(self, chapters_per_file: int = 10):
        """
        Args:
            chapters_per_file: 每个文件包含的章节数（默认10章）
        """
        self.chapters_per_file = chapters_per_file
    
    def execute(self, 
                novel_text: str, 
                output_dir: Path,
                introduction_override: str = None) -> Dict[str, Any]:
        """
        执行章节处理
        
        Args:
            novel_text: 原始小说文本（已分段处理）
            output_dir: 输出目录（novel/）
            introduction_override: 外部提供的简介（已过滤），如果提供则使用此简介而不是从文本中提取
        
        Returns:
            处理结果统计
        """
        logger.info("Starting novel chapter processing")
        
        # 1. 解析文本结构
        metadata, chapters_content = self._parse_novel_structure(novel_text)
        
        # 2. 生成简介文件（chpt_0000.md）
        intro_file = output_dir / "chpt_0000.md"
        # 使用外部提供的过滤后的简介，或回退到提取的简介
        introduction_to_write = introduction_override if introduction_override is not None else metadata.introduction
        self._write_introduction(intro_file, introduction_to_write, metadata.title)
        logger.info(f"Created introduction file: {intro_file}")
        
        # 3. 按章节分组
        chapter_groups = self._group_chapters(chapters_content)
        
        # 4. 写入章节文件
        for group in chapter_groups:
            chapter_file = output_dir / group.filename
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(group.content)
            logger.info(f"Created chapter file: {chapter_file} ({len(group.chapter_titles)} chapters)")
        
        # 5. 生成处理报告
        report = {
            "total_chapters": metadata.total_chapters,
            "introduction_file": "chpt_0000.md",
            "chapter_files": [g.filename for g in chapter_groups],
            "chapters_per_file": self.chapters_per_file,
            "metadata": {
                "title": metadata.title,
                "author": metadata.author,
                "tags": metadata.tags
            }
        }
        
        # 保存报告
        import json
        report_file = output_dir / "processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processing complete: {len(chapter_groups)} chapter files created")
        return report
    
    def _parse_novel_structure(self, text: str) -> Tuple[NovelMetadata, List[Dict[str, Any]]]:
        """
        解析小说结构
        
        Returns:
            (metadata, chapters_content)
        """
        lines = text.split('\n')
        
        # 提取元数据
        metadata = self._extract_metadata(lines)
        
        # 提取章节内容
        chapters_content = self._extract_chapters(lines)
        
        metadata.total_chapters = len(chapters_content)
        
        return metadata, chapters_content
    
    def _extract_metadata(self, lines: List[str]) -> NovelMetadata:
        """提取元数据：标题、作者、标签、简介"""
        title = ""
        author = ""
        tags = []
        introduction_lines = []
        
        in_introduction = False
        metadata_end = False
        
        for i, line in enumerate(lines):
            # 跳过封面链接
            if line.startswith('[封面:'):
                continue
            
            # 提取标题
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
                continue
            
            # 提取作者
            if line.startswith('Author:'):
                author = line.replace('Author:', '').strip()
                continue
            
            # 检测简介开始
            if line.strip() == '简介:':
                in_introduction = True
                continue
            
            # 检测分隔符（简介结束）
            if '========' in line or line.startswith('==='):
                if in_introduction:
                    metadata_end = True
                    break
                continue
            
            # 提取简介内容
            if in_introduction and line.strip():
                # 检测标签行
                if '【' in line and '】' in line:
                    tags = self._extract_tags(line)
                    continue
                
                # 添加简介行
                introduction_lines.append(line.strip())
        
        # 合并简介（段内连续，段间双空行）
        introduction = '\n\n'.join(introduction_lines) if introduction_lines else ""
        
        return NovelMetadata(
            title=title,
            author=author,
            tags=tags,
            introduction=introduction,
            total_chapters=0  # 稍后填充
        )
    
    def _extract_tags(self, text: str) -> List[str]:
        """
        从文本中提取标签
        
        Example:
            【题材新颖+非无脑爽文+非无敌+序列魔药】
            → ["题材新颖", "非无脑爽文", "非无敌", "序列魔药"]
        """
        pattern = r'【([^】]+)】'
        matches = re.findall(pattern, text)
        
        tags = []
        for match in matches:
            # 按 + 分割
            parts = match.split('+')
            tags.extend([p.strip() for p in parts if p.strip()])
        
        return tags
    
    def _extract_chapters(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        提取章节内容
        
        Returns:
            List of {
                "number": 1,
                "title": "车队第一铁律",
                "content": "..."
            }
        """
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            # 检测章节标题
            chapter_match = self._match_chapter_title(line)
            
            if chapter_match:
                # 保存上一章
                if current_chapter is not None:
                    current_chapter['content'] = '\n\n'.join(current_content)
                    chapters.append(current_chapter)
                
                # 开始新章节
                chapter_num, chapter_title = chapter_match
                current_chapter = {
                    'number': chapter_num,
                    'title': chapter_title,
                    'header': line.strip()
                }
                current_content = []  # 不包含标题行（标题将在Markdown中单独渲染）
            
            elif current_chapter is not None:
                # 添加到当前章节内容
                if line.strip():
                    current_content.append(line.strip())
                elif current_content and current_content[-1] != '':
                    # 保留段落间的空行（用空字符串表示）
                    current_content.append('')
        
        # 保存最后一章
        if current_chapter is not None:
            current_chapter['content'] = '\n\n'.join(current_content)
            chapters.append(current_chapter)
        
        logger.info(f"Extracted {len(chapters)} chapters")
        return chapters
    
    def _match_chapter_title(self, line: str) -> Optional[Tuple[int, str]]:
        """
        匹配章节标题
        
        Returns:
            (chapter_number, chapter_title) or None
        """
        for pattern in self.CHAPTER_PATTERNS:
            match = re.match(pattern, line.strip())
            if match:
                num_str = match.group(1)
                title = match.group(2).strip() if len(match.groups()) > 1 else ""
                
                # 转换章节号
                try:
                    # 尝试直接转换数字
                    chapter_num = int(num_str)
                except ValueError:
                    # 尝试中文数字转换
                    chapter_num = self._chinese_to_number(num_str)
                
                if chapter_num:
                    return (chapter_num, title)
        
        return None
    
    def _chinese_to_number(self, cn_str: str) -> Optional[int]:
        """
        中文数字转阿拉伯数字（简化版）
        
        Examples:
            一 → 1
            十 → 10
            二十三 → 23
        """
        # 简单实现，只处理常见情况
        if cn_str in self.CN_NUM:
            return self.CN_NUM[cn_str]
        
        # TODO: 实现更复杂的中文数字转换
        return None
    
    def _group_chapters(self, chapters: List[Dict[str, Any]]) -> List[ChapterGroup]:
        """
        按章节分组（每10章一组）
        
        Returns:
            List of ChapterGroup
        """
        groups = []
        
        for i in range(0, len(chapters), self.chapters_per_file):
            group_chapters = chapters[i:i + self.chapters_per_file]
            
            start_num = group_chapters[0]['number']
            end_num = group_chapters[-1]['number']
            
            # 生成文件名: chpt_0001-0010.md
            filename = f"chpt_{start_num:04d}-{end_num:04d}.md"
            
            # 合并章节内容（Markdown格式）
            content_parts = []
            chapter_titles = []
            
            for chapter in group_chapters:
                # 添加章节标题（Markdown H2）
                title_line = f"## 第{chapter['number']}章 {chapter['title']}"
                content_parts.append(title_line)
                content_parts.append("")  # 空行
                
                # 添加章节内容
                content_parts.append(chapter['content'])
                
                chapter_titles.append(f"第{chapter['number']}章 {chapter['title']}")
            
            content = '\n\n'.join(content_parts)
            
            groups.append(ChapterGroup(
                filename=filename,
                start_chapter=start_num,
                end_chapter=end_num,
                content=content,
                chapter_titles=chapter_titles
            ))
        
        return groups
    
    def _write_introduction(self, filepath: Path, introduction: str, novel_title: str = ""):
        """写入简介文件（Markdown格式）"""
        with open(filepath, 'w', encoding='utf-8') as f:
            # 写入Markdown标题
            if novel_title:
                f.write(f"# {novel_title}\n\n")
                f.write("## 简介\n\n")
            
            # 写入简介内容（段落之间已有双换行）
            f.write(introduction)


class MetadataExtractor(BaseTool):
    """
    元数据提取工具
    
    从小说文本中提取元数据并更新 metadata.json
    使用 LLM 智能过滤简介内容
    """
    
    name = "metadata_extractor"
    description = "Extract novel metadata (title, author, tags) with LLM-powered introduction filtering"
    
    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: 是否使用 LLM 智能过滤简介（推荐开启）
        """
        self.use_llm = use_llm
        self.llm_client = None
        self.prompt_config = None
        
        if self.use_llm:
            try:
                from openai import OpenAI
                from src.core.config import config
                from src.utils.prompt_loader import load_prompts
                
                # 检查API key是否可用
                if config.llm.api_key:
                    self.llm_client = OpenAI(
                        api_key=config.llm.api_key,
                        base_url=config.llm.base_url
                    )
                    self.prompt_config = load_prompts("introduction_extraction")
                    logger.info("LLM introduction filtering enabled")
                else:
                    logger.warning("API key not found, falling back to rule-based filtering")
                    self.use_llm = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}, falling back to rule-based filtering")
                self.use_llm = False
    
    def execute(self, novel_text: str) -> Dict[str, Any]:
        """
        提取元数据
        
        Returns:
            {
                "novel": {
                    "title": "...",
                    "author": "...",
                    "tags": [...],
                    "introduction": "...",
                    "chapters": {...}
                }
            }
        """
        lines = novel_text.split('\n')
        
        title = ""
        author = ""
        tags = []
        raw_introduction_lines = []
        
        in_introduction = False
        
        # 第一遍：提取所有内容
        for line in lines:
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
            elif line.startswith('Author:'):
                author = line.replace('Author:', '').strip()
            elif line.strip() == '简介:':
                in_introduction = True
            elif '========' in line or line.startswith('=== 第'):
                if in_introduction:
                    break
            elif in_introduction and line.strip():
                # 提取标签
                if '【' in line and '】' in line:
                    tags = self._extract_tags(line)
                
                # 收集所有简介行（包括标签行和元信息）
                raw_introduction_lines.append(line.strip())
        
        raw_introduction = '\n'.join(raw_introduction_lines)
        
        # 使用 LLM 智能过滤（如果启用且可用）
        if self.use_llm and self.llm_client and raw_introduction:
            try:
                filtered_introduction = self._filter_introduction_with_llm(raw_introduction)
                logger.info(f"LLM filtered introduction: {len(raw_introduction)} → {len(filtered_introduction)} chars")
            except Exception as e:
                logger.warning(f"LLM filtering failed, using fallback: {e}")
                filtered_introduction = self._filter_introduction_rules(raw_introduction_lines)
        else:
            # 降级方案：使用规则过滤
            if self.use_llm:
                logger.info("LLM not available, using rule-based filtering")
            filtered_introduction = self._filter_introduction_rules(raw_introduction_lines)
        
        return {
            "novel": {
                "title": title,
                "author": author,
                "tags": tags,
                "introduction": filtered_introduction
            }
        }
    
    def _filter_introduction_with_llm(self, raw_text: str) -> str:
        """
        使用 LLM 智能过滤简介内容
        
        Args:
            raw_text: 原始简介文本（可能包含标签、元信息等）
        
        Returns:
            过滤后的纯净简介文本
        """
        user_prompt = self.prompt_config["user_template"].format(
            introduction_text=raw_text
        )
        
        response = self.llm_client.chat.completions.create(
            model=self.prompt_config.get("settings", {}).get("model", "deepseek-chat"),
            messages=[
                {"role": "system", "content": self.prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.prompt_config.get("settings", {}).get("temperature", 0.2),
            max_tokens=self.prompt_config.get("settings", {}).get("max_tokens", 1000)
        )
        
        filtered_text = response.choices[0].message.content.strip()
        
        # 清理可能的markdown格式
        filtered_text = filtered_text.replace('```', '').strip()
        
        return filtered_text
    
    def _filter_introduction_rules(self, lines: List[str]) -> str:
        """
        降级方案：使用规则过滤简介
        
        Args:
            lines: 简介行列表
        
        Returns:
            过滤后的简介
        """
        filtered_lines = []
        
        for line in lines:
            logger.debug(f"Processing line: '{line}'")
            
            # 跳过标签行
            if '【' in line and '】' in line:
                logger.debug("  -> Skipped (tags)")
                continue
            
            # 跳过"又有书名"
            if '又有书名' in line or line.startswith('又有书名：'):
                logger.debug("  -> Skipped (又有书名)")
                continue
            
            # 跳过其他元信息关键词
            meta_keywords = ['推荐票', '月票', '打赏', '订阅', '更新', '本书特点', '强推']
            if any(kw in line for kw in meta_keywords):
                logger.debug(f"  -> Skipped (meta keyword)")
                continue
            
            logger.debug("  -> Kept")
            filtered_lines.append(line)
        
        logger.info(f"Filtered {len(lines)} -> {len(filtered_lines)} lines")
        return '\n\n'.join(filtered_lines)
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        pattern = r'【([^】]+)】'
        matches = re.findall(pattern, text)
        
        tags = []
        for match in matches:
            parts = match.split('+')
            tags.extend([p.strip() for p in parts if p.strip()])
        
        return tags
