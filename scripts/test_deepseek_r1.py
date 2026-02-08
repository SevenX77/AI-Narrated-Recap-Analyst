"""
测试 DeepSeek R1 (Reasoning Model) - 对比推理能力
用简化的 prompt 测试，让 R1 自己推理分段逻辑
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
import json


def extract_chapter_content(novel_file: Path, chapter_num: int):
    """提取指定章节内容"""
    with open(novel_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    chapter_pattern = r'===\s*第\s*(\d+)\s*章\s*(.*)===\s*\n'
    matches = list(re.finditer(chapter_pattern, content))
    
    if len(matches) < chapter_num:
        return None, None
    
    start_match = matches[chapter_num - 1]
    chapter_number = int(start_match.group(1))
    chapter_title = start_match.group(2).strip()
    
    start_pos = start_match.end()
    end_pos = matches[chapter_num].start() if len(matches) > chapter_num else len(content)
    chapter_content = content[start_pos:end_pos].strip()
    
    return chapter_title, chapter_content


def build_simple_prompt(chapter_content: str, chapter_title: str) -> str:
    """构建简化的 prompt - 让 R1 自己推理"""
    return f"""你是小说分析专家。请将以下章节按**叙事功能**分段，并为每段标注。

## 分段原则（核心）

1. **时间/空间转折** → 必须分段（如：从现在到"几个月前"的回忆）
2. **叙事功能转折** → 应该分段（如：从对话到背景交代）
3. **情绪连贯** → 可以合并（但不能跨越1、2）

## 关键判断

- "刺激-反应"必须在一起（如：广播-陈野听到后的反应）
- 看到时间标记词（"几个月前"、"此时"）要警惕转折
- 段落过长（>300字）时考虑是否能拆分

## 章节内容

**第1章 - {chapter_title}**

```
{chapter_content}
```

## 输出格式

请按以下JSON格式输出：

```json
{{
  "segments": [
    {{
      "segment_id": "seg_01",
      "title": "段落1：开篇钩子（广播与反应）",
      "content": "段落原文...",
      "word_count": 165,
      "reasoning": "为什么这样分段的推理过程（R1请详细说明）",
      "tags": ["故事推进", "核心设定(首次)"]
    }}
  ],
  "分段决策说明": "整体分段思路（R1请说明你的推理过程）"
}}
```

请开始分析。
"""


def main():
    """测试 R1 的推理能力"""
    print("\n" + "🧠" * 40)
    print("  DeepSeek R1 (Reasoning Model) 测试")
    print("🧠" * 40)
    print("\n📝 使用简化 Prompt，让 R1 自己推理分段逻辑\n")
    
    # 读取小说内容
    project_dir = Path(__file__).parent.parent / "data/projects/with_novel/末哥超凡公路"
    novel_file = project_dir / "raw/novel.txt"
    
    chapter_title, chapter_content = extract_chapter_content(novel_file, 1)
    
    if not chapter_content:
        print("❌ 无法提取章节内容")
        return
    
    print(f"📖 章节: 第1章 - {chapter_title}")
    print(f"📝 内容长度: {len(chapter_content)} 字符\n")
    
    # 创建输出目录
    output_dir = project_dir / "novel/functional_analysis/r1_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置 R1
    from src.core.config import config as app_config
    
    api_key = app_config.llm.api_key
    if not api_key:
        print("❌ 未找到 API KEY，请在 .env 文件中设置 DEEPSEEK_API_KEY")
        return
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    
    print(f"✅ 使用 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    print("="*80)
    print("  调用 DeepSeek R1 (deepseek-reasoner)")
    print("="*80)
    print("\n🔄 正在调用 R1... (这可能需要 30-60 秒)\n")
    
    # 构建 prompt
    prompt = build_simple_prompt(chapter_content, chapter_title)
    
    # 保存 prompt
    with open(output_dir / "r1_prompt.txt", 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    try:
        # 调用 R1
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model="deepseek-reasoner",  # R1 模型
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1.0  # R1 推荐使用 1.0
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 获取结果
        reasoning_content = response.choices[0].message.reasoning_content  # R1 的推理过程
        final_content = response.choices[0].message.content  # 最终输出
        
        print(f"✅ R1 分析完成！耗时: {duration:.1f} 秒\n")
        
        # 保存推理过程
        print("="*80)
        print("  R1 的推理过程")
        print("="*80)
        print(f"\n{reasoning_content}\n")
        
        reasoning_file = output_dir / f"r1_reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(reasoning_file, 'w', encoding='utf-8') as f:
            f.write(f"# DeepSeek R1 推理过程\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**耗时**: {duration:.1f} 秒\n\n")
            f.write("## 推理内容\n\n")
            f.write(reasoning_content)
            f.write("\n\n## 最终输出\n\n")
            f.write(final_content)
        
        print(f"💾 推理过程已保存: {reasoning_file.name}\n")
        
        # 解析最终输出
        print("="*80)
        print("  最终分段结果")
        print("="*80)
        
        # 提取 JSON
        json_text = final_content
        if "```json" in final_content:
            json_text = final_content.split("```json")[1].split("```")[0].strip()
        elif "```" in final_content:
            json_text = final_content.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(json_text)
            
            print(f"\n📊 分段数量: {len(result.get('segments', []))}")
            print(f"\n### 各段落信息\n")
            
            for i, seg in enumerate(result.get('segments', []), 1):
                print(f"**段落{i}**: {seg.get('title', 'N/A')}")
                print(f"  - 字数: {seg.get('word_count', 'N/A')}")
                print(f"  - 推理: {seg.get('reasoning', 'N/A')[:100]}...")
                print()
            
            if '分段决策说明' in result:
                print(f"### 整体分段思路\n")
                print(result['分段决策说明'])
            
            # 保存 JSON
            json_file = output_dir / f"r1_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 结果已保存: {json_file.name}")
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败: {e}")
            print(f"\n原始输出:\n{final_content[:500]}...")
            
            # 保存原始输出
            raw_file = output_dir / f"r1_raw_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"\n💾 原始输出已保存: {raw_file.name}")
        
        # 生成对比报告
        print("\n" + "="*80)
        print("  📊 关键观察点")
        print("="*80)
        print("\n请检查 R1 的推理过程，看它是否：")
        print("  1. ✅ 识别了'几个月前'是时间转折")
        print("  2. ✅ 将'广播+陈野反应'合并为一段")
        print("  3. ✅ 在时间转折处分段")
        print("  4. ✅ 平衡了情绪连贯和功能转折")
        print(f"\n📄 详细推理过程: {reasoning_file}")
        
    except Exception as e:
        print(f"❌ R1 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
