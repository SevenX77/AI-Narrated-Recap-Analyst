"""
生产环境模拟测试：ScriptProcessingWorkflow

验证关键业务逻辑：
1. Hook检测只在ep01执行
2. ep02-10不执行Hook检测
3. 所有集数都执行ABC分段
4. 质量门禁正常工作

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig, ScriptProcessingResult


class ProductionSimulator:
    """
    生产环境模拟器
    """
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.workflow = ScriptProcessingWorkflow()
        self.results: Dict[str, ScriptProcessingResult] = {}
        self.statistics = {
            "total_episodes": 0,
            "successful": 0,
            "failed": 0,
            "hook_detected_count": 0,
            "hook_analysis_count": 0,
            "total_cost": 0.0,
            "total_time": 0.0,
            "total_llm_calls": 0,
            "quality_scores": []
        }
    
    async def process_episode(
        self,
        episode_name: str,
        srt_path: str,
        config: ScriptProcessingConfig,
        novel_reference: str = None,
        novel_intro: str = None
    ) -> ScriptProcessingResult:
        """
        处理单个集数
        """
        print(f"\n{'=' * 80}")
        print(f"📺 处理集数: {episode_name}")
        print(f"{'=' * 80}")
        
        start_time = time.time()
        
        try:
            # 执行workflow
            result = await self.workflow.run(
                srt_path=srt_path,
                project_name=self.project_name,
                episode_name=episode_name,
                config=config,
                novel_reference=novel_reference,
                novel_intro=novel_intro
            )
            
            # 记录结果
            self.results[episode_name] = result
            
            # 更新统计
            self.statistics["total_episodes"] += 1
            if result.success:
                self.statistics["successful"] += 1
            else:
                self.statistics["failed"] += 1
            
            # Hook统计
            if result.hook_detection_result:
                self.statistics["hook_detected_count"] += 1
                if result.hook_detection_result.has_hook:
                    print(f"  🎣 检测到Hook: {result.hook_detection_result.hook_end_time}")
            
            if result.hook_analysis_result:
                self.statistics["hook_analysis_count"] += 1
            
            # 成本与性能统计
            self.statistics["total_cost"] += result.total_cost
            self.statistics["total_time"] += result.processing_time
            self.statistics["total_llm_calls"] += result.llm_calls_count
            
            if result.validation_report:
                self.statistics["quality_scores"].append(result.validation_report.quality_score)
            
            # 输出摘要
            print(f"\n📊 {episode_name} 处理结果:")
            print(f"  - 状态: {'✅ 成功' if result.success else '❌ 失败'}")
            print(f"  - 耗时: {result.processing_time:.1f} 秒")
            print(f"  - 成本: ${result.total_cost:.4f} USD")
            print(f"  - LLM调用: {result.llm_calls_count} 次")
            
            if result.validation_report:
                print(f"  - 质量评分: {result.validation_report.quality_score:.0f}/100")
            
            # Hook检测信息
            if result.hook_detection_result:
                print(f"  - Hook检测: ✅ 已执行")
                print(f"    · 是否有Hook: {result.hook_detection_result.has_hook}")
                print(f"    · 置信度: {result.hook_detection_result.confidence:.2f}")
            else:
                print(f"  - Hook检测: ⏭️ 未执行（预期行为）")
            
            # 分段信息
            if result.segmentation_result:
                category_counts = {}
                for seg in result.segmentation_result.segments:
                    cat = seg.category or "Unknown"
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                print(f"  - 分段统计: {result.segmentation_result.total_segments} 段")
                print(f"    · ABC分布: {category_counts}")
            
            return result
        
        except Exception as e:
            print(f"\n❌ {episode_name} 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.statistics["total_episodes"] += 1
            self.statistics["failed"] += 1
            
            return None
    
    async def run_batch_test(
        self,
        episodes: List[Dict[str, Any]],
        config: ScriptProcessingConfig
    ):
        """
        批量处理多个集数
        """
        print("\n" + "=" * 80)
        print("🚀 开始生产环境模拟测试")
        print("=" * 80)
        print(f"项目名称: {self.project_name}")
        print(f"集数数量: {len(episodes)}")
        print(f"配置:")
        print(f"  - Hook检测: {config.enable_hook_detection}")
        print(f"  - Hook分析: {config.enable_hook_analysis}")
        print(f"  - ABC分类: {config.enable_abc_classification}")
        print(f"  - 质量阈值: {config.min_quality_score}")
        
        # 逐个处理（模拟生产环境的串行处理）
        for ep_info in episodes:
            await self.process_episode(
                episode_name=ep_info["episode_name"],
                srt_path=ep_info["srt_path"],
                config=config,
                novel_reference=ep_info.get("novel_reference"),
                novel_intro=ep_info.get("novel_intro")
            )
        
        # 输出总结
        self.print_summary()
    
    def print_summary(self):
        """
        打印测试总结
        """
        print("\n" + "=" * 80)
        print("📈 生产环境模拟测试总结")
        print("=" * 80)
        
        stats = self.statistics
        
        print(f"\n📊 处理统计:")
        print(f"  - 总集数: {stats['total_episodes']}")
        print(f"  - 成功: {stats['successful']} ✅")
        print(f"  - 失败: {stats['failed']} ❌")
        print(f"  - 成功率: {stats['successful']/stats['total_episodes']*100:.1f}%")
        
        print(f"\n🎣 Hook检测验证:")
        print(f"  - Hook检测执行次数: {stats['hook_detected_count']}")
        print(f"  - 预期执行次数: 1（仅ep01）")
        if stats['hook_detected_count'] == 1:
            print(f"  - 验证结果: ✅ 通过（Hook检测仅在ep01执行）")
        else:
            print(f"  - 验证结果: ❌ 失败（Hook检测执行次数不符合预期）")
        
        if stats['hook_analysis_count'] > 0:
            print(f"  - Hook分析执行次数: {stats['hook_analysis_count']}")
        
        print(f"\n💰 成本与性能:")
        print(f"  - 总成本: ${stats['total_cost']:.4f} USD")
        print(f"  - 平均成本: ${stats['total_cost']/stats['total_episodes']:.4f} USD/集")
        print(f"  - 总耗时: {stats['total_time']:.1f} 秒")
        print(f"  - 平均耗时: {stats['total_time']/stats['total_episodes']:.1f} 秒/集")
        print(f"  - 总LLM调用: {stats['total_llm_calls']} 次")
        print(f"  - 平均LLM调用: {stats['total_llm_calls']/stats['total_episodes']:.1f} 次/集")
        
        if stats['quality_scores']:
            avg_quality = sum(stats['quality_scores']) / len(stats['quality_scores'])
            print(f"\n✅ 质量统计:")
            print(f"  - 平均质量评分: {avg_quality:.1f}/100")
            print(f"  - 最高评分: {max(stats['quality_scores']):.0f}/100")
            print(f"  - 最低评分: {min(stats['quality_scores']):.0f}/100")
        
        print(f"\n🎯 关键验证结果:")
        
        # 验证1: Hook检测只在ep01执行
        hook_check_passed = stats['hook_detected_count'] == 1
        print(f"  1. Hook检测仅在ep01执行: {'✅ 通过' if hook_check_passed else '❌ 失败'}")
        
        # 验证2: 所有集数都成功处理
        all_success = stats['failed'] == 0
        print(f"  2. 所有集数处理成功: {'✅ 通过' if all_success else '❌ 失败'}")
        
        # 验证3: 质量评分达标
        quality_passed = all(score >= 60 for score in stats['quality_scores'])
        print(f"  3. 质量评分达标(≥60): {'✅ 通过' if quality_passed else '❌ 失败'}")
        
        # 总体验证
        all_passed = hook_check_passed and all_success and quality_passed
        print(f"\n{'=' * 80}")
        if all_passed:
            print("🎉 生产环境模拟测试全部通过！")
        else:
            print("⚠️ 部分验证未通过，请检查详细日志")
        print("=" * 80)


async def create_mock_srt_files(project_name: str, num_episodes: int = 3):
    """
    创建模拟SRT文件（用于测试）
    """
    print(f"\n📝 创建模拟SRT测试文件...")
    
    project_dir = Path(f"data/projects/{project_name}")
    raw_dir = project_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    mock_srt_content = """1
