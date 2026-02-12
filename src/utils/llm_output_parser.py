"""
LLM Output Parser - 统一的 LLM 输出解析工具

提供通用的解析方法，避免在各个工具中重复实现相似的解析逻辑。

使用场景：
- 小说章节分段（NovelSegmenter）
- 脚本分段（ScriptSegmenter）
- 事件标注（NovelAnnotator）
- 设定标注（NovelAnnotator）

作者：AI-Narrated Recap Analyst Team
创建时间：2026-02-10
"""

import re
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class LLMOutputParser:
    """
    统一的 LLM 输出解析器
    
    提供可复用的解析方法，减少代码重复。
    """
    
    @staticmethod
    def parse_segmented_output(
        llm_output: str,
        paragraph_pattern: str,
        range_pattern: str,
        range_key: str = "行号",
        description_group: int = 3,
        type_group: Optional[int] = 2
    ) -> List[Dict[str, Any]]:
        """
        通用的分段输出解析器
        
        解析形如以下格式的 LLM 输出：
        ```
        - **段落1（B类-事件）**：收音机播报上沪沦陷
          行号：1-5
        
        - **段落2（A类-设定）**：诡异爆发背景
          行号：6-10
        ```
        
        Args:
            llm_output: LLM 输出的结构化文本
            paragraph_pattern: 段落头部匹配正则表达式
                例如：r'^\- \*\*段落(\d+)（([ABC])类.*?）\*\*：(.+?)$'
            range_pattern: 范围匹配正则表达式
                例如：r'^\s*行号[：:]\s*(\d+)-(\d+)'
            range_key: 范围关键字（"行号" 或 "句号"），用于日志
            description_group: 描述文本在段落pattern中的组号（默认3）
            type_group: 类型在段落pattern中的组号（可选，默认2）
        
        Returns:
            List[Dict]: 解析后的段落列表
                [
                    {
                        "index": 1,
                        "type": "B",  # 如果有 type_group
                        "description": "收音机播报上沪沦陷",
                        "start_line": 1,
                        "end_line": 5
                    },
                    ...
                ]
        
        Example:
            ```python
            paragraphs = LLMOutputParser.parse_segmented_output(
                llm_output=llm_result,
                paragraph_pattern=r'^\- \*\*段落(\d+)（([ABC])类.*?）\*\*：(.+?)$',
                range_pattern=r'^\s*行号[：:]\s*(\d+)-(\d+)',
                range_key="行号"
            )
            ```
        """
        paragraphs = []
        lines = llm_output.split('\n')
        current_paragraph = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配段落头部
            para_match = re.match(paragraph_pattern, line_stripped)
            if para_match:
                # 保存上一个段落
                if current_paragraph:
                    paragraphs.append(current_paragraph)
                
                # 创建新段落
                current_paragraph = {
                    "index": int(para_match.group(1)),
                    "description": para_match.group(description_group).strip(),
                    "start_line": None,
                    "end_line": None
                }
                
                # 添加类型（如果有）
                if type_group is not None:
                    try:
                        current_paragraph["type"] = para_match.group(type_group)
                    except IndexError:
                        pass
                
                continue
            
            # 匹配范围
            range_match = re.match(range_pattern, line_stripped)
            if range_match and current_paragraph:
                current_paragraph["start_line"] = int(range_match.group(1))
                current_paragraph["end_line"] = int(range_match.group(2))
                continue
        
        # 保存最后一个段落
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        logger.info(f"解析了 {len(paragraphs)} 个段落")
        
        # 验证解析结果
        for para in paragraphs:
            if para.get("start_line") is None or para.get("end_line") is None:
                logger.warning(f"段落 {para['index']} 缺少{range_key}范围")
            else:
                logger.debug(f"段落 {para['index']}: {range_key} {para['start_line']}-{para['end_line']}")
        
        return paragraphs
    
    @staticmethod
    def parse_structured_list(
        llm_output: str,
        entry_pattern: str,
        field_patterns: Dict[str, str],
        entry_name: str = "条目"
    ) -> List[Dict[str, Any]]:
        """
        通用的结构化列表解析器
        
        解析形如以下格式的 LLM 输出：
        ```
        **事件1**：陈野发现诡异世界
        - 时间点：Story-1
        - 概要：收音机播报上沪沦陷，诡异爆发
        - 相关设定：【A1】诡异爆发、【A2】超凡物品
        
        **事件2**：车队夜晚露营
        - 时间点：Story-2
        - 概要：车队在荒野露营
        ```
        
        Args:
            llm_output: LLM 输出文本
            entry_pattern: 条目头部匹配正则（必须捕获序号）
                例如：r'^\*\*事件(\d+)\*\*：(.+?)$'
            field_patterns: 字段匹配模式字典
                例如：{
                    "时间点": r'^\s*-\s*时间点[：:]\s*(.+?)$',
                    "概要": r'^\s*-\s*概要[：:]\s*(.+?)$'
                }
            entry_name: 条目名称（用于日志），默认"条目"
        
        Returns:
            List[Dict]: 解析后的条目列表
                [
                    {
                        "index": 1,
                        "title": "陈野发现诡异世界",
                        "时间点": "Story-1",
                        "概要": "收音机播报..."
                    },
                    ...
                ]
        
        Example:
            ```python
            events = LLMOutputParser.parse_structured_list(
                llm_output=llm_result,
                entry_pattern=r'^\*\*事件(\d+)\*\*：(.+?)$',
                field_patterns={
                    "时间点": r'^\s*-\s*时间点[：:]\s*(.+?)$',
                    "概要": r'^\s*-\s*概要[：:]\s*(.+?)$',
                    "相关设定": r'^\s*-\s*相关设定[：:]\s*(.+?)$'
                },
                entry_name="事件"
            )
            ```
        """
        entries = []
        lines = llm_output.split('\n')
        current_entry = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 匹配条目头部
            entry_match = re.match(entry_pattern, line_stripped)
            if entry_match:
                # 保存上一个条目
                if current_entry:
                    entries.append(current_entry)
                
                # 创建新条目
                current_entry = {
                    "index": int(entry_match.group(1)),
                    "title": entry_match.group(2).strip() if len(entry_match.groups()) > 1 else ""
                }
                continue
            
            # 匹配字段
            if current_entry:
                for field_name, field_pattern in field_patterns.items():
                    field_match = re.match(field_pattern, line_stripped)
                    if field_match:
                        current_entry[field_name] = field_match.group(1).strip()
                        break
        
        # 保存最后一个条目
        if current_entry:
            entries.append(current_entry)
        
        logger.info(f"解析了 {len(entries)} 个{entry_name}")
        
        # 验证必需字段
        for entry in entries:
            missing_fields = [f for f in field_patterns.keys() if f not in entry]
            if missing_fields:
                logger.warning(f"{entry_name} {entry['index']} 缺少字段: {missing_fields}")
        
        return entries
    
    @staticmethod
    def extract_content_by_ranges(
        text: str,
        ranges: List[Dict[str, int]],
        start_key: str = "start_line",
        end_key: str = "end_line",
        split_by: str = '\n'
    ) -> List[str]:
        """
        根据行号/句号范围提取文本内容
        
        Args:
            text: 完整文本
            ranges: 范围列表 [{"start_line": 1, "end_line": 5}, ...]
            start_key: 起始位置的键名（默认 "start_line"）
            end_key: 结束位置的键名（默认 "end_line"）
            split_by: 分割符（默认 '\n' 按行分割）
        
        Returns:
            List[str]: 提取的内容列表
        
        Example:
            ```python
            chapter_lines = chapter_content.split('\n')
            contents = LLMOutputParser.extract_content_by_ranges(
                text=chapter_content,
                ranges=[
                    {"start_line": 1, "end_line": 5},
                    {"start_line": 6, "end_line": 10}
                ]
            )
            ```
        """
        units = text.split(split_by)
        extracted = []
        
        for range_dict in ranges:
            start = range_dict.get(start_key)
            end = range_dict.get(end_key)
            
            if start is None or end is None:
                logger.warning(f"范围缺少起始或结束位置: {range_dict}")
                extracted.append("")
                continue
            
            # 提取内容（1-based index）
            if split_by == '\n':
                content = '\n'.join(units[start-1:end])
            else:
                content = split_by.join(units[start-1:end])
            
            extracted.append(content)
        
        return extracted
    
    @staticmethod
    def validate_no_overlap(
        ranges: List[Dict[str, int]],
        start_key: str = "start_line",
        end_key: str = "end_line"
    ) -> List[str]:
        """
        验证范围是否有重叠
        
        Args:
            ranges: 范围列表
            start_key: 起始位置的键名
            end_key: 结束位置的键名
        
        Returns:
            List[str]: 重叠问题列表（空列表表示无问题）
        
        Example:
            ```python
            issues = LLMOutputParser.validate_no_overlap(paragraphs)
            if issues:
                logger.warning(f"发现重叠: {issues}")
            ```
        """
        issues = []
        sorted_ranges = sorted(ranges, key=lambda x: x.get(start_key, 0))
        
        for i in range(len(sorted_ranges) - 1):
            current_end = sorted_ranges[i].get(end_key)
            next_start = sorted_ranges[i+1].get(start_key)
            
            if current_end is None or next_start is None:
                continue
            
            if current_end >= next_start:
                issues.append(
                    f"范围 {i+1} (结束={current_end}) 与范围 {i+2} (开始={next_start}) 重叠"
                )
        
        return issues
