"""
热度驱动的训练工作流 (Training Workflow V2)

基于真实热度数据的规则学习和内容评估系统
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.interfaces import BaseWorkflow
from src.core.schemas_feedback import RuleBook, ValidationResult, ComparativeFeedback
from src.agents.rule_extractor import RuleExtractorAgent
from src.agents.rule_validator import RuleValidatorAgent
from src.agents.comparative_evaluator import ComparativeEvaluatorAgent
from src.agents.deepseek_analyst import get_llm_client
from src.core.artifact_manager import artifact_manager
from src.core.project_manager import project_manager
from src.utils.logger import logger, op_logger


class HeatDrivenTrainingWorkflow(BaseWorkflow):
    """
    热度驱动的训练工作流
    
    工作流程：
    1. 规则提取：从多个GT项目中提取爆款规则
    2. 规则验证：验证规则能否预测GT项目的热度
    3. 规则优化：根据验证结果调整规则权重
    4. 内容评估：用优化后的规则评估新生成的内容
    """
    
    def __init__(self):
        """初始化工作流"""
        super().__init__()
        self.client = get_llm_client()
        
        # 初始化Agents
        self.rule_extractor = RuleExtractorAgent(self.client)
        self.rule_validator = RuleValidatorAgent(self.client)
        self.comparative_evaluator = ComparativeEvaluatorAgent(self.client)
        
        # 注册Agents
        self.register_agent(self.rule_extractor)
        self.register_agent(self.rule_validator)
        self.register_agent(self.comparative_evaluator)
        
        # 规则库存储路径
        self.rulebook_dir = os.path.join("data", "rule_books")
        os.makedirs(self.rulebook_dir, exist_ok=True)
    
    async def run(self, mode: str = "extract", **kwargs):
        """
        运行工作流
        
        Args:
            mode: 运行模式
                - "extract": 提取规则
                - "validate": 验证规则
                - "evaluate": 评估新内容
                - "full": 完整流程（提取→验证→评估）
            **kwargs: 其他参数
        """
        logger.info(f"🚀 启动热度驱动训练工作流 (模式: {mode})")
        
        if mode == "extract":
            return await self._run_rule_extraction(**kwargs)
        elif mode == "validate":
            return await self._run_rule_validation(**kwargs)
        elif mode == "evaluate":
            return await self._run_content_evaluation(**kwargs)
        elif mode == "full":
            return await self._run_full_pipeline(**kwargs)
        else:
            raise ValueError(f"未知模式: {mode}")
    
    async def _run_rule_extraction(
        self,
        gt_project_ids: Optional[List[str]] = None,
        **kwargs
    ) -> RuleBook:
        """
        运行规则提取流程
        
        Args:
            gt_project_ids: Ground Truth项目ID列表
            
        Returns:
            RuleBook: 提取的规则库
        """
        logger.info("=" * 60)
        logger.info("阶段1: 规则提取")
        logger.info("=" * 60)
        
        # 1. 加载项目索引，获取热度数据
        project_index = self._load_project_index()
        
        # 2. 筛选Ground Truth项目
        if not gt_project_ids:
            gt_project_ids = [
                pid for pid, info in project_index["projects"].items()
                if info.get("is_ground_truth", False) and info.get("heat_score") is not None
            ]
        
        if not gt_project_ids:
            raise ValueError("未找到可用的Ground Truth项目（需要设置is_ground_truth=true且有heat_score）")
        
        logger.info(f"📋 找到 {len(gt_project_ids)} 个Ground Truth项目: {gt_project_ids}")
        
        # 3. 加载各项目数据
        projects_data = {}
        heat_scores = {}
        explosive_flags = {}
        
        for project_id in gt_project_ids:
            project_info = project_index["projects"][project_id]
            heat_score = project_info.get("heat_score")
            
            if heat_score is None:
                logger.warning(f"⚠️  {project_id} 缺少热度值，跳过")
                continue
            
            # 加载项目数据
            project_data = self._load_project_data(project_id)
            if project_data:
                projects_data[project_id] = project_data
                heat_scores[project_id] = heat_score
                explosive_flags[project_id] = project_info.get("is_explosive", False)
                
                explosive_tag = " 🔥" if explosive_flags[project_id] else ""
                logger.info(f"✅ {project_id}: 热度={heat_score}{explosive_tag}")
        
        if not projects_data:
            raise ValueError("没有成功加载任何项目数据")
        
        # 4. 提取规则
        logger.info("\n🔍 开始提取规则...")
        explosive_count = sum(1 for is_exp in explosive_flags.values() if is_exp)
        if explosive_count > 0:
            logger.info(f"   📌 包含 {explosive_count} 个已验证爆款项目（将获得更高权重）")
        
        rulebook = self.rule_extractor.extract_rules_from_projects(
            projects_data,
            heat_scores,
            explosive_flags
        )
        
        # 5. 保存规则库
        rulebook_path = self._save_rulebook(rulebook)
        logger.info(f"\n✅ 规则库已保存: {rulebook_path}")
        
        # 6. 记录操作
        op_logger.log_operation(
            project_id="SYSTEM",
            action="Rule Extraction",
            output_files=[rulebook_path],
            details=f"从 {len(projects_data)} 个项目提取规则"
        )
        
        return rulebook
    
    async def _run_rule_validation(
        self,
        rulebook: Optional[RuleBook] = None,
        rulebook_version: Optional[str] = None,
        **kwargs
    ) -> ValidationResult:
        """
        运行规则验证流程
        
        Args:
            rulebook: 规则库对象（如果不提供，则加载最新版本）
            rulebook_version: 规则库版本（如果不提供rulebook对象）
            
        Returns:
            ValidationResult: 验证结果
        """
        logger.info("=" * 60)
        logger.info("阶段2: 规则验证")
        logger.info("=" * 60)
        
        # 1. 加载规则库
        if not rulebook:
            rulebook = self._load_rulebook(rulebook_version)
        
        logger.info(f"📖 使用规则库: {rulebook.version}")
        
        # 2. 加载GT项目数据
        project_index = self._load_project_index()
        gt_project_ids = rulebook.extracted_from_projects
        
        projects_data = {}
        actual_heat_scores = {}
        
        for project_id in gt_project_ids:
            project_info = project_index["projects"].get(project_id)
            if not project_info:
                continue
            
            heat_score = project_info.get("heat_score")
            if heat_score is None:
                continue
            
            project_data = self._load_project_data(project_id)
            if project_data:
                projects_data[project_id] = project_data
                actual_heat_scores[project_id] = heat_score
        
        # 3. 验证规则
        logger.info("\n🔍 开始验证规则...")
        validation_result = self.rule_validator.validate_rulebook(
            rulebook,
            projects_data,
            actual_heat_scores
        )
        
        # 4. 保存验证结果
        validation_path = os.path.join(
            self.rulebook_dir,
            f"validation_{rulebook.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(validation_path, 'w', encoding='utf-8') as f:
            json.dump(validation_result.model_dump(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ 验证结果已保存: {validation_path}")
        logger.info(f"   - 相关性: {validation_result.correlation:.2f}")
        logger.info(f"   - 是否通过: {validation_result.is_valid}")
        
        # 5. 如果验证通过，更新规则库状态
        if validation_result.is_valid:
            rulebook.heat_prediction_accuracy = validation_result.correlation
            self._save_rulebook(rulebook)
            logger.info("✅ 规则库已更新预测准确率")
        else:
            logger.warning("⚠️  规则验证未通过，建议根据优化建议调整规则")
            for suggestion in validation_result.optimization_suggestions:
                logger.warning(f"   - {suggestion}")
        
        # 6. 记录操作
        op_logger.log_operation(
            project_id="SYSTEM",
            action="Rule Validation",
            output_files=[validation_path],
            details=f"验证规则库 {rulebook.version}, 相关性={validation_result.correlation:.2f}"
        )
        
        return validation_result
    
    async def _run_content_evaluation(
        self,
        project_id: str,
        generated_content: Optional[Dict[str, Any]] = None,
        gt_reference_project: Optional[str] = None,
        rulebook: Optional[RuleBook] = None,
        **kwargs
    ) -> ComparativeFeedback:
        """
        运行内容评估流程
        
        Args:
            project_id: 待评估项目ID
            generated_content: 生成的内容数据（如果不提供，则从项目中加载）
            gt_reference_project: 参考的GT项目ID
            rulebook: 规则库（如果不提供，则加载最新版本）
            
        Returns:
            ComparativeFeedback: 评估报告
        """
        logger.info("=" * 60)
        logger.info(f"阶段3: 内容评估 (项目: {project_id})")
        logger.info("=" * 60)
        
        # 1. 加载规则库
        if not rulebook:
            rulebook = self._load_rulebook()
        
        logger.info(f"📖 使用规则库: {rulebook.version}")
        
        # 2. 加载Generated内容
        if not generated_content:
            generated_content = self._load_generated_content(project_id)
        
        # 3. 确定参考GT项目
        if not gt_reference_project:
            # 使用热度最高的GT项目作为参考
            heat_scores = rulebook.project_heat_scores
            gt_reference_project = max(heat_scores.items(), key=lambda x: x[1])[0]
        
        logger.info(f"📚 参考GT项目: {gt_reference_project}")
        
        # 4. 加载GT内容
        gt_content = self._load_project_data(gt_reference_project)
        gt_heat_score = rulebook.project_heat_scores[gt_reference_project]
        
        # 5. 对比评估
        logger.info("\n🔍 开始对比评估...")
        feedback = self.comparative_evaluator.compare_with_ground_truth(
            generated_content,
            gt_content,
            gt_heat_score,
            rulebook,
            gt_reference_project
        )
        
        # 6. 保存评估报告
        paths = project_manager.get_project_paths(project_id)
        report_dir = os.path.join(paths['root'], "training", "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = artifact_manager.save_artifact(
            feedback.model_dump(),
            "comparative_feedback",
            project_id,
            report_dir
        )
        
        logger.info(f"\n✅ 评估报告已保存: {report_path}")
        logger.info(f"   - 总分: {feedback.total_score}/{feedback.max_score}")
        logger.info(f"   - 预测热度: {feedback.predicted_heat_score:.1f}")
        logger.info(f"   - 建议: {feedback.recommendation}")
        
        # 7. 记录操作
        op_logger.log_operation(
            project_id=project_id,
            action="Content Evaluation",
            output_files=[report_path],
            details=f"得分={feedback.total_score}, 预测热度={feedback.predicted_heat_score:.1f}"
        )
        
        return feedback
    
    async def _run_full_pipeline(self, **kwargs) -> Dict[str, Any]:
        """
        运行完整流程：提取→验证→评估
        
        Returns:
            包含所有结果的字典
        """
        logger.info("🚀 运行完整热度驱动训练流程")
        
        # 1. 提取规则
        rulebook = await self._run_rule_extraction(**kwargs)
        
        # 2. 验证规则
        validation_result = await self._run_rule_validation(rulebook=rulebook, **kwargs)
        
        # 3. 如果有待评估项目，进行评估
        project_id = kwargs.get('eval_project_id')
        feedback = None
        if project_id:
            feedback = await self._run_content_evaluation(
                project_id=project_id,
                rulebook=rulebook,
                **kwargs
            )
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 完整流程执行完毕")
        logger.info("=" * 60)
        
        return {
            "rulebook": rulebook,
            "validation_result": validation_result,
            "feedback": feedback
        }
    
    # ==================== 辅助方法 ====================
    
    def _load_project_index(self) -> Dict[str, Any]:
        """加载项目索引"""
        index_path = os.path.join("data", "project_index.json")
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_project_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        加载项目数据
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目数据字典
        """
        try:
            paths = project_manager.get_project_paths(project_id)
            
            # 加载SRT
            srt_path = os.path.join(paths['raw'], "ep01.srt")
            if not os.path.exists(srt_path):
                logger.warning(f"⚠️  {project_id}: 未找到ep01.srt")
                return None
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # 加载事件数据（如果有）
            events_path = os.path.join(paths['alignment'], "_backup", "ep01_script_events_latest.json")
            events = []
            if os.path.exists(events_path):
                with open(events_path, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
                    events = events_data.get('events', [])
            
            return {
                'srt_content': srt_content,
                'events': events,
                'hook_info': {}  # 可以从hook检测结果中加载
            }
            
        except Exception as e:
            logger.error(f"❌ 加载项目 {project_id} 数据失败: {e}")
            return None
    
    def _load_generated_content(self, project_id: str) -> Dict[str, Any]:
        """加载生成的内容"""
        paths = project_manager.get_project_paths(project_id)
        script_path = os.path.join(paths['root'], "production", "scripts", "ep01_script_latest.json")
        
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"未找到生成的script: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_rulebook(self, rulebook: RuleBook) -> str:
        """保存规则库"""
        filename = f"rulebook_{rulebook.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.rulebook_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rulebook.model_dump(), f, indent=2, ensure_ascii=False)
        
        # 同时保存一份latest版本
        latest_path = os.path.join(self.rulebook_dir, f"rulebook_{rulebook.version}_latest.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(rulebook.model_dump(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _load_rulebook(self, version: Optional[str] = None) -> RuleBook:
        """
        加载规则库
        
        Args:
            version: 版本号（如果不提供，加载最新版本）
            
        Returns:
            RuleBook
        """
        if version:
            filepath = os.path.join(self.rulebook_dir, f"rulebook_{version}_latest.json")
        else:
            # 查找最新的rulebook文件
            files = [f for f in os.listdir(self.rulebook_dir) if f.startswith("rulebook_") and f.endswith("_latest.json")]
            if not files:
                raise FileNotFoundError("未找到任何规则库文件")
            files.sort(reverse=True)
            filepath = os.path.join(self.rulebook_dir, files[0])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return RuleBook(**data)