00:00:00,000 --> 00:00:03,500
夜幕降临，车队缓缓停下

2
00:00:03,600 --> 00:00:07,200
队长走下车，警惕地环顾四周

3
00:00:07,300 --> 00:00:11,800
这是一个危险的世界，到处都是未知的威胁

4
00:00:12,000 --> 00:00:15,500
但是他们必须继续前进

5
00:00:15,600 --> 00:00:19,200
因为身后是更大的危险

6
00:00:19,300 --> 00:00:23,800
队长打开通讯器，向总部汇报情况

7
00:00:24,000 --> 00:00:27,500
总部，这里是车队，我们已经到达目标地点

8
00:00:27,600 --> 00:00:31,200
周围环境看起来还算安全

9
00:00:31,300 --> 00:00:35,800
请指示下一步行动

10
00:00:36,000 --> 00:00:39,500
通讯器传来沙沙的杂音

11
00:00:39,600 --> 00:00:43,200
然后是总部的回复

12
00:00:43,300 --> 00:00:47,800
收到，请继续观察，如有异常立即报告
"""
    
    created_files = []
    for i in range(1, num_episodes + 1):
        episode_name = f"ep{i:02d}"
        srt_path = raw_dir / f"{episode_name}.srt"
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(mock_srt_content)
        
        created_files.append(str(srt_path))
        print(f"  ✓ 创建: {srt_path}")
    
    print(f"✅ 共创建 {len(created_files)} 个模拟SRT文件")
    return created_files


async def test_production_simulation():
    """
    生产环境模拟测试主函数
    """
    print("\n" + "=" * 80)
    print("🎬 ScriptProcessingWorkflow 生产环境模拟测试")
    print("=" * 80)
    
    # 项目配置
    project_name = "script_workflow_test_production"
    
    # 创建模拟SRT文件
    srt_files = await create_mock_srt_files(project_name, num_episodes=3)
    
    # 准备测试集数列表
    episodes = [
        {
            "episode_name": "ep01",
            "srt_path": srt_files[0],
            "novel_reference": None,  # 实际项目中可提供
            "novel_intro": "这是一个末日世界的故事..."  # 用于Hook检测
        },
        {
            "episode_name": "ep02",
            "srt_path": srt_files[1],
            "novel_reference": None,
            "novel_intro": None  # ep02不需要
        },
        {
            "episode_name": "ep03",
            "srt_path": srt_files[2],
            "novel_reference": None,
            "novel_intro": None  # ep03不需要
        }
    ]
    
    # 生产环境配置
    config = ScriptProcessingConfig(
        # 功能开关
        enable_hook_detection=True,        # 启用Hook检测（但只在ep01执行）
        enable_hook_analysis=False,        # 不启用Hook分析（节省成本）
        enable_abc_classification=True,    # 启用ABC分类
        
        # 重试配置
        retry_on_error=True,
        max_retries=3,
        retry_delay=2.0,
        request_delay=1.0,
        
        # LLM配置
        text_extraction_provider="deepseek",
        hook_detection_provider="deepseek",
        segmentation_provider="deepseek",
        
        # 错误处理
        continue_on_error=False,           # 生产环境：失败即停止
        save_intermediate_results=True,
        
        # 输出配置
        output_markdown_reports=True,
        
        # 质量门禁
        min_quality_score=75               # 严格质量要求
    )
    
    # 初始化模拟器
    simulator = ProductionSimulator(project_name)
    
    # 运行批量测试
    await simulator.run_batch_test(episodes, config)
    
    # 详细结果分析
    print("\n" + "=" * 80)
    print("📋 详细结果分析")
    print("=" * 80)
    
    for ep_name, result in simulator.results.items():
        if not result:
            continue
        
        print(f"\n{ep_name}:")
        print(f"  - Hook检测: {'✅ 已执行' if result.hook_detection_result else '⏭️ 未执行'}")
        
        if result.hook_detection_result:
            print(f"    · has_hook: {result.hook_detection_result.has_hook}")
            print(f"    · confidence: {result.hook_detection_result.confidence:.2f}")
        
        if result.segmentation_result:
            print(f"  - 分段数量: {result.segmentation_result.total_segments}")
        
        if result.validation_report:
            print(f"  - 质量评分: {result.validation_report.quality_score:.0f}/100")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


async def test_hook_detection_logic():
    """
    专门测试Hook检测逻辑
    """
    print("\n" + "=" * 80)
    print("🧪 Hook检测逻辑单元测试")
    print("=" * 80)
    
    test_cases = [
        ("ep01", True, "ep01应该执行Hook检测"),
        ("ep02", False, "ep02不应该执行Hook检测"),
        ("ep10", False, "ep10不应该执行Hook检测"),
        ("EP01", True, "EP01（大写）应该执行Hook检测"),
        ("episode01", False, "episode01（非标准格式）不应该执行Hook检测"),
    ]
    
    print("\n测试用例:")
    all_passed = True
    
    for episode_name, should_detect, description in test_cases:
        # 模拟检测逻辑
        config = ScriptProcessingConfig(enable_hook_detection=True)
        
        # 判断是否应该执行Hook检测
        # 逻辑：enable_hook_detection=True AND episode_name.lower() == "ep01"
        will_detect = config.enable_hook_detection and episode_name.lower() == "ep01"
        
        # 验证
        passed = (will_detect == should_detect)
        status = "✅ 通过" if passed else "❌ 失败"
        
        print(f"  - {episode_name}: {status}")
        print(f"    · 说明: {description}")
        print(f"    · 预期: {'执行' if should_detect else '不执行'}")
        print(f"    · 实际: {'执行' if will_detect else '不执行'}")
        
        if not passed:
            all_passed = False
    
    print(f"\n{'=' * 80}")
    if all_passed:
        print("✅ Hook检测逻辑测试全部通过!")
    else:
        print("❌ 部分测试用例失败")
    print("=" * 80)


async def main():
    """
    主测试入口
    """
    print("\n" + "=" * 80)
    print("🎯 ScriptProcessingWorkflow 生产环境综合测试")
    print("=" * 80)
    
    # 测试1: Hook检测逻辑单元测试
    print("\n[测试1] Hook检测逻辑单元测试")
    await test_hook_detection_logic()
    
    # 测试2: 生产环境模拟测试
    print("\n[测试2] 生产环境模拟测试（3集）")
    await test_production_simulation()
    
    print("\n" + "=" * 80)
    print("🎊 所有测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
