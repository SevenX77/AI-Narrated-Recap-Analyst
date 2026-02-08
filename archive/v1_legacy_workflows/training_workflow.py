import os
import json
from typing import List
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.agents.feedback_agent import FeedbackAgent
from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine
from src.core.interfaces import BaseWorkflow
from src.core.schemas import NarrativeEvent
from src.utils.logger import logger, op_logger
from src.core.artifact_manager import artifact_manager
from src.core.project_manager import project_manager

class TrainingWorkflow(BaseWorkflow):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.paths = project_manager.get_project_paths(project_id)
        self.client = get_llm_client()
        self.analyst = DeepSeekAnalyst(self.client)
        self.aligner = DeepSeekAlignmentEngine(self.client)
        self.feedback_agent = FeedbackAgent(self.client)
        
        # Register agents
        self.register_agent(self.analyst)

    async def run(self, **kwargs):
        logger.info(f"🚀 开始训练流程: {self.project_id}")
        
        # 1. Load Artifacts (Novel Events & Alignment)
        # Assuming Ingestion Workflow has already run and produced these
        logger.info("1. 加载对齐数据...")
        
        novel_events_db = artifact_manager.load_latest_artifact("novel_events", self.paths['alignment'])
        if not novel_events_db:
            logger.error("❌ 未找到 Novel Events，请先运行 Ingestion Workflow")
            return

        # Load Alignment Map (Ground Truth)
        # In a real training loop, we might iterate over this map
        # For now, we are simulating the feedback loop based on existing alignment results
        # But wait, the original code WAS doing alignment. 
        # According to new logic_flows.md, Workflow 2 is "Training Loop", which uses alignment.json as input.
        # However, the previous implementation was DOING alignment.
        # Let's align with the doc: "Workflow 2: Training Workflow... 3. Alignment... 4. Feedback"
        # Wait, doc says Workflow 1 produces alignment.json. Workflow 2 USES it.
        # But the USER's prompt implied Workflow 2 is "Training/Optimization".
        # Let's look at logic_flows.md again.
        
        # Doc says:
        # Workflow 1: Ingestion & Alignment -> Output alignment.json
        # Workflow 2: Training Loop -> Input alignment.json -> Writer generates -> Evaluation
        
        # The OLD TrainingWorkflow was actually doing Alignment. 
        # So I should rename the old logic to IngestionWorkflow? 
        # OR, I should change TrainingWorkflow to actually do Training (Writer generation).
        
        # Given the user's request "Refactor TrainingWorkflow to use ArtifactManager", 
        # and the context of "Check Workflow 2 consistency", 
        # I should make TrainingWorkflow match "Workflow 2: Training Loop" in the doc.
        
        # BUT, currently we don't have an IngestionWorkflow code file.
        # So if I strip Alignment out of here, we lose the ability to generate alignment.json.
        # I have a TODO "Create IngestionWorkflow implementation".
        # So I will move the Alignment logic to IngestionWorkflow later, 
        # and here I will implement the Training Loop (Writer Generation).
        
        # HOWEVER, looking at the previous code, it was doing:
        # Load Novel -> Extract Events -> Process SRT -> Align -> Feedback.
        # This is basically "Ingestion + Alignment + Feedback".
        
        # Let's implement the "Training Loop" as defined in the doc:
        # 1. Load Context (from alignment.json)
        # 2. Writer Generation
        # 3. Evaluation
        
        # Save Alignment Results (if we were generating them here, but we are loading them)
        # However, we are generating FEEDBACK reports, so we should save those as artifacts.
        
        feedback = self.feedback_agent.analyze_alignment(alignment_results)
        
        # Save Methodology
        methodology_path = artifact_manager.save_artifact(
            feedback.methodology_update,
            "methodology",
            self.project_id,
            os.path.join(self.paths['root'], "training", "reports"),
            extension="txt"
        )
            
        report_path = artifact_manager.save_artifact(
            feedback.model_dump(),
            "feedback_report",
            self.project_id,
            os.path.join(self.paths['root'], "training", "reports")
        )
            
        # Log operation
        op_logger.log_operation(
            project_id=self.project_id,
            action="Training Workflow Completed",
            output_files=[methodology_path, report_path],
            details=f"Score: {feedback.score}"
        )


