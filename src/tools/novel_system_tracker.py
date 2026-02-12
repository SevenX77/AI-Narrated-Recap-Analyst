"""
NovelSystemTracker - 章节系统元素追踪工具（Phase 3）

追踪每个事件中的系统元素变化（数量、状态、获得/消耗等）。

核心功能：
1. 读取章节标注结果（AnnotatedChapter）
2. 读取系统目录（SystemCatalog）
3. 为每个事件追踪系统元素变化
4. 生成系统追踪表（SystemTrackingResult）

设计理念：
- 独立工具，专注系统追踪
- 轻量级LLM调用（输入<3K tokens）
- 结构化输出（易于生成表格）
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.interfaces import BaseTool
from src.core.schemas_novel import (
    AnnotatedChapter,
    SystemCatalog,
    SystemChange,
    SystemTrackingEntry,
    SystemTrackingResult
)
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelSystemTracker(BaseTool):
    """
    章节系统元素追踪工具
    
    追踪每个事件中的系统元素变化。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        SystemTrackingResult: 系统追踪结果
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化系统追踪工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        logger.info(f"NovelSystemTracker initialized with {provider}/{self.model}")
    
    def execute(
        self,
        annotated_chapter: AnnotatedChapter,
        system_catalog: SystemCatalog,
        **kwargs
    ) -> SystemTrackingResult:
        """
        执行系统追踪
        
        Args:
            annotated_chapter: 章节标注结果
            system_catalog: 系统目录
            **kwargs: 其他参数
        
        Returns:
            SystemTrackingResult: 系统追踪结果
        """
        logger.info(f"Starting system tracking for chapter {annotated_chapter.chapter_number}")
        
        start_time = time.time()
        
        # Step 1: 准备输入数据
        logger.info("Step 1: Preparing input data")
        catalog_summary = self._format_catalog_summary(system_catalog)
        events_detail = self._format_events_detail(annotated_chapter)
        
        # Step 2: LLM追踪
        logger.info("Step 2: LLM system tracking")
        llm_result = self._llm_track_systems(
            chapter_number=annotated_chapter.chapter_number,
            catalog_summary=catalog_summary,
            events_detail=events_detail
        )
        
        # Step 3: 解析追踪结果
        logger.info("Step 3: Parsing tracking result")
        tracking_entries = self._parse_tracking_result(
            llm_result,
            annotated_chapter=annotated_chapter
        )
        
        processing_time = time.time() - start_time
        
        # 统计有变化的事件数
        events_with_changes = sum(1 for entry in tracking_entries if entry.has_system_changes)
        
        # 构建结果
        result = SystemTrackingResult(
            chapter_number=annotated_chapter.chapter_number,
            total_events=len(tracking_entries),
            events_with_changes=events_with_changes,
            tracking_entries=tracking_entries,
            metadata={
                "processing_time": round(processing_time, 2),
                "model_used": self.model,
                "provider": self.provider
            }
        )
        
        logger.info(f"Tracking complete: {events_with_changes}/{len(tracking_entries)} events with changes, {processing_time:.2f}s")
        
        return result
    
    def _format_catalog_summary(self, catalog: SystemCatalog) -> str:
        """格式化系统目录摘要（用于Prompt）"""
        lines = []
        
        for cat in catalog.categories:
            lines.append(f"### {cat.category_id} - {cat.category_name}")
            lines.append(f"**元素**: {', '.join(cat.elements[:15])}")
            if len(cat.elements) > 15:
                lines.append(f"... 还有 {len(cat.elements) - 15} 个")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_events_detail(self, chapter: AnnotatedChapter) -> str:
        """格式化事件详情（用于Prompt）"""
        lines = []
        
        for event in chapter.event_timeline.events:
            lines.append(f"## 事件：{event.event_id}")
            lines.append(f"**摘要**: {event.event_summary}")
            lines.append(f"**段落**: {', '.join(map(str, event.paragraph_indices))}")
            
            # 添加事件内容摘要（前300字）
            if event.paragraph_contents:
                # 合并所有段落内容
                full_content = '\n'.join(event.paragraph_contents)
                content_preview = full_content[:300]
                if len(full_content) > 300:
                    content_preview += "..."
                lines.append(f"**内容**: {content_preview}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _llm_track_systems(
        self,
        chapter_number: int,
        catalog_summary: str,
        events_detail: str
    ) -> str:
        """
        LLM系统追踪
        
        Args:
            chapter_number: 章节号
            catalog_summary: 系统目录摘要
            events_detail: 事件详情
        
        Returns:
            str: LLM输出（Markdown格式）
        """
        # 加载Prompt
        prompt = load_prompts("novel_system_tracking")
        
        user_prompt = prompt["user_template"].format(
            chapter_number=chapter_number,
            system_catalog_summary=catalog_summary,
            events_detail=events_detail
        )
        
        # LLM调用
        tracking_start = time.time()
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        tracking_time = time.time() - tracking_start
        
        result = response.choices[0].message.content.strip()
        logger.info(f"LLM tracking complete: {tracking_time:.2f}s")
        
        return result
    
    def _parse_tracking_result(
        self,
        llm_result: str,
        annotated_chapter: AnnotatedChapter
    ) -> List[SystemTrackingEntry]:
        """
        解析LLM追踪结果
        
        Args:
            llm_result: LLM输出
            annotated_chapter: 章节标注结果
        
        Returns:
            List[SystemTrackingEntry]: 追踪记录列表
        """
        tracking_entries = []
        
        # 匹配事件块：## 事件1：[事件ID] - [事件摘要]
        event_pattern = r'##\s*事件\d+[：:]\s*([A-Z0-9]+)\s*-\s*(.+?)$'
        system_change_pattern = r'\*\*系统变化\*\*[：:]\s*(有|无)'
        
        # 匹配变化块：### 变化1
        change_header_pattern = r'###\s*变化\d+'
        element_pattern = r'\*\*元素\*\*[：:]\s*(.+?)（(.+?)\s*-\s*(.+?)）'
        change_type_pattern = r'\*\*变化类型\*\*[：:]\s*(获得|消耗|升级|遭遇|状态变化)'
        change_desc_pattern = r'\*\*变化描述\*\*[：:]\s*(.+?)$'
        quantity_pattern = r'\*\*数量变化\*\*[：:]\s*(.+?)$'
        quantity_before_pattern = r'\*\*变化前存量\*\*[：:]\s*(.+?)$'
        quantity_after_pattern = r'\*\*变化后存量\*\*[：:]\s*(.+?)$'
        
        lines = llm_result.split('\n')
        current_entry = None
        current_change = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配事件头部
            event_match = re.match(event_pattern, line_stripped)
            if event_match:
                # 保存上一个事件
                if current_entry:
                    tracking_entries.append(self._build_tracking_entry(current_entry, annotated_chapter))
                
                # 创建新事件
                event_id = event_match.group(1)
                event_summary = event_match.group(2).strip()
                current_entry = {
                    "event_id": event_id,
                    "event_summary": event_summary,
                    "has_system_changes": False,
                    "system_changes": []
                }
                current_change = None
                continue
            
            if not current_entry:
                continue
            
            # 匹配系统变化标志
            system_change_match = re.search(system_change_pattern, line_stripped)
            if system_change_match:
                has_changes = (system_change_match.group(1) == "有")
                current_entry["has_system_changes"] = has_changes
                continue
            
            # 匹配变化头部
            if re.match(change_header_pattern, line_stripped):
                # 保存上一个变化
                if current_change and current_change.get("element_name"):
                    current_entry["system_changes"].append(current_change)
                
                # 创建新变化
                current_change = {
                    "element_name": "",
                    "category_id": "",
                    "change_type": "状态变化",  # 默认值
                    "change_description": "",
                    "quantity_change": None,
                    "quantity_before": None,
                    "quantity_after": None
                }
                continue
            
            if not current_change:
                continue
            
            # 匹配元素
            element_match = re.search(element_pattern, line_stripped)
            if element_match:
                current_change["element_name"] = element_match.group(1).strip()
                current_change["category_id"] = element_match.group(2).strip()
            
            # 匹配变化类型
            change_type_match = re.search(change_type_pattern, line_stripped)
            if change_type_match:
                current_change["change_type"] = change_type_match.group(1)
            
            # 匹配变化描述
            change_desc_match = re.search(change_desc_pattern, line_stripped)
            if change_desc_match:
                current_change["change_description"] = change_desc_match.group(1).strip()
            
            # 匹配数量变化
            quantity_match = re.search(quantity_pattern, line_stripped)
            if quantity_match:
                quantity_str = quantity_match.group(1).strip()
                if quantity_str not in ["未知", "null", "无"]:
                    current_change["quantity_change"] = quantity_str
            
            # 匹配变化前存量
            quantity_before_match = re.search(quantity_before_pattern, line_stripped)
            if quantity_before_match:
                before_str = quantity_before_match.group(1).strip()
                if before_str not in ["未知", "null", "无"]:
                    current_change["quantity_before"] = before_str
            
            # 匹配变化后存量
            quantity_after_match = re.search(quantity_after_pattern, line_stripped)
            if quantity_after_match:
                after_str = quantity_after_match.group(1).strip()
                if after_str not in ["未知", "null", "无"]:
                    current_change["quantity_after"] = after_str
        
        # 保存最后一个变化和事件
        if current_change and current_change.get("element_name"):
            current_entry["system_changes"].append(current_change)
        
        if current_entry:
            tracking_entries.append(self._build_tracking_entry(current_entry, annotated_chapter))
        
        logger.info(f"Parsed {len(tracking_entries)} tracking entries")
        
        return tracking_entries
    
    def _build_tracking_entry(
        self,
        entry_data: Dict[str, Any],
        annotated_chapter: AnnotatedChapter
    ) -> SystemTrackingEntry:
        """构建SystemTrackingEntry对象"""
        # 构建SystemChange列表
        system_changes = []
        for change_data in entry_data.get("system_changes", []):
            if change_data.get("element_name"):
                system_changes.append(SystemChange(
                    element_name=change_data["element_name"],
                    category_id=change_data.get("category_id", "SC999"),
                    change_type=change_data.get("change_type", "状态变化"),
                    change_description=change_data.get("change_description", ""),
                    quantity_change=change_data.get("quantity_change"),
                    quantity_before=change_data.get("quantity_before"),
                    quantity_after=change_data.get("quantity_after")
                ))
        
        # 从annotated_chapter中获取完整的event_summary（如果LLM输出的不完整）
        event_summary = entry_data["event_summary"]
        for event in annotated_chapter.event_timeline.events:
            if event.event_id == entry_data["event_id"]:
                event_summary = event.event_summary
                break
        
        return SystemTrackingEntry(
            event_id=entry_data["event_id"],
            event_summary=event_summary,
            has_system_changes=entry_data.get("has_system_changes", False),
            system_changes=system_changes
        )
