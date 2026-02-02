import os
import json
from dotenv import load_dotenv
from src.agents.deepseek_writer import DeepSeekWriter
from src.agents.analyst import SceneAnalysis, Character, NarrativeBeat

load_dotenv()

def get_llm_client():
    from openai import OpenAI
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url)

def test_writer():
    print("正在初始化 Writer Agent...")
    client = get_llm_client()
    agent = DeepSeekWriter(client)
    
    # Mock Analysis Data (simulating the output of AnalystAgent)
    mock_analysis = SceneAnalysis(
        summary="陈野在末日初期觉醒了万物升级系统，他将自己的破旧自行车升级成了全地形三轮车，引发了周围幸存者的震惊和嫉妒。",
        scene_type="生存/升级",
        characters=[
            Character(name="陈野", role="主角", status="冷静/暗爽"),
            Character(name="强子", role="反派打手", status="贪婪/忌惮"),
            Character(name="女人", role="配角", status="势利")
        ],
        beats=[
            NarrativeBeat(event_type="Upgrade", description="陈野花费杀戮点将自行车升级为三轮车", intensity=8),
            NarrativeBeat(event_type="Conflict", description="女人想坐车被拒，怂恿强子抢车", intensity=6),
            NarrativeBeat(event_type="Twist", description="强子看到陈野手中的手弩，不敢轻举妄动", intensity=7)
        ],
        potential_hooks=["生锈的自行车变成了装甲战车", "末日里别人都在逃命，我却在升级装备"],
        narrative_pattern="主角获得金手指 -> 展示能力 -> 震惊路人 -> 解决潜在冲突",
        flashback_candidate="生锈的自行车在我手中升级为装甲战车",
        protagonist_name="陈野"
    )
    
    print("正在生成解说稿...")
    script = agent.generate_script(mock_analysis, style="first_person")
    
    print("\n" + "="*50)
    print(f"标题: {script.title}")
    print(f"策略: {script.narrative_strategy}")
    print(f"总时长: {script.total_duration}秒")
    print("="*50)
    
    for i, seg in enumerate(script.segments):
        print(f"[{i+1}] ({seg.duration}s) {seg.text}")
        print(f"    画面: {seg.visual_cue}")
        print("-" * 30)

if __name__ == "__main__":
    test_writer()
