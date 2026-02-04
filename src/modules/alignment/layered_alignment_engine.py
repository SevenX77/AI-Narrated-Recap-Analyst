"""
分层对齐引擎 (Layered Alignment Engine)

核心功能：
    1. 直接从原始文本提取Plot Nodes（4层）
    2. 4层分别对齐（设定/系统/道具/情节）
    3. 生成对齐质量评分
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


@dataclass
class PlotNode:
    """Plot节点（分层信息的基本单元）"""
    node_id: str
    layer: str  # "world_building" / "game_mechanics" / "items_equipment" / "plot_events"
    content: str
    summary: str
    source_type: str  # "script" / "novel"
    source_ref: str  # 时间戳（script）或章节号（novel）
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "layer": self.layer,
            "content": self.content,
            "summary": self.summary,
            "source_type": self.source_type,
            "source_ref": self.source_ref
        }


@dataclass
class LayerAlignment:
    """单层对齐结果"""
    layer: str
    script_nodes: List[PlotNode]
    novel_nodes: List[PlotNode]
    alignments: List[Dict]  # 对齐对列表
    coverage_score: float  # 覆盖率分数
    
    def to_dict(self) -> Dict:
        return {
            "layer": self.layer,
            "script_node_count": len(self.script_nodes),
            "novel_node_count": len(self.novel_nodes),
            "alignment_count": len(self.alignments),
            "alignments": self.alignments,
            "coverage_score": self.coverage_score
        }


@dataclass
class LayeredAlignmentResult:
    """完整的分层对齐结果"""
    episode: str
    script_time_range: str
    matched_novel_chapters: List[str]
    
    world_building_alignment: LayerAlignment
    game_mechanics_alignment: LayerAlignment
    items_equipment_alignment: LayerAlignment
    plot_events_alignment: LayerAlignment
    
    overall_score: float
    layer_scores: Dict[str, float]
    
    def to_dict(self) -> Dict:
        return {
            "episode": self.episode,
            "script_time_range": self.script_time_range,
            "matched_novel_chapters": self.matched_novel_chapters,
            "layered_alignment": {
                "world_building": self.world_building_alignment.to_dict(),
                "game_mechanics": self.game_mechanics_alignment.to_dict(),
                "items_equipment": self.items_equipment_alignment.to_dict(),
                "plot_events": self.plot_events_alignment.to_dict()
            },
            "alignment_quality": {
                "overall_score": self.overall_score,
                "layer_scores": self.layer_scores
            }
        }


class LayeredAlignmentEngine:
    """
    分层对齐引擎
    
    工作流程：
        1. 提取：从Script和Novel中提取4层Plot Nodes
        2. 对齐：4层分别进行语义匹配
        3. 评分：计算各层覆盖率和总体质量
    """
    
    def __init__(self, llm_client, model_name: str = "deepseek-chat"):
        """
        初始化分层对齐引擎
        
        Args:
            llm_client: LLM客户端
            model_name: 模型名称
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = self._load_prompts()
        
        logger.info("✅ LayeredAlignmentEngine 初始化完成")
    
    def _load_prompts(self) -> Dict:
        """加载Prompts"""
        try:
            return load_prompts("layered_extraction")
        except Exception as e:
            logger.error(f"加载prompts失败: {e}")
            return {}
    
    async def align(
        self,
        script_srt_text: str,
        novel_chapters_text: str,
        episode: str,
        script_time_range: str = ""
    ) -> LayeredAlignmentResult:
        """
        执行完整的分层对齐
        
        Args:
            script_srt_text: Script的SRT文本（Body部分）
            novel_chapters_text: Novel的章节文本（移除简介）
            episode: 集数（如 "ep01"）
            script_time_range: Script的时间范围（如 "00:00:30 - 00:12:45"）
        
        Returns:
            LayeredAlignmentResult
        """
        logger.info(f"🚀 开始分层对齐: {episode}")
        
        # Step 1: 提取Script的Plot Nodes
        logger.info("Step 1: 提取Script Plot Nodes...")
        script_nodes = await self.extract_plot_nodes(
            text=script_srt_text,
            source_type="script"
        )
        
        # Step 2: 提取Novel的Plot Nodes
        logger.info("Step 2: 提取Novel Plot Nodes...")
        novel_nodes = await self.extract_plot_nodes(
            text=novel_chapters_text,
            source_type="novel"
        )
        
        # Step 3: 4层分别对齐
        logger.info("Step 3: 执行4层对齐...")
        
        wb_alignment = await self._align_single_layer(
            "world_building",
            script_nodes["world_building"],
            novel_nodes["world_building"]
        )
        
        gm_alignment = await self._align_single_layer(
            "game_mechanics",
            script_nodes["game_mechanics"],
            novel_nodes["game_mechanics"]
        )
        
        ie_alignment = await self._align_single_layer(
            "items_equipment",
            script_nodes["items_equipment"],
            novel_nodes["items_equipment"]
        )
        
        pe_alignment = await self._align_single_layer(
            "plot_events",
            script_nodes["plot_events"],
            novel_nodes["plot_events"]
        )
        
        # Step 4: 计算总体质量
        logger.info("Step 4: 计算对齐质量...")
        layer_scores = {
            "world_building": wb_alignment.coverage_score,
            "game_mechanics": gm_alignment.coverage_score,
            "items_equipment": ie_alignment.coverage_score,
            "plot_events": pe_alignment.coverage_score
        }
        
        # 加权平均（情节层权重最高）
        overall_score = (
            layer_scores["world_building"] * 0.2 +
            layer_scores["game_mechanics"] * 0.2 +
            layer_scores["items_equipment"] * 0.1 +
            layer_scores["plot_events"] * 0.5
        )
        
        # Step 5: 推断匹配的Novel章节
        matched_chapters = self._infer_matched_chapters(novel_nodes)
        
        result = LayeredAlignmentResult(
            episode=episode,
            script_time_range=script_time_range,
            matched_novel_chapters=matched_chapters,
            world_building_alignment=wb_alignment,
            game_mechanics_alignment=gm_alignment,
            items_equipment_alignment=ie_alignment,
            plot_events_alignment=pe_alignment,
            overall_score=overall_score,
            layer_scores=layer_scores
        )
        
        logger.info(f"✅ 分层对齐完成: overall_score={overall_score:.2f}")
        
        return result
    
    async def extract_plot_nodes(
        self,
        text: str,
        source_type: str
    ) -> Dict[str, List[PlotNode]]:
        """
        从文本中提取4层Plot Nodes
        
        Args:
            text: 原始文本（SRT或Novel）
            source_type: "script" 或 "novel"
        
        Returns:
            {
                "world_building": [PlotNode, ...],
                "game_mechanics": [PlotNode, ...],
                "items_equipment": [PlotNode, ...],
                "plot_events": [PlotNode, ...]
            }
        """
        logger.info(f"   提取{source_type}的Plot Nodes...")
        
        # 如果是SRT，先提取纯文本
        if source_type == "script":
            text = self._extract_pure_text_from_srt(text)
        
        # 分层提取
        plot_nodes = {}
        
        for layer, prompt_key in [
            ("world_building", "extract_world_building"),
            ("game_mechanics", "extract_game_mechanics"),
            ("items_equipment", "extract_items_equipment"),
            ("plot_events", "extract_plot_events")
        ]:
            nodes = await self._extract_layer_nodes(
                text=text,
                layer=layer,
                prompt_key=prompt_key,
                source_type=source_type
            )
            plot_nodes[layer] = nodes
        
        total_nodes = sum(len(nodes) for nodes in plot_nodes.values())
        logger.info(f"      → 提取到 {total_nodes} 个节点")
        
        return plot_nodes
    
    async def _extract_layer_nodes(
        self,
        text: str,
        layer: str,
        prompt_key: str,
        source_type: str
    ) -> List[PlotNode]:
        """提取单层节点"""
        layer_prompts = self.prompts.get(prompt_key, {})
        if not layer_prompts:
            logger.warning(f"未找到prompt: {prompt_key}，跳过")
            return []
        
        system_prompt = layer_prompts.get("system", "")
        user_prompt = layer_prompts.get("user", "").format(
            text=text,
            source_type=source_type
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
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # 解析节点
            nodes = []
            
            if isinstance(result_json, list):
                nodes_data = result_json
            elif isinstance(result_json, dict):
                nodes_data = result_json.get("nodes", result_json.get("items", []))
            else:
                nodes_data = []
            
            for i, node_data in enumerate(nodes_data):
                content = node_data.get("content", node_data.get("source_text", ""))
                summary = node_data.get("summary", content[:20] if content else "")
                
                if content:
                    node = PlotNode(
                        node_id=f"{layer}_{source_type}_{i+1}",
                        layer=layer,
                        content=content,
                        summary=summary,
                        source_type=source_type,
                        source_ref=""  # TODO: 提取时间戳或章节号
                    )
                    nodes.append(node)
            
            return nodes
            
        except Exception as e:
            logger.error(f"提取 {layer} 失败: {e}")
            return []
    
    async def _align_single_layer(
        self,
        layer: str,
        script_nodes: List[PlotNode],
        novel_nodes: List[PlotNode]
    ) -> LayerAlignment:
        """
        对齐单层节点
        
        策略：基于语义相似度的贪心匹配
        """
        logger.info(f"   对齐 {layer} ({len(script_nodes)} script, {len(novel_nodes)} novel)...")
        
        if not script_nodes or not novel_nodes:
            logger.warning(f"   {layer} 节点数为0，跳过对齐")
            return LayerAlignment(
                layer=layer,
                script_nodes=script_nodes,
                novel_nodes=novel_nodes,
                alignments=[],
                coverage_score=0.0
            )
        
        # 简单实现：基于内容长度和关键词的粗匹配
        # TODO: 改进为使用LLM计算语义相似度
        alignments = []
        matched_novel_indices = set()
        
        for script_node in script_nodes:
            best_match = None
            best_score = 0.0
            best_index = -1
            
            for i, novel_node in enumerate(novel_nodes):
                if i in matched_novel_indices:
                    continue
                
                # 简单相似度：关键词匹配
                score = self._calculate_simple_similarity(
                    script_node.content,
                    novel_node.content
                )
                
                if score > best_score:
                    best_score = score
                    best_match = novel_node
                    best_index = i
            
            if best_match and best_score > 0.3:  # 阈值
                alignments.append({
                    "script_node": script_node.to_dict(),
                    "novel_node": best_match.to_dict(),
                    "similarity": best_score,
                    "confidence": "high" if best_score > 0.7 else "medium"
                })
                matched_novel_indices.add(best_index)
        
        # 计算覆盖率
        coverage_score = len(alignments) / max(len(script_nodes), len(novel_nodes))
        
        logger.info(f"      → {len(alignments)} 对匹配, 覆盖率={coverage_score:.2f}")
        
        return LayerAlignment(
            layer=layer,
            script_nodes=script_nodes,
            novel_nodes=novel_nodes,
            alignments=alignments,
            coverage_score=coverage_score
        )
    
    def _calculate_simple_similarity(self, text1: str, text2: str) -> float:
        """
        计算简单的文本相似度
        
        基于共同字符的比例（简单实现）
        TODO: 改进为使用embedding或LLM
        """
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _infer_matched_chapters(self, novel_nodes: Dict[str, List[PlotNode]]) -> List[str]:
        """
        从Novel节点推断匹配的章节
        
        TODO: 从source_ref中提取章节信息
        """
        # 简单实现：返回占位
        return ["第1章", "第2章"]  # TODO: 实现真实的章节推断
    
    def _extract_pure_text_from_srt(self, srt_text: str) -> str:
        """从SRT文本中提取纯文本"""
        lines = srt_text.strip().split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过空行、序号行、时间戳行
            if not line or line.isdigit() or '-->' in line:
                continue
            text_lines.append(line)
        
        return ' '.join(text_lines)
