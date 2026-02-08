"""
Novel Metadata Extractor Tool
小说元数据提取工具：提取标题、作者、标签、简介

职责：
1. 读取小说文件
2. 提取基本信息（标题、作者）
3. 提取并解析标签
4. 提取原始简介
5. 智能过滤简介（LLM优先，规则降级）
6. 返回结构化的元数据
"""

import re
import logging
from pathlib import Path
from typing import Union, List, Tuple

# OpenAI 是可选依赖，LLM功能需要时才导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.core.interfaces import BaseTool
from src.core.schemas_novel import NovelMetadata
from src.core.config import config
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelMetadataExtractor(BaseTool):
    """
    小说元数据提取工具
    
    功能：
    - 提取标题、作者、标签
    - 智能过滤简介内容（移除营销文案、标签等元信息）
    - 支持 LLM 智能过滤 + 规则降级策略
    
    Example:
        >>> extractor = NovelMetadataExtractor()
        >>> metadata = extractor.execute(
        ...     novel_file="data/projects/xxx/raw/novel.txt"
        ... )
        >>> print(metadata.title)     # "超凡公路"
        >>> print(metadata.author)    # "末哥"
        >>> print(len(metadata.tags)) # 4
    """
    
    name = "novel_metadata_extractor"
    description = "Extract novel metadata with intelligent introduction filtering"
    
    # 正则表达式模式
    TAG_PATTERN = r'【([^】]+)】'  # 匹配【标签】格式
    
    def __init__(self, use_llm: bool = True, provider: str = "deepseek"):
        """
        初始化元数据提取器
        
        Args:
            use_llm: 是否使用 LLM 智能过滤简介（推荐开启）
            provider: LLM Provider ("claude" | "deepseek")，默认使用 DeepSeek（简单任务）
        """
        self.use_llm = use_llm
        self.provider = provider
        self.llm_client = None
        self.model_name = None
        self.prompt_config = None
        
        # 初始化 LLM 客户端（如果启用）
        if self.use_llm:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library not available, LLM filtering disabled")
                self.use_llm = False
            else:
                try:
                    from src.core.llm_client_manager import get_llm_client, get_model_name
                    
                    self.llm_client = get_llm_client(provider)
                    self.model_name = get_model_name(provider)
                    self.prompt_config = load_prompts("introduction_extraction")
                    logger.info(f"✅ LLM introduction filtering enabled (provider: {provider})")
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM client: {e}")
                    self.use_llm = False
    
    def execute(
        self,
        novel_file: Union[str, Path],
        use_llm: bool = None
    ) -> NovelMetadata:
        """
        提取小说元数据
        
        Args:
            novel_file: 小说文件路径（通常是 data/projects/xxx/raw/novel.txt）
            use_llm: 是否使用 LLM（None则使用初始化时的设置）
        
        Returns:
            NovelMetadata: 提取的元数据
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 缺少必填字段或提取失败
        """
        novel_file = Path(novel_file)
        
        # 确定是否使用 LLM
        if use_llm is not None:
            use_llm_this_call = use_llm and self.llm_client is not None
        else:
            use_llm_this_call = self.use_llm
        
        logger.info(f"Extracting metadata from: {novel_file}")
        logger.info(f"LLM filtering: {'enabled' if use_llm_this_call else 'disabled'}")
        
        # Step 1: 读取文件
        content = self._read_file(novel_file)
        
        # Step 2: 提取基本信息
        title, author = self._extract_basic_info(content)
        logger.info(f"Extracted - Title: {title}, Author: {author}")
        
        # Step 3: 提取原始简介（包含标签）
        raw_introduction = self._extract_raw_introduction(content)
        logger.info(f"Extracted raw introduction: {len(raw_introduction)} chars")
        
        # Step 4: 从简介中提取标签
        tags = self._extract_tags(raw_introduction)
        logger.info(f"Extracted - Tags: {tags}")
        
        # Step 5: 智能过滤简介
        if use_llm_this_call and raw_introduction:
            try:
                filtered_introduction = self._filter_introduction_with_llm(raw_introduction)
                logger.info(f"LLM filtered: {len(raw_introduction)} → {len(filtered_introduction)} chars")
            except Exception as e:
                logger.warning(f"LLM filtering failed: {e}, falling back to rules")
                filtered_introduction = self._filter_introduction_with_rules(raw_introduction)
        else:
            filtered_introduction = self._filter_introduction_with_rules(raw_introduction)
            logger.info(f"Rule filtered: {len(raw_introduction)} → {len(filtered_introduction)} chars")
        
        # Step 6: 验证结果
        if not filtered_introduction.strip():
            raise ValueError("Introduction is empty after filtering")
        
        # Step 7: 构建返回结果
        return NovelMetadata(
            title=title,
            author=author,
            tags=tags,
            introduction=filtered_introduction,
            chapter_count=None  # 由 NovelChapterDetector 填充
        )
    
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
    
    def _extract_basic_info(self, content: str) -> Tuple[str, str]:
        """
        提取标题和作者
        
        Args:
            content: 文件内容
        
        Returns:
            (title, author): 标题和作者
        
        Raises:
            ValueError: 缺少必填字段
        """
        lines = content.split('\n')
        
        title = ""
        author = ""
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Title:'):
                title = line.replace('Title:', '').strip()
            elif line.startswith('Author:'):
                author = line.replace('Author:', '').strip()
            
            # 如果都找到了，可以提前退出
            if title and author:
                break
        
        # 验证必填字段
        if not title:
            raise ValueError("Title not found in file")
        if not author:
            raise ValueError("Author not found in file")
        
        return title, author
    
    def _extract_tags(self, introduction_text: str) -> List[str]:
        """
        从简介中提取标签
        
        从【标签1+标签2+标签3】格式中提取
        注意：只从简介文本中提取，避免提取正文中的【】内容
        
        Args:
            introduction_text: 简介文本（已提取）
        
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 在简介文本的前几行查找标签（通常在开头）
        lines = introduction_text.split('\n')
        
        # 只在前5行中查找标签
        for i, line in enumerate(lines[:5]):
            matches = re.findall(self.TAG_PATTERN, line)
            
            for match in matches:
                # 按 + 分割标签
                parts = match.split('+')
                for part in parts:
                    tag = part.strip()
                    # 过滤掉过长的内容（不是真正的标签）
                    if tag and len(tag) <= 20 and tag not in tags:
                        tags.append(tag)
        
        logger.debug(f"Found {len(tags)} valid tags")
        return tags
    
    def _extract_raw_introduction(self, content: str) -> str:
        """
        提取原始简介（未过滤）
        
        从"简介:"标记到分隔符（=====）之间的内容
        
        Args:
            content: 文件内容
        
        Returns:
            str: 原始简介
        
        Raises:
            ValueError: 简介未找到
        """
        lines = content.split('\n')
        
        introduction_lines = []
        in_introduction = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # 检测简介开始
            if line_stripped == '简介:':
                in_introduction = True
                continue
            
            # 检测简介结束（遇到分隔符或章节标题）
            if in_introduction:
                if '====' in line or line.startswith('=== 第'):
                    break
                
                # 收集简介行（包括空行）
                if line_stripped:
                    introduction_lines.append(line_stripped)
        
        if not introduction_lines:
            raise ValueError("Introduction not found in file")
        
        # 合并为文本（段落之间用双换行）
        raw_introduction = '\n'.join(introduction_lines)
        
        return raw_introduction
    
    def _filter_introduction_with_llm(self, raw_text: str) -> str:
        """
        使用 LLM 智能过滤简介
        
        移除：标签、书名变体、营销文案、作者注释
        保留：世界观、主角设定、核心冲突、悬念
        
        Args:
            raw_text: 原始简介文本
        
        Returns:
            str: 过滤后的简介
        
        Raises:
            Exception: LLM 调用失败
        """
        user_prompt = self.prompt_config["user_template"].format(
            introduction_text=raw_text
        )
        
        response = self.llm_client.chat.completions.create(
            model=self.model_name or self.prompt_config.get("settings", {}).get("model", "deepseek-chat"),
            messages=[
                {"role": "system", "content": self.prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.prompt_config.get("settings", {}).get("temperature", 0.1),
            max_tokens=self.prompt_config.get("settings", {}).get("max_tokens", 1000)
        )
        
        filtered_text = response.choices[0].message.content.strip()
        
        # 清理可能的 markdown 格式
        filtered_text = filtered_text.replace('```', '').strip()
        
        return filtered_text
    
    def _filter_introduction_with_rules(self, raw_text: str) -> str:
        """
        使用规则过滤简介（降级方案）
        
        过滤规则：
        1. 移除包含【】的标签行
        2. 移除"又有书名"行
        3. 移除营销关键词行
        
        Args:
            raw_text: 原始简介文本
        
        Returns:
            str: 过滤后的简介
        """
        lines = raw_text.split('\n')
        filtered_lines = []
        
        # 营销关键词列表
        meta_keywords = [
            '推荐票', '月票', '打赏', '订阅', '更新', 
            '本书特点', '强推', '收藏', '投票'
        ]
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 跳过标签行
            if '【' in line and '】' in line:
                logger.debug(f"Skipped (tags): {line[:50]}...")
                continue
            
            # 跳过"又有书名"
            if '又有书名' in line:
                logger.debug(f"Skipped (alt title): {line[:50]}...")
                continue
            
            # 跳过营销关键词行
            if any(keyword in line for keyword in meta_keywords):
                logger.debug(f"Skipped (meta keyword): {line[:50]}...")
                continue
            
            # 保留这一行
            filtered_lines.append(line)
        
        # 合并为文本（段落之间用双换行）
        filtered_text = '\n\n'.join(filtered_lines)
        
        return filtered_text
