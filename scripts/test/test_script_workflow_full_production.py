"""
完整生产环境测试：ScriptProcessingWorkflow

使用真实SRT数据（末哥超凡公路）完整测试workflow：
1. 从分析资料/目录导入原始SRT
2. 处理ep01-ep03（验证Hook检测只在ep01执行）
3. 生成完整的分段结果
4. 验证Hook分离效果

Author: AI-Narrated Recap Analyst Team
Created: 2026-02-10
"""

import asyncio
import os
import sys
from pathlib import Path
import time
from typing import Dict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.script_processing_workflow import ScriptProcessingWorkflow
from src.core.schemas_script import ScriptProcessingConfig, ScriptProcessingResult


async def test_full_production_workflow():
    """
    完整生产环境测试
    """
    print("=" * 80)
    print("🎬 ScriptProcessingWorkflow 完整生产环境测试")
    print("=" * 80)
    print("使用真实数据: 末哥超凡公路")
    print("=" * 80)
    
    # ============================================================
    # 配置
    # ============================================================
    
    # 原始SRT文件位置（分析资料目录）
    source_dir = "分析资料/有原小说/01_末哥超凡公路/srt"
    
    # 测试集数
    episodes_to_test = ["ep01", "ep02", "ep03"]
    
    # 检查文件是否存在
    print(f"\n📋 检查原始SRT文件:")
    available_episodes = []
    for ep in episodes_to_test:
        srt_path = f"{source_dir}/{ep}.srt"
        if os.path.exists(srt_path):
            file_size = os.path.getsize(srt_path)
            print(f"  ✓ {ep}.srt - {file_size/1024:.1f} KB")
            available_episodes.append(ep)
        else:
            print(f"  ✗ {ep}.srt - 未找到")
    
    if not available_episodes:
        print("\n❌ 没有找到可用的SRT文件")
        return
    
    print(f"\n✅ 找到 {len(available_episodes)} 个可用的SRT文件")
    
    # 项目名称
    project_name = "末哥超凡公路_script_test"
    
    # Novel简介（用于Hook检测）
    novel_intro = """
诡异末日降临，城市不再属于人类。
热武器失效，诡异无法被杀死。
能活下来的人只能依靠序列超凡，不断迁徙。
    """.strip()
    
    # Workflow配置
    config = ScriptProcessingConfig(
        # 功能开关
        enable_hook_detection=True,        # 启用Hook检测（只在ep01执行）
        enable_hook_analysis=False,        # 不启用Hook分析（节省成本）
        enable_abc_classification=True,    # 启用ABC分类
        
        # 重试配置
        retry_on_error=True,
        max_retries=3,
        retry_delay=2.0,
        request_delay=1.5,  # 稍微慢一点，避免API限流
        
        # LLM配置
        text_extraction_provider="deepseek",
        hook_detection_provider="deepseek",
        segmentation_provider="deepseek",
        
        # 错误处理
        continue_on_error=False,
        save_intermediate_results=True,
        
        # 输出配置
        output_markdown_reports=True,
        
        # 质量门禁
        min_quality_score=75
    )
    
    # ============================================================
    # 执行Workflow
    # ============================================================
    
    print(f"\n配置信息:")
    print(f"  - 项目名称: {project_name}")
    print(f"  - 集数数量: {len(available_episodes)}")
    print(f"  - Hook检测: {config.enable_hook_detection}")
    print(f"  - ABC分类: {config.enable_abc_classification}")
    print(f"  - 质量阈值: {config.min_quality_score}")
    
    # 初始化workflow
    workflow = ScriptProcessingWorkflow()
    
    # 存储结果
    results: Dict[str, ScriptProcessingResult] = {}
    
    # 统计信息
    total_start_time = time.time()
    
    # 逐个处理集数
    for ep in available_episodes:
        print(f"\n{'=' * 80}")
        print(f"📺 开始处理: {ep}")
        print(f"{'=' * 80}")
        
        # 原始SRT路径
        source_srt_path = f"{source_dir}/{ep}.srt"
        
        try:
            # 执行workflow
            result = await workflow.run(
                srt_path=source_srt_path,
                project_name=project_name,
                episode_name=ep,
                config=config,
                novel_intro=novel_intro if ep == "ep01" else None  # 只给ep01提供简介
            )
            
            results[ep] = result
            
            # 显示处理结果
            print(f"\n📊 {ep} 处理完成:")
            print(f"  - 状态: {'✅ 成功' if result.success else '❌ 失败'}")
            print(f"  - 总耗时: {result.processing_time:.1f} 秒")
            print(f"  - 总成本: ${result.total_cost:.4f} USD")
            print(f"  - LLM调用: {result.llm_calls_count} 次")
            
            # Phase 1: 导入结果
            if result.import_result:
                print(f"\n  📥 Phase 1: SRT导入")
                print(f"    - 原始路径: {result.import_result.original_path}")
                print(f"    - 保存路径: {result.import_result.saved_path}")
                print(f"    - 条目数量: {result.import_result.entry_count}")
                print(f"    - 总时长: {result.import_result.total_duration}")
                print(f"    - 文件大小: {result.import_result.file_size/1024:.1f} KB")
            
            # Phase 2: 文本提取
            if result.extraction_result:
                print(f"\n  🔧 Phase 2: 文本提取")
                print(f"    - 原始字符: {result.extraction_result.original_chars}")
                print(f"    - 处理后字符: {result.extraction_result.processed_chars}")
                print(f"    - 处理模式: {result.extraction_result.processing_mode}")
                print(f"    - 耗时: {result.extraction_result.processing_time:.1f} 秒")
            
            # Phase 3: Hook检测
            if result.hook_detection_result:
                print(f"\n  🎣 Phase 3: Hook检测")
                print(f"    - 状态: ✅ 已执行")
                print(f"    - 是否有Hook: {result.hook_detection_result.has_hook}")
                print(f"    - 置信度: {result.hook_detection_result.confidence:.2f}")
                
                if result.hook_detection_result.has_hook:
                    print(f"    - Hook结束: {result.hook_detection_result.hook_end_time}")
                    print(f"    - Body起点: {result.hook_detection_result.body_start_time}")
                    print(f"    - Hook段落: {len(result.hook_detection_result.hook_segment_indices)} 个")
                    print(f"    - Body段落: {len(result.hook_detection_result.body_segment_indices)} 个")
                    print(f"    - 判断理由: {result.hook_detection_result.reasoning[:80]}...")
            else:
                print(f"\n  🎣 Phase 3: Hook检测")
                print(f"    - 状态: ⏭️ 未执行（{ep}不是ep01）")
            
            # Phase 5: 脚本分段
            if result.segmentation_result:
                print(f"\n  ✂️ Phase 5: 脚本分段")
                print(f"    - 总段落数: {result.segmentation_result.total_segments}")
                print(f"    - 平均句子数: {result.segmentation_result.avg_sentence_count:.1f}")
                
                # ABC分布
                category_counts = {}
                for seg in result.segmentation_result.segments:
                    cat = seg.category or "Unknown"
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                print(f"    - ABC分布: {category_counts}")
                
                # 显示前3个段落
                print(f"\n    前3个段落:")
                for i, seg in enumerate(result.segmentation_result.segments[:3], 1):
                    print(f"      {i}. [{seg.start_time}-{seg.end_time}] [{seg.category}]")
                    content_preview = seg.content[:60].replace('\n', ' ')
                    print(f"         {content_preview}...")
            
            # Phase 6: 质量验证
            if result.validation_report:
                print(f"\n  ✅ Phase 6: 质量验证")
                print(f"    - 质量评分: {result.validation_report.quality_score:.0f}/100")
                print(f"    - 是否通过: {result.validation_report.is_valid}")
                
                if result.validation_report.issues:
                    print(f"    - 问题数量: {len(result.validation_report.issues)}")
                    if result.validation_report.issues:
                        print(f"    - 首个问题: {result.validation_report.issues[0].description[:60]}...")
            
            # 查看生成的Markdown文件
            md_path = f"data/projects/{project_name}/script/{ep}.md"
            if os.path.exists(md_path):
                print(f"\n  📄 生成文件: {md_path}")
                with open(md_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"    - 文件行数: {len(lines)}")
                print(f"    - 前5行预览:")
                for line in lines[:5]:
                    print(f"      {line.rstrip()}")
        
        except Exception as e:
            print(f"\n❌ {ep} 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # ============================================================
    # 总结报告
    # ============================================================
    
    total_time = time.time() - total_start_time
    
    print(f"\n{'=' * 80}")
    print("📈 完整测试总结")
    print("=" * 80)
    
    # 统计
    successful = sum(1 for r in results.values() if r and r.success)
    failed = sum(1 for r in results.values() if not r or not r.success)
    
    hook_detected = sum(1 for r in results.values() if r and r.hook_detection_result)
    has_hook = sum(1 for r in results.values() if r and r.hook_detection_result and r.hook_detection_result.has_hook)
    
    total_cost = sum(r.total_cost for r in results.values() if r)
    total_llm_calls = sum(r.llm_calls_count for r in results.values() if r)
    
    print(f"\n📊 处理统计:")
    print(f"  - 处理集数: {len(results)}")
    print(f"  - 成功: {successful} ✅")
    print(f"  - 失败: {failed} ❌")
    print(f"  - 成功率: {successful/len(results)*100:.1f}%")
    
    print(f"\n🎣 Hook检测验证:")
    print(f"  - Hook检测执行次数: {hook_detected}")
    print(f"  - 预期执行次数: 1（仅ep01）")
    if hook_detected == 1:
        print(f"  - ✅ 验证通过: Hook检测仅在ep01执行")
    else:
        print(f"  - ❌ 验证失败: Hook检测执行次数不符合预期")
    
    if has_hook > 0:
        print(f"  - 实际检测到Hook: {has_hook} 个集数")
    
    print(f"\n💰 成本与性能:")
    print(f"  - 总成本: ${total_cost:.4f} USD")
    print(f"  - 平均成本: ${total_cost/len(results):.4f} USD/集")
    print(f"  - 总耗时: {total_time:.1f} 秒")
    print(f"  - 总LLM调用: {total_llm_calls} 次")
    
    # 质量统计
    quality_scores = [
        r.validation_report.quality_score 
        for r in results.values() 
        if r and r.validation_report
    ]
    if quality_scores:
        print(f"\n✅ 质量统计:")
        print(f"  - 平均质量评分: {sum(quality_scores)/len(quality_scores):.1f}/100")
        print(f"  - 最高评分: {max(quality_scores):.0f}/100")
        print(f"  - 最低评分: {min(quality_scores):.0f}/100")
    
    # 项目目录
    project_dir = f"data/projects/{project_name}"
    
    # 生成的文件
    print(f"\n📁 生成的项目文件:")
    
    print(f"\n  原始SRT（导入后）:")
    for ep in results.keys():
        path = f"{project_dir}/raw/{ep}.srt"
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"    ✓ {path} ({size/1024:.1f} KB)")
    
    print(f"\n  分段结果（Markdown）:")
    for ep in results.keys():
        path = f"{project_dir}/script/{ep}.md"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            print(f"    ✓ {path} ({lines} 行)")
    
    # 详细结果分析
    print(f"\n{'=' * 80}")
    print("📋 详细结果对比")
    print("=" * 80)
    
    for ep, result in results.items():
        if not result:
            continue
        
        print(f"\n{ep}:")
        
        # Hook检测
        if result.hook_detection_result:
            print(f"  🎣 Hook检测: ✅ 已执行")
            print(f"     - 是否有Hook: {result.hook_detection_result.has_hook}")
            print(f"     - 置信度: {result.hook_detection_result.confidence:.2f}")
            if result.hook_detection_result.has_hook:
                print(f"     - Hook时长: 0 → {result.hook_detection_result.hook_end_time}")
        else:
            print(f"  🎣 Hook检测: ⏭️ 未执行")
        
        # 分段统计
        if result.segmentation_result:
            print(f"  ✂️ 分段: {result.segmentation_result.total_segments} 段")
            
            category_counts = {}
            for seg in result.segmentation_result.segments:
                cat = seg.category or "Unknown"
                category_counts[cat] = category_counts.get(cat, 0) + 1
            print(f"     - ABC分布: {category_counts}")
        
        # 质量
        if result.validation_report:
            score = result.validation_report.quality_score
            status = "✅" if score >= 85 else ("⚠️" if score >= 70 else "❌")
            print(f"  {status} 质量: {score:.0f}/100")
        
        # 成本
        print(f"  💰 成本: ${result.total_cost:.4f} ({result.llm_calls_count} 次LLM)")
    
    # 最终验证
    print(f"\n{'=' * 80}")
    print("🎯 核心验证结果")
    print("=" * 80)
    
    checks = {
        "Hook检测仅在ep01执行": hook_detected == 1,
        "所有集数处理成功": failed == 0,
        "质量评分达标": all(s >= 70 for s in quality_scores) if quality_scores else False
    }
    
    for check_name, passed in checks.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {check_name}: {status}")
    
    if all(checks.values()):
        print(f"\n{'=' * 80}")
        print("🎉 完整生产环境测试全部通过！")
        print("=" * 80)
    else:
        print(f"\n{'=' * 80}")
        print("⚠️ 部分验证未通过")
        print("=" * 80)
    
    return results


async def main():
    """
    主函数
    """
    results = await test_full_production_workflow()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    
    # 提示查看文件
    if results:
        project_name = "末哥超凡公路_script_test"
        print(f"\n📂 查看生成的文件:")
        print(f"  - 原始SRT: data/projects/{project_name}/raw/")
        print(f"  - 分段结果: data/projects/{project_name}/script/")
        
        # 显示ep01的特殊之处
        if "ep01" in results and results["ep01"].hook_detection_result:
            print(f"\n🎣 Hook检测结果（仅ep01）:")
            hook_res = results["ep01"].hook_detection_result
            if hook_res.has_hook:
                print(f"  ✅ 检测到Hook!")
                print(f"     查看分离效果: cat data/projects/{project_name}/script/ep01.md")
            else:
                print(f"  ⏭️ 未检测到Hook（判断为无Hook）")
                print(f"     查看标准分段: cat data/projects/{project_name}/script/ep01.md")


if __name__ == "__main__":
    asyncio.run(main())
