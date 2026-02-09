"""
NovelSegmenter - 小说章节分段工具（v3, Two-Pass）

基于A/B/C原则对小说章节进行叙事分段，输出JSON格式结果。

- A类-设定：跳脱时间线的设定信息（世界观、规则）
- B类-事件：现实时间线的事件（动作、场景）
- C类-系统：次元空间事件（系统觉醒、系统交互）

实现方式：
1. Two-Pass LLM调用（Pass 1初步分段 + Pass 2校验修正）
2. 代码解析LLM输出（结构化文本 → 段落边界）
3. 在原文中定位段落位置，切分原文
4. 生成JSON输出（可完全还原原文）
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from src.core.interfaces import BaseTool
from src.core.schemas_novel import ParagraphSegment, ParagraphSegmentationResult
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelSegmenter(BaseTool):
    """
    小说章节分段工具
    
    使用Two-Pass策略对章节进行A/B/C分段，输出JSON格式结果。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        ParagraphSegmentationResult: 分段结果（JSON格式，可完全还原原文）
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化分段工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        logger.info(f"NovelSegmenter initialized with {provider}/{self.model}")
    
    def execute(
        self,
        chapter_content: str,
        chapter_number: int,
        **kwargs
    ) -> ParagraphSegmentationResult:
        """
        执行章节分段
        
        Args:
            chapter_content: 章节文本内容（不包含章节标题行）
            chapter_number: 章节序号
            **kwargs: 其他参数
        
        Returns:
            ParagraphSegmentationResult: 分段结果
        """
        logger.info(f"Starting segmentation for chapter {chapter_number}")
        logger.info(f"Chapter content length: {len(chapter_content)} chars")
        
        start_time = time.time()
        
        # Step 1: Two-Pass LLM调用
        logger.info("Step 1: Two-Pass LLM segmentation")
        llm_result_pass2 = self._twopass_llm_segmentation(chapter_content, chapter_number)
        
        # Step 2: 解析LLM输出，提取段落边界
        logger.info("Step 2: Parsing LLM output")
        parsed_paragraphs = self._parse_llm_output(llm_result_pass2)
        
        # Step 3: 在原文中定位段落位置，切分原文
        logger.info("Step 3: Locating paragraph boundaries in original text")
        paragraphs = self._extract_paragraph_contents(
            chapter_content, 
            parsed_paragraphs
        )
        
        # Step 4: 验证原文还原
        logger.info("Step 4: Validating text restoration")
        self._validate_text_restoration(chapter_content, paragraphs)
        
        processing_time = time.time() - start_time
        
        # Step 5: 生成结果
        result = ParagraphSegmentationResult(
            chapter_number=chapter_number,
            total_paragraphs=len(paragraphs),
            paragraphs=paragraphs,
            metadata={
                "type_distribution": self._calculate_type_distribution(paragraphs),
                "processing_time": round(processing_time, 2),
                "model_used": self.model,
                "provider": self.provider
            }
        )
        
        logger.info(f"Segmentation complete: {len(paragraphs)} paragraphs, {processing_time:.2f}s")
        logger.info(f"Type distribution: {result.metadata['type_distribution']}")
        
        return result
    
    def _twopass_llm_segmentation(
        self, 
        chapter_content: str, 
        chapter_number: int
    ) -> str:
        """
        Two-Pass LLM分段
        
        Args:
            chapter_content: 章节内容
            chapter_number: 章节序号
        
        Returns:
            str: Pass 2的修正结果（结构化文本）
        """
        # 为章节内容添加行号
        chapter_lines = chapter_content.split('\n')
        chapter_with_line_numbers = '\n'.join(
            [f"{i+1:4d}| {line}" for i, line in enumerate(chapter_lines)]
        )
        
        # Pass 1: 初步分段
        logger.info("Pass 1: Initial segmentation")
        prompt_pass1 = load_prompts("novel_chapter_segmentation_pass1")
        
        user_prompt_pass1 = prompt_pass1["user_template"].format(
            chapter_content_with_line_numbers=chapter_with_line_numbers,
            chapter_number=chapter_number
        )
        
        pass1_start = time.time()
        response_pass1 = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_pass1["system"]},
                {"role": "user", "content": user_prompt_pass1}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass1_time = time.time() - pass1_start
        
        pass1_result = response_pass1.choices[0].message.content.strip()
        logger.info(f"Pass 1 complete: {pass1_time:.2f}s")
        
        # Pass 2: 校验修正
        logger.info("Pass 2: Validation and correction")
        prompt_pass2 = load_prompts("novel_chapter_segmentation_pass2")
        
        user_prompt_pass2 = prompt_pass2["user_template"].format(
            chapter_content=chapter_content,
            pass1_result=pass1_result,
            chapter_number=chapter_number
        )
        
        pass2_start = time.time()
        response_pass2 = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_pass2["system"]},
                {"role": "user", "content": user_prompt_pass2}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        pass2_time = time.time() - pass2_start
        
        pass2_result = response_pass2.choices[0].message.content.strip()
        logger.info(f"Pass 2 complete: {pass2_time:.2f}s")
        
        # 保存LLM输出用于调试（临时）
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_pass2.md', encoding='utf-8') as f:
            f.write(pass2_result)
            logger.info(f"DEBUG: Pass 2 output saved to {f.name}")
        
        # 判断是否修正
        if "✅ 分段正确，无需修改" in pass2_result or "分段正确" in pass2_result:
            logger.info("Pass 2: No correction needed")
            
            # 保存Pass 1输出用于调试
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_pass1.md', encoding='utf-8') as f:
                f.write(pass1_result)
                logger.info(f"DEBUG: Pass 1 output saved to {f.name}")
            
            return pass1_result
        else:
            logger.info("Pass 2: Corrections applied")
            return pass2_result
    
    def _parse_llm_output(self, llm_output: str) -> List[Dict[str, Any]]:
        """
        解析LLM输出，提取段落行号范围
        
        LLM输出格式示例：
        - **段落1（B类-事件）**：收音机播报上沪沦陷
          行号：1-5
        
        Args:
            llm_output: LLM输出的结构化文本
        
        Returns:
            List[Dict]: 解析后的段落列表
                [
                    {
                        "index": 1,
                        "type": "B",
                        "description": "收音机播报上沪沦陷",
                        "start_line": 1,
                        "end_line": 5
                    },
                    ...
                ]
        """
        paragraphs = []
        
        # 正则匹配段落头部
        # 匹配: - **段落1（B类-事件）**：收音机播报上沪沦陷
        paragraph_pattern = r'^\- \*\*段落(\d+)（([ABC])类.*?）\*\*：(.+?)$'
        
        # 匹配: 行号：1-5
        line_range_pattern = r'^\s*行号[：:]\s*(\d+)-(\d+)'
        
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
                    "type": para_match.group(2),
                    "description": para_match.group(3).strip(),
                    "start_line": None,
                    "end_line": None
                }
                continue
            
            # 匹配行号范围
            range_match = re.match(line_range_pattern, line_stripped)
            if range_match and current_paragraph:
                current_paragraph["start_line"] = int(range_match.group(1))
                current_paragraph["end_line"] = int(range_match.group(2))
                continue
        
        # 保存最后一个段落
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        logger.info(f"Parsed {len(paragraphs)} paragraphs from LLM output")
        
        # 验证解析结果
        for para in paragraphs:
            if para.get("start_line") is None or para.get("end_line") is None:
                logger.warning(f"Paragraph {para['index']} missing line range")
            else:
                logger.debug(f"Paragraph {para['index']}: lines {para['start_line']}-{para['end_line']}")
        
        return paragraphs
    
    def _extract_paragraph_contents(
        self,
        chapter_content: str,
        parsed_paragraphs: List[Dict[str, Any]]
    ) -> List[ParagraphSegment]:
        """
        根据行号从原文中提取段落内容
        
        策略：
        1. 使用LLM输出的行号范围
        2. 从原文中按行号切分段落
        3. 计算字符位置
        
        Args:
            chapter_content: 章节原文
            parsed_paragraphs: 解析后的段落列表（包含行号范围）
        
        Returns:
            List[ParagraphSegment]: 包含完整内容的段落列表
        """
        segments = []
        chapter_lines = chapter_content.split('\n')
        
        for para in parsed_paragraphs:
            start_line = para.get("start_line")
            end_line = para.get("end_line")
            
            if start_line is None or end_line is None:
                raise ValueError(f"Paragraph {para['index']} missing line range")
            
            # 行号从1开始，转换为0-based索引
            start_idx = start_line - 1
            end_idx = end_line  # end_line是inclusive，所以不-1
            
            # 验证行号范围
            if start_idx < 0 or end_idx > len(chapter_lines):
                raise ValueError(
                    f"Paragraph {para['index']} line range out of bounds: "
                    f"{start_line}-{end_line} (total lines: {len(chapter_lines)})"
                )
            
            # 提取段落内容
            paragraph_lines = chapter_lines[start_idx:end_idx]
            content = '\n'.join(paragraph_lines)
            
            # 计算字符位置
            start_char = sum(len(line) + 1 for line in chapter_lines[:start_idx])  # +1 for \n
            end_char = start_char + len(content)
            
            # 创建ParagraphSegment
            segment = ParagraphSegment(
                index=para["index"],
                type=para["type"],
                content=content,
                start_char=start_char,
                end_char=end_char,
                start_line=start_idx,
                end_line=end_idx
            )
            
            segments.append(segment)
            
            logger.debug(f"Paragraph {para['index']} ({para['type']}): "
                        f"lines [{start_line}, {end_line}], "
                        f"chars [{start_char}, {end_char}), "
                        f"length {len(content)}")
        
        return segments
    
    def _validate_text_restoration(
        self,
        original_text: str,
        paragraphs: List[ParagraphSegment]
    ):
        """
        验证段落拼接是否能还原原文
        
        Args:
            original_text: 原始章节文本
            paragraphs: 段落列表
        
        Raises:
            ValueError: 如果无法还原原文
        """
        # 拼接所有段落内容
        restored_text = ''.join([p.content for p in paragraphs])
        
        # 去除尾部空白后比较
        original_stripped = original_text.rstrip()
        restored_stripped = restored_text.rstrip()
        
        if original_stripped == restored_stripped:
            logger.info("✅ Text restoration validation passed")
        else:
            # 计算差异
            diff_ratio = len(set(original_stripped) - set(restored_stripped)) / max(len(original_stripped), 1)
            logger.warning(f"⚠️ Text restoration mismatch: {diff_ratio:.2%} difference")
            logger.warning(f"Original length: {len(original_stripped)}, Restored length: {len(restored_stripped)}")
            
            if diff_ratio > 0.05:  # 差异超过5%
                raise ValueError("Text restoration validation failed: significant difference detected")
    
    def _calculate_type_distribution(
        self,
        paragraphs: List[ParagraphSegment]
    ) -> Dict[str, int]:
        """计算段落类型分布"""
        distribution = {"A": 0, "B": 0, "C": 0}
        for para in paragraphs:
            distribution[para.type] += 1
        return distribution
