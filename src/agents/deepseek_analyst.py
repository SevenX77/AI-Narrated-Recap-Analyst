import os
import json
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from src.core.schemas import SceneAnalysis, NarrativeEvent
from .analyst import AnalystAgent

load_dotenv()

def get_llm_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "ollama")
        base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

    return OpenAI(api_key=api_key, base_url=base_url)

class DeepSeekAnalyst(AnalystAgent):
    def extract_events(self, text: str, context_id: str = "") -> List[NarrativeEvent]:
        """
        使用 LLM 提取 SVO 事件流，返回结构化对象列表
        """
        system_prompt = """
        你是一个精准的剧情事件提取器。
        请阅读输入文本，忽略修饰性描写，将核心剧情提取为“主语+谓语+宾语/结果”的 SVO 格式。
        请务必返回合法的 JSON 数组格式。
        """
        
        user_prompt = f"""
        【文本来源】：{context_id}
        【文本内容】：
        {text}
        
        【任务】：
        提取核心事件，每条事件包含：
        - subject: 主语 (Who)
        - action: 谓语/动作 (Did what)
        - outcome: 宾语/结果 (To whom/what)
        - event_type: 类型 (plot/setting/emotion)
        
        请直接返回 JSON 数组，例如：
        [
            {{"subject": "陈野", "action": "觉醒了", "outcome": "升级系统", "event_type": "plot"}}
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            events_list = []
            if isinstance(data, list):
                events_list = data
            elif isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        events_list = val
                        break
            
            return [NarrativeEvent(**e) for e in events_list]
            
        except Exception as e:
            print(f"Error extracting events for {context_id}: {e}")
            return []

    def analyze(self, text_chunk: str, previous_context: str = "") -> SceneAnalysis:
        system_prompt = """
        你是一个资深的小说拆解分析师。你的任务不是创作，而是**精准提取**。
        你需要阅读输入的小说片段，将其拆解为结构化的数据，供下游的“解说生成Agent”使用。

        **核心原则：**
        1. **客观准确**：不要臆造剧情。
        2. **关注节奏**：重点识别剧情的起伏（Beats）。
        3. **抽象模式**：在 narrative_pattern 字段中，你需要识别出这段剧情的骨架。这对于将一种题材的解说经验迁移到另一种题材至关重要。
           - 错误示范：陈野用弩箭射杀了强子。
           - 正确示范：主角果断出手，消灭了产生威胁的次要反派，震慑全场。

        请务必返回合法的 JSON 格式，不要包含 Markdown 代码块标记。
        """

        user_prompt = f"""
        【前情提要】：
        {previous_context}

        【当前小说片段】：
        {text_chunk}

        请分析上述片段，并以 JSON 格式返回 SceneAnalysis 对象的数据结构：
        {{
            "summary": "...",
            "scene_type": "...",
            "characters": [
                {{"name": "...", "role": "...", "status": "..."}}
            ],
            "beats": [
                {{"event_type": "...", "description": "...", "intensity": 1-10}}
            ],
            "potential_hooks": ["..."],
            "narrative_pattern": "...",
            "flashback_candidate": "...",
            "protagonist_name": "..."
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )

            result_json = response.choices[0].message.content
            data = json.loads(result_json)
            return SceneAnalysis(**data)

        except Exception as e:
            print(f"Error during analysis: {e}")
            return SceneAnalysis(
                summary=f"Analysis failed: {str(e)}",
                scene_type="Error",
                characters=[],
                beats=[],
                potential_hooks=[],
                narrative_pattern="Error",
                flashback_candidate=None,
                protagonist_name="Unknown"
            )
