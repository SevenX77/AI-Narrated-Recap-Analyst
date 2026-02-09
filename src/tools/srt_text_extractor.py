"""
SRT Text Extractor Tool
SRT文本提取工具：从SRT条目中提取文本并使用LLM进行智能修复

职责：
1. 从SRT条目中提取纯文本（移除时间轴）
2. 使用LLM智能添加标点符号
3. 修正错别字和同音错字
4. 实体标准化（有/无小说参考两种模式）
5. 修复缺字问题
6. 确保语义通顺连贯
"""

import logging
import json
import re
import time
from typing import List, Dict, Any, Tuple, Optional

from src.core.interfaces import BaseTool
from src.core.schemas_script import SrtEntry, SrtTextExtractionResult

logger = logging.getLogger(__name__)


class SrtTextExtractor(BaseTool):
    """
    SRT文本提取工具
    
    职责：
    - 从SRT条目列表中提取纯文本
    - 智能添加标点符号（逗号、句号、问号、感叹号等）
    - 修正明显的错别字和同音错字
    - 实体标准化（有小说参考时使用小说实体，无参考时智能识别）
    - 修复缺字问题（如"到达上"→"到达上海"）
    - 确保整体语义通顺连贯
    
    两种处理模式：
    - **with_novel**: 有小说参考，从小说提取标准实体，直接对齐
    - **without_novel**: 无小说参考，从字幕自身识别实体变体，智能推断标准形式
    
    Example:
        >>> extractor = SrtTextExtractor()
        >>> result = extractor.execute(
        ...     srt_entries=entries,
        ...     project_name="末哥超凡公路",
        ...     episode_name="ep01",
        ...     novel_reference=novel_text  # 可选
        ... )
        >>> print(result.processed_text)
        >>> print(result.processing_mode)  # "with_novel" or "without_novel"
    """
    
    name = "srt_text_extractor"
    description = "Extract text from SRT entries and process with LLM"
    
    def __init__(self, use_llm: bool = True, provider: str = "deepseek"):
        """
        Args:
            use_llm: 是否使用LLM智能处理（默认True，False则使用规则降级）
            provider: LLM Provider ("claude" | "deepseek")，默认使用 DeepSeek（简单格式处理）
        """
        self.use_llm = use_llm
        self.provider = provider
        self.llm_client = None
        self.model_name = None
        self.prompt_config_with_novel = None
        self.prompt_config_without_novel = None
        
        if self.use_llm:
            try:
                from src.core.llm_client_manager import get_llm_client, get_model_name
                from src.utils.prompt_loader import load_prompts
                
                self.llm_client = get_llm_client(provider)
                self.model_name = get_model_name(provider)
                self.prompt_config_with_novel = load_prompts("srt_script_processing_with_novel")
                self.prompt_config_without_novel = load_prompts("srt_script_processing_without_novel")
                logger.info(f"✅ LLM-based SRT processing enabled (provider: {provider})")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}, falling back to rule-based processing")
                self.use_llm = False
    
    def execute(
        self,
        srt_entries: List[SrtEntry],
        project_name: str,
        episode_name: str,
        novel_reference: Optional[str] = None
    ) -> SrtTextExtractionResult:
        """
        执行SRT文本提取和处理
        
        Args:
            srt_entries: SRT条目列表（从 SrtImporter 输出）
            project_name: 项目名称
            episode_name: 集数名称
            novel_reference: 小说参考文本（可选，前3章即可）
        
        Returns:
            SrtTextExtractionResult: 提取结果（包含处理后的文本和元数据）
        """
        start_time = time.time()
        
        logger.info(f"Extracting text from {len(srt_entries)} SRT entries")
        logger.info(f"Mode: {'with_novel' if novel_reference else 'without_novel'}")
        
        # Step 1: 提取原始文本
        raw_text = self._extract_text_from_entries(srt_entries)
        original_chars = len(raw_text)
        logger.info(f"Extracted raw text: {original_chars} chars")
        
        # Step 2: 根据是否有小说参考选择处理模式
        if novel_reference and self.use_llm:
            processed_text, entity_info = self._process_with_novel_reference(
                raw_text, novel_reference
            )
            processing_mode = "with_novel"
        elif self.use_llm:
            processed_text, entity_info = self._process_without_novel_reference(raw_text)
            processing_mode = "without_novel"
        else:
            # 降级：规则处理
            processed_text = self._process_rule_based(raw_text)
            entity_info = {}
            processing_mode = "rule_based"
        
        processed_chars = len(processed_text)
        logger.info(f"Processed text: {processed_chars} chars ({processing_mode} mode)")
        
        # Step 3: 统计修正信息（简化）
        corrections = {
            "punctuation_added": processed_text.count('，') + processed_text.count('。'),
            "char_difference": abs(processed_chars - original_chars)
        }
        
        processing_time = time.time() - start_time
        
        # Step 4: 构建返回结果
        return SrtTextExtractionResult(
            processed_text=processed_text,
            processing_mode=processing_mode,
            raw_text=raw_text,
            entity_standardization=entity_info,
            corrections=corrections,
            processing_time=processing_time,
            original_chars=original_chars,
            processed_chars=processed_chars
        )
    
    def _extract_text_from_entries(self, entries: List[SrtEntry]) -> str:
        """
        从SRT条目中提取文本
        
        Args:
            entries: SRT条目列表
        
        Returns:
            连续文本（无标点，保留换行）
        """
        texts = [entry.text for entry in entries]
        return '\n'.join(texts)
    
    def _process_with_novel_reference(
        self,
        raw_text: str,
        novel_reference: str
    ) -> Tuple[str, Dict]:
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
        
        # 构建符合schema的entity_info（Dict[str, Dict[str, Any]]）
        entity_info = {}
        for category, entity_list in novel_entities.items():
            if entity_list:
                entity_info[category] = {
                    "source": "novel_reference",
                    "entities": entity_list,
                    "count": len(entity_list)
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
        entities = {
            "characters": [],
            "locations": [],
            "items": []
        }
        
        # 提取人名（常见姓氏+名字，或带称谓）
        name_pattern = r'[\u4e00-\u9fa5]{2,4}(?:公主|王爷|皇帝|淑妃|大人|先生|小姐|队长|博士|教授)'
        characters = re.findall(name_pattern, novel_text[:3000])
        entities["characters"] = list(set(characters))[:20]  # 取前20个
        
        # 提取地点（含"地"/"城"/"宫"等）
        location_pattern = r'[\u4e00-\u9fa5]{2,6}(?:城|宫|地|国|州|省|县|市|镇|村)'
        locations = re.findall(location_pattern, novel_text[:3000])
        entities["locations"] = list(set(locations))[:15]
        
        logger.info(
            f"Extracted entities from novel: "
            f"{len(entities['characters'])} characters, "
            f"{len(entities['locations'])} locations"
        )
        
        return entities
    
    def _process_with_llm_and_entities(
        self,
        raw_text: str,
        entities: Dict[str, List[str]],
        mode: str
    ) -> str:
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
            logger.info("LLM processing completed successfully")
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
            
            logger.info("LLM entity extraction and processing completed successfully")
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
