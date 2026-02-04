"""
Body起点检测器

用于识别Script中"故事正式开始线性叙述"的时间点
"""

import json
import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


@dataclass
class BodyStartDetectionResult:
    """Body起点检测结果"""
    has_hook: bool
    body_start_time: str  # SRT时间戳格式，如 "00:00:30,900"
    hook_end_time: Optional[str]  # Hook结束时间（如果has_hook=True）
    confidence: float  # 0.0-1.0
    reasoning: str  # 判断理由
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "has_hook": self.has_hook,
            "body_start_time": self.body_start_time,
            "hook_end_time": self.hook_end_time,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


class BodyStartDetector:
    """
    Body起点检测器
    
    核心逻辑：识别Script中从"概括/预告"转为"线性叙述"的时间点
    
    判断依据（按权重）：
        1. 叙事模式转换 (40%) - 从概括转为具体叙述
        2. 连贯性突变 (35%) - 句子间连贯性变化
        3. 时间线明确 (15%) - 出现叙事起点标志
        4. 场景具象化 (10%) - 从抽象到具体
        5. Novel匹配 (0-5%, 可选) - 仅供参考
    """
    
    def __init__(self, llm_client, model_name: str = "deepseek-chat"):
        """
        初始化Body起点检测器
        
        Args:
            llm_client: LLM客户端
            model_name: 模型名称
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """加载Prompts"""
        try:
            all_prompts = load_prompts("layered_extraction")
            return all_prompts.get("body_start_detection", {})
        except Exception as e:
            logger.warning(f"加载prompts失败: {e}，使用默认prompt")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """获取默认Prompt（如果YAML加载失败）"""
        return {
            "system": """你是一个专业的叙事结构分析师。
你的任务是找到Script中"故事正式开始线性叙述"的时间点。

【核心判断标准】（按重要性排序）

1. 叙事模式转换（最重要，权重40%）
   - Hook部分: 概括性描述、预告、世界观介绍
   - Body部分: 开始线性推进，按时间顺序讲故事
   - 寻找标志: "那天"、"我从XX出发"、"故事开始于..."

2. 连贯性变化（次重要，权重35%）
   - Hook: 各句间跳跃，无直接因果关系
     例: "诡异降临" → "主角觉醒系统" → "装备升级" → "成为希望"
   - Body: 各句间流畅，有明确时序/因果
     例: "从江城逃出" → "组成车队" → "前往基地" → "制定规则"

3. 辅助特征（权重15%）
   - 时间线明确化: 出现具体时间标记
   - 场景具象化: 从抽象概念到具体场景/对话/行动

【重要提示】
- 不要期望Body起点一定能在Novel第1章找到对应
- Script可能跳过Novel的前几章来优化节奏
- 专注于Script自身的叙事结构转换
- Body起点通常在前30-60秒内

【输出要求】
返回JSON格式：
{
    "has_hook": true/false,
    "body_start_time": "00:00:30,900",
    "confidence": 0.95,
    "reasoning": "识别到'我从江城逃了出来'为明确的叙事起点，之后内容连贯流畅，从概括描述转为具体行动。"
}""",
            "user": """【Script前60秒内容】
{script_preview}

【Novel前5章概要】（仅供参考，不强制匹配）
{novel_preview}

