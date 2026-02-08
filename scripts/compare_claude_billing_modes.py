#!/usr/bin/env python3
"""
Claude 计费模式对比测试脚本
比较 OneChats 的次数模式和额度模式，找出最适合章节分析的计费方式
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import time
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from openai import OpenAI
import json

# 加载环境变量
load_dotenv()

# OneChats 两种计费模式的 endpoint（根据官方文档，必须加 /v1/ 后缀）
BILLING_MODES = {
    "次数模式": "https://api.onechats.top/v1/",
    "额度模式": "https://chatapi.onechats.top/v1/"
}

def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（粗略估计）"""
    # 中文：1个字符 ≈ 1.5 tokens
    # 英文：1个字符 ≈ 0.25 tokens
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars * 1.5 + other_chars * 0.25)

def create_test_cases() -> List[Dict]:
    """创建不同规模的测试用例"""
    return [
        {
            "name": "简单问答",
            "prompt": "请用一句话介绍什么是小说解说。",
            "scenario": "快速问答、简单指令",
            "estimated_input_tokens": 20,
            "estimated_output_tokens": 50,
        },
        {
            "name": "短文本分析",
            "prompt": """
请分析以下小说片段的叙事功能：

"张明推开门，屋内一片漆黑。他摸索着找到开关，灯光亮起的瞬间，他看到了桌上那封信。"

请简要分析：
1. 情节推进作用
2. 氛围营造
3. 人物塑造
""",
            "scenario": "段落级分析",
            "estimated_input_tokens": 150,
            "estimated_output_tokens": 300,
        },
        {
            "name": "中等章节分析",
            "prompt": """
请对以下小说章节进行功能段划分和分析（约1000字）：

第一章 末日降临

清晨六点，末哥从睡梦中醒来。窗外传来急促的警报声，这是全城紧急广播。

"所有市民请注意！异常气候即将来袭，请立即前往最近的避难所！重复..."

末哥快速穿上衣服，冲到窗边。天空呈现出诡异的暗红色，远处的建筑物笼罩在一层血色雾气中。街道上，人群慌乱奔跑，车辆拥堵成一片。

他的手机震动不停，屏幕上跳出无数条消息。父母、朋友、同事，所有人都在询问彼此的安危。末哥快速回复了几条信息，然后开始收拾应急物资。

食物、水、药品、手电筒...他按照多年前学过的紧急求生清单，有条不紊地打包。就在这时，一道刺眼的闪电划破天空，紧接着是震耳欲聋的雷声。

整栋建筑剧烈摇晃，末哥差点摔倒。他抓起背包，冲出房门。楼道里已经挤满了慌张的居民，电梯早已停运，所有人都在往楼下跑。

十二层楼梯，末哥用了不到五分钟就跑完了。冲出大门的瞬间，他看到了令人震惊的一幕——

天空中，一条巨大的裂缝正在缓缓张开，里面透出诡异的紫色光芒。空气中弥漫着令人窒息的压迫感。

"这是什么..."末哥喃喃自语。

人群开始失控，尖叫声、哭喊声混杂在一起。就在这时，裂缝中突然射出一道光束，直直地击中了远处的高楼。那栋三十层的大厦瞬间化为齑粉。

末哥愣在原地，大脑一片空白。这不是自然灾害，这是...末日？

请进行以下分析：
1. 划分功能段（开端、发展、高潮等）
2. 识别关键情节点
3. 分析氛围营造手法
4. 主角心理状态变化
5. 爆点设计分析
""",
            "scenario": "标准章节分析（1000字左右）",
            "estimated_input_tokens": 800,
            "estimated_output_tokens": 1000,
        },
        {
            "name": "长章节深度分析",
            "prompt": """
请对以下长章节进行详细的功能段划分和深度分析（约3000字）：

[此处应为3000字的小说章节，为简化测试，用占位文本表示]

第二章 超凡公路

末哥在废墟中艰难前行。周围的建筑物已经面目全非，到处是倒塌的墙体和破碎的玻璃。天空的裂缝还在不断扩大，紫色的光芒让整个世界笼罩在诡异的氛围中。

他不知道要去哪里，只是本能地想要离开这个危险的地方。脚步声、碎石滚落的声音、远处的爆炸声...各种声音混杂在一起，构成了末日交响曲。

突然，前方出现了一个奇怪的东西。那是一条笔直的公路，从废墟中突兀地延伸出来，一直通向远方。公路表面泛着淡淡的金光，与周围的灰暗形成鲜明对比。

末哥停下脚步，警惕地打量着这条诡异的公路。直觉告诉他，这不是普通的道路。

就在他犹豫的时候，身后传来了恐怖的咆哮声。末哥猛地回头，看到了一只巨大的怪物正从废墟中爬出来。那东西有着狰狞的面孔，全身覆盖着黑色的鳞片，眼睛闪烁着红光。

来不及多想，末哥拔腿就跑，直直地冲向那条金色公路。

当他的脚踏上公路的瞬间，一切都变了。时间仿佛静止，周围的声音全部消失。末哥感觉到一股强大的力量涌入体内，身体变得轻盈无比。

他低头看向自己的双手，掌心竟然出现了淡淡的金色纹路。这些纹路像是活的一样，缓缓流动着。

"欢迎来到超凡公路。"一个声音突然在脑海中响起。

末哥环顾四周，没有看到任何人。

"不要寻找我，我就在你的意识中。"那个声音继续说道，"这条公路是通向新世界的唯一道路。只有踏上这条路的人，才有资格在末日中生存。"

"什么意思？"末哥忍不住问道。

"你会明白的。现在，开始你的第一次试炼吧。"

话音刚落，公路前方突然出现了一扇巨大的门。门上雕刻着复杂的纹路，散发着神秘的气息。

末哥深吸一口气，迈步走向那扇门。当他推开门的瞬间，一道刺眼的白光将他吞没...

（此处省略2000字内容，实际测试时应使用完整3000字章节）

请进行全面深度分析：
1. 详细的功能段划分（至少8个段落）
2. 每个功能段的叙事功能说明
3. 关键情节点识别与转折分析
4. 氛围营造的多层次手法分析
5. 主角心理状态的细腻变化追踪
6. 世界观设定的展现方式
7. 悬念设置与爆点设计的详细分析
8. 与前一章节的衔接关系
9. 改编建议（如何适配短视频解说）
""",
            "scenario": "深度章节分析（3000字以上）",
            "estimated_input_tokens": 2500,
            "estimated_output_tokens": 2000,
        }
    ]

