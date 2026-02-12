"""
Script Segmenter Tool v2
脚本分段工具：使用Two-Pass LLM将脚本按语义分段

职责：
1. 接收连续的脚本文本（已处理好标点）
2. 使用Two-Pass LLM按照叙事逻辑进行语义分段
3. 为每个段落匹配对应的SRT时间范围
4. 返回JSON格式的分段结果
"""

import logging
import time
import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.core.interfaces import BaseTool
from src.core.schemas_script import SrtEntry, ScriptSegment, ScriptSegmentationResult
from src.utils.prompt_loader import load_prompts
from src.utils.llm_output_parser import LLMOutputParser
from src.core.exceptions import ToolExecutionError, LLMCallError, ParsingError

logger = logging.getLogger(__name__)


class ScriptSegmenter(BaseTool):
    """
    脚本分段工具 v2 - Two-Pass + JSON输出
    
    职责：
    - 接收连续的脚本文本（从 SrtTextExtractor 输出）
    - 使用Two-Pass LLM按照叙事逻辑进行语义分段
    - 分段原则：
      * 场景转换：当故事场景、时间、地点发生明显变化时分段
      * 情节转折：当故事出现新的事件、冲突或转折时分段
      * 对话切换：当不同角色的对话结束，进入新的叙述时分段
      * 因果关系：保持因果关系紧密的句子在同一段
    - 为每个段落匹配对应的SRT时间戳范围
    - 输出JSON格式的分段结果
    
    Example:
        >>> segmenter = ScriptSegmenter()
        >>> result = segmenter.execute(
        ...     processed_text=text,
        ...     srt_entries=entries,
        ...     project_name="末哥超凡公路",
        ...     episode_name="ep01"
        ... )
        >>> print(result.total_segments)
        >>> print(result.segments)
    """
    
    name = "script_segmenter"
    description = "Segment script text using Two-Pass LLM semantic analysis"
    
    def __init__(self, provider: str = "deepseek"):
        """
        Args:
            provider: LLM Provider ("claude" | "deepseek")，默认使用 DeepSeek（待测试性能）
        """
        self.provider = provider
        self.llm_client = None
        self.model_name = None
        
        try:
            from src.core.llm_client_manager import get_llm_client, get_model_name
            
            self.llm_client = get_llm_client(provider)
            self.model_name = get_model_name(provider)
            logger.info(f"ScriptSegmenter initialized with {provider}/{self.model_name}")
        except Exception as e:
            raise ValueError(f"Failed to initialize LLM client: {e}")
    
    def execute(
        self,
        processed_text: str,
        srt_entries: List[SrtEntry],
        project_name: str,
        episode_name: str
    ) -> ScriptSegmentationResult:
        """
        执行脚本分段
        
        Args:
            processed_text: 连续的脚本文本（从 SrtTextExtractor 输出）
            srt_entries: SRT条目列表（用于匹配时间戳）
            project_name: 项目名称
            episode_name: 集数名称
        
        Returns:
            ScriptSegmentationResult: 分段结果（JSON格式）
        """
        start_time = time.time()
        
        logger.info(f"Starting segmentation for {episode_name}")
        logger.info(f"Script text length: {len(processed_text)} chars")
        
        # Step 1: Two-Pass LLM segmentation
        logger.info("Step 1: Two-Pass LLM segmentation")
        pass2_result = self._twopass_llm_segmentation(processed_text, episode_name)
        
        # Step 2: Parsing LLM output
        logger.info("Step 2: Parsing LLM output")
        parsed_paragraphs = self._parse_llm_output(pass2_result)
        
        # Step 3: Extracting paragraph contents by sentence numbers
        logger.info("Step 3: Extracting paragraph contents by sentence numbers")
        segments = self._extract_paragraph_contents_by_sentences(
            processed_text, 
            parsed_paragraphs,
            srt_entries
        )
        
        # Step 3.5: ABC Classification
        logger.info("Step 3.5: ABC Classification")
        segments = self._classify_segments_abc(segments)
        
        # Step 4: Statistics
        avg_sentence_count = (
            sum(seg.sentence_count for seg in segments) / len(segments)
            if segments else 0.0
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Segmentation complete: {len(segments)} segments, {processing_time:.2f}s")
        logger.info(f"Average sentence count per segment: {avg_sentence_count:.1f}")
        
        # Step 5: Generate and save Markdown
        logger.info("Step 4: Generating Markdown output")
        output_file = self._generate_and_save_markdown(
            segments, project_name, episode_name
        )
        
        # Step 6: Build result
        return ScriptSegmentationResult(
            segments=segments,
            total_segments=len(segments),
            avg_sentence_count=avg_sentence_count,
            segmentation_mode="two_pass",
            output_file=str(output_file),
            processing_time=processing_time
        )
    
    def _twopass_llm_segmentation(
        self, 
        script_content: str, 
        episode_name: str
    ) -> str:
        """
        Two-Pass LLM分段
        
        Args:
            script_content: 脚本内容
            episode_name: 集数名称
        
        Returns:
            str: Pass 2的修正结果（结构化文本）
        """
        # 为脚本内容添加句子序号
        sentences = self._split_sentences(script_content)
        script_with_sentence_numbers = '\n'.join(
            [f"{i+1:4d}. {sent}" for i, sent in enumerate(sentences)]
        )
        
        # Pass 1: 初步分段
        logger.info("Pass 1: Initial segmentation")
        prompt_pass1 = load_prompts("script_segmentation_pass1")
        
        user_prompt_pass1 = prompt_pass1["user_template"].format(
            script_content_with_sentence_numbers=script_with_sentence_numbers,
            episode_name=episode_name
        )
        
        start_time_pass1 = time.time()
        response_pass1 = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": prompt_pass1["system"]},
                {"role": "user", "content": user_prompt_pass1}
            ],
            temperature=0.1,
            max_tokens=4096
        )
        pass1_result = response_pass1.choices[0].message.content.strip()
        logger.info(f"Pass 1 complete: {time.time() - start_time_pass1:.2f}s")
        
        # Pass 2: 校验修正
        logger.info("Pass 2: Validation and correction")
        prompt_pass2 = load_prompts("script_segmentation_pass2")
        
        user_prompt_pass2 = prompt_pass2["user_template"].format(
            script_content_with_sentence_numbers=script_with_sentence_numbers,
            pass1_result=pass1_result,
            episode_name=episode_name
        )
        
        start_time_pass2 = time.time()
        response_pass2 = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": prompt_pass2["system"]},
                {"role": "user", "content": user_prompt_pass2}
            ],
            temperature=0.1,
            max_tokens=4096
        )
        pass2_result = response_pass2.choices[0].message.content.strip()
        logger.info(f"Pass 2 complete: {time.time() - start_time_pass2:.2f}s")
        
        # 判断是否需要修正
        if "✅ 分段正确，无需修改" in pass2_result or "无需修改" in pass2_result:
            logger.info("Pass 2: No corrections needed")
            return pass1_result
        else:
            logger.info("Pass 2: Corrections applied")
            return pass2_result
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        将文本按句子拆分
        
        Args:
            text: 完整文本
        
        Returns:
            List[str]: 句子列表
        """
        # 按中文句子结束符拆分
        sentences = re.split(r'([。！？])', text)
        
        # 将标点符号合并回句子
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                if sentence.strip():
                    result.append(sentence.strip())
        
        # 处理最后可能剩余的文本
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1].strip())
        
        return result
    
    def _parse_llm_output(self, llm_output: str) -> List[Dict[str, Any]]:
        """
        解析LLM输出，提取段落句子序号范围
        
        使用统一的 LLMOutputParser 工具进行解析。
        
        LLM输出格式示例：
        - **段落1**：收音机播报消息
          句号：1-3
        
        Args:
            llm_output: LLM输出的结构化文本
        
        Returns:
            List[Dict]: 解析后的段落列表
        
        Raises:
            ParsingError: 解析失败时抛出
        """
        try:
            # 使用统一的解析工具
            paragraphs = LLMOutputParser.parse_segmented_output(
                llm_output=llm_output,
                paragraph_pattern=r'^\- \*\*段落(\d+)\*\*：(.+?)$',
                range_pattern=r'^\s*句号[：:]\s*(\d+)-(\d+)',
                range_key="句号",
                description_group=2,
                type_group=None  # 脚本分段没有类型
            )
            
            # 转换字段名（start_line → start_sentence）
            for para in paragraphs:
                para["start_sentence"] = para.pop("start_line")
                para["end_sentence"] = para.pop("end_line")
            
            logger.info(f"✅ 成功解析 {len(paragraphs)} 个段落")
            return paragraphs
            
        except Exception as e:
            logger.error(f"❌ LLM输出解析失败: {e}")
            raise ParsingError(
                message="脚本分段解析失败",
                parser_name="ScriptSegmenter",
                raw_output=llm_output[:200],
                original_error=e
            )
    
    def _extract_paragraph_contents_by_sentences(
        self,
        script_content: str,
        parsed_paragraphs: List[Dict[str, Any]],
        srt_entries: List[SrtEntry]
    ) -> List[ScriptSegment]:
        """
        根据句子序号从原文中提取段落内容，并匹配SRT时间戳
        
        Args:
            script_content: 脚本原文
            parsed_paragraphs: 解析后的段落列表（包含句子序号范围）
            srt_entries: SRT条目列表
        
        Returns:
            List[ScriptSegment]: 包含完整内容和时间戳的段落列表
        """
        segments = []
        sentences = self._split_sentences(script_content)
        
        for para in parsed_paragraphs:
            start_sent = para.get("start_sentence")
            end_sent = para.get("end_sentence")
            
            if start_sent is None or end_sent is None:
                raise ValueError(f"Paragraph {para['index']} missing sentence range")
            
            # 句子序号从1开始，转换为0-based索引
            start_idx = start_sent - 1
            end_idx = end_sent  # end_sent是inclusive，所以不-1
            
            # 验证句子序号范围
            if start_idx < 0 or end_idx > len(sentences):
                raise ValueError(
                    f"Paragraph {para['index']} sentence range out of bounds: "
                    f"{start_sent}-{end_sent} (total sentences: {len(sentences)})"
                )
            
            # 提取段落内容
            paragraph_sentences = sentences[start_idx:end_idx]
            content = ''.join(paragraph_sentences)
            
            # 计算字符位置（用于匹配SRT时间戳）
            start_char = sum(len(s) for s in sentences[:start_idx])
            end_char = start_char + len(content)
            
            # 匹配SRT时间戳
            start_time, end_time = self._match_timestamps(
                start_char, end_char, script_content, srt_entries
            )
            
            # 创建ScriptSegment
            segment = ScriptSegment(
                index=para["index"],
                content=content,
                start_time=start_time,
                end_time=end_time,
                sentence_count=len(paragraph_sentences),
                char_count=len(content)
            )
            
            segments.append(segment)
            
            logger.debug(f"Segment {para['index']}: "
                        f"sentences [{start_sent}, {end_sent}], "
                        f"chars [{start_char}, {end_char}), "
                        f"time [{start_time} - {end_time}]")
        
        return segments
    
    def _match_timestamps(
        self,
        start_char: int,
        end_char: int,
        script_content: str,
        srt_entries: List[SrtEntry]
    ) -> tuple:
        """
        根据字符位置匹配SRT时间戳
        
        Args:
            start_char: 段落起始字符位置
            end_char: 段落结束字符位置
            script_content: 完整脚本内容
            srt_entries: SRT条目列表
        
        Returns:
            (start_time, end_time): 时间戳元组
        """
        # 简单策略：根据字符位置比例映射到SRT条目
        total_chars = len(script_content)
        
        # 计算起始和结束位置占比
        start_ratio = start_char / total_chars if total_chars > 0 else 0
        end_ratio = end_char / total_chars if total_chars > 0 else 0
        
        # 映射到SRT条目索引
        start_index = int(start_ratio * len(srt_entries))
        end_index = int(end_ratio * len(srt_entries))
        
        # 边界检查
        start_index = max(0, min(start_index, len(srt_entries) - 1))
        end_index = max(start_index, min(end_index, len(srt_entries) - 1))
        
        start_time = srt_entries[start_index].start_time
        end_time = srt_entries[end_index].end_time
        
        return start_time, end_time
    
    def _classify_segments_abc(
        self,
        segments: List[ScriptSegment]
    ) -> List[ScriptSegment]:
        """
        对段落进行ABC分类
        
        Args:
            segments: 段落列表
        
        Returns:
            添加了category字段的段落列表
        """
        if not segments:
            return segments
        
        # 格式化段落文本
        segments_text = []
        for seg in segments:
            segments_text.append(f"【段落{seg.index}】({seg.start_time} - {seg.end_time})")
            segments_text.append(f"{seg.content}")
            segments_text.append("")
        
        segments_text_str = '\n'.join(segments_text)
        
        # 加载Prompt
        prompt_abc = load_prompts("script_segmentation_abc_classification")
        
        user_prompt = prompt_abc["user_template"].format(
            segments_text=segments_text_str
        )
        
        # 调用LLM进行分类
        try:
            start_time = time.time()
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt_abc["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            classifications = result_json.get("classifications", [])
            
            logger.info(f"ABC Classification complete: {time.time() - start_time:.2f}s")
            
            # 将分类结果应用到segments
            classification_dict = {
                item["index"]: item["category"] 
                for item in classifications
            }
            
            for seg in segments:
                seg.category = classification_dict.get(seg.index, "B")  # 默认B类
            
            # 统计各类数量
            category_counts = {"A": 0, "B": 0, "C": 0}
            for seg in segments:
                if seg.category in category_counts:
                    category_counts[seg.category] += 1
            
            logger.info(f"   Classification: A={category_counts['A']}, B={category_counts['B']}, C={category_counts['C']}")
            
        except Exception as e:
            logger.error(f"ABC Classification failed: {e}")
            logger.info("   Falling back to default category (B) for all segments")
            for seg in segments:
                seg.category = "B"
        
        return segments
    
    def _generate_and_save_markdown(
        self,
        segments: List[ScriptSegment],
        project_name: str,
        episode_name: str
    ) -> Path:
        """
        生成Markdown格式输出并保存
        
        Args:
            segments: 段落列表
            project_name: 项目名称
            episode_name: 集数名称
        
        Returns:
            输出文件路径
        """
        # 生成Markdown内容
        lines = []
        
        # 添加标题
        lines.append(f"# {episode_name}\n")
        
        # 添加每个段落
        for seg in segments:
            # 段落标题：时间戳 + 分类
            category_tag = f" [{seg.category}]" if seg.category else ""
            lines.append(f"## [{seg.start_time} - {seg.end_time}]{category_tag}\n")
            
            # 段落内容
            lines.append(f"{seg.content}\n")
        
        markdown_content = '\n'.join(lines)
        
        # 保存到项目目录
        project_dir = Path("data/projects") / project_name / "script"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = project_dir / f"{episode_name}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown saved to: {output_file}")
        
        return output_file