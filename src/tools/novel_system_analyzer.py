"""
NovelSystemAnalyzer - 小说系统元素分析工具（Phase 1）

分析小说前N章内容，识别核心系统元素并智能归类。

核心功能：
1. 快速读取多章内容（前50章）
2. 识别小说类型
3. 提取核心系统元素
4. 智能归类（避免碎片化）
5. 生成系统目录（SystemCatalog）

策略：
- 使用章节摘要而非完整内容（降低token成本）
- 参考系统类型模板，但灵活适应创新设定
- 关注与剧情推进紧密相关的元素
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.interfaces import BaseTool
from src.core.schemas_novel import SystemCategory, SystemCatalog
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelSystemAnalyzer(BaseTool):
    """
    小说系统元素分析工具
    
    分析小说前N章，识别核心系统元素并归类。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        SystemCatalog: 系统目录
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化系统分析工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        logger.info(f"NovelSystemAnalyzer initialized with {provider}/{self.model}")
    
    def execute(
        self,
        novel_path: str,
        novel_name: str = "",
        max_chapters: int = 50,
        use_chapter_detector: bool = True,
        **kwargs
    ) -> SystemCatalog:
        """
        执行系统分析
        
        Args:
            novel_path: 小说文件路径（data/projects/xxx/raw/novel.txt）
            novel_name: 小说名称
            max_chapters: 最大分析章节数（默认50）
            use_chapter_detector: 是否使用章节检测器（默认True）
            **kwargs: 其他参数
        
        Returns:
            SystemCatalog: 系统目录
        """
        logger.info(f"Starting system analysis for novel: {novel_name}")
        logger.info(f"Max chapters to analyze: {max_chapters}")
        
        start_time = time.time()
        
        # Step 1: 读取小说内容
        logger.info("Step 1: Reading novel content")
        novel_content = self._read_novel(novel_path)
        
        # Step 2: 提取章节摘要（降低token成本）
        logger.info("Step 2: Extracting chapter summaries")
        chapters_summary = self._extract_chapters_summary(
            novel_content, 
            max_chapters,
            use_chapter_detector
        )
        
        # Step 3: LLM分析系统元素
        logger.info("Step 3: LLM system analysis")
        llm_result = self._llm_system_analysis(
            novel_name=novel_name,
            chapters_summary=chapters_summary,
            total_chapters=max_chapters
        )
        
        # Step 4: 解析LLM输出
        logger.info("Step 4: Parsing LLM output")
        system_catalog = self._parse_system_catalog(
            llm_result,
            novel_name=novel_name,
            analyzed_chapters=f"1-{max_chapters}"
        )
        
        processing_time = time.time() - start_time
        system_catalog.metadata["processing_time"] = round(processing_time, 2)
        
        logger.info(f"System analysis complete: {len(system_catalog.categories)} categories, {processing_time:.2f}s")
        
        return system_catalog
    
    def _read_novel(self, novel_path: str) -> str:
        """读取小说文件"""
        path = Path(novel_path)
        if not path.exists():
            raise FileNotFoundError(f"Novel file not found: {novel_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Read novel: {len(content)} chars")
        return content
    
    def _extract_chapters_summary(
        self,
        novel_content: str,
        max_chapters: int,
        use_detector: bool
    ) -> str:
        """
        提取章节摘要（降低token成本）
        
        策略：
        1. 如果use_detector=True：使用NovelChapterDetector
        2. 否则：使用简单的正则匹配
        3. 每章只保留前500字 + 关键段落
        
        Args:
            novel_content: 小说内容
            max_chapters: 最大章节数
            use_detector: 是否使用章节检测器
        
        Returns:
            str: 章节摘要文本
        """
        if use_detector:
            # 使用章节检测器（更准确）
            try:
                from src.tools.novel_chapter_detector import NovelChapterDetector
                detector = NovelChapterDetector()
                chapters = detector.execute(novel_content)
                
                summaries = []
                for i, chapter in enumerate(chapters[:max_chapters], 1):
                    # 提取章节内容
                    start = chapter.start_char
                    end = chapter.end_char or len(novel_content)
                    chapter_text = novel_content[start:end]
                    
                    # 保留前800字（约2-3段）
                    preview = chapter_text[:800]
                    if len(chapter_text) > 800:
                        preview += "\n[...]"
                    
                    summaries.append(f"### 第{i}章：{chapter.title}\n{preview}\n")
                
                logger.info(f"Extracted {len(summaries)} chapter summaries using detector")
                return '\n'.join(summaries)
                
            except Exception as e:
                logger.warning(f"Chapter detector failed: {e}, falling back to regex")
        
        # 使用简单正则（降级方案）
        return self._extract_chapters_summary_regex(novel_content, max_chapters)
    
    def _extract_chapters_summary_regex(
        self,
        novel_content: str,
        max_chapters: int
    ) -> str:
        """
        使用正则表达式提取章节摘要（降级方案）
        
        Args:
            novel_content: 小说内容
            max_chapters: 最大章节数
        
        Returns:
            str: 章节摘要文本
        """
        # 匹配章节标题
        chapter_pattern = r'^第[零一二三四五六七八九十百千\d]+章[：:\s]*.+?$'
        
        lines = novel_content.split('\n')
        summaries = []
        current_chapter = None
        current_content = []
        chapter_count = 0
        
        for line in lines:
            if re.match(chapter_pattern, line.strip()):
                # 保存上一章
                if current_chapter and chapter_count < max_chapters:
                    content = '\n'.join(current_content[:30])  # 前30行
                    summaries.append(f"### {current_chapter}\n{content}\n[...]\n")
                
                # 开始新章
                chapter_count += 1
                if chapter_count > max_chapters:
                    break
                
                current_chapter = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一章
        if current_chapter and chapter_count <= max_chapters and current_content:
            content = '\n'.join(current_content[:30])
            summaries.append(f"### {current_chapter}\n{content}\n[...]\n")
        
        logger.info(f"Extracted {len(summaries)} chapter summaries using regex")
        return '\n'.join(summaries)
    
    def _llm_system_analysis(
        self,
        novel_name: str,
        chapters_summary: str,
        total_chapters: int
    ) -> str:
        """
        LLM系统分析
        
        Args:
            novel_name: 小说名称
            chapters_summary: 章节摘要
            total_chapters: 章节总数
        
        Returns:
            str: LLM输出（Markdown格式）
        """
        # 加载Prompt
        prompt = load_prompts("novel_system_analysis")
        
        user_prompt = prompt["user_template"].format(
            novel_name=novel_name,
            total_chapters=total_chapters,
            chapters_summary=chapters_summary
        )
        
        # LLM调用
        analysis_start = time.time()
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        analysis_time = time.time() - analysis_start
        
        result = response.choices[0].message.content.strip()
        logger.info(f"LLM analysis complete: {analysis_time:.2f}s")
        
        return result
    
    def _parse_system_catalog(
        self,
        llm_result: str,
        novel_name: str,
        analyzed_chapters: str
    ) -> SystemCatalog:
        """
        解析LLM输出，构建SystemCatalog
        
        Args:
            llm_result: LLM输出
            novel_name: 小说名称
            analyzed_chapters: 分析的章节范围
        
        Returns:
            SystemCatalog: 系统目录
        """
        # 提取小说类型
        novel_type = self._extract_novel_type(llm_result)
        
        # 提取类别
        categories = self._extract_categories(llm_result)
        
        catalog = SystemCatalog(
            novel_type=novel_type,
            novel_name=novel_name,
            analyzed_chapters=analyzed_chapters,
            categories=categories,
            metadata={
                "total_elements": sum(len(cat.elements) for cat in categories),
                "category_count": len(categories)
            }
        )
        
        logger.info(f"Parsed {len(categories)} categories with {catalog.metadata['total_elements']} total elements")
        
        return catalog
    
    def _extract_novel_type(self, llm_result: str) -> str:
        """提取小说类型"""
        # 匹配: ## 小说类型
        type_pattern = r'##\s*小说类型\s*\n+(.+?)(?=\n##|\Z)'
        
        match = re.search(type_pattern, llm_result, re.DOTALL)
        if match:
            type_block = match.group(1).strip()
            # 提取第一行作为类型名称
            first_line = type_block.split('\n')[0].strip()
            # 去除markdown格式
            novel_type = re.sub(r'[*_\[\]]', '', first_line)
            return novel_type
        
        return "unknown"
    
    def _extract_categories(self, llm_result: str) -> List[SystemCategory]:
        """提取系统元素类别"""
        categories = []
        
        # 匹配类别块: ### SC001 - 生存资源
        category_pattern = r'###\s*(SC\d+)\s*-\s*(.+?)$'
        
        # 匹配字段
        importance_pattern = r'\*\*重要程度\*\*[：:]\s*(critical|important|minor)'
        tracking_pattern = r'\*\*追踪策略\*\*[：:]\s*(quantity|state_change|ownership|encounter)'
        desc_pattern = r'\*\*类别描述\*\*[：:]\s*(.+?)$'
        
        lines = llm_result.split('\n')
        current_category = None
        in_elements_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配类别头部
            category_match = re.match(category_pattern, line_stripped)
            if category_match:
                # 保存上一个类别
                if current_category:
                    categories.append(self._build_category(current_category))
                
                # 创建新类别
                category_id = category_match.group(1)
                category_name = category_match.group(2).strip()
                current_category = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "category_desc": "",
                    "importance": "important",  # 默认值
                    "tracking_strategy": "state_change",  # 默认值
                    "elements": []
                }
                in_elements_block = False
                continue
            
            if not current_category:
                continue
            
            # 匹配重要程度
            importance_match = re.search(importance_pattern, line_stripped)
            if importance_match:
                current_category["importance"] = importance_match.group(1)
            
            # 匹配追踪策略
            tracking_match = re.search(tracking_pattern, line_stripped)
            if tracking_match:
                current_category["tracking_strategy"] = tracking_match.group(1)
            
            # 匹配类别描述
            desc_match = re.search(desc_pattern, line_stripped)
            if desc_match:
                current_category["category_desc"] = desc_match.group(1).strip()
            
            # 匹配元素列表
            if '**元素列表**' in line_stripped or '元素列表：' in line_stripped:
                in_elements_block = True
                continue
            
            if in_elements_block:
                # 匹配列表项: - 元素名
                if line_stripped.startswith('-') or line_stripped.startswith('*'):
                    element = line_stripped.lstrip('-*').strip()
                    if element and not element.startswith('['):
                        current_category["elements"].append(element)
                elif line_stripped.startswith('---') or line_stripped.startswith('###'):
                    # 结束元素列表
                    in_elements_block = False
        
        # 保存最后一个类别
        if current_category:
            categories.append(self._build_category(current_category))
        
        logger.info(f"Parsed {len(categories)} categories")
        
        return categories
    
    def _build_category(self, category_data: Dict[str, Any]) -> SystemCategory:
        """构建SystemCategory对象"""
        return SystemCategory(
            category_id=category_data["category_id"],
            category_name=category_data["category_name"],
            category_desc=category_data["category_desc"],
            importance=category_data["importance"],
            elements=category_data["elements"],
            tracking_strategy=category_data["tracking_strategy"]
        )
    
    def estimate_cost(self, max_chapters: int, avg_chapter_length: int = 3000) -> Dict[str, Any]:
        """
        估算分析成本
        
        Args:
            max_chapters: 章节数
            avg_chapter_length: 平均章节字数
        
        Returns:
            Dict: 成本估算
        """
        # 每章保留前800字
        preview_per_chapter = 800
        total_input_chars = preview_per_chapter * max_chapters
        
        # 按中文计算token（约1.5字符/token）
        estimated_input_tokens = int(total_input_chars / 1.5)
        estimated_output_tokens = 2000  # 输出约2000 tokens
        
        # Claude Sonnet 4.5价格（示例）
        # Input: $3/M tokens, Output: $15/M tokens
        cost_input = (estimated_input_tokens / 1_000_000) * 3
        cost_output = (estimated_output_tokens / 1_000_000) * 15
        total_cost = cost_input + cost_output
        
        # 预估时间（约15-30秒）
        estimated_time = "20-30秒"
        
        return {
            "max_chapters": max_chapters,
            "preview_per_chapter": preview_per_chapter,
            "total_input_chars": total_input_chars,
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost_usd": round(total_cost, 4),
            "estimated_time": estimated_time
        }
