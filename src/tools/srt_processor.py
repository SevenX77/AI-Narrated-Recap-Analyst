"""
SRT Script Processor
SRT字幕处理工具：将碎片化字幕转换为可读文本
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from src.core.interfaces import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class SrtEntry:
    """SRT字幕条目"""
    index: int
    start_time: str
    end_time: str
    text: str


@dataclass
class SemanticParagraph:
    """语义段落"""
    content: str
    start_time: str
    end_time: str
    sentence_count: int


@dataclass
class EntityStandardization:
    """实体标准化结果"""
    standard_form: str
    variants: List[str]
    reasoning: str
    confidence: float


@dataclass
class ProcessingReport:
    """处理报告"""
    episode: str
    processing_mode: str  # "with_novel" or "without_novel"
    original_chars: int
    processed_chars: int
    paragraphs: int
    srt_entries: int
    entity_standardization: Dict[str, Dict[str, EntityStandardization]]
    corrections: Dict[str, int]
    processing_time_seconds: float


class SrtScriptProcessor(BaseTool):
    """
    SRT字幕处理工具
    
    功能：
    1. 解析SRT格式，提取文本
    2. 智能添加标点符号
    3. 实体识别与标准化（有/无小说参考两种模式）
    4. 上下文修复（缺字、错字）
    5. 自然段落划分
    
    使用场景：
    - with_novel模式：从小说提取标准实体，直接对齐
    - without_novel模式：从字幕自身识别实体变体，智能推断标准形式
    """
    
    name = "srt_script_processor"
    description = "Process SRT subtitles into readable script text with entity standardization"
    
    def __init__(self, use_llm: bool = True, min_paragraph_length: int = 50, max_paragraph_length: int = 300):
        """
        Args:
            use_llm: 是否使用LLM智能处理
            min_paragraph_length: 最小段落字符数
            max_paragraph_length: 最大段落字符数
        """
        self.use_llm = use_llm
        self.min_paragraph_length = min_paragraph_length
        self.max_paragraph_length = max_paragraph_length
        self.llm_client = None
        self.prompt_config_with_novel = None
        self.prompt_config_without_novel = None
        
        if self.use_llm:
            try:
                from openai import OpenAI
                from src.core.config import config
                from src.utils.prompt_loader import load_prompts
                
                if config.llm.api_key:
                    self.llm_client = OpenAI(
                        api_key=config.llm.api_key,
                        base_url=config.llm.base_url
                    )
                    self.prompt_config_with_novel = load_prompts("srt_script_processing_with_novel")
                    self.prompt_config_without_novel = load_prompts("srt_script_processing_without_novel")
                    logger.info("LLM-based SRT processing enabled")
                else:
                    logger.warning("API key not found, falling back to rule-based processing")
                    self.use_llm = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}, falling back to rule-based processing")
                self.use_llm = False
    
    def execute(self, 
                srt_file_path: Path,
                output_dir: Path,
                novel_reference: Optional[str] = None,
                episode_name: Optional[str] = None,
                use_semantic_segmentation: bool = True) -> Dict[str, Any]:
        """
        执行SRT处理
        
        Args:
            srt_file_path: SRT文件路径
            output_dir: 输出目录（script/）
            novel_reference: 小说参考文本（可选，前3章即可）
            episode_name: 集数名称（如"ep01"，用于报告）
        
        Returns:
            处理报告
        """
        import time
        start_time = time.time()
        
        if episode_name is None:
            episode_name = srt_file_path.stem
        
        logger.info(f"Processing SRT file: {srt_file_path.name} (mode: {'with_novel' if novel_reference else 'without_novel'})")
        
        # 1. 解析SRT
        srt_entries = self._parse_srt(srt_file_path)
        raw_text = self._extract_text_from_entries(srt_entries)
        
        # 2. 根据是否有小说参考选择处理模式
        if novel_reference and self.use_llm:
            processed_text, entity_info = self._process_with_novel_reference(raw_text, novel_reference)
            processing_mode = "with_novel"
        elif self.use_llm:
            processed_text, entity_info = self._process_without_novel_reference(raw_text)
            processing_mode = "without_novel"
        else:
            # 降级：规则处理
            processed_text = self._process_rule_based(raw_text)
            entity_info = {}
            processing_mode = "rule_based"
        
        # 3. 语义段落划分（使用LLM或规则）
        if use_semantic_segmentation and self.use_llm:
            paragraphs = self._segment_paragraphs_semantic(processed_text, srt_entries)
        else:
            # 降级：简单规则分段
            paragraphs = self._segment_paragraphs_simple(processed_text, srt_entries)
        
        # 4. 生成Markdown格式输出
        markdown_content = self._generate_markdown(paragraphs, episode_name)
        
        # 5. 写入输出（markdown格式）
        output_file = output_dir / f"{episode_name}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Script saved to: {output_file}")
        
        # 6. 生成报告
        processing_time = time.time() - start_time
        report = {
            "episode": episode_name,
            "processing_mode": processing_mode,
            "output_file": str(output_file),
            "stats": {
                "original_chars": len(raw_text),
                "processed_chars": len(markdown_content),
                "paragraphs": len(paragraphs),
                "srt_entries": len(srt_entries),
                "avg_paragraph_sentences": sum(p.sentence_count for p in paragraphs) / len(paragraphs) if paragraphs else 0,
                "processing_time_seconds": round(processing_time, 2)
            },
            "entity_standardization": entity_info,
            "paragraphs_info": [
                {
                    "index": i,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "sentence_count": p.sentence_count,
                    "char_count": len(p.content)
                }
                for i, p in enumerate(paragraphs, 1)
            ]
        }
        
        # 保存报告
        report_file = output_dir / f"{episode_name}_processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processing complete: {len(srt_entries)} entries → {report['stats']['paragraphs']} paragraphs")
        return report
    
    def _parse_srt(self, srt_file_path: Path) -> List[SrtEntry]:
        """
        解析SRT文件
        
        Args:
            srt_file_path: SRT文件路径
        
        Returns:
            SRT条目列表
        """
        with open(srt_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 规范化换行符
        content = content.replace('\r\n', '\n')
        
        entries = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
                time_line = lines[1]
                text = '\n'.join(lines[2:])
                
                # 解析时间戳
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                if time_match:
                    start_time = time_match.group(1)
                    end_time = time_match.group(2)
                    
                    entries.append(SrtEntry(
                        index=index,
                        start_time=start_time,
                        end_time=end_time,
                        text=text.strip()
                    ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse SRT block: {block[:50]}... Error: {e}")
                continue
        
        logger.info(f"Parsed {len(entries)} SRT entries from {srt_file_path.name}")
        return entries
    
    def _extract_text_from_entries(self, entries: List[SrtEntry]) -> str:
        """
        从SRT条目中提取文本
        
        Args:
            entries: SRT条目列表
        
        Returns:
            连续文本
        """
        texts = [entry.text for entry in entries]
        return '\n'.join(texts)
    
    def _process_with_novel_reference(self, raw_text: str, novel_reference: str) -> Tuple[str, Dict]:
        """
        有小说参考时的处理流程
        
        Args:
            raw_text: 原始字幕文本
            novel_reference: 小说参考文本
        
        Returns:
            (processed_text, entity_info)
        """
        logger.info("Processing with novel reference")
        
        # 步骤1：从小说提取标准实体
        novel_entities = self._extract_entities_from_novel(novel_reference)
        
        # 步骤2：使用LLM处理字幕
        processed_text = self._process_with_llm_and_entities(
            raw_text, 
            novel_entities, 
            mode="with_novel"
        )
        
        entity_info = {
            "source": "novel_reference",
            "entities": novel_entities
        }
        
        return processed_text, entity_info
    
    def _process_without_novel_reference(self, raw_text: str) -> Tuple[str, Dict]:
        """
        无小说参考时的处理流程
        
        Args:
            raw_text: 原始字幕文本
        
        Returns:
            (processed_text, entity_info)
        """
        logger.info("Processing without novel reference (intelligent entity extraction)")
        
        # 使用LLM智能提取和标准化实体
        result = self._extract_and_standardize_entities_with_llm(raw_text)
        
        return result["processed_text"], result["entity_standardization"]
    
    def _extract_entities_from_novel(self, novel_text: str) -> Dict[str, List[str]]:
        """
        从小说中提取标准实体名称
        
        Args:
            novel_text: 小说文本（前3章）
        
        Returns:
            {
                "characters": [...],
                "locations": [...],
                "items": [...]
            }
        """
        # 简化实现：使用正则和常见模式提取
        # TODO: 可以增强为LLM提取
        
        entities = {
            "characters": [],
            "locations": [],
            "items": []
        }
        
        # 提取人名（常见姓氏+名字）
        name_pattern = r'[\u4e00-\u9fa5]{2,4}(?:公主|王爷|皇帝|淑妃|大人|先生|小姐)'
        characters = re.findall(name_pattern, novel_text[:2000])
        entities["characters"] = list(set(characters))[:20]  # 取前20个
        
        # 提取地点（含"地"/"城"/"宫"等）
        location_pattern = r'[\u4e00-\u9fa5]{2,6}(?:城|宫|地|国|州|省|县)'
        locations = re.findall(location_pattern, novel_text[:2000])
        entities["locations"] = list(set(locations))[:15]
        
        logger.info(f"Extracted entities from novel: {len(entities['characters'])} characters, {len(entities['locations'])} locations")
        
        return entities
    
    def _process_with_llm_and_entities(self, raw_text: str, entities: Dict[str, List[str]], mode: str) -> str:
        """
        使用LLM和实体表处理文本
        
        Args:
            raw_text: 原始文本
            entities: 实体表
            mode: "with_novel" 或其他
        
        Returns:
            处理后的文本
        """
        if not self.llm_client or not self.prompt_config_with_novel:
            logger.warning("LLM not available, falling back to rule-based")
            return self._process_rule_based(raw_text)
        
        # 构建prompt
        user_prompt = self.prompt_config_with_novel["user_template"].format(
            srt_text=raw_text,
            novel_characters=", ".join(entities.get("characters", [])),
            novel_locations=", ".join(entities.get("locations", [])),
            novel_items=", ".join(entities.get("items", []))
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.prompt_config_with_novel.get("settings", {}).get("model", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": self.prompt_config_with_novel["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.prompt_config_with_novel.get("settings", {}).get("temperature", 0.2),
                max_tokens=self.prompt_config_with_novel.get("settings", {}).get("max_tokens", 3000)
            )
            
            processed_text = response.choices[0].message.content.strip()
            return processed_text
        
        except Exception as e:
            logger.error(f"LLM processing failed: {e}", exc_info=True)
            return self._process_rule_based(raw_text)
    
    def _extract_and_standardize_entities_with_llm(self, raw_text: str) -> Dict[str, Any]:
        """
        使用LLM提取并标准化实体（无小说参考模式）
        
        Args:
            raw_text: 原始字幕文本
        
        Returns:
            {
                "processed_text": "...",
                "entity_standardization": {...}
            }
        """
        if not self.llm_client or not self.prompt_config_without_novel:
            logger.warning("LLM not available, falling back to rule-based")
            return {
                "processed_text": self._process_rule_based(raw_text),
                "entity_standardization": {}
            }
        
        # 构建prompt
        user_prompt = self.prompt_config_without_novel["user_template"].format(
            srt_text=raw_text
        )
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.prompt_config_without_novel.get("settings", {}).get("model", "deepseek-chat"),
                messages=[
                    {"role": "system", "content": self.prompt_config_without_novel["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.prompt_config_without_novel.get("settings", {}).get("temperature", 0.2),
                max_tokens=self.prompt_config_without_novel.get("settings", {}).get("max_tokens", 4000)
            )
            
            content = response.choices[0].message.content.strip()
            
            # 解析输出（期望格式：JSON实体表 + 分隔符 + 处理后文本）
            result = self._parse_llm_output_without_novel(content)
            
            return result
        
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}", exc_info=True)
            return {
                "processed_text": self._process_rule_based(raw_text),
                "entity_standardization": {}
            }
    
    def _parse_llm_output_without_novel(self, llm_output: str) -> Dict[str, Any]:
        """
        解析LLM输出（无小说参考模式）
        
        期望格式：
        【实体表】
        ```json
        {...}
        ```
        
        【处理后文本】
        ...
        
        Args:
            llm_output: LLM原始输出
        
        Returns:
            {
                "processed_text": "...",
                "entity_standardization": {...}
            }
        """
        # 尝试提取JSON部分
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', llm_output, re.DOTALL)
        
        entity_standardization = {}
        processed_text = llm_output
        
        if json_match:
            try:
                entity_data = json.loads(json_match.group(1))
                entity_standardization = entity_data
                
                # 提取处理后文本（JSON之后的部分）
                text_start = json_match.end()
                remaining_text = llm_output[text_start:].strip()
                
                # 查找"处理后文本"标记
                text_markers = ['【处理后文本】', '【处理后的文本】', '处理后文本：', '---']
                for marker in text_markers:
                    if marker in remaining_text:
                        processed_text = remaining_text.split(marker, 1)[1].strip()
                        break
                else:
                    # 如果没有找到标记，使用所有剩余文本
                    processed_text = remaining_text
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM output: {e}")
        
        else:
            # 如果没有JSON，尝试查找分隔符
            if '---' in llm_output:
                parts = llm_output.split('---', 1)
                if len(parts) > 1:
                    processed_text = parts[1].strip()
        
        # 清理可能的markdown格式
        processed_text = processed_text.replace('```', '').strip()
        
        return {
            "processed_text": processed_text,
            "entity_standardization": entity_standardization
        }
    
    def _process_rule_based(self, raw_text: str) -> str:
        """
        基于规则的降级处理
        
        Args:
            raw_text: 原始文本
        
        Returns:
            处理后的文本
        """
        logger.info("Using rule-based processing (fallback)")
        
        # 简单合并行，添加基本标点
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # 合并短句
        merged = []
        buffer = ""
        
        for line in lines:
            buffer += line
            
            # 如果遇到明显的句子结尾，或buffer过长
            if len(buffer) > 100 or line.endswith(('。', '！', '？', '：')):
                merged.append(buffer)
                buffer = ""
        
        if buffer:
            merged.append(buffer)
        
        # 简单标点处理
        processed = []
        for sentence in merged:
            # 如果没有标点，添加句号
            if not sentence.endswith(('。', '！', '？', '：', '，')):
                sentence += '。'
            processed.append(sentence)
        
        return ''.join(processed)
    
    def _segment_paragraphs_semantic(self, text: str, srt_entries: List[SrtEntry]) -> List[SemanticParagraph]:
        """
        使用LLM进行语义分段
        
        Args:
            text: 处理后的完整文本
            srt_entries: SRT条目列表（用于获取时间戳）
        
        Returns:
            语义段落列表
        """
        if not self.llm_client:
            logger.warning("LLM not available, falling back to simple segmentation")
            return self._segment_paragraphs_simple(text, srt_entries)
        
        try:
            # 构建分段prompt
            prompt = f"""请将以下文本按照语义逻辑分段。

