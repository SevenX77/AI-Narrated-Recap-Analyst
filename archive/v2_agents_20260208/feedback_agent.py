import json
from typing import List, Any
from src.core.schemas import AlignmentItem, FeedbackReport
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts

class FeedbackAgent:
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name
        self.prompts = load_prompts("feedback")

    def analyze_alignment(self, alignment_items: List[AlignmentItem]) -> FeedbackReport:
        """
        分析对齐结果，生成反馈报告
        """
        # Prepare context for LLM
        alignment_context = ""
        for item in alignment_items:
            alignment_context += f"""
            [Time: {item.script_time}]
            Script: {item.script_event}
            Novel Match: {item.matched_novel_chapter} - {item.matched_novel_event}
            Reason: {item.match_reason}
            Confidence: {item.confidence}
            --------------------------------------------------
            """

        system_prompt = self.prompts["feedback_analysis"]["system"]
        user_prompt = self.prompts["feedback_analysis"]["user"].format(
            alignment_context=alignment_context
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
            return FeedbackReport(**data)

        except Exception as e:
            logger.error(f"Error during feedback analysis: {e}")
            return FeedbackReport(
                score=0.0,
                issues=[f"Error: {str(e)}"],
                suggestions=[],
                methodology_update="Analysis Failed"
            )
