#!/usr/bin/env python3
"""
使用 Claude 按照 NOVEL_SEGMENTATION_METHODOLOGY.md 严格格式分析第一章
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
load_dotenv()


def read_methodology():
    """读取方法论文档"""
    methodology_path = project_root / "docs/NOVEL_SEGMENTATION_METHODOLOGY.md"
    with open(methodology_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_chapter1():
    """读取第一章内容"""
    novel_path = project_root / "data/projects/with_novel/末哥超凡公路/raw/novel.txt"
    
    if not novel_path.exists():
        print(f"❌ 找不到小说文件: {novel_path}")
        return None, None
    
    with open(novel_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取章节
    chapter_pattern = re.compile(r'第(\d+|一|二|三|四|五|六|七|八|九|十)章[：:\s]*([^\n]+)')
    chapters = list(chapter_pattern.finditer(content))
    
    if len(chapters) < 1:
        print("❌ 未找到章节")
        return None, None
    
    # 第一章
    chapter1_start = chapters[0].start()
    chapter1_end = chapters[1].start() if len(chapters) > 1 else len(content)
    chapter1_content = content[chapter1_start:chapter1_end].strip()
    chapter_title = chapters[0].group(2).strip()
    
    return chapter1_content, chapter_title


def build_methodology_prompt(chapter_content: str, chapter_title: str, methodology: str) -> str:
    """构建严格遵循方法论的 Prompt"""
    return f"""# 任务：按照《小说叙事分段分析方法论》分析小说章节

## 方法论文档

{methodology}

---

## 分析任务

请严格按照上述方法论，对以下章节进行完整的功能段分析。

**章节信息**：
- 小说：末哥超凡公路
- 章节：第1章 {chapter_title}
- 字数：{len(chapter_content)} 字

**输出要求**：
1. 严格使用方法论定义的六个维度标签：
   - [叙事功能]
   - [叙事结构]
   - [角色与关系]
   - [浓缩优先级]
   - [浓缩建议]
   - [时空]

2. 使用方法论定义的标签格式：
   - 列表形式，不要用 | 分隔
   - 保留 [首次信息] 标注
   - 保留 [重复强调x次] 标注
   - 保留子标签格式（如 `[人物登场：角色名]`）

3. 输出格式示例：
```markdown
## 段落1：[段落标题]

```
[原文内容]
```

**[叙事功能]**
- 故事推进
- 核心故事设定（首次）
- 关键信息

**[叙事结构]**
- 钩子-悬念制造
- 伏笔
- 重复强调x3："不要掉队"

**[角色与关系]**
- 人物登场：陈野
- 人物塑造：主角 - 果断务实

**[浓缩优先级]**
- P0-骨架：[内容]
- P1-血肉：[内容]
- P2-皮肤：[内容]
- 首次信息：[标注]

**[浓缩建议]**
保留：[核心内容概括]
删除：[可删减的细节]

**[时空]**
- 地点：[地点]
- 时间：[时间]
```

4. 在所有功能段分析后，添加章节整体分析：
   - 核心功能统计（表格）
   - 优先级分布
   - 时空轨迹
   - 情绪曲线
   - 结构特点
   - 浓缩建议（500字版本）

---

## 章节原文

{chapter_content}

---

**请严格按照方法论格式输出分析结果。**
"""


def analyze_with_claude(chapter_content: str, chapter_title: str, methodology: str):
    """使用 Claude 分析章节"""
    print("\n" + "="*80)
    print("🤖 Claude - 严格方法论格式分析")
    print("="*80)
    
    # 检查配置
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL", "https://chatapi.onechats.ai/v1/")
    model = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "8000"))
    
    if not api_key:
        print("❌ 错误: CLAUDE_API_KEY 未设置")
        return None
    
    print(f"\n📋 配置:")
    print(f"   Model: {model}")
    print(f"   Max Tokens: {max_tokens}")
    print(f"   Chapter: 第1章 {chapter_title}")
    print(f"   字数: {len(chapter_content)}")
    
    # 构建 prompt
    prompt = build_methodology_prompt(chapter_content, chapter_title, methodology)
    
    print(f"\n🧠 开始分析...")
    print(f"   Prompt 长度: {len(prompt)} 字符")
    print(f"   预计输入 tokens: ~{len(prompt)//4}")
    
    try:
        # 调用 Claude
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        start_time = datetime.now()
        
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = response.choices[0].message.content
        
        # 统计
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        print(f"\n✅ 分析完成!")
        print(f"   耗时: {duration:.2f} 秒")
        print(f"   输入 tokens: {input_tokens}")
        print(f"   输出 tokens: {output_tokens}")
        print(f"   总计 tokens: {total_tokens}")
        print(f"   输出长度: {len(result)} 字符")
        print(f"   生成速度: {output_tokens/duration:.1f} tokens/秒")
        
        # 费用估算
        input_cost = (input_tokens / 1_000_000) * 3
        output_cost = (output_tokens / 1_000_000) * 15
        total_cost = input_cost + output_cost
        
        print(f"\n💰 费用:")
        print(f"   本次: ${total_cost:.4f} (≈ ¥{total_cost*7.2:.2f})")
        print(f"   预计10章: ${total_cost*10:.2f} (≈ ¥{total_cost*10*7.2:.1f})")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_result(result: str, chapter_title: str):
    """保存分析结果"""
    output_dir = project_root / "data/projects/with_novel/末哥超凡公路/novel"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_path = output_dir / f"第1章完整分段分析_Claude_方法论格式.md"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n💾 已保存:")
    print(f"   {output_path}")
    print(f"   大小: {len(result)} 字符")


def main():
    print("\n" + "="*80)
    print("🚀 Claude - 严格按照 NOVEL_SEGMENTATION_METHODOLOGY.md 分析")
    print("="*80)
    
    # 1. 读取方法论
    print("\n📖 读取方法论...")
    methodology = read_methodology()
    print(f"   ✅ 方法论文档: {len(methodology)} 字符")
    
    # 2. 读取章节
    print("\n📖 读取第一章...")
    chapter_content, chapter_title = read_chapter1()
    
    if not chapter_content:
        return
    
    print(f"   ✅ 第1章: {chapter_title}")
    print(f"   字数: {len(chapter_content)}")
    
    # 3. 分析
    result = analyze_with_claude(chapter_content, chapter_title, methodology)
    
    if not result:
        return
    
    # 4. 保存
    save_result(result, chapter_title)
    
    print("\n" + "="*80)
    print("✅ 完成！")
    print("="*80)
    print("\n📝 下一步：")
    print("   1. 对比分析结果与手工分析")
    print("   2. 验证是否严格遵循方法论格式")
    print("   3. 如果格式正确，可用于批量分析2-10章")


if __name__ == "__main__":
    main()