分段原则：
1. **场景转换**：当故事场景、时间、地点发生明显变化时分段
2. **情节转折**：当故事出现新的事件、冲突或转折时分段
3. **对话切换**：当不同角色的对话结束，进入新的叙述时分段
4. **因果关系**：保持因果关系紧密的句子在同一段
5. **自然长度**：每段3-8句话为宜，避免过长或过短

输出格式：
使用"---BREAK---"标记分段位置（插入在需要分段的句子之间）

文本：
{text}

请在合适的位置插入"---BREAK---"来标记分段。"""
            
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是专业的文本编辑，擅长按照语义逻辑进行段落划分。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=5000
            )
            
            marked_text = response.choices[0].message.content.strip()
            
            # 按标记分段
            segments = marked_text.split("---BREAK---")
            segments = [seg.strip() for seg in segments if seg.strip()]
            
            # 为每个段落匹配时间戳
            paragraphs = self._match_timestamps_to_paragraphs(segments, srt_entries)
            
            logger.info(f"Semantic segmentation: {len(paragraphs)} paragraphs")
            return paragraphs
        
        except Exception as e:
            logger.error(f"Semantic segmentation failed: {e}", exc_info=True)
            return self._segment_paragraphs_simple(text, srt_entries)
    
    def _segment_paragraphs_simple(self, text: str, srt_entries: List[SrtEntry]) -> List[SemanticParagraph]:
        """
        简单规则分段（降级方案）
        
        Args:
            text: 连续文本
            srt_entries: SRT条目列表（用于获取时间戳）
        
        Returns:
            段落列表
        """
        # 按句号分割
        sentences = re.split(r'([。！？])', text)
        
        # 重新组合句子（保留标点）
        complete_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                complete_sentences.append(sentences[i] + sentences[i + 1])
        
        # 按长度简单分段（每5-8句一段）
        segments = []
        current_segment = []
        
        for sentence in complete_sentences:
            current_segment.append(sentence)
            if len(current_segment) >= 6:  # 每6句分一段
                segments.append(''.join(current_segment))
                current_segment = []
        
        if current_segment:
            segments.append(''.join(current_segment))
        
        # 匹配时间戳
        paragraphs = self._match_timestamps_to_paragraphs(segments, srt_entries)
        
        return paragraphs
    
    def _match_timestamps_to_paragraphs(self, segments: List[str], srt_entries: List[SrtEntry]) -> List[SemanticParagraph]:
        """
        为段落匹配时间戳
        
        Args:
            segments: 文本段落列表
            srt_entries: SRT条目列表
        
        Returns:
            带时间戳的段落列表
        """
        paragraphs = []
        entry_index = 0
        
        for segment in segments:
            # 粗略计算这段文本对应的SRT条目范围
            segment_length = len(segment)
            char_count = 0
            start_index = entry_index
            
            while entry_index < len(srt_entries) and char_count < segment_length:
                char_count += len(srt_entries[entry_index].text)
                entry_index += 1
            
            # 获取起止时间
            start_time = srt_entries[start_index].start_time if start_index < len(srt_entries) else "00:00:00,000"
            end_time = srt_entries[min(entry_index - 1, len(srt_entries) - 1)].end_time if entry_index > 0 else start_time
            
            sentence_count = segment.count('。') + segment.count('！') + segment.count('？')
            
            paragraphs.append(SemanticParagraph(
                content=segment,
                start_time=start_time,
                end_time=end_time,
                sentence_count=sentence_count
            ))
        
        return paragraphs
    
    def _generate_markdown(self, paragraphs: List[SemanticParagraph], episode_name: str) -> str:
        """
        生成Markdown格式输出
        
        Args:
            paragraphs: 段落列表
            episode_name: 集数名称
        
        Returns:
            Markdown文本
        """
        lines = []
        
        # 添加标题
        lines.append(f"# {episode_name}\n")
        
        # 添加每个段落
        for i, para in enumerate(paragraphs, 1):
            # 段落标题：时间戳
            lines.append(f"## [{para.start_time} - {para.end_time}]\n")
            
            # 段落内容
            lines.append(f"{para.content}\n")
        
        return '\n'.join(lines)


# 便捷函数
def process_srt_file(srt_path: Path, 
                     output_dir: Path,
                     novel_reference: Optional[str] = None,
                     use_llm: bool = True) -> Dict[str, Any]:
    """
    处理单个SRT文件的便捷函数
    
    Args:
        srt_path: SRT文件路径
        output_dir: 输出目录
        novel_reference: 小说参考文本（可选）
        use_llm: 是否使用LLM
    
    Returns:
        处理报告
    """
    processor = SrtScriptProcessor(use_llm=use_llm)
    return processor.execute(srt_path, output_dir, novel_reference)