def test_billing_mode(mode_name: str, base_url: str, test_case: Dict) -> Dict:
    """测试特定计费模式"""
    print(f"\n{'='*60}")
    print(f"🧪 测试: {test_case['name']} | 模式: {mode_name}")
    print(f"{'='*60}")
    
    api_key = os.getenv("CLAUDE_API_KEY")
    model = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    
    if not api_key:
        return {"error": "CLAUDE_API_KEY 未设置"}
    
    try:
        # OneChats 使用 OpenAI 兼容的 API
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        print(f"📤 发送请求...")
        print(f"   场景: {test_case['scenario']}")
        print(f"   预估输入: ~{test_case['estimated_input_tokens']} tokens")
        print(f"   预估输出: ~{test_case['estimated_output_tokens']} tokens")
        
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": test_case['prompt']
            }]
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 获取实际 token 使用情况
        actual_input = response.usage.prompt_tokens
        actual_output = response.usage.completion_tokens
        
        print(f"\n✅ 请求成功!")
        print(f"   耗时: {duration:.2f} 秒")
        print(f"   实际输入: {actual_input} tokens")
        print(f"   实际输出: {actual_output} tokens")
        print(f"   总计: {actual_input + actual_output} tokens")
        
        # 响应内容预览
        response_text = response.choices[0].message.content
        preview_length = 200
        preview = response_text[:preview_length] + "..." if len(response_text) > preview_length else response_text
        print(f"\n📄 响应预览:")
        print("-" * 60)
        print(preview)
        print("-" * 60)
        
        return {
            "success": True,
            "mode": mode_name,
            "base_url": base_url,
            "test_case": test_case['name'],
            "scenario": test_case['scenario'],
            "duration": duration,
            "input_tokens": actual_input,
            "output_tokens": actual_output,
            "total_tokens": actual_input + actual_output,
            "response_length": len(response_text),
            "estimated_input": test_case['estimated_input_tokens'],
            "estimated_output": test_case['estimated_output_tokens'],
        }
        
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return {
            "success": False,
            "mode": mode_name,
            "base_url": base_url,
            "test_case": test_case['name'],
            "error": str(e)
        }

