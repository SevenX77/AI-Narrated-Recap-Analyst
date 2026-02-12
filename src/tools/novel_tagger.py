"""
NovelTagger - Novel叙事特征标注工具

分析Novel章节的叙事特征（视角、节奏、基调等）。
"""

import logging
import json
import time
from collections import Counter
from typing import List, Optional

from src.core.interfaces import BaseTool
from src.core.schemas_novel import (
    ParagraphSegmentationResult,
    ChapterTags,
    NovelTaggingResult
)
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelTagger(BaseTool):
    """
    Novel叙事特征标注工具
    
    职责 (Responsibility):
        分析Novel章节的叙事特征，提供标准化标签。
        与NovelAnnotator互补：
        - NovelAnnotator: 事实性标注（时间线、人物、地点、设定）
        - NovelTagger: 叙事特征（视角、节奏、基调、主题）
    
    接口 (Interface):
        输入:
            - segmentation_results: List[ParagraphSegmentationResult] (章节分段结果)
            - project_name: str (项目名称)
            - preview_length: int (章节预览长度，默认1000字)
        
        输出:
            - NovelTaggingResult: 标注结果
    
    依赖 (Dependencies):
        - Schema: ChapterTags, NovelTaggingResult
        - Tool: NovelSegmenter (前置工具)
        - Prompt: novel_tagging.yaml
        - LLM: DeepSeek v3.2 或 Claude
    """
    
    name = "novel_tagger"
    description = "标注Novel叙事特征"
    
    def __init__(self, provider: str = "deepseek"):
        """
        初始化Novel标注器
        
        Args:
            provider: LLM Provider（"deepseek" 或 "claude"）
        """
        super().__init__()
        self.provider = provider
        self.llm_client = get_llm_client(provider)
        self.model_name = get_model_name(provider)
        self.prompts = load_prompts("novel_tagging")
    
    def execute(
        self,
        segmentation_results: List[ParagraphSegmentationResult],
        project_name: str,
        preview_length: int = 1000,
        **kwargs
    ) -> NovelTaggingResult:
        """
        标注Novel叙事特征
        
        Args:
            segmentation_results: 章节分段结果列表
            project_name: 项目名称
            preview_length: 章节预览长度（字符数）
        
        Returns:
            NovelTaggingResult: 标注结果
        """
        logger.info(f"🏷️  开始标注Novel叙事特征...")
        logger.info(f"   项目: {project_name}")
        logger.info(f"   章节数: {len(segmentation_results)}")
        
        start_time = time.time()
        
        chapter_tags_list = []
        
        # 为每个章节提取特征
        for seg_result in segmentation_results:
            logger.info(f"   处理章节{seg_result.chapter_number}...")
            
            # 拼接章节内容
            chapter_content = self._build_chapter_content(
                seg_result,
                preview_length
            )
            
            # 提取叙事特征
            tags = self._extract_chapter_tags(
                seg_result.chapter_number,
                chapter_content,
                preview_length
            )
            
            if tags:
                chapter_tags_list.append(tags)
        
        # 汇总整体特征
        overall_perspective, dominant_tone, common_themes = self._aggregate_features(
            chapter_tags_list
        )
        
        processing_time = time.time() - start_time
        
        result = NovelTaggingResult(
            project_name=project_name,
            total_chapters=len(segmentation_results),
            chapter_tags=chapter_tags_list,
            overall_perspective=overall_perspective,
            dominant_tone=dominant_tone,
            common_themes=common_themes,
            processing_time=round(processing_time, 2)
        )
        
        logger.info(f"✅ Novel标注完成")
        logger.info(f"   整体视角: {overall_perspective}")
        logger.info(f"   主导基调: {dominant_tone}")
        logger.info(f"   常见主题: {', '.join(common_themes[:3])}")
        logger.info(f"   处理时长: {processing_time:.2f}秒")
        
        return result
    
    def _build_chapter_content(
        self,
        seg_result: ParagraphSegmentationResult,
        max_length: int
    ) -> str:
        """
        构建章节内容（用于特征提取）
        
        Args:
            seg_result: 章节分段结果
            max_length: 最大长度
        
        Returns:
            章节内容字符串
        """
        contents = []
        total_length = 0
        
        for paragraph in seg_result.paragraphs:
            para_content = paragraph.content
            if total_length + len(para_content) > max_length:
                # 截断
                remaining = max_length - total_length
                contents.append(para_content[:remaining] + "...")
                break
            
            contents.append(para_content)
            total_length += len(para_content)
        
        return "\n\n".join(contents)
    
    def _extract_chapter_tags(
        self,
        chapter_number: int,
        chapter_content: str,
        preview_length: int
    ) -> Optional[ChapterTags]:
        """
        提取章节叙事特征
        
        Args:
            chapter_number: 章节号
            chapter_content: 章节内容
            preview_length: 预览长度
        
        Returns:
            ChapterTags: 章节标签
        """
        system_prompt = self.prompts.get("system", "")
        user_prompt = self.prompts.get("user_template", "").format(
            chapter_number=chapter_number,
            preview_length=preview_length,
            chapter_content=chapter_content
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            tags = ChapterTags(
                chapter_number=result_json.get("chapter_number", chapter_number),
                narrative_perspective=result_json.get("narrative_perspective", "第三人称限制"),
                time_structure=result_json.get("time_structure", "线性"),
                pacing=result_json.get("pacing", "中速"),
                tone=result_json.get("tone", "中性"),
                key_themes=result_json.get("key_themes", []),
                genre_tags=result_json.get("genre_tags", []),
                narrative_techniques=result_json.get("narrative_techniques", []),
                confidence=result_json.get("confidence", 1.0)
            )
            
            return tags
            
        except Exception as e:
            logger.error(f"章节{chapter_number}特征提取失败: {e}")
            return None
    
    def _aggregate_features(
        self,
        chapter_tags_list: List[ChapterTags]
    ) -> tuple:
        """
        汇总整体特征
        
        Args:
            chapter_tags_list: 章节标签列表
        
        Returns:
            (overall_perspective, dominant_tone, common_themes)
        """
        if not chapter_tags_list:
            return ("未知", "未知", [])
        
        # 统计最常见的视角
        perspectives = [tags.narrative_perspective for tags in chapter_tags_list]
        perspective_counter = Counter(perspectives)
        overall_perspective = perspective_counter.most_common(1)[0][0]
        
        # 统计最常见的基调
        tones = [tags.tone for tags in chapter_tags_list]
        tone_counter = Counter(tones)
        dominant_tone = tone_counter.most_common(1)[0][0]
        
        # 统计常见主题
        all_themes = []
        for tags in chapter_tags_list:
            all_themes.extend(tags.key_themes)
        
        theme_counter = Counter(all_themes)
        common_themes = [theme for theme, _ in theme_counter.most_common(5)]
        
        return (overall_perspective, dominant_tone, common_themes)