请分析并返回Body起点的时间戳（JSON格式）。"""
        }
    
    def detect_body_start(
        self,
        script_srt_text: str,
        novel_chapters_text: str,
        max_check_duration: int = 90
    ) -> BodyStartDetectionResult:
        """
        检测Body起点
        
        Args:
            script_srt_text: Script的SRT原始文本
            novel_chapters_text: Novel前几章的文本（用于参考）
            max_check_duration: 最多检查的秒数（默认90秒）
        
        Returns:
            BodyStartDetectionResult
        """
        logger.info(f"🔍 开始检测Body起点...")
        
        # Step 1: 提取Script前N秒的字幕
        script_preview = self._extract_srt_preview(script_srt_text, max_check_duration)
        
        # Step 2: 提取Novel前几章的概要
        novel_preview = self._extract_novel_preview(novel_chapters_text)
        
        # Step 3: 构造Prompt
        system_prompt = self.prompts.get("system", self._get_default_prompts()["system"])
        user_prompt = self.prompts.get("user", self._get_default_prompts()["user"])
        
        user_prompt = user_prompt.format(
            script_preview=script_preview,
            novel_preview=novel_preview
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"   → 调用LLM进行Body起点检测...")
        
        # Step 4: 调用LLM
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # 解析结果
            has_hook = result_json.get("has_hook", False)
            body_start_time = result_json.get("body_start_time", "00:00:00,000")
            confidence = result_json.get("confidence", 0.0)
            reasoning = result_json.get("reasoning", "")
            
            # 计算hook_end_time（如果有Hook）
            hook_end_time = None
            if has_hook:
                hook_end_time = self._calculate_hook_end_time(body_start_time)
            
            result = BodyStartDetectionResult(
                has_hook=has_hook,
                body_start_time=body_start_time,
                hook_end_time=hook_end_time,
                confidence=confidence,
                reasoning=reasoning
            )
            
            logger.info(f"✅ Body起点检测完成:")
            logger.info(f"   has_hook={has_hook}")
            logger.info(f"   body_start_time={body_start_time}")
            logger.info(f"   confidence={confidence:.2f}")
            logger.info(f"   reasoning: {reasoning[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Body起点检测失败: {e}")
            # 返回默认结果（假设没有Hook）
            return BodyStartDetectionResult(
                has_hook=False,
                body_start_time="00:00:00,000",
                hook_end_time=None,
                confidence=0.0,
                reasoning=f"检测失败: {str(e)}"
            )
    
    def _extract_srt_preview(self, srt_text: str, max_seconds: int) -> str:
        """
        提取SRT前N秒的内容
        
        返回格式化的字幕预览，包含时间戳和文本
        """
        lines = srt_text.strip().split('\n')
        preview_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                i += 1
                continue
            
            # 跳过序号行
            if line.isdigit():
                i += 1
                continue
            
            # 检查是否是时间戳行
            if '-->' in line:
                # 解析起始时间
                start_time_str = line.split('-->')[0].strip()
                start_seconds = self._parse_srt_time_to_seconds(start_time_str)
                
                # 如果超过max_seconds，停止
                if start_seconds > max_seconds:
                    break
                
                # 读取字幕文本（下一行）
                i += 1
                if i < len(lines):
                    subtitle_text = lines[i].strip()
                    preview_lines.append(f"{start_time_str} - {subtitle_text}")
            
            i += 1
        
        return '\n'.join(preview_lines)
    
    def _extract_novel_preview(self, novel_text: str, max_chars: int = 2000) -> str:
        """提取Novel前N个字符作为概要"""
        preview = novel_text[:max_chars]
        if len(novel_text) > max_chars:
            preview += "\n..."
        return preview
    
    def _parse_srt_time_to_seconds(self, time_str: str) -> float:
        """
        将SRT时间戳转换为秒数
        
        例: "00:00:30,900" -> 30.9
        """
        try:
            # 格式: HH:MM:SS,mmm
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            
            total_seconds = h * 3600 + m * 60 + s + ms / 1000.0
            return total_seconds
        except Exception as e:
            logger.warning(f"解析时间戳失败: {time_str}, {e}")
            return 0.0
    
    def _calculate_hook_end_time(self, body_start_time: str) -> str:
        """
        计算Hook结束时间（即Body开始时间的前一刻）
        
        实际上Hook结束时间就是Body开始时间
        这里只是为了语义清晰
        """
        return body_start_time
    
    def filter_srt_by_time(
        self,
        srt_text: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> str:
        """
        根据时间范围过滤SRT内容
        
        Args:
            srt_text: 完整的SRT文本
            start_time: 开始时间（如 "00:00:30,900"），None表示从头开始
            end_time: 结束时间，None表示到末尾
        
        Returns:
            过滤后的SRT文本
        """
        start_seconds = self._parse_srt_time_to_seconds(start_time) if start_time else 0.0
        end_seconds = self._parse_srt_time_to_seconds(end_time) if end_time else float('inf')
        
        lines = srt_text.strip().split('\n')
        filtered_lines = []
        
        i = 0
        subtitle_index = 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过空行
            if not line:
                i += 1
                continue
            
            # 检查是否是序号行
            if line.isdigit():
                # 读取时间戳行
                i += 1
                if i >= len(lines):
                    break
                
                timestamp_line = lines[i].strip()
                
                if '-->' in timestamp_line:
                    # 解析时间戳
                    start_str = timestamp_line.split('-->')[0].strip()
                    subtitle_start = self._parse_srt_time_to_seconds(start_str)
                    
                    # 判断是否在范围内
                    if start_seconds <= subtitle_start <= end_seconds:
                        # 读取字幕文本
                        i += 1
                        if i >= len(lines):
                            break
                        
                        subtitle_text = lines[i].strip()
                        
                        # 添加到结果（重新编号）
                        filtered_lines.append(str(subtitle_index))
                        filtered_lines.append(timestamp_line)
                        filtered_lines.append(subtitle_text)
                        filtered_lines.append('')  # 空行分隔
                        
                        subtitle_index += 1
            
            i += 1
        
        return '\n'.join(filtered_lines)
