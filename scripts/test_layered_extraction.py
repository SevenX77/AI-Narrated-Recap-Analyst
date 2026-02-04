#!/usr/bin/env python3
"""
测试脚本：分层信息提取
用于验证新的分层对齐方案的可行性

测试内容：
1. 从Novel第1章提取四层信息
2. 从Script前2分钟提取四层信息  
3. 对比两者的提取结果
4. 评估匹配可行性
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.deepseek_analyst import get_llm_client
from src.utils.prompt_loader import load_prompts
from src.utils.logger import logger


class LayeredExtractionTester:
    """分层信息提取测试器"""
    
    def __init__(self):
        self.client = get_llm_client()
        self.prompts = load_prompts("layered_extraction")
        
    async def extract_layer(
        self, 
        text: str, 
        layer_name: str, 
        source_type: str
    ) -> dict:
        """
        提取单层信息
        
        Args:
            text: 文本内容
            layer_name: 层名称 (world_building, game_mechanics, items, plot_events)
            source_type: 来源类型 (script, novel)
            
        Returns:
            提取结果
        """
        prompt_key = f"extract_{layer_name}"
        
        if prompt_key not in self.prompts:
            logger.error(f"Prompt not found: {prompt_key}")
            return {}
        
        system_prompt = self.prompts[prompt_key]["system"]
        user_prompt = self.prompts[prompt_key]["user"].format(
            text=text,
            source_type=source_type
        )
        
        logger.info(f"🔍 提取 {layer_name} ({source_type})...")
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            result = json.loads(content)
            logger.info(f"✅ 提取成功: {len(result)} 项")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"   LLM返回内容: {content[:200]}...")
            return []
        except Exception as e:
            logger.error(f"❌ 提取失败: {e}")
            return []
    
    async def extract_all_layers(
        self, 
        text: str, 
        source_type: str
    ) -> dict:
        """
        提取所有层信息
        
        Args:
            text: 文本内容
            source_type: 来源类型 (script, novel)
            
        Returns:
            {
                "world_building": [...],
                "game_mechanics": [...],
                "items": [...],
                "plot_events": [...]
            }
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"开始提取 {source_type} 的四层信息")
        logger.info(f"{'='*60}\n")
        
        layers = ["world_building", "game_mechanics", "items", "plot_events"]
        
        results = {}
        for layer in layers:
            results[layer] = await self.extract_layer(text, layer, source_type)
            await asyncio.sleep(1)  # 避免API rate limit
        
        logger.info(f"\n✅ {source_type} 提取完成")
        logger.info(f"   - 设定层: {len(results['world_building'])} 项")
        logger.info(f"   - 系统层: {len(results['game_mechanics'])} 项")
        logger.info(f"   - 道具层: {len(results['items'])} 项")
        logger.info(f"   - 情节层: {len(results['plot_events'])} 项")
        
        return results
    
    def compare_layers(
        self, 
        script_layers: dict, 
        novel_layers: dict
    ):
        """
        对比Script和Novel的提取结果
        
        分析：
        1. 两者提取的信息是否重合
        2. 哪些信息在位置上有差异
        3. 匹配的可行性
        """
        logger.info(f"\n{'='*60}")
        logger.info("对比分析")
        logger.info(f"{'='*60}\n")
        
        for layer_name in ["world_building", "game_mechanics", "items", "plot_events"]:
            logger.info(f"\n📊 【{layer_name}】")
            logger.info(f"   Script: {len(script_layers[layer_name])} 项")
            logger.info(f"   Novel:  {len(novel_layers[layer_name])} 项")
            
            # 显示前3项内容对比
            script_items = script_layers[layer_name][:3]
            novel_items = novel_layers[layer_name][:3]
            
            logger.info(f"\n   Script 示例:")
            for i, item in enumerate(script_items, 1):
                content = item.get('content', '???')
                logger.info(f"     {i}. {content}")
            
            logger.info(f"\n   Novel 示例:")
            for i, item in enumerate(novel_items, 1):
                content = item.get('content', '???')
                logger.info(f"     {i}. {content}")
    
    def save_results(
        self, 
        script_layers: dict, 
        novel_layers: dict, 
        output_dir: str
    ):
        """保存提取结果"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存Script结果
        script_path = os.path.join(output_dir, "script_layers.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_layers, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ 保存Script结果: {script_path}")
        
        # 保存Novel结果
        novel_path = os.path.join(output_dir, "novel_layers.json")
        with open(novel_path, 'w', encoding='utf-8') as f:
            json.dump(novel_layers, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 保存Novel结果: {novel_path}")


async def main():
    """主函数"""
    
    # 读取测试数据
    project_root = Path(__file__).parent.parent
    novel_path = project_root / "data/projects/PROJ_002/raw/novel.txt"
    script_path = project_root / "data/projects/PROJ_002/raw/ep01.srt"
    
    logger.info("="*60)
    logger.info("分层信息提取测试")
    logger.info("="*60)
    
    # 读取Novel第1章
    logger.info("\n📖 读取Novel第1章...")
    with open(novel_path, 'r', encoding='utf-8') as f:
        novel_text = f.read()
    
    # 提取第1章
    import re
    chapter_match = re.search(
        r'=== 第1章[^=]+=+\s*(.*?)\s*=== 第2章',
        novel_text,
        re.DOTALL
    )
    
    if not chapter_match:
        logger.error("❌ 未找到第1章")
        return
    
    novel_chapter1 = chapter_match.group(1).strip()
    logger.info(f"✅ 第1章长度: {len(novel_chapter1)} 字符")
    
    # 读取Script前2分钟（前350行左右）
    logger.info("\n📺 读取Script前2分钟...")
    with open(script_path, 'r', encoding='utf-8') as f:
        script_lines = f.readlines()
    
    # 提取前2分钟的内容
    script_text_parts = []
    for i in range(0, len(script_lines), 4):
        if i + 3 >= len(script_lines):
            break
        
        # SRT格式：序号、时间、文本、空行
        time_line = script_lines[i + 1].strip()
        text_line = script_lines[i + 2].strip()
        
        # 解析时间
        if '-->' in time_line:
            start_time = time_line.split('-->')[0].strip()
            # 转换为秒数
            parts = start_time.replace(',', ':').split(':')
            if len(parts) >= 3:
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_seconds = minutes * 60 + seconds
                
                # 只取前2分钟
                if total_seconds <= 120:
                    script_text_parts.append(text_line)
                else:
                    break
    
    script_text = " ".join(script_text_parts)
    logger.info(f"✅ Script前2分钟长度: {len(script_text)} 字符")
    
    # 初始化测试器
    tester = LayeredExtractionTester()
    
    # 提取Novel的四层信息
    novel_layers = await tester.extract_all_layers(novel_chapter1, "novel")
    
    # 提取Script的四层信息
    script_layers = await tester.extract_all_layers(script_text, "script")
    
    # 对比分析
    tester.compare_layers(script_layers, novel_layers)
    
    # 保存结果
    output_dir = project_root / "data/projects/PROJ_002/test_layered_extraction"
    tester.save_results(script_layers, novel_layers, str(output_dir))
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ 测试完成！")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
