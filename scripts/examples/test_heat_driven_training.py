"""
热度驱动训练系统测试脚本

演示如何使用新的热度驱动训练工作流
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.workflows.training_workflow_v2 import HeatDrivenTrainingWorkflow
from src.utils.logger import logger


async def test_rule_extraction():
    """
    测试规则提取
    
    前提条件：
    1. project_index.json中至少有2个项目标记为is_ground_truth=true
    2. 这些项目有heat_score值
    3. 这些项目的data/projects/PROJ_XXX/raw/ep01.srt文件存在
    """
    logger.info("=" * 60)
    logger.info("测试1: 规则提取")
    logger.info("=" * 60)
    
    workflow = HeatDrivenTrainingWorkflow()
    
    try:
        rulebook = await workflow.run(mode="extract")
        
        logger.info("\n✅ 规则提取成功!")
        logger.info(f"   版本: {rulebook.version}")
        logger.info(f"   源项目: {rulebook.extracted_from_projects}")
        logger.info(f"   Hook规则数: {len(rulebook.hook_rules)}")
        logger.info(f"   Ep01规则数: {len(rulebook.ep01_rules)}")
        logger.info(f"   Ep02+规则数: {len(rulebook.ep02_plus_rules)}")
        
        return rulebook
        
    except Exception as e:
        logger.error(f"❌ 规则提取失败: {e}")
        raise


async def test_rule_validation(rulebook=None):
    """
    测试规则验证
    
    Args:
        rulebook: 规则库对象（如果不提供，则加载最新版本）
    """
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 规则验证")
    logger.info("=" * 60)
    
    workflow = HeatDrivenTrainingWorkflow()
    
    try:
        validation_result = await workflow.run(
            mode="validate",
            rulebook=rulebook
        )
        
        logger.info("\n✅ 规则验证完成!")
        logger.info(f"   相关性: {validation_result.correlation:.2f}")
        logger.info(f"   是否通过: {validation_result.is_valid}")
        
        if validation_result.is_valid:
            logger.info("   ✅ 规则验证通过，可以用于评估")
        else:
            logger.warning("   ⚠️  规则验证未通过，建议优化")
            logger.warning("   优化建议:")
            for suggestion in validation_result.optimization_suggestions[:3]:
                logger.warning(f"     - {suggestion}")
        
        # 显示各项目评分
        logger.info("\n   各项目评分:")
        for project_id, scores in validation_result.project_scores.items():
            predicted = scores.get('predicted_heat', 0)
            actual = scores.get('actual_heat', 0)
            gap = scores.get('gap', 0)
            logger.info(f"     {project_id}: 预测={predicted:.1f}, 实际={actual:.1f}, 差距={gap:+.1f}")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ 规则验证失败: {e}")
        raise


async def test_content_evaluation(project_id="PROJ_002", rulebook=None):
    """
    测试内容评估
    
    Args:
        project_id: 待评估的项目ID
        rulebook: 规则库对象（如果不提供，则加载最新版本）
    """
    logger.info("\n" + "=" * 60)
    logger.info(f"测试3: 内容评估 (项目: {project_id})")
    logger.info("=" * 60)
    
    workflow = HeatDrivenTrainingWorkflow()
    
    try:
        feedback = await workflow.run(
            mode="evaluate",
            project_id=project_id,
            rulebook=rulebook
        )
        
        logger.info("\n✅ 内容评估完成!")
        logger.info(f"   总分: {feedback.total_score}/{feedback.max_score}")
        logger.info(f"   预测热度: {feedback.predicted_heat_score:.1f}/10")
        logger.info(f"   GT参考: {feedback.gt_project_id} (热度={feedback.gt_heat_score})")
        logger.info(f"   分数差距: {feedback.score_gap:+.1f}")
        logger.info(f"   建议: {feedback.recommendation}")
        
        # 显示各维度得分
        logger.info("\n   各维度得分:")
        for dim_score in feedback.dimension_scores[:5]:  # 只显示前5个
            logger.info(f"     {dim_score.dimension}: {dim_score.score}/{dim_score.max_score}")
        
        # 显示关键问题
        if feedback.critical_issues:
            logger.warning("\n   ⚠️  关键问题:")
            for issue in feedback.critical_issues[:3]:
                logger.warning(f"     - {issue}")
        
        # 显示改进建议
        if feedback.major_improvements:
            logger.info("\n   💡 改进建议:")
            for improvement in feedback.major_improvements[:3]:
                logger.info(f"     - {improvement}")
        
        # 显示亮点
        if feedback.strengths:
            logger.info("\n   ✨ 亮点:")
            for strength in feedback.strengths[:3]:
                logger.info(f"     - {strength}")
        
        return feedback
        
    except Exception as e:
        logger.error(f"❌ 内容评估失败: {e}")
        raise


async def test_full_pipeline(eval_project_id="PROJ_002"):
    """
    测试完整流程
    
    Args:
        eval_project_id: 待评估的项目ID
    """
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 完整流程（提取→验证→评估）")
    logger.info("=" * 60)
    
    workflow = HeatDrivenTrainingWorkflow()
    
    try:
        results = await workflow.run(
            mode="full",
            eval_project_id=eval_project_id
        )
        
        logger.info("\n✅ 完整流程执行成功!")
        logger.info(f"   规则库版本: {results['rulebook'].version}")
        logger.info(f"   验证相关性: {results['validation_result'].correlation:.2f}")
        if results['feedback']:
            logger.info(f"   评估得分: {results['feedback'].total_score}/100")
            logger.info(f"   预测热度: {results['feedback'].predicted_heat_score:.1f}/10")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ 完整流程失败: {e}")
        raise


async def main():
    """主测试函数"""
    logger.info("🚀 开始测试热度驱动训练系统\n")
    
    # 选择测试模式
    test_mode = "full"  # 可选: "extract", "validate", "evaluate", "full"
    
    if test_mode == "extract":
        # 仅测试规则提取
        await test_rule_extraction()
        
    elif test_mode == "validate":
        # 先提取规则，再验证
        rulebook = await test_rule_extraction()
        await test_rule_validation(rulebook)
        
    elif test_mode == "evaluate":
        # 先提取规则，再评估内容
        rulebook = await test_rule_extraction()
        await test_content_evaluation(project_id="PROJ_002", rulebook=rulebook)
        
    elif test_mode == "full":
        # 完整流程
        await test_full_pipeline(eval_project_id="PROJ_002")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 所有测试完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
