"""测试解析逻辑"""
import re

# 测试段落索引解析
paragraphs_pattern = r'\*\*包含段落\*\*[：:]\s*\[([^\]]+)\]'

test_cases = [
    "**包含段落**：[段落2]",
    "**包含段落**：[段落1, 段落6]",
    "**包含段落**：[3, 4]",
    "**包含段落**：[段落7]",
]

for test in test_cases:
    match = re.search(paragraphs_pattern, test)
    if match:
        para_str = match.group(1)
        print(f"原文: {test}")
        print(f"  提取: {para_str}")
        
        # 解析段落编号
        para_indices = []
        for item in para_str.split(','):
            item_stripped = item.strip()
            # 提取数字
            if '段落' in item_stripped:
                num_match = re.search(r'\d+', item_stripped)
                if num_match:
                    para_indices.append(int(num_match.group()))
            else:
                try:
                    para_indices.append(int(item_stripped))
                except ValueError:
                    print(f"    ❌ 解析失败: {item_stripped}")
        
        print(f"  结果: {para_indices}")
        print()