def calculate_cost_comparison(results: List[Dict]) -> Dict:
    """
    计算成本对比
    
    假设定价（需要根据实际平台更新）：
    - 次数模式: 固定每次调用成本（例如：0.1元/次）
    - 额度模式: 按 token 计费（例如：输入 $3/M, 输出 $15/M）
    """
    # 这里使用假设的定价，实际使用时需要更新为真实价格
    PRICING = {
        "次数模式": {
            "per_call": 0.10,  # 每次调用 0.1 元（假设值）
            "description": "固定每次调用成本"
        },
        "额度模式": {
            "input_per_1k": 0.003 * 7.2 / 1000,  # $3/M tokens * 7.2 CNY/USD
            "output_per_1k": 0.015 * 7.2 / 1000,  # $15/M tokens * 7.2 CNY/USD
            "description": "按 token 计费"
        }
    }
    
    comparison = {}
    
    for result in results:
        if not result.get("success"):
            continue
        
        mode = result["mode"]
        test_case = result["test_case"]
        
        if test_case not in comparison:
            comparison[test_case] = {}
        
        if mode == "次数模式":
            cost = PRICING["次数模式"]["per_call"]
        else:  # 额度模式
            input_cost = result["input_tokens"] * PRICING["额度模式"]["input_per_1k"]
            output_cost = result["output_tokens"] * PRICING["额度模式"]["output_per_1k"]
            cost = input_cost + output_cost
        
        comparison[test_case][mode] = {
            "cost_cny": cost,
            "input_tokens": result["input_tokens"],
            "output_tokens": result["output_tokens"],
            "total_tokens": result["total_tokens"],
            "duration": result["duration"]
        }
    
    return comparison

def print_cost_comparison(comparison: Dict):
    """打印成本对比报告"""
    print("\n" + "="*80)
    print("💰 成本对比分析报告")
    print("="*80)
    
    print("\n⚠️  注意：以下价格为假设值，请根据 OneChats 实际定价更新！")
    print("   假设定价：")
    print("   - 次数模式: ¥0.10/次")
    print("   - 额度模式: 输入 ¥0.0216/1K tokens, 输出 ¥0.108/1K tokens")
    
    for test_case, modes in comparison.items():
        print(f"\n{'─'*80}")
        print(f"📊 {test_case}")
        print(f"{'─'*80}")
        
        if "次数模式" in modes and "额度模式" in modes:
            count_mode = modes["次数模式"]
            quota_mode = modes["额度模式"]
            
            print(f"\n次数模式：")
            print(f"   成本: ¥{count_mode['cost_cny']:.4f}")
            print(f"   Tokens: {count_mode['total_tokens']} (输入{count_mode['input_tokens']} + 输出{count_mode['output_tokens']})")
            print(f"   耗时: {count_mode['duration']:.2f}秒")
            
            print(f"\n额度模式：")
            print(f"   成本: ¥{quota_mode['cost_cny']:.4f}")
            print(f"   Tokens: {quota_mode['total_tokens']} (输入{quota_mode['input_tokens']} + 输出{quota_mode['output_tokens']})")
            print(f"   耗时: {quota_mode['duration']:.2f}秒")
            
            # 计算差异
            cost_diff = count_mode['cost_cny'] - quota_mode['cost_cny']
            percentage = (cost_diff / quota_mode['cost_cny']) * 100 if quota_mode['cost_cny'] > 0 else 0
            
            if cost_diff > 0:
                print(f"\n💡 结论: 额度模式更优惠，节省 ¥{cost_diff:.4f} ({percentage:.1f}%)")
            elif cost_diff < 0:
                print(f"\n💡 结论: 次数模式更优惠，节省 ¥{-cost_diff:.4f} ({-percentage:.1f}%)")
            else:
                print(f"\n💡 结论: 两种模式成本相同")

