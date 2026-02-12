"""
NovelSystemDetector - 章节系统元素检测工具（Phase 2）

基于NovelAnnotator的标注结果和全局SystemCatalog，检测本章中新出现的系统元素。

核心功能：
1. 读取章节标注结果（AnnotatedChapter）
2. 读取系统目录（SystemCatalog）
3. 检测新出现的系统元素
4. 更新系统目录
5. 输出检测结果（SystemUpdateResult）

设计理念：
- 独立Pass 3，避免污染NovelAnnotator
- 轻量级LLM调用（输入<2K tokens）
- 简洁的输出格式（易解析）
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.interfaces import BaseTool
from src.core.schemas_novel import (
    AnnotatedChapter,
    ParagraphSegmentationResult,
    SystemCatalog,
    SystemCategory,
    SystemElementUpdate,
    SystemUpdateResult
)
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelSystemDetector(BaseTool):
    """
    章节系统元素检测工具
    
    检测本章中新出现的系统元素，并更新系统目录。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        SystemUpdateResult: 检测结果 + 更新后的SystemCatalog
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化系统检测工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        logger.info(f"NovelSystemDetector initialized with {provider}/{self.model}")
    
    def execute(
        self,
        annotated_chapter: AnnotatedChapter,
        segmentation_result: ParagraphSegmentationResult,
        system_catalog: SystemCatalog,
        **kwargs
    ) -> tuple[SystemUpdateResult, SystemCatalog]:
        """
        执行系统元素检测
        
        Args:
            annotated_chapter: 章节标注结果
            segmentation_result: 章节分段结果（用于获取C类段落）
            system_catalog: 当前系统目录
            **kwargs: 其他参数
        
        Returns:
            tuple: (SystemUpdateResult, 更新后的SystemCatalog)
        """
        logger.info(f"Starting system detection for chapter {annotated_chapter.chapter_number}")
        
        start_time = time.time()
        
        # Step 1: 准备输入数据
        logger.info("Step 1: Preparing input data")
        catalog_summary = self._format_catalog_summary(system_catalog)
        events_summary = self._format_events_summary(annotated_chapter)
        c_class_paragraphs = self._extract_c_class_paragraphs(segmentation_result)
        
        # Step 2: LLM检测
        logger.info("Step 2: LLM system detection")
        llm_result = self._llm_detect_elements(
            chapter_number=annotated_chapter.chapter_number,
            catalog_summary=catalog_summary,
            events_summary=events_summary,
            c_class_paragraphs=c_class_paragraphs
        )
        
        # Step 3: 解析检测结果
        logger.info("Step 3: Parsing detection result")
        new_elements = self._parse_detection_result(
            llm_result,
            chapter_number=annotated_chapter.chapter_number
        )
        
        # Step 4: 更新系统目录
        logger.info("Step 4: Updating system catalog")
        updated_catalog = self._update_catalog(system_catalog, new_elements)
        
        processing_time = time.time() - start_time
        
        # 构建结果
        result = SystemUpdateResult(
            chapter_number=annotated_chapter.chapter_number,
            has_new_elements=(len(new_elements) > 0),
            new_elements=new_elements,
            catalog_updated=(len(new_elements) > 0),
            metadata={
                "processing_time": round(processing_time, 2),
                "model_used": self.model,
                "provider": self.provider
            }
        )
        
        logger.info(f"Detection complete: {len(new_elements)} new elements, {processing_time:.2f}s")
        
        return result, updated_catalog
    
    def _format_catalog_summary(self, catalog: SystemCatalog) -> str:
        """格式化系统目录摘要（用于Prompt）"""
        lines = [
            f"**小说类型**: {catalog.novel_type}",
            "",
            "**系统元素类别**:",
            ""
        ]
        
        for cat in catalog.categories:
            lines.append(f"### {cat.category_id} - {cat.category_name}")
            lines.append(f"**重要程度**: {cat.importance}")
            lines.append(f"**已有元素**: {', '.join(cat.elements[:10])}")
            if len(cat.elements) > 10:
                lines.append(f"... 还有 {len(cat.elements) - 10} 个元素")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_events_summary(self, chapter: AnnotatedChapter) -> str:
        """格式化事件摘要（用于Prompt）"""
        lines = []
        
        for event in chapter.event_timeline.events:
            lines.append(f"- **{event.event_id}**: {event.event_summary}")
        
        return '\n'.join(lines) if lines else "（本章无事件）"
    
    def _extract_c_class_paragraphs(self, segmentation: ParagraphSegmentationResult) -> str:
        """提取C类段落内容（用于Prompt）"""
        lines = []
        
        for para in segmentation.paragraphs:
            if para.type == "C":
                lines.append(f"### 段落{para.index}（{para.type}类）")
                lines.append(para.content)
                lines.append("")
        
        return '\n'.join(lines) if lines else "（本章无C类段落）"
    
    def _llm_detect_elements(
        self,
        chapter_number: int,
        catalog_summary: str,
        events_summary: str,
        c_class_paragraphs: str
    ) -> str:
        """
        LLM检测系统元素
        
        Args:
            chapter_number: 章节号
            catalog_summary: 系统目录摘要
            events_summary: 事件摘要
            c_class_paragraphs: C类段落内容
        
        Returns:
            str: LLM输出（Markdown格式）
        """
        # 加载Prompt
        prompt = load_prompts("novel_system_detection")
        
        user_prompt = prompt["user_template"].format(
            chapter_number=chapter_number,
            system_catalog_summary=catalog_summary,
            events_summary=events_summary,
            c_class_paragraphs=c_class_paragraphs
        )
        
        # LLM调用
        detection_start = time.time()
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        detection_time = time.time() - detection_start
        
        result = response.choices[0].message.content.strip()
        logger.info(f"LLM detection complete: {detection_time:.2f}s")
        
        return result
    
    def _parse_detection_result(
        self,
        llm_result: str,
        chapter_number: int
    ) -> List[SystemElementUpdate]:
        """
        解析LLM检测结果
        
        Args:
            llm_result: LLM输出
            chapter_number: 章节号
        
        Returns:
            List[SystemElementUpdate]: 新元素列表
        """
        new_elements = []
        
        # 检查是否无新元素
        if "无新元素" in llm_result or "无新元素" in llm_result:
            logger.info("No new elements detected")
            return new_elements
        
        # 匹配元素块：### 1. [元素名称]
        element_pattern = r'###\s*\d+\.\s*(.+?)$'
        category_pattern = r'\*\*归类\*\*[：:]\s*(SC\d+)\s*-\s*(.+?)$'
        confidence_pattern = r'\*\*置信度\*\*[：:]\s*(high|medium|low)'
        
        lines = llm_result.split('\n')
        current_element = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配元素名称
            element_match = re.match(element_pattern, line_stripped)
            if element_match:
                # 保存上一个元素
                if current_element and current_element.get("element_name"):
                    new_elements.append(self._build_element_update(current_element, chapter_number))
                
                # 创建新元素
                element_name = element_match.group(1).strip()
                # 移除可能的markdown格式
                element_name = re.sub(r'[*_\[\]]', '', element_name)
                
                current_element = {
                    "element_name": element_name,
                    "category_id": "",
                    "category_name": "",
                    "confidence": "medium"  # 默认值
                }
                continue
            
            if not current_element:
                continue
            
            # 匹配归类
            category_match = re.search(category_pattern, line_stripped)
            if category_match:
                current_element["category_id"] = category_match.group(1)
                current_element["category_name"] = category_match.group(2).strip()
            
            # 匹配置信度
            confidence_match = re.search(confidence_pattern, line_stripped)
            if confidence_match:
                current_element["confidence"] = confidence_match.group(1)
        
        # 保存最后一个元素
        if current_element and current_element.get("element_name"):
            new_elements.append(self._build_element_update(current_element, chapter_number))
        
        logger.info(f"Parsed {len(new_elements)} new elements")
        
        return new_elements
    
    def _build_element_update(
        self,
        element_data: Dict[str, Any],
        chapter_number: int
    ) -> SystemElementUpdate:
        """构建SystemElementUpdate对象"""
        return SystemElementUpdate(
            element_name=element_data["element_name"],
            category_id=element_data.get("category_id", "SC999"),
            category_name=element_data.get("category_name", "未分类"),
            chapter_number=chapter_number,
            confidence=element_data.get("confidence", "medium")
        )
    
    def _update_catalog(
        self,
        catalog: SystemCatalog,
        new_elements: List[SystemElementUpdate]
    ) -> SystemCatalog:
        """
        更新系统目录
        
        Args:
            catalog: 原系统目录
            new_elements: 新元素列表
        
        Returns:
            SystemCatalog: 更新后的系统目录
        """
        if not new_elements:
            return catalog
        
        # 创建目录副本
        updated_catalog = catalog.model_copy(deep=True)
        
        # 按类别分组新元素
        elements_by_category: Dict[str, List[str]] = {}
        for elem in new_elements:
            if elem.category_id not in elements_by_category:
                elements_by_category[elem.category_id] = []
            elements_by_category[elem.category_id].append(elem.element_name)
        
        # 更新各类别
        for cat in updated_catalog.categories:
            if cat.category_id in elements_by_category:
                # 去重并添加新元素
                new_elems = elements_by_category[cat.category_id]
                for elem in new_elems:
                    if elem not in cat.elements:
                        cat.elements.append(elem)
                        logger.info(f"Added '{elem}' to {cat.category_id} - {cat.category_name}")
        
        # 更新元数据
        updated_catalog.metadata["total_elements"] = sum(len(cat.elements) for cat in updated_catalog.categories)
        updated_catalog.metadata["last_updated_chapter"] = new_elements[0].chapter_number if new_elements else None
        
        return updated_catalog
