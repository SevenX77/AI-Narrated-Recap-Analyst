"""
HookContentAnalyzer - Hook内容来源分析工具

分析Hook的内容来源，判断其与Novel简介的相似度。
"""

import logging
import json
import time
from typing import List, Dict, Any

from src.core.interfaces import BaseTool
from src.core.schemas_script import (
    ScriptSegment,
    HookDetectionResult,
    HookAnalysisResult,
    LayeredContent
)
from src.core.schemas_novel import NovelMetadata
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class HookContentAnalyzer(BaseTool):
    """
    Hook内容来源分析工具
    
    职责 (Responsibility):
        分析Hook的内容来源，判断其与Novel简介的相似度，
        为对齐流程提供策略建议。
    
    分析步骤:
        1. 分层提取Hook内容（4层）
        2. 分层提取简介内容（4层）
        3. 计算各层相似度
        4. 推断来源类型
        5. 生成对齐策略建议
    
    接口 (Interface):
        输入:
            - hook_segments: List[ScriptSegment] (Hook段落)
            - novel_intro: str (Novel简介)
            - novel_metadata: NovelMetadata (可选，辅助分析)
        
        输出:
            - HookAnalysisResult: 分析结果
    
    依赖 (Dependencies):
        - Schema: HookAnalysisResult, LayeredContent
        - Tool: HookDetector (前置工具)
        - Prompt: hook_content_analysis.yaml
        - LLM: DeepSeek v3.2 或 Claude
    """
    
    name = "hook_content_analyzer"
    description = "分析Hook内容来源"
    
    def __init__(self, provider: str = "deepseek"):
        """
        初始化Hook内容分析器
        
        Args:
            provider: LLM Provider（"deepseek" 或 "claude"）
        """
        super().__init__()
        self.provider = provider
        self.llm_client = get_llm_client(provider)
        self.model_name = get_model_name(provider)
        self.prompts = load_prompts("hook_content_analysis")
    
    def execute(
        self,
        hook_segments: List[ScriptSegment],
        novel_intro: str,
        novel_metadata: NovelMetadata = None,
        **kwargs
    ) -> HookAnalysisResult:
        """
        分析Hook内容来源
        
        Args:
            hook_segments: Hook段落列表
            novel_intro: Novel简介文本
            novel_metadata: Novel元数据（可选）
        
        Returns:
            HookAnalysisResult: 分析结果
        """
        logger.info(f"🔍 开始分析Hook内容来源...")
        start_time = time.time()
        
        # 1. 提取Hook分层内容
        hook_text = "\n\n".join([seg.content for seg in hook_segments])
        hook_layers = self._extract_layered_content(hook_text, "Hook")
        
        # 2. 提取简介分层内容
        intro_layers = self._extract_layered_content(novel_intro, "简介")
        
        # 3. 计算各层相似度
        layer_similarity = self._calculate_layer_similarity(hook_layers, intro_layers)
        
        # 4. 计算总体相似度
        similarity_score = sum(layer_similarity.values()) / len(layer_similarity) if layer_similarity else 0.0
        
        # 5. 推断来源类型
        source_type = self._infer_source_type(similarity_score)
        
        # 6. 生成对齐策略建议
        alignment_strategy = self._recommend_alignment_strategy(similarity_score, source_type)
        
        processing_time = time.time() - start_time
        
        result = HookAnalysisResult(
            source_type=source_type,
            similarity_score=round(similarity_score, 3),
            matched_chapter=None,  # 暂不支持章节匹配
            hook_layers=hook_layers,
            intro_layers=intro_layers,
            layer_similarity=layer_similarity,
            alignment_strategy=alignment_strategy,
            metadata={
                "processing_time": round(processing_time, 2),
                "model_used": self.model_name,
                "provider": self.provider,
                "hook_segment_count": len(hook_segments)
            }
        )
        
        logger.info(f"✅ Hook内容分析完成")
        logger.info(f"   来源类型: {source_type}")
        logger.info(f"   相似度: {similarity_score:.2%}")
        logger.info(f"   建议策略: {alignment_strategy}")
        
        return result
    
    def _extract_layered_content(self, text: str, source_name: str) -> LayeredContent:
        """
        提取分层内容
        
        Args:
            text: 文本内容
            source_name: 来源名称（用于日志）
        
        Returns:
            LayeredContent: 分层内容
        """
        logger.info(f"   提取 {source_name} 的分层内容...")
        
        system_prompt = self.prompts.get("system", "")
        user_prompt = self.prompts.get("user_template", "").format(text=text)
        
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
            
            # 解析四层内容
            layers = LayeredContent(
                world_building=result_json.get("world_building", []),
                game_mechanics=result_json.get("game_mechanics", []),
                items_equipment=result_json.get("items_equipment", []),
                plot_events=result_json.get("plot_events", [])
            )
            
            # 统计
            total_elements = (
                len(layers.world_building) +
                len(layers.game_mechanics) +
                len(layers.items_equipment) +
                len(layers.plot_events)
            )
            logger.info(f"      → 提取到 {total_elements} 个元素")
            
            return layers
            
        except Exception as e:
            logger.error(f"提取 {source_name} 分层内容失败: {e}")
            return LayeredContent()
    
    def _calculate_layer_similarity(
        self,
        hook_layers: LayeredContent,
        intro_layers: LayeredContent
    ) -> Dict[str, float]:
        """
        计算各层的相似度
        
        使用Jaccard相似度：交集大小 / 并集大小
        
        Args:
            hook_layers: Hook分层内容
            intro_layers: 简介分层内容
        
        Returns:
            各层相似度字典
        """
        layer_similarity = {}
        
        for layer_name in ["world_building", "game_mechanics", "items_equipment", "plot_events"]:
            hook_set = set(getattr(hook_layers, layer_name, []))
            intro_set = set(getattr(intro_layers, layer_name, []))
            
            if not hook_set and not intro_set:
                layer_similarity[layer_name] = 0.0
                continue
            
            if not hook_set or not intro_set:
                layer_similarity[layer_name] = 0.0
                continue
            
            # Jaccard相似度
            intersection = len(hook_set & intro_set)
            union = len(hook_set | intro_set)
            
            similarity = intersection / union if union > 0 else 0.0
            layer_similarity[layer_name] = round(similarity, 3)
        
        return layer_similarity
    
    def _infer_source_type(self, similarity_score: float) -> str:
        """
        推断来源类型
        
        Args:
            similarity_score: 总体相似度
        
        Returns:
            来源类型：简介/章节/独立创作
        """
        if similarity_score >= 0.7:
            return "简介"
        elif similarity_score >= 0.4:
            return "章节"
        else:
            return "独立创作"
    
    def _recommend_alignment_strategy(
        self,
        similarity_score: float,
        source_type: str
    ) -> str:
        """
        推荐对齐策略
        
        Args:
            similarity_score: 相似度
            source_type: 来源类型
        
        Returns:
            对齐策略：direct_intro/chapter_based/skip
        """
        if source_type == "简介" and similarity_score >= 0.7:
            return "direct_intro"  # 直接与简介对齐
        elif source_type == "章节":
            return "chapter_based"  # 基于章节进行对齐
        else:
            return "skip"  # 跳过对齐（独立创作）
