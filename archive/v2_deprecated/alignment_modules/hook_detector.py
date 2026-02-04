"""
Hook检测器模块

用于识别ep01中"Hook"（开场钩子）与"线性叙事"的边界
"""

import logging
from typing import List, Dict, Any, Optional
import json

from src.core.schemas import SemanticBlock, Event
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class HookDetectionResult:
    """Hook检测结果"""
    
    def __init__(
        self,
        has_hook: bool,
        hook_end_index: int,
        linear_start_index: int,
        confidence: float,
        reasoning: str,
        hook_blocks: Optional[List[SemanticBlock]] = None
    ):
        self.has_hook = has_hook
        self.hook_end_index = hook_end_index  # Hook结束的block/event索引
        self.linear_start_index = linear_start_index  # 线性叙事起点的block/event索引
        self.confidence = confidence
        self.reasoning = reasoning
        self.hook_blocks = hook_blocks or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "has_hook": self.has_hook,
            "hook_end_index": self.hook_end_index,
            "linear_start_index": self.linear_start_index,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "hook_block_count": len(self.hook_blocks)
        }


class HookDetector:
    """
    Hook检测器
    
    基于用户总结的5个特征识别Hook边界：
    1. 独立语义的段落
    2. 非具象的当下描述（更像总结/预告）
    3. Hook后的文字连贯性更强（进入线性叙事）
    4. Hook后的文字能在小说开头匹配到
    5. Hook可能与小说序言/简介匹配度高
    """
    
    def __init__(self, llm_client, model_name: str = "deepseek-chat"):
        """
        初始化Hook检测器
        
        Args:
            llm_client: LLM客户端（用于调用模型）
            model_name: 模型名称
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> Dict[str, str]:
        """加载Hook检测的prompt模板"""
        # 暂时使用简单的prompt，后续可以优化
        return {
            "system": """你是一个专业的叙事结构分析师。
任务：识别视频解说第一集中"Hook"（开场钩子）的结束位置。

【Hook的5个特征】
1. 独立语义的段落（与后文不是直接的因果关系）
2. 非具象的当下描述（更像是总结、预告、回顾）
3. Hook后的文字连贯性更强，能明显看出进入了线性叙事
4. Hook后的文字能在小说开头部分匹配到对应内容
5. Hook可能与小说的序言/简介匹配度很高

【判断标准】
- 如果开头没有明显的Hook特征，直接从第一个block开始就是线性叙事
- Hook通常在开头的前3-5个blocks内
- 线性叙事的起点应该能在小说第一章的开头找到对应

【输出要求】
返回JSON格式：
{
    "has_hook": true/false,
    "hook_end_index": 2,  // Hook结束的block索引（如果has_hook=false则为-1）
    "linear_start_index": 3,  // 线性叙事起点的block索引
    "confidence": 0.85,  // 置信度 (0.0-1.0)
    "reasoning": "判断理由"
}
""",
            "user": """【Script开头的意思块】
{script_blocks}

【Novel开头的意思块】
{novel_blocks}

请分析并返回Hook边界检测结果（JSON格式）。"""
        }
    
    def detect_hook_boundary(
        self,
        script_blocks: List[SemanticBlock],
        novel_blocks: List[SemanticBlock],
        check_count: int = 20
    ) -> HookDetectionResult:
        """
        检测Hook的边界
        
        Args:
            script_blocks: Script的意思块列表（按顺序）
            novel_blocks: Novel的意思块列表（按顺序）
            check_count: 检查前N个blocks（默认20个）
        
        Returns:
            HookDetectionResult: Hook检测结果
        """
        logger.info(f"🔍 开始Hook边界检测...")
        
        # 只检查前N个blocks
        script_preview = script_blocks[:min(check_count, len(script_blocks))]
        novel_preview = novel_blocks[:min(50, len(novel_blocks))]  # Novel多检查一些
        
        # 格式化blocks为可读文本
        script_text = self._format_blocks(script_preview)
        novel_text = self._format_blocks(novel_preview)
        
        # 构造prompt
        messages = [
            {"role": "system", "content": self.prompt_template["system"]},
            {"role": "user", "content": self.prompt_template["user"].format(
                script_blocks=script_text,
                novel_blocks=novel_text
            )}
        ]
        
        logger.info(f"   → 调用LLM进行Hook检测 (检查{len(script_preview)}个Script blocks, {len(novel_preview)}个Novel blocks)...")
        
        # 调用LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # 解析结果
            has_hook = result_json.get("has_hook", False)
            hook_end_index = result_json.get("hook_end_index", -1)
            linear_start_index = result_json.get("linear_start_index", 0)
            confidence = result_json.get("confidence", 0.0)
            reasoning = result_json.get("reasoning", "")
            
            # 提取hook_blocks
            hook_blocks = []
            if has_hook and hook_end_index >= 0:
                hook_blocks = script_blocks[:hook_end_index + 1]
            
            result = HookDetectionResult(
                has_hook=has_hook,
                hook_end_index=hook_end_index,
                linear_start_index=linear_start_index,
                confidence=confidence,
                reasoning=reasoning,
                hook_blocks=hook_blocks
            )
            
            logger.info(f"✅ Hook检测完成: has_hook={has_hook}, linear_start={linear_start_index}")
            logger.info(f"   推理: {reasoning}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Hook检测失败: {e}")
            # 返回默认结果（假设没有Hook）
            return HookDetectionResult(
                has_hook=False,
                hook_end_index=-1,
                linear_start_index=0,
                confidence=0.0,
                reasoning=f"检测失败: {str(e)}"
            )
    
    def _format_blocks(self, blocks: List[SemanticBlock]) -> str:
        """格式化意思块为可读文本"""
        lines = []
        for i, block in enumerate(blocks):
            lines.append(f"Block {i}:")
            lines.append(f"  主题: {block.theme}")
            lines.append(f"  概括: {block.summary}")
            lines.append(f"  角色: {', '.join(block.characters) if block.characters else '无'}")
            lines.append(f"  地点: {block.location or '未知'}")
            lines.append(f"  时间: {block.time_context or '未知'}")
            lines.append("")
        return "\n".join(lines)
