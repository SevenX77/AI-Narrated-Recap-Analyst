"""
Script Segmenter Tool
脚本分段工具：使用LLM将连续的脚本文本按语义分段

职责：
1. 接收连续的脚本文本（已处理好标点）
2. 使用LLM按照叙事逻辑进行语义分段
3. 为每个段落匹配对应的SRT时间范围
4. 生成Markdown格式的输出文件
5. 返回分段结果和统计信息
"""

import logging
import time
import re
from pathlib import Path
from typing import List, Optional

from src.core.interfaces import BaseTool
from src.core.schemas_script import SrtEntry, ScriptSegment, ScriptSegmentationResult

logger = logging.getLogger(__name__)


class ScriptSegmenter(BaseTool):
    """
    脚本分段工具
    
    职责：
    - 接收连续的脚本文本（从 SrtTextExtractor 输出）
    - 使用LLM按照叙事逻辑进行语义分段
    - 分段原则：
      * 场景转换：当故事场景、时间、地点发生明显变化时分段
      * 情节转折：当故事出现新的事件、冲突或转折时分段
      * 对话切换：当不同角色的对话结束，进入新的叙述时分段
      * 因果关系：保持因果关系紧密的句子在同一段
      * 自然长度：每段3-8句话为宜
    - 为每个段落匹配对应的SRT时间戳范围
    - 生成Markdown格式输出并保存
    
    Example:
        >>> segmenter = ScriptSegmenter()
        >>> result = segmenter.execute(
        ...     processed_text=text,
        ...     srt_entries=entries,
        ...     project_name="末哥超凡公路",
        ...     episode_name="ep01"
        ... )
        >>> print(result.total_segments)
        >>> print(result.output_file)
    """
    
    name = "script_segmenter"
    description = "Segment script text using LLM semantic analysis"
    
    # 分段标记
    BREAK_MARKER = "---BREAK---"
    
    def __init__(self, use_llm: bool = True, provider: str = "deepseek"):
        """
        Args:
            use_llm: 是否使用LLM语义分段（默认True，必须启用）
            provider: LLM Provider ("claude" | "deepseek")，默认使用 DeepSeek（格式化任务）
        """
        if not use_llm:
            raise ValueError(
                "ScriptSegmenter requires LLM. "
                "Simple rule-based segmentation is not supported."
            )
        
        self.use_llm = use_llm
        self.provider = provider
        self.llm_client = None
        self.model_name = None
        
        try:
            from src.core.llm_client_manager import get_llm_client, get_model_name
            
            self.llm_client = get_llm_client(provider)
            self.model_name = get_model_name(provider)
            logger.info(f"✅ LLM-based script segmentation enabled (provider: {provider})")
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
            ScriptSegmentationResult: 分段结果（包含段落列表和输出文件路径）
        """
        start_time = time.time()
        
        logger.info(f"Segmenting script text: {len(processed_text)} chars")
        
        # Step 1: 使用LLM进行语义分段
        marked_text = self._segment_with_llm(processed_text)
        
        # Step 2: 按标记分割段落
        text_segments = self._split_by_markers(marked_text)
        logger.info(f"Split into {len(text_segments)} text segments")
        
        # Step 3: 为每个段落匹配时间戳
        segments = self._match_timestamps_to_paragraphs(text_segments, srt_entries)
        logger.info(f"Matched timestamps to {len(segments)} segments")
        
        # Step 4: 生成Markdown并保存
        output_file = self._generate_and_save_markdown(
            segments, project_name, episode_name
        )
        
        # Step 5: 统计信息
        avg_sentence_count = (
            sum(seg.sentence_count for seg in segments) / len(segments)
            if segments else 0.0
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Segmentation complete: {len(segments)} paragraphs in {processing_time:.2f}s")
        
        # Step 6: 构建返回结果
        return ScriptSegmentationResult(
            segments=segments,
            total_segments=len(segments),
            avg_sentence_count=avg_sentence_count,
            segmentation_mode="semantic",
            output_file=str(output_file),
            processing_time=processing_time
        )
    
    def _segment_with_llm(self, text: str) -> str:
        """
        使用LLM进行语义分段
        
        Args:
            text: 处理后的完整文本
        
        Returns:
            带分段标记的文本
        """
        if not self.llm_client:
            raise RuntimeError("LLM client not initialized")
        
        # 构建分段prompt
        prompt = f"""请将以下解说词文本按照语义逻辑分段。

