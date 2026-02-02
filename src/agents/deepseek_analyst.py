import os
import json
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from src.core.schemas import SceneAnalysis, NarrativeEvent
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts
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
    def __init__(self, client=None, model_name: str = "deepseek-chat"):
        super().__init__(client, model_name)
        self.prompts = load_prompts("analyst")

    def extract_events(self, text: str, context_id: str = "") -> List[NarrativeEvent]:
        """
        使用 LLM 提取 SVO 事件流，返回结构化对象列表
        """
        system_prompt = self.prompts["extract_events"]["system"]
        user_prompt = self.prompts["extract_events"]["user"].format(
            context_id=context_id,
            text=text
        )
        
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
            logger.error(f"Error extracting events for {context_id}: {e}")
            return []

    def analyze(self, text_chunk: str, previous_context: str = "") -> SceneAnalysis:
        system_prompt = self.prompts["analyze_scene"]["system"]
        user_prompt = self.prompts["analyze_scene"]["user"].format(
            previous_context=previous_context,
            text_chunk=text_chunk
        )

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
            logger.error(f"Error during analysis: {e}")
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