def generate_recommendations(comparison: Dict):
    """生成使用建议"""
    print("\n" + "="*80)
    print("📝 使用建议")
    print("="*80)
    
    # 分析不同规模任务的最优模式
    recommendations = []
    
    for test_case, modes in comparison.items():
        if "次数模式" in modes and "额度模式" in modes:
            count_cost = modes["次数模式"]["cost_cny"]
            quota_cost = modes["额度模式"]["cost_cny"]
            total_tokens = modes["额度模式"]["total_tokens"]
            
            if count_cost < quota_cost:
                better_mode = "次数模式"
                savings = quota_cost - count_cost
            else:
                better_mode = "额度模式"
                savings = count_cost - quota_cost
            
            recommendations.append({
                "test_case": test_case,
                "better_mode": better_mode,
                "savings": savings,
                "total_tokens": total_tokens
            })
    
    # 打印建议
    print("\n🎯 按任务类型推荐：\n")
    
    for rec in recommendations:
        print(f"• {rec['test_case']} ({rec['total_tokens']} tokens)")
        print(f"  → 推荐: {rec['better_mode']} (节省 ¥{rec['savings']:.4f})")
        print()
    
    # 总结性建议
    print("="*80)
    print("\n📌 总体建议：\n")
    
    avg_tokens = sum(r['total_tokens'] for r in recommendations) / len(recommendations) if recommendations else 0
    
    if avg_tokens < 500:
        print("✅ 对于您的使用场景（章节分析），任务规模较小")
        print("   推荐: 次数模式 - 成本固定，简单易算")
    elif avg_tokens < 2000:
        print("✅ 对于您的使用场景（章节分析），任务规模中等")
        print("   推荐: 根据实际测试结果选择")
        print("   - 如果两种模式差异不大，选择次数模式更简单")
        print("   - 如果额度模式明显更优惠，选择额度模式")
    else:
        print("✅ 对于您的使用场景（章节分析），任务规模较大")
        print("   推荐: 额度模式 - 长文本任务通常更划算")
    
    print("\n💡 实际使用建议：")
    print("   1. 先用本脚本测试您的真实章节内容")
    print("   2. 对比实际成本差异")
    print("   3. 考虑任务频率（高频小任务 vs 低频大任务）")
    print("   4. 在 .env 中切换 CLAUDE_BASE_URL 即可")

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 Claude 计费模式对比测试")
    print("   OneChats 中转服务 - 次数模式 vs 额度模式")
    print("="*80)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查配置
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("\n❌ 错误: CLAUDE_API_KEY 未设置")
        print("请在 .env 文件中配置 CLAUDE_API_KEY")
        return
    
    # 获取测试用例
    test_cases = create_test_cases()
    
    print(f"\n📋 将测试 {len(test_cases)} 个用例，每个用例在两种模式下各测试一次")
    print(f"   总计 {len(test_cases) * 2} 次 API 调用")
    print("\n⏳ 开始测试...")
    
    # 执行测试
    all_results = []
    
    for test_case in test_cases:
        for mode_name, base_url in BILLING_MODES.items():
            result = test_billing_mode(mode_name, base_url, test_case)
            all_results.append(result)
            
            # 避免请求过快
            time.sleep(1)
    
    # 生成对比报告
    comparison = calculate_cost_comparison(all_results)
    print_cost_comparison(comparison)
    generate_recommendations(comparison)
    
    # 保存详细结果
    output_dir = project_root / "logs"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"claude_billing_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": datetime.now().isoformat(),
            "results": all_results,
            "comparison": comparison
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细结果已保存至: {output_file}")
    
    print("\n" + "="*80)
    print("✅ 测试完成!")
    print("="*80)
    print("\n💡 下一步:")
    print("   1. 查看上述对比报告")
    print("   2. 在 .env 中选择合适的 CLAUDE_BASE_URL")
    print("   3. 使用 python scripts/test_claude_api.py 验证配置")
    print()

if __name__ == "__main__":
    main()
