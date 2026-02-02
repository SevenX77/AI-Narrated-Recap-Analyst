import json
from typing import List, Any
from src.core.schemas import AlignmentItem, FeedbackReport

class FeedbackAgent:
    def __init__(self, client: Any, model_name: str = "deepseek-chat"):
        self.client = client
        self.model_name = model_name

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

        system_prompt = """
        你是一个资深的短视频解说内容总监。
        你的任务是分析“解说文案”与“原著小说”的对齐情况，反向推导出“爆款解说改编法则”。
        
        请分析以下几个维度：
        1. **取舍逻辑**：什么样的剧情被保留了？什么样的被删减了？（如：心理描写、环境描写、次要人物）
        2. **节奏变化**：解说是否进行了倒叙、插叙或加速？
        3. **情绪渲染**：解说是否夸大了某些冲突或爽点？
        
        最后，请总结出一套“改编方法论”，用于指导 AI 生成类似的解说文案。
        """

        user_prompt = f"""
        【对齐数据】：
        {alignment_context}
        
        【任务】：
        请生成一份反馈报告，包含：
        1. score: 总体改编质量评分 (0-100，基于是否符合爆款逻辑)
        2. issues: 发现的问题（如果有）
        3. suggestions: 具体改进建议
        4. methodology_update: 提炼出的核心改编法则（请用精炼的语言描述，如“开篇必须前置高潮”、“删除所有非必要的环境描写”）
        
        请返回 JSON 格式。
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
            return FeedbackReport(**data)

        except Exception as e:
            print(f"Error during feedback analysis: {e}")
            return FeedbackReport(
                score=0.0,
                issues=[f"Error: {str(e)}"],
                suggestions=[],
                methodology_update="Analysis Failed"
            )
