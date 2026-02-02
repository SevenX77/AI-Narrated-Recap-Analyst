import sys
import os
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine
from src.utils.logger import logger, op_logger

def debug_hook_detection():
    load_dotenv()
    
    # 1. Prepare Test Data
    # Mock Novel Start (Chapter 1)
    novel_start_context = """
【第1章】:
- [深夜] 在出租屋 陈野 缩在 出租屋
- [深夜] 在出租屋 陈野 攥着 军用收音机
- [深夜] 在收音机 广播 [电流声] 传来了 上沪沦陷的消息
- [深夜] 在出租屋 陈野 感到 浑身冰凉
- [三个月前] 全球诡异 爆发 人类文明毁于一旦
- [三个月前] 在逃难车队 陈野 [骑着自行车] 加入了 逃难车队
- [三个月前] 车队 制定了 两条铁律
- 在路边 陈野 停下 在路边
- 在路边 陈野 [用露营锅] 煮了 泡面
- 在路边 香味 引来了 幸存者贪婪的目光
- 在路边 陈野 摸了摸 腰间的手弩
    """
    
    # Mock Script Start (With Hook)
    # 00:00-00:25 is Hook (Future Climax/Setting)
    # 00:30 starts Body (Linear with novel)
    script_context = """
【时间 00:00】:
- 陈野 觉醒 升级万物的系统
【时间 00:05】:
- 全球 沦为 诡异乐园
【时间 00:10】:
- 有人 觉醒了 火焰序列
【时间 00:15】:
- 有人 觉醒了 寒冰序列
【时间 00:20】:
- 陈野 升级 自行车成核动力战车
【时间 00:25】:
- 上沪 沦陷 防线崩溃
【时间 00:30】:
- 我 从江城逃了出来
【时间 00:35】:
- 我 [骑着自行车] 加入了 幸存者车队
【时间 00:40】:
- 车队 制定了 铁律
    """
    
    print("\n>>> Testing Hook Detection Logic...")
    print("-" * 50)
    
    # 2. Initialize Engine
    from src.agents.deepseek_analyst import get_llm_client
    client = get_llm_client()
    engine = DeepSeekAlignmentEngine(client=client)
    
    # 3. Run Detection
    hook_info = engine._detect_hook_boundary(script_context, novel_start_context)
    
    # 4. Output Results
    print(f"Has Hook: {hook_info.get('has_hook')}")
    print(f"Body Start Time: {hook_info.get('body_start_time')}")
    print(f"Hook Summary: {hook_info.get('hook_summary')}")
    print(f"Reasoning: {hook_info.get('reason')}")
    print("-" * 50)
    
    # 5. Log Operation (Simulating the requirement)
    op_logger.log_operation(
        project_id="DEBUG_TEST",
        action="Debug Hook Detection",
        output_files=["console_output"],
        details=f"Detected Body Start at {hook_info.get('body_start_time')}"
    )

if __name__ == "__main__":
    debug_hook_detection()
