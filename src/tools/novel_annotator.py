"""
NovelAnnotator - 小说章节标注工具（v4, Two-Pass）

基于NovelSegmenter的分段结果，进行事件时间线分析和设定关联标注。

核心功能：
1. 时间线重排：将段落按故事时间顺序重排
2. 事件聚合：将连续段落聚合成事件
3. 设定关联：将A类设定关联到事件（BF/BT/AF）
4. 知识库构建：累积设定知识库

实现方式：
- Two-Pass LLM调用（Pass 1事件聚合 + Pass 2设定关联）
- 解析LLM输出并生成结构化数据
- 输出JSON格式（事件表 + 设定表）
"""

import logging
import re
import time
from typing import Optional, Dict, Any, List

from src.core.interfaces import BaseTool
from src.core.schemas_novel import (
    ParagraphSegmentationResult,
    EventEntry,
    EventTimeline,
    SettingEntry,
    SettingLibrary,
    AnnotatedChapter,
    ParagraphFunctionalTags,
    FunctionalTagsLibrary
)
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts
from src.utils.llm_output_parser import LLMOutputParser
from src.core.exceptions import ToolExecutionError, LLMCallError, ParsingError

logger = logging.getLogger(__name__)


class NovelAnnotator(BaseTool):
    """
    小说章节标注工具
    
    使用Two-Pass策略完成事件时间线分析和设定关联标注。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        AnnotatedChapter: 完整的章节标注结果（事件表 + 设定表）
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化标注工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        logger.info(f"NovelAnnotator initialized with {provider}/{self.model}")
    
    def execute(
        self,
        segmentation_result: ParagraphSegmentationResult,
        enable_functional_tags: bool = True,
        **kwargs
    ) -> AnnotatedChapter:
        """
        执行章节标注
        
        Args:
            segmentation_result: NovelSegmenter的分段结果
            enable_functional_tags: 是否启用Pass 3功能性标签标注（默认True）
            **kwargs: 其他参数
        
        Returns:
            AnnotatedChapter: 完整的章节标注结果
        """
        chapter_number = segmentation_result.chapter_number
        logger.info(f"Starting annotation for chapter {chapter_number}")
        logger.info(f"Total paragraphs: {segmentation_result.total_paragraphs}")
        logger.info(f"Functional tags enabled: {enable_functional_tags}")
        
        start_time = time.time()
        
        # Step 1: Pass 1 - 时间线分析 + 事件聚合
        logger.info("Step 1: Pass 1 - Timeline analysis and event aggregation")
        pass1_result = self._pass1_event_aggregation(segmentation_result)
        
        # Step 2: 解析Pass 1输出，提取事件列表
        logger.info("Step 2: Parsing Pass 1 output")
        events = self._parse_events(pass1_result, segmentation_result)
        
        # Step 3: Pass 2 - 设定关联 + 校验
        logger.info("Step 3: Pass 2 - Setting correlation and validation")
        pass2_result = self._pass2_setting_correlation(
            segmentation_result, 
            events, 
            pass1_result
        )
        
        # Step 4: 解析Pass 2输出，提取设定列表
        logger.info("Step 4: Parsing Pass 2 output")
        settings = self._parse_settings(pass2_result, events)
        
        pass12_time = time.time() - start_time
        
        # Step 5: Pass 3 - 功能性标签标注（可选）
        functional_tags_library = None
        if enable_functional_tags:
            logger.info("Step 5: Pass 3 - Functional tags annotation")
            pass3_start = time.time()
            pass3_result = self._pass3_functional_tags(segmentation_result, events)
            functional_tags_library = self._parse_functional_tags(pass3_result, segmentation_result)
            pass3_time = time.time() - pass3_start
            logger.info(f"Pass 3 completed in {pass3_time:.2f}s")
        
        total_processing_time = time.time() - start_time
        
        # Step 6: 构建完整结果
        event_timeline = EventTimeline(
            chapter_number=chapter_number,
            total_events=len(events),
            events=events,
            metadata={
                "type_distribution": self._calculate_event_type_distribution(events),
                "processing_time": round(pass12_time / 2, 2)
            }
        )
        
        setting_library = SettingLibrary(
            chapter_number=chapter_number,
            total_settings=len(settings),
            settings=settings,
            metadata={
                "position_distribution": self._calculate_position_distribution(settings),
                "processing_time": round(pass12_time / 2, 2)
            }
        )
        
        annotated_chapter = AnnotatedChapter(
            chapter_number=chapter_number,
            event_timeline=event_timeline,
            setting_library=setting_library,
            functional_tags=functional_tags_library,
            metadata={
                "total_processing_time": round(total_processing_time, 2),
                "model_used": self.model,
                "provider": self.provider
            }
        )
        
        logger.info(f"Annotation complete: {len(events)} events, {len(settings)} settings, {total_processing_time:.2f}s")
        
        return annotated_chapter
    
    def _pass1_event_aggregation(
        self,
        segmentation_result: ParagraphSegmentationResult
    ) -> str:
        """
        Pass 1: 时间线分析 + 事件聚合
        
        Args:
            segmentation_result: 分段结果
        
        Returns:
            str: Pass 1的LLM输出（Markdown格式）
        """
        # 准备输入：格式化分段结果
        segmented_paragraphs = self._format_segmented_paragraphs(segmentation_result)
        
        # 加载Prompt
        prompt_pass1 = load_prompts("novel_annotation_pass1")
        
        user_prompt = prompt_pass1["user_template"].format(
            segmented_paragraphs=segmented_paragraphs,
            chapter_number=segmentation_result.chapter_number
        )
        
        # LLM调用
        pass1_start = time.time()
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_pass1["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass1_time = time.time() - pass1_start
        
        pass1_result = response.choices[0].message.content.strip()
        logger.info(f"Pass 1 complete: {pass1_time:.2f}s")
        
        return pass1_result
    
    def _pass2_setting_correlation(
        self,
        segmentation_result: ParagraphSegmentationResult,
        events: List[EventEntry],
        pass1_result: str
    ) -> str:
        """
        Pass 2: 设定关联 + 校验
        
        Args:
            segmentation_result: 分段结果
            events: Pass 1解析出的事件列表
            pass1_result: Pass 1的LLM输出
        
        Returns:
            str: Pass 2的LLM输出（Markdown格式）
        """
        # 准备输入：提取A类段落
        a_class_paragraphs = self._format_a_class_paragraphs(segmentation_result)
        
        # 加载Prompt
        prompt_pass2 = load_prompts("novel_annotation_pass2")
        
        user_prompt = prompt_pass2["user_template"].format(
            pass1_result=pass1_result,
            a_class_paragraphs=a_class_paragraphs,
            chapter_number=segmentation_result.chapter_number
        )
        
        # LLM调用
        pass2_start = time.time()
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_pass2["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass2_time = time.time() - pass2_start
        
        pass2_result = response.choices[0].message.content.strip()
        logger.info(f"Pass 2 complete: {pass2_time:.2f}s")
        
        return pass2_result
    
    def _format_segmented_paragraphs(
        self,
        segmentation_result: ParagraphSegmentationResult
    ) -> str:
        """
        格式化分段结果为Markdown
        
        Args:
            segmentation_result: 分段结果
        
        Returns:
            str: Markdown格式的分段列表
        """
        lines = []
        for para in segmentation_result.paragraphs:
            type_name = {
                "A": "A类-设定",
                "B": "B类-事件",
                "C": "C类-系统"
            }.get(para.type, para.type)
            
            lines.append(f"### 段落 {para.index} [{type_name}]")
            lines.append("")
            lines.append(para.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_a_class_paragraphs(
        self,
        segmentation_result: ParagraphSegmentationResult
    ) -> str:
        """
        格式化A类段落为Markdown
        
        Args:
            segmentation_result: 分段结果
        
        Returns:
            str: Markdown格式的A类段落列表
        """
        lines = []
        for para in segmentation_result.paragraphs:
            if para.type == "A":
                lines.append(f"### 段落 {para.index} [A类-设定]")
                lines.append("")
                lines.append(para.content)
                lines.append("")
                lines.append("---")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _parse_events(
        self,
        pass1_result: str,
        segmentation_result: ParagraphSegmentationResult
    ) -> List[EventEntry]:
        """
        解析Pass 1输出，提取事件列表
        
        Args:
            pass1_result: Pass 1的LLM输出
            segmentation_result: 分段结果（用于获取段落内容）
        
        Returns:
            List[EventEntry]: 事件列表
        """
        events = []
        
        # 正则匹配事件块
        # 匹配: ## 事件1：陈野从江城逃出来，和一众幸存者组成车队
        event_pattern = r'##\s*事件(\d+)[：:]\s*(.+?)$'
        
        # 匹配字段
        type_pattern = r'\*\*类型\*\*[：:]\s*([BC])类'
        paragraphs_pattern = r'\*\*包含段落\*\*[：:]\s*\[([^\]]+)\]'
        location_pattern = r'\*\*地点\*\*[：:]\s*(.+?)$'
        location_change_pattern = r'\*\*地点变化\*\*[：:]\s*(.+?)$'
        time_pattern = r'\*\*时间\*\*[：:]\s*(.+?)$'
        time_change_pattern = r'\*\*时间变化\*\*[：:]\s*(.+?)$'
        
        lines = pass1_result.split('\n')
        current_event = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配事件头部
            event_match = re.match(event_pattern, line_stripped)
            if event_match:
                # 保存上一个事件
                if current_event:
                    events.append(self._build_event_entry(current_event, segmentation_result))
                
                # 创建新事件
                event_num = int(event_match.group(1))
                event_summary = event_match.group(2).strip()
                current_event = {
                    "event_num": event_num,
                    "event_summary": event_summary,
                    "event_type": None,
                    "paragraph_indices": [],
                    "location": None,
                    "location_change": None,
                    "time": None,
                    "time_change": None
                }
                continue
            
            if not current_event:
                continue
            
            # 匹配类型
            type_match = re.search(type_pattern, line_stripped)
            if type_match:
                current_event["event_type"] = type_match.group(1)
            
            # 匹配包含段落
            paragraphs_match = re.search(paragraphs_pattern, line_stripped)
            if paragraphs_match:
                para_str = paragraphs_match.group(1)
                # 解析段落编号，支持 "2" 或 "段落2" 两种格式
                para_indices = []
                for item in para_str.split(','):
                    item_stripped = item.strip()
                    # 提取数字：如果包含"段落"，则提取数字部分
                    if '段落' in item_stripped:
                        num_match = re.search(r'\d+', item_stripped)
                        if num_match:
                            para_indices.append(int(num_match.group()))
                    else:
                        # 直接是数字
                        try:
                            para_indices.append(int(item_stripped))
                        except ValueError:
                            logger.warning(f"Failed to parse paragraph index: {item_stripped}")
                current_event["paragraph_indices"] = para_indices
            
            # 匹配地点
            location_match = re.search(location_pattern, line_stripped)
            if location_match and '**地点变化**' not in line_stripped:
                current_event["location"] = location_match.group(1).strip()
            
            # 匹配地点变化
            location_change_match = re.search(location_change_pattern, line_stripped)
            if location_change_match:
                current_event["location_change"] = location_change_match.group(1).strip()
            
            # 匹配时间
            time_match = re.search(time_pattern, line_stripped)
            if time_match and '**时间变化**' not in line_stripped:
                current_event["time"] = time_match.group(1).strip()
            
            # 匹配时间变化
            time_change_match = re.search(time_change_pattern, line_stripped)
            if time_change_match:
                current_event["time_change"] = time_change_match.group(1).strip()
        
        # 保存最后一个事件
        if current_event:
            events.append(self._build_event_entry(current_event, segmentation_result))
        
        logger.info(f"Parsed {len(events)} events from Pass 1 output")
        
        return events
    
    def _build_event_entry(
        self,
        event_data: Dict[str, Any],
        segmentation_result: ParagraphSegmentationResult
    ) -> EventEntry:
        """
        构建EventEntry对象
        
        Args:
            event_data: 解析出的事件数据
            segmentation_result: 分段结果
        
        Returns:
            EventEntry: 事件条目
        """
        chapter_number = segmentation_result.chapter_number
        event_num = event_data["event_num"]
        event_type = event_data["event_type"] or "B"
        
        # 生成事件编号: 章节4位 + 序号5位 + 类型1位
        event_id = f"{chapter_number:04d}{event_num:05d}{event_type}"
        
        # 获取段落内容
        paragraph_indices = event_data["paragraph_indices"]
        paragraph_contents = []
        
        for para_idx in paragraph_indices:
            # 查找对应段落
            para = next((p for p in segmentation_result.paragraphs if p.index == para_idx), None)
            if para:
                type_name = {
                    "A": "A类-设定",
                    "B": "B类-事件",
                    "C": "C类-系统"
                }.get(para.type, para.type)
                content = f"## 段落 {para.index} [{type_name}]\n\n{para.content}"
                paragraph_contents.append(content)
        
        return EventEntry(
            event_id=event_id,
            event_summary=event_data["event_summary"],
            event_type=event_type,
            paragraph_indices=paragraph_indices,
            paragraph_contents=paragraph_contents,
            location=event_data["location"] or "未指定",
            location_change=event_data["location_change"] or "不变",
            time=event_data["time"] or "未指定",
            time_change=event_data["time_change"] or "不变"
        )
    
    def _parse_settings(
        self,
        pass2_result: str,
        events: List[EventEntry]
    ) -> List[SettingEntry]:
        """
        解析Pass 2输出，提取设定列表
        
        Args:
            pass2_result: Pass 2的LLM输出
            events: 事件列表
        
        Returns:
            List[SettingEntry]: 设定列表
        """
        settings = []
        accumulated_knowledge = []
        
        # 正则匹配设定块
        # 匹配: ## 设定1：全球诡异爆发
        setting_pattern = r'##\s*设定(\d+)[：:]\s*(.+?)$'
        
        # 匹配字段
        paragraph_pattern = r'\*\*段落\*\*[：:]\s*(\d+)'
        setting_id_pattern = r'\*\*设定编号\*\*[：:]\s*(S\d+)'
        related_event_pattern = r'\*\*关联事件\*\*[：:]\s*事件(\d+)\s*\((\w+)\)'
        time_position_pattern = r'\*\*时间位置\*\*[：:]\s*(BF|BT|AF)'
        acquisition_time_pattern = r'\*\*获得时间点\*\*[：:]\s*(\w+_\w+)'
        
        lines = pass2_result.split('\n')
        current_setting = None
        in_knowledge_block = False
        knowledge_content = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # 匹配设定头部
            setting_match = re.match(setting_pattern, line_stripped)
            if setting_match:
                # 保存上一个设定
                if current_setting:
                    current_setting["setting_summary"] = '\n'.join(knowledge_content).strip()
                    settings.append(self._build_setting_entry(current_setting, accumulated_knowledge[:]))
                
                # 创建新设定
                setting_title = setting_match.group(2).strip()
                
                current_setting = {
                    "setting_title": setting_title,
                    "paragraph_index": None,
                    "related_event_id": None,
                    "time_position": None,
                    "setting_id": None,
                    "acquisition_time": None,
                    "setting_summary": None,
                    "paragraph_content": None
                }
                in_knowledge_block = False
                knowledge_content = []
                continue
            
            if not current_setting:
                continue
            
            # 匹配段落
            paragraph_match = re.search(paragraph_pattern, line_stripped)
            if paragraph_match:
                current_setting["paragraph_index"] = int(paragraph_match.group(1))
            
            # 匹配设定编号
            setting_id_match = re.search(setting_id_pattern, line_stripped)
            if setting_id_match:
                current_setting["setting_id"] = setting_id_match.group(1)
                # 当获得设定编号时，添加到累积知识库
                if current_setting["setting_id"] not in accumulated_knowledge:
                    accumulated_knowledge.append(current_setting["setting_id"])
            
            # 匹配关联事件
            related_event_match = re.search(related_event_pattern, line_stripped)
            if related_event_match:
                event_num = int(related_event_match.group(1))
                event_id = related_event_match.group(2)
                # 如果event_id不是标准格式，从events列表中查找
                if not re.match(r'^\d{9}[BC]$', event_id):
                    # 根据事件序号从events列表中获取正确的ID
                    if 0 < event_num <= len(events):
                        event_id = events[event_num - 1].event_id
                        logger.info(f"Found event ID from events list: {event_id}")
                current_setting["related_event_id"] = event_id
            
            # 匹配时间位置
            time_position_match = re.search(time_position_pattern, line_stripped)
            if time_position_match:
                current_setting["time_position"] = time_position_match.group(1)
            
            # 匹配获得时间点
            acquisition_time_match = re.search(acquisition_time_pattern, line_stripped)
            if acquisition_time_match:
                current_setting["acquisition_time"] = acquisition_time_match.group(1)
            
            # 匹配核心知识点块
            if '**核心知识点**' in line_stripped:
                in_knowledge_block = True
                continue
            
            if in_knowledge_block:
                if line_stripped.startswith('**累积知识库**') or line_stripped.startswith('---'):
                    in_knowledge_block = False
                elif line_stripped and not line_stripped.startswith('#'):
                    knowledge_content.append(line_stripped)
        
        # 保存最后一个设定
        if current_setting:
            current_setting["setting_summary"] = '\n'.join(knowledge_content).strip()
            settings.append(self._build_setting_entry(current_setting, accumulated_knowledge[:]))
        
        logger.info(f"Parsed {len(settings)} settings from Pass 2 output")
        
        return settings
    
    def _build_setting_entry(
        self,
        setting_data: Dict[str, Any],
        accumulated_knowledge: List[str]
    ) -> SettingEntry:
        """
        构建SettingEntry对象
        
        Args:
            setting_data: 解析出的设定数据
            accumulated_knowledge: 累积知识库（设定编号列表）
        
        Returns:
            SettingEntry: 设定条目
        """
        # 验证和修正related_event_id格式
        related_event_id = setting_data.get("related_event_id") or ""
        # 如果不是标准格式（9位数字+1位字母），尝试提取
        if not re.match(r'^\d{9}[BC]$', related_event_id):
            # 尝试从字符串中提取事件ID
            match = re.search(r'\d{9}[BC]', related_event_id)
            if match:
                related_event_id = match.group()
            else:
                logger.warning(f"Invalid related_event_id format: {related_event_id}")
        
        # 验证和修正acquisition_time格式
        acquisition_time = setting_data.get("acquisition_time") or ""
        time_position = setting_data.get("time_position") or "BF"
        # 如果acquisition_time格式不正确，重新构建
        if not re.match(r'^(BF|BT|AF)_\d{9}[BC]$', acquisition_time):
            if related_event_id and re.match(r'^\d{9}[BC]$', related_event_id):
                acquisition_time = f"{time_position}_{related_event_id}"
                logger.info(f"Fixed acquisition_time: {acquisition_time}")
        
        return SettingEntry(
            setting_id=setting_data["setting_id"] or "UNKNOWN",
            setting_title=setting_data["setting_title"] or "",
            setting_summary=setting_data["setting_summary"] or "",
            paragraph_index=setting_data["paragraph_index"] or 1,  # schema要求>=1
            paragraph_content="",  # 稍后补充
            acquisition_time=acquisition_time,
            related_event_id=related_event_id,
            time_position=time_position,
            accumulated_knowledge=accumulated_knowledge
        )
    
    def _calculate_event_type_distribution(
        self,
        events: List[EventEntry]
    ) -> Dict[str, int]:
        """计算事件类型分布"""
        distribution = {"B": 0, "C": 0}
        for event in events:
            distribution[event.event_type] += 1
        return distribution
    
    def _calculate_position_distribution(
        self,
        settings: List[SettingEntry]
    ) -> Dict[str, int]:
        """计算设定时间位置分布"""
        distribution = {"BF": 0, "BT": 0, "AF": 0}
        for setting in settings:
            distribution[setting.time_position] += 1
        return distribution
    
    # ==================== Pass 3: 功能性标签标注 ====================
    
    def _pass3_functional_tags(
        self,
        segmentation_result: ParagraphSegmentationResult,
        events: List[EventEntry]
    ) -> str:
        """
        Pass 3: 功能性标签标注
        
        Args:
            segmentation_result: 分段结果
            events: Pass 1解析出的事件列表
        
        Returns:
            LLM输出的Markdown格式功能性标签
        """
        # 加载Prompt
        prompts = load_prompts("novel_annotation_pass3_functional_tags")
        system_prompt = prompts.get("system", "")
        user_template = prompts.get("user_template", "")
        
        # 格式化段落内容
        formatted_paragraphs = self._format_paragraphs_for_pass3(segmentation_result)
        
        # 格式化事件摘要（供参考）
        event_summary = self._format_event_summary(events)
        
        # 填充模板
        user_prompt = user_template.format(
            chapter_number=segmentation_result.chapter_number,
            total_paragraphs=segmentation_result.total_paragraphs,
            formatted_paragraphs=formatted_paragraphs,
            event_summary=event_summary
        )
        
        # 调用LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=8000
        )
        
        return response.choices[0].message.content
    
    def _format_paragraphs_for_pass3(
        self,
        segmentation_result: ParagraphSegmentationResult
    ) -> str:
        """
        格式化段落内容供Pass 3使用
        
        Args:
            segmentation_result: 分段结果
        
        Returns:
            格式化后的段落内容
        """
        lines = []
        for i, paragraph in enumerate(segmentation_result.paragraphs, 1):
            lines.append(f"### 段落{i} [{paragraph.type}类]")
            lines.append("")
            lines.append(paragraph.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_event_summary(self, events: List[EventEntry]) -> str:
        """
        格式化事件摘要供Pass 3参考
        
        Args:
            events: 事件列表
        
        Returns:
            格式化后的事件摘要
        """
        if not events:
            return "（无事件）"
        
        lines = []
        for i, event in enumerate(events, 1):
            lines.append(f"{i}. **事件{event.event_id}**：{event.event_summary}")
            lines.append(f"   - 类型：{event.event_type}类")
            lines.append(f"   - 段落：{event.paragraph_indices}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _parse_functional_tags(
        self,
        pass3_output: str,
        segmentation_result: ParagraphSegmentationResult
    ) -> FunctionalTagsLibrary:
        """
        解析Pass 3输出，提取功能性标签
        
        Args:
            pass3_output: Pass 3的LLM输出
            segmentation_result: 分段结果
        
        Returns:
            FunctionalTagsLibrary: 功能性标签库
        """
        logger.info("Parsing Pass 3 output...")
        
        paragraph_tags_list = []
        priority_dist = {"P0-骨架": 0, "P1-血肉": 0, "P2-皮肤": 0}
        first_occurrence_count = 0
        
        # 按段落分割
        paragraph_blocks = re.split(r'##\s*段落\[?(\d+)\]?', pass3_output)
        
        for i in range(1, len(paragraph_blocks), 2):
            paragraph_index = int(paragraph_blocks[i])
            block_content = paragraph_blocks[i + 1] if i + 1 < len(paragraph_blocks) else ""
            
            # 解析标签
            tags = self._parse_paragraph_tags(paragraph_index, block_content)
            if tags:
                paragraph_tags_list.append(tags)
                
                # 统计
                priority_dist[tags.priority] += 1
                if tags.is_first_occurrence:
                    first_occurrence_count += 1
        
        library = FunctionalTagsLibrary(
            chapter_number=segmentation_result.chapter_number,
            total_paragraphs=len(paragraph_tags_list),
            paragraph_tags=paragraph_tags_list,
            priority_distribution=priority_dist,
            first_occurrence_count=first_occurrence_count,
            metadata={}
        )
        
        logger.info(f"Parsed {len(paragraph_tags_list)} paragraph tags")
        logger.info(f"Priority distribution: {priority_dist}")
        logger.info(f"First occurrence count: {first_occurrence_count}")
        
        return library
    
    def _parse_paragraph_tags(
        self,
        paragraph_index: int,
        block_content: str
    ) -> Optional[ParagraphFunctionalTags]:
        """
        解析单个段落的功能性标签
        
        Args:
            paragraph_index: 段落索引
            block_content: 段落标签内容块
        
        Returns:
            ParagraphFunctionalTags或None
        """
        try:
            # 提取各个字段
            narrative_functions = self._extract_list_field(block_content, r'\*\*叙事功能\*\*：\n((?:- .+\n?)+)')
            narrative_structures = self._extract_list_field(block_content, r'\*\*叙事结构\*\*：\n((?:- .+\n?)+)')
            character_tags = self._extract_list_field(block_content, r'\*\*角色与关系\*\*：\n((?:- .+\n?)+)')
            
            # 提取优先级
            priority_match = re.search(r'\*\*浓缩优先级\*\*：\s*(P[0-2]-[^\n]+)', block_content)
            priority = priority_match.group(1).strip() if priority_match else "P1-血肉"
            
            # 提取优先级理由
            reason_match = re.search(r'\*\*优先级理由\*\*：\s*([^\n]+)', block_content)
            priority_reason = reason_match.group(1).strip() if reason_match else ""
            
            # 提取情绪基调
            tone_match = re.search(r'\*\*情绪基调\*\*：\s*([^\n]+)', block_content)
            emotional_tone = tone_match.group(1).strip() if tone_match else None
            if emotional_tone and emotional_tone.lower() in ["无", "中性"]:
                emotional_tone = None
            
            # 提取首次信息
            first_info_match = re.search(r'\*\*首次信息\*\*：\s*(true|false)', block_content, re.IGNORECASE)
            is_first_occurrence = first_info_match.group(1).lower() == "true" if first_info_match else False
            
            # 提取重复强调
            repetition_match = re.search(r'\*\*重复强调\*\*：\s*(\d+)', block_content)
            repetition_count = int(repetition_match.group(1)) if repetition_match else None
            
            # 提取浓缩建议
            advice_match = re.search(r'\*\*浓缩建议\*\*：\n(.+?)(?=\n\n|$)', block_content, re.DOTALL)
            condensation_advice = advice_match.group(1).strip() if advice_match else None
            
            return ParagraphFunctionalTags(
                paragraph_index=paragraph_index,
                narrative_functions=narrative_functions,
                narrative_structures=narrative_structures,
                character_tags=character_tags,
                priority=priority,
                priority_reason=priority_reason,
                emotional_tone=emotional_tone,
                is_first_occurrence=is_first_occurrence,
                repetition_count=repetition_count,
                condensation_advice=condensation_advice
            )
        
        except Exception as e:
            logger.warning(f"Failed to parse paragraph {paragraph_index} tags: {e}")
            return None
    
    def _extract_list_field(self, content: str, pattern: str) -> List[str]:
        """
        提取列表字段（如叙事功能）
        
        Args:
            content: 内容块
            pattern: 正则表达式模式
        
        Returns:
            标签列表
        """
        match = re.search(pattern, content)
        if not match:
            return []
        
        list_content = match.group(1)
        items = re.findall(r'-\s*(.+)', list_content)
        
        # 过滤"无"
        items = [item.strip() for item in items if item.strip().lower() not in ["无", "none"]]
        
        return items
