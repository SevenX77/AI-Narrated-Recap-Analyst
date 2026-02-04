"""
Hook内容提取器

用于提取Hook部分的分层信息（设定/系统/道具/情节）
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


@dataclass
class LayeredNode:
    """分层节点"""
    node_type: str  # "world_building" / "game_mechanics" / "items_equipment" / "plot_events"
    content: str  # 原文内容
    summary: str  # 简要概括
    
    def to_dict(self) -> Dict:
        return {
            "node_type": self.node_type,
            "content": self.content,
            "summary": self.summary
        }


@dataclass
class HookContent:
    """Hook内容"""
    time_range: str  # 如 "00:00:00,000 - 00:00:30,900"
    raw_text: str  # Hook的原始字幕文本
    layered_nodes: Dict[str, List[LayeredNode]]  # 分层节点
    
    def to_dict(self) -> Dict:
        return {
            "time_range": self.time_range,
            "raw_text": self.raw_text,
            "layered_extraction": {
                layer: [node.to_dict() for node in nodes]
                for layer, nodes in self.layered_nodes.items()
            }
        }


class HookContentExtractor:
    """
    Hook内容提取器
    
    功能：从Hook部分提取四层信息
        - 设定层 (world_building)
        - 系统层 (game_mechanics)
        - 道具层 (items_equipment)
        - 情节层 (plot_events)
    """
    
    def __init__(self, llm_client, model_name: str = "deepseek-chat"):
        """
        初始化Hook内容提取器
        
        Args:
            llm_client: LLM客户端
            model_name: 模型名称
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict:
        """加载Prompts"""
        try:
            return load_prompts("layered_extraction")
        except Exception as e:
            logger.error(f"加载prompts失败: {e}")
            return {}
    
    def extract_hook_content(
        self,
        hook_srt_text: str,
        hook_time_range: str
    ) -> HookContent:
        """
        提取Hook分层内容
        
        Args:
            hook_srt_text: Hook部分的SRT文本
            hook_time_range: Hook的时间范围（如 "00:00 - 00:30"）
        
        Returns:
            HookContent
        """
        logger.info(f"🔍 开始提取Hook分层内容 ({hook_time_range})...")
        
        # 提取纯文本（去除时间戳）
        raw_text = self._extract_pure_text_from_srt(hook_srt_text)
        
        # 提取四层信息
        layered_nodes = {}
        
        # Layer 1: 世界观设定
        layered_nodes["world_building"] = self._extract_layer(
            text=raw_text,
            layer_name="world_building",
            prompt_key="extract_world_building"
        )
        
        # Layer 2: 系统机制
        layered_nodes["game_mechanics"] = self._extract_layer(
            text=raw_text,
            layer_name="game_mechanics",
            prompt_key="extract_game_mechanics"
        )
        
        # Layer 3: 道具装备
        layered_nodes["items_equipment"] = self._extract_layer(
            text=raw_text,
            layer_name="items_equipment",
            prompt_key="extract_items_equipment"
        )
        
        # Layer 4: 情节事件
        layered_nodes["plot_events"] = self._extract_layer(
            text=raw_text,
            layer_name="plot_events",
            prompt_key="extract_plot_events"
        )
        
        hook_content = HookContent(
            time_range=hook_time_range,
            raw_text=raw_text,
            layered_nodes=layered_nodes
        )
        
        # 统计提取结果
        total_nodes = sum(len(nodes) for nodes in layered_nodes.values())
        logger.info(f"✅ Hook分层内容提取完成: 共{total_nodes}个节点")
        for layer, nodes in layered_nodes.items():
            logger.info(f"   {layer}: {len(nodes)}个节点")
        
        return hook_content
    
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
    
    def _extract_layer(
        self,
        text: str,
        layer_name: str,
        prompt_key: str
    ) -> List[LayeredNode]:
        """
        提取单层信息
        
        Args:
            text: 文本内容
            layer_name: 层名称（如 "world_building"）
            prompt_key: Prompt的key（如 "extract_world_building"）
        
        Returns:
            该层的节点列表
        """
        logger.info(f"   提取 {layer_name}...")
        
        # 获取prompt
        layer_prompts = self.prompts.get(prompt_key, {})
        if not layer_prompts:
            logger.warning(f"未找到prompt: {prompt_key}，跳过")
            return []
        
        system_prompt = layer_prompts.get("system", "")
        user_prompt = layer_prompts.get("user", "").format(
            text=text,
            source_type="script"  # Hook来自script
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
            
            # 解析节点（支持两种格式）
            nodes = []
            
            # 格式1: 直接返回列表 [{"type": ..., "content": ...}, ...]
            # 格式2: 返回字典 {"nodes": [...]} 或 {"items": [...]}
            if isinstance(result_json, list):
                nodes_data = result_json
            elif isinstance(result_json, dict):
                nodes_data = result_json.get("nodes", result_json.get("items", []))
            else:
                logger.warning(f"未知的LLM返回格式: {type(result_json)}")
                nodes_data = []
            
            for node_data in nodes_data:
                # 提取content和summary
                # 不同layer的字段名可能不同
                content = node_data.get("content", node_data.get("source_text", ""))
                summary = node_data.get("summary", content[:20] if content else "")
                
                if content:  # 只添加有内容的节点
                    node = LayeredNode(
                        node_type=layer_name,
                        content=content,
                        summary=summary
                    )
                    nodes.append(node)
            
            logger.info(f"      → 提取到 {len(nodes)} 个节点")
            return nodes
            
        except Exception as e:
            logger.error(f"提取 {layer_name} 失败: {e}")
            return []
    
    def calculate_intro_similarity(
        self,
        hook_content: HookContent,
        intro_content: HookContent
    ) -> float:
        """
        计算Hook与简介的相似度
        
        Args:
            hook_content: Hook的分层内容
            intro_content: 简介的分层内容
        
        Returns:
            相似度分数 (0.0-1.0)
        """
        logger.info(f"🔍 计算Hook与简介的相似度...")
        
        # 简单实现：计算各层节点数的重叠度
        # TODO: 可以改进为使用embedding计算语义相似度
        
        total_similarity = 0.0
        layer_count = 0
        
        for layer in ["world_building", "game_mechanics", "items_equipment", "plot_events"]:
            hook_nodes = hook_content.layered_nodes.get(layer, [])
            intro_nodes = intro_content.layered_nodes.get(layer, [])
            
            if not hook_nodes and not intro_nodes:
                continue
            
            layer_count += 1
            
            # 计算该层的相似度（基于节点数比例）
            if not hook_nodes or not intro_nodes:
                layer_similarity = 0.0
            else:
                overlap_count = min(len(hook_nodes), len(intro_nodes))
                total_count = max(len(hook_nodes), len(intro_nodes))
                layer_similarity = overlap_count / total_count
            
            total_similarity += layer_similarity
            logger.info(f"   {layer}: {layer_similarity:.2f}")
        
        if layer_count == 0:
            return 0.0
        
        overall_similarity = total_similarity / layer_count
        logger.info(f"✅ 总体相似度: {overall_similarity:.2f}")
        
        return overall_similarity
