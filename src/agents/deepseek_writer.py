import json
import logging
from openai import OpenAI

from src.core.config import config
from src.core.schemas import SceneAnalysis
from src.core.schemas_writer import Script
from src.utils.prompt_loader import load_prompts
from .writer import WriterAgent

# Configure logging
logger = logging.getLogger(__name__)

class DeepSeekWriter(WriterAgent):
    def __init__(self, client=None):
        if not client:
            client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
        super().__init__(client=client, model_name=config.llm.model_name)
        self.prompts = load_prompts("writer")

    def generate_script(self, analysis: SceneAnalysis, style: str = "first_person") -> Script:
        try:
            prompt_templates = self.prompts["generate_script"]
            system_prompt = prompt_templates["system"]
            
            # Prepare dynamic parts of the prompt
            pronoun_instruction = f"请使用第一人称“我”来替代主角“{analysis.protagonist_name}”。" if style == "first_person" else ""
            
            flashback_instruction = ""
            if analysis.flashback_candidate:
                flashback_instruction = f"【强烈建议】：使用倒叙手法，开篇先展示“{analysis.flashback_candidate}”这一高潮/悬念场景，然后再回调时间线讲起因。"

            user_prompt = prompt_templates["user"].format(
                summary=analysis.summary,
                beats=json.dumps([b.model_dump() for b in analysis.beats], ensure_ascii=False),
                potential_hooks=analysis.potential_hooks,
                flashback_candidate=analysis.flashback_candidate,
                pronoun_instruction=pronoun_instruction,
                flashback_instruction=flashback_instruction
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7, # Slightly higher creativity for writing
                response_format={ "type": "json_object" }
            )

            result_json = response.choices[0].message.content
            data = json.loads(result_json)
            return Script(**data)

        except Exception as e:
            logger.error(f"Error during script generation: {e}", exc_info=True)
            # Return a dummy script on error
            return Script(
                title="Error Generation",
                segments=[],
                total_duration=0,
                narrative_strategy="Error"
            )