分段原则：
1. **场景转换**：当故事场景、时间、地点发生明显变化时分段
2. **情节转折**：当故事出现新的事件、冲突或转折时分段
3. **对话切换**：当不同角色的对话结束，进入新的叙述时分段
4. **因果关系**：保持因果关系紧密的句子在同一段
5. **自然长度**：每段3-8句话为宜，避免过长或过短

输出格式：
使用"{self.BREAK_MARKER}"标记分段位置（插入在需要分段的句子之间）

文本：
{text}

请在合适的位置插入"{self.BREAK_MARKER}"来标记分段。只输出带标记的文本，不要添加任何解释。"""
        
        try:
            logger.info("Calling LLM for semantic segmentation...")
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的文本编辑，擅长按照语义逻辑进行段落划分。你的任务是在文本中插入分段标记，不要添加任何其他内容。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=6000
            )
            
            marked_text = response.choices[0].message.content.strip()
            logger.info("LLM segmentation completed successfully")
            return marked_text
        
        except Exception as e:
            logger.error(f"LLM segmentation failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to segment text with LLM: {e}")
    
    def _split_by_markers(self, marked_text: str) -> List[str]:
        """
        按标记分割段落
        
        Args:
            marked_text: 带分段标记的文本
        
        Returns:
            段落列表
        """
        segments = marked_text.split(self.BREAK_MARKER)
        segments = [seg.strip() for seg in segments if seg.strip()]
        
        if not segments:
            # 如果没有标记，至少返回完整文本
            logger.warning("No break markers found, treating entire text as one segment")
            segments = [marked_text.strip()]
        
        return segments
    
    def _match_timestamps_to_paragraphs(
        self,
        text_segments: List[str],
        srt_entries: List[SrtEntry]
    ) -> List[ScriptSegment]:
        """
        为段落匹配时间戳
        
        Args:
            text_segments: 文本段落列表
            srt_entries: SRT条目列表
        
        Returns:
            带时间戳的段落列表
        """
        segments = []
        entry_index = 0
        
        for seg_idx, segment_text in enumerate(text_segments, 1):
            # 计算这段文本大约对应的SRT条目范围
            segment_length = len(segment_text)
            char_count = 0
            start_index = entry_index
            
            # 累积字符数直到达到segment_length
            while entry_index < len(srt_entries) and char_count < segment_length:
                char_count += len(srt_entries[entry_index].text)
                entry_index += 1
            
            # 确保至少匹配一个条目
            if entry_index == start_index and entry_index < len(srt_entries):
                entry_index += 1
            
            # 获取起止时间
            start_time = (
                srt_entries[start_index].start_time
                if start_index < len(srt_entries)
                else "00:00:00,000"
            )
            end_time = (
                srt_entries[min(entry_index - 1, len(srt_entries) - 1)].end_time
                if entry_index > 0
                else start_time
            )
            
            # 计算句子数量
            sentence_count = (
                segment_text.count('。') +
                segment_text.count('！') +
                segment_text.count('？')
            )
            
            segments.append(ScriptSegment(
                index=seg_idx,
                content=segment_text,
                start_time=start_time,
                end_time=end_time,
                sentence_count=sentence_count,
                char_count=len(segment_text)
            ))
        
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
            # 段落标题：时间戳
            lines.append(f"## [{seg.start_time} - {seg.end_time}]\n")
            
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
