"""
Novel Segmenter Tool
小说章节叙事分段分析工具

职责：
1. 读取指定章节内容
2. 使用LLM进行叙事分段分析
3. 生成详细的Markdown分析报告
4. 保存到项目analysis目录
"""

import logging
import re
from pathlib import Path
from typing import Union, Optional
from datetime import datetime
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.utils.prompt_loader import load_prompts
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_metadata_extractor import NovelMetadataExtractor

logger = logging.getLogger(__name__)


class NovelSegmenter(BaseTool):
    """
    小说章节叙事分段分析工具
    
    功能：
    - 使用LLM对小说章节进行叙事功能分段
    - 标注每个段落的叙事特征（功能、类型、优先级等）
    - 生成详细的Markdown分析报告
    
    Example:
        >>> segmenter = NovelSegmenter()
        >>> report_path = segmenter.execute(
        ...     novel_file="data/projects/xxx/raw/novel.txt",
        ...     chapter_number=1
        ... )
        >>> print(f"Analysis saved to: {report_path}")
    """
    
    name = "novel_segmenter"
    description = "Perform narrative segmentation analysis on novel chapters using LLM"
    
    def __init__(self, provider: str = "claude"):
        """
        初始化工具
        
        Args:
            provider: LLM Provider ("claude" | "deepseek")
                     默认使用 Claude（小说分段是复杂任务，需要高质量理解）
        """
        from src.core.llm_client_manager import get_llm_client, get_model_name
        
        self.provider = provider
        self.llm_client = get_llm_client(provider)
        self.model_name = get_model_name(provider)
        
        # 加载prompt配置
        self.prompt_config = load_prompts("novel_chapter_segmentation")
        
        # 初始化依赖工具
        self.chapter_detector = NovelChapterDetector()
        self.metadata_extractor = NovelMetadataExtractor(use_llm=False)
        
        logger.info(f"✅ NovelSegmenter initialized (provider: {provider})")
    
    def execute(
        self,
        novel_file: Union[str, Path],
        chapter_number: int,
        output_dir: Optional[Path] = None,
        model: Optional[str] = None
    ) -> Path:
        """
        执行章节分段分析
        
        Args:
            novel_file: 小说文件路径（data/projects/xxx/raw/novel.txt）
            chapter_number: 章节号（从1开始）
            output_dir: 输出目录（可选），默认为 data/projects/xxx/analysis/
            model: LLM模型名称（可选），默认使用配置文件中的模型
        
        Returns:
            Path: 生成的Markdown分析报告路径
        
        Raises:
            FileNotFoundError: 小说文件不存在
            ValueError: 章节不存在或LLM调用失败
        """
        novel_file = Path(novel_file)
        
        logger.info(f"Starting chapter segmentation analysis")
        logger.info(f"Novel file: {novel_file}")
        logger.info(f"Chapter: {chapter_number}")
        
        # Step 1: 获取章节信息
        chapter_info = self._get_chapter_info(novel_file, chapter_number)
        logger.info(f"Chapter title: {chapter_info['title']}")
        
        # Step 2: 提取章节内容
        chapter_content = self._extract_chapter_content(novel_file, chapter_info)
        logger.info(f"Chapter content: {len(chapter_content)} chars")
        
        # Step 3: 获取小说元数据
        metadata = self._get_novel_metadata(novel_file)
        logger.info(f"Novel title: {metadata['title']}, Author: {metadata['author']}")
        
        # Step 4: 调用LLM进行分析
        logger.info("Calling LLM for segmentation analysis...")
        analysis_markdown = self._analyze_with_llm(
            chapter_content=chapter_content,
            chapter_number=chapter_number,
            chapter_title=chapter_info['title'],
            novel_title=metadata['title'],
            author=metadata['author'],
            model=model
        )
        logger.info(f"LLM analysis complete: {len(analysis_markdown)} chars")
        
        # Step 5: 保存Markdown报告
        output_path = self._save_analysis(
            markdown_content=analysis_markdown,
            chapter_number=chapter_number,
            novel_file=novel_file,
            output_dir=output_dir
        )
        logger.info(f"Analysis saved to: {output_path}")
        
        return output_path
    
    def _get_chapter_info(self, novel_file: Path, chapter_number: int) -> dict:
        """
        获取章节信息
        
        Args:
            novel_file: 小说文件路径
            chapter_number: 章节号
        
        Returns:
            dict: 章节信息 {'title': str, 'start_line': int, 'end_line': int}
        
        Raises:
            ValueError: 章节不存在
        """
        # 使用 NovelChapterDetector 获取章节索引
        chapters = self.chapter_detector.execute(
            novel_file=novel_file,
            validate_continuity=False
        )
        
        # 查找指定章节
        target_chapter = None
        for chapter in chapters:
            if chapter.number == chapter_number:
                target_chapter = chapter
                break
        
        if not target_chapter:
            raise ValueError(
                f"Chapter {chapter_number} not found. "
                f"Available chapters: {[ch.number for ch in chapters]}"
            )
        
        return {
            'title': target_chapter.title,
            'start_line': target_chapter.start_line,
            'end_line': target_chapter.end_line
        }
    
    def _extract_chapter_content(self, novel_file: Path, chapter_info: dict) -> str:
        """
        提取章节内容
        
        Args:
            novel_file: 小说文件路径
            chapter_info: 章节信息
        
        Returns:
            str: 章节文本内容
        """
        with open(novel_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 提取章节内容（包含标题行）
        start_line = chapter_info['start_line']
        end_line = chapter_info['end_line']
        
        chapter_lines = lines[start_line:end_line]
        chapter_content = ''.join(chapter_lines)
        
        return chapter_content.strip()
    
    def _get_novel_metadata(self, novel_file: Path) -> dict:
        """
        获取小说元数据
        
        Args:
            novel_file: 小说文件路径
        
        Returns:
            dict: {'title': str, 'author': str}
        """
        metadata = self.metadata_extractor.execute(
            novel_file=novel_file,
            use_llm=False
        )
        
        return {
            'title': metadata.title,
            'author': metadata.author
        }
    
    def _analyze_with_llm(
        self,
        chapter_content: str,
        chapter_number: int,
        chapter_title: str,
        novel_title: str,
        author: str,
        model: Optional[str] = None
    ) -> str:
        """
        使用LLM进行章节分段分析
        
        Args:
            chapter_content: 章节内容
            chapter_number: 章节号
            chapter_title: 章节标题
            novel_title: 小说标题
            author: 作者
            model: LLM模型名称（可选）
        
        Returns:
            str: Markdown格式的分析报告
        
        Raises:
            ValueError: LLM调用失败
        """
        # 获取当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 构建user prompt
        user_prompt = self.prompt_config["user_template"].format(
            chapter_content=chapter_content,
            novel_title=novel_title,
            author=author,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            date=current_date
        )
        
        # 确定使用的模型（优先使用初始化时指定的 provider 对应的模型）
        model_name = model or self.model_name
        temperature = self.prompt_config.get("settings", {}).get("temperature", 0.3)
        max_tokens = self.prompt_config.get("settings", {}).get("max_tokens", 16000)
        
        logger.info(f"LLM settings: model={model_name}, temperature={temperature}, max_tokens={max_tokens}")
        
        try:
            response = self.llm_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.prompt_config["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            markdown_content = response.choices[0].message.content.strip()
            
            # 清理可能的markdown代码块标记
            if markdown_content.startswith('```markdown'):
                markdown_content = markdown_content[len('```markdown'):].strip()
            if markdown_content.startswith('```'):
                markdown_content = markdown_content[3:].strip()
            if markdown_content.endswith('```'):
                markdown_content = markdown_content[:-3].strip()
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise ValueError(f"LLM analysis failed: {e}")
    
    def _save_analysis(
        self,
        markdown_content: str,
        chapter_number: int,
        novel_file: Path,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        保存分析报告
        
        Args:
            markdown_content: Markdown内容
            chapter_number: 章节号
            novel_file: 小说文件路径
            output_dir: 输出目录（可选）
        
        Returns:
            Path: 保存的文件路径
        """
        # 确定输出目录
        if output_dir is None:
            # 默认：data/projects/{project_name}/analysis/
            project_dir = novel_file.parent.parent  # raw/ -> project/
            output_dir = project_dir / "analysis"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"第{chapter_number}章完整分段分析.md"
        output_path = output_dir / filename
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return output_path
