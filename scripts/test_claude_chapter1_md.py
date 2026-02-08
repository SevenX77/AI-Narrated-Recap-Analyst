#!/usr/bin/env python3
"""
使用 Claude Sonnet 4.5 Thinking 分析第一章 - 直接输出 Markdown
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


def build_prompt(chapter_content: str, chapter_title: str) -> str:
    """构建 Markdown 输出的 Prompt"""
    return f"""# 任务：小说章节功能段分析（Markdown 输出）

## 分析目标
对以下小说章节按**叙事功能**进行分段分析，并以 **Markdown 格式**输出完整分析报告。

## 章节信息
- **小说**: 末哥超凡公路
- **章节**: 第1章 {chapter_title}
- **字数**: {len(chapter_content)} 字

---

## 分析要求

### 1. 功能段划分原则
- **按叙事功能分段**，而非自然段
- **保持语义完整性**：同一功能的内容不可拆分
- **情绪连贯性**：广播+人物反应 = 一个功能段
- **典型功能段数量**: 8-12个/章

### 2. 每个功能段需标注
- **段落标题**：概括本段的叙事功能
- **原文内容**：完整引用原文
- **叙事功能标签**：故事推进/角色塑造/氛围营造/伏笔铺垫/世界观构建
- **结构标签**：开篇/高潮/转折/铺垫/收尾
- **浓缩优先级**：P0（核心）/P1（重要）/P2（可压缩）
- **浓缩建议**：保留什么/删除什么/如何简化

### 3. 章节级分析
- **章节摘要**：一句话总结
- **情节要点**：3-5个关键事件
- **核心冲突**：主要矛盾
- **伏笔线索**：埋下的悬念

---

## 输出格式示例

```markdown
# 第1章 功能段分析：{chapter_title}

## 元数据
- 章节编号: 1
- 总字数: {len(chapter_content)}
- 功能段数: [实际数量]
- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 分析模型: Claude Sonnet 4.5 Thinking

---

## 功能段详细分析

### 段落1：[段落标题]

**原文内容：**
```
[完整引用原文]
```

**叙事功能：** 故事推进 | 氛围营造 | 世界观构建(首次)

**结构位置：** 开篇钩子

**浓缩优先级：** P0（核心情节）

**浓缩建议：**
- **保留**：广播内容（核心世界观）、车队绝望氛围
- **删除**：无
- **简化方式**：直接引用关键广播内容，压缩陈野的反应描写

**字数统计：** [原文字数]

---

### 段落2：[段落标题]

...（重复上述格式）

---

## 章节整体分析

### 📝 章节摘要
[一句话概括本章]

### 🎯 情节要点
1. [关键事件1]
2. [关键事件2]
3. [关键事件3]

### ⚔️ 核心冲突
[主要矛盾]

### 🔮 伏笔与线索
1. [伏笔1]
2. [伏笔2]

### 🎭 人物发展
- **陈野**: [性格/状态变化]
- **其他角色**: [变化]

### 🌍 世界观扩展
[本章揭示的设定]

---

## 浓缩策略总结

### P0 核心段落（必须保留）
- 段落1, 段落3, 段落5...

### P1 重要段落（适度压缩）
- 段落2, 段落4...

### P2 可压缩段落（大幅简化）
- 段落6, 段落7...

### 预计浓缩比例
- 原文字数: {len(chapter_content)}
- 浓缩后: [预计字数]
- 压缩率: [百分比]
```

---

## 章节原文

{chapter_content}

---

请严格按照上述格式输出完整的 Markdown 分析报告。**不要使用 JSON 格式**，直接输出 Markdown 文本。
"""


def analyze_with_claude(chapter_content: str, chapter_title: str):
    """使用 Claude 分析章节"""
    print("\n" + "="*80)
    print("🤖 Claude Sonnet 4.5 Thinking - 第一章分析")
    print("="*80)
    
    # 检查配置
    api_key = os.getenv("CLAUDE_API_KEY")
    base_url = os.getenv("CLAUDE_BASE_URL", "https://chatapi.onechats.top/v1/")
    model = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-5-20250929")
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "8000"))
    
    if not api_key:
        print("❌ 错误: CLAUDE_API_KEY 未设置")
        return None
    
    print(f"\n📋 配置:")
    print(f"   API Key: {api_key[:20]}...{api_key[-10:]}")
    print(f"   Model: {model}")
    print(f"   Max Tokens: {max_tokens}")
    print(f"   Chapter: 第1章 {chapter_title}")
    print(f"   字数: {len(chapter_content)}")
    
    # 构建 prompt
    prompt = build_prompt(chapter_content, chapter_title)
    
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
    
    output_path = output_dir / f"第1章完整分段分析_Claude.md"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n💾 已保存:")
    print(f"   {output_path}")
    print(f"   大小: {len(result)} 字符")
    
    # 显示前几行预览
    lines = result.split('\n')
    print(f"\n📄 内容预览 (前10行):")
    print("─" * 80)
    for line in lines[:10]:
        print(line)
    print("─" * 80)
    print(f"   ... 还有 {len(lines)-10} 行")


def main():
    print("\n" + "="*80)
    print("🚀 Claude Sonnet 4.5 Thinking - 第一章功能段分析（Markdown 输出）")
    print("="*80)
    
    # 1. 读取章节
    print("\n📖 读取第一章...")
    chapter_content, chapter_title = read_chapter1()
    
    if not chapter_content:
        return
    
    print(f"   ✅ 第1章: {chapter_title}")
    print(f"   字数: {len(chapter_content)}")
    
    # 2. 分析
    result = analyze_with_claude(chapter_content, chapter_title)
    
    if not result:
        return
    
    # 3. 保存
    save_result(result, chapter_title)
    
    print("\n" + "="*80)
    print("✅ 完成！")
    print("="*80)


if __name__ == "__main__":
    main()
