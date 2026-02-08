# Hook-Body分离架构 - 快速开始指南

**版本**: V4.0  
**更新日期**: 2026-02-04

---

## 🚀 快速开始

### 使用方式1：一键运行完整流程

```python
import asyncio
from src.workflows.ingestion_workflow_v3 import IngestionWorkflowV3

async def main():
    workflow = IngestionWorkflowV3("PROJ_002")
    
    # 自动处理所有SRT文件
    result = await workflow.run()
    
    # 或指定特定集数
    result = await workflow.run(episodes=["ep01", "ep02", "ep03"])

asyncio.run(main())
```

### 使用方式2：分阶段运行（推荐用于调试）

```python
import asyncio
from src.workflows.ingestion_workflow_v3 import IngestionWorkflowV3

async def main():
    workflow = IngestionWorkflowV3("PROJ_002")
    
    # Phase 0: 预处理Novel（一次性）
    result_0 = await workflow.preprocess_novel()
    print(f"简介长度: {result_0['introduction_length']} 字符")
    print(f"总章节数: {result_0['total_chapters']}")
    
    # Phase 1: 分析Hook（仅ep01）
    result_1 = await workflow.analyze_hook("ep01")
    print(f"has_hook: {result_1['detection']['has_hook']}")
    print(f"body_start_time: {result_1['detection']['body_start_time']}")
    
    # Phase 2: 对齐Body（所有集数）
    result_2 = await workflow.align_body("ep01")
    result_3 = await workflow.align_body("ep02")

asyncio.run(main())
```

### 使用方式3：命令行测试

```bash
# 运行完整测试流程
cd /path/to/AI-Narrated\ Recap\ Analyst
python3 scripts/test_hook_body_workflow.py
```

---

## 📁 输出文件位置

```
data/projects/PROJ_002/
├── preprocessing/
│   ├── novel_introduction_clean.txt    # 纯净简介
│   └── novel_chapters_index.json       # 章节索引
│
├── hook_analysis/
│   └── ep01_hook_analysis.json         # Hook分析结果
│
└── alignment/
    ├── ep01_body_alignment.json        # Body对齐结果
    ├── ep02_body_alignment.json
    └── ...
```

---

## 🔍 查看结果

### 1. 查看Hook分析结果

```python
import json

with open('data/projects/PROJ_002/hook_analysis/ep01_hook_analysis.json', 'r') as f:
    hook_result = json.load(f)

print(f"has_hook: {hook_result['detection']['has_hook']}")
print(f"body_start_time: {hook_result['detection']['body_start_time']}")
print(f"confidence: {hook_result['detection']['confidence']}")
print(f"reasoning: {hook_result['detection']['reasoning']}")
```

### 2. 查看纯净简介

```python
with open('data/projects/PROJ_002/preprocessing/novel_introduction_clean.txt', 'r') as f:
    intro = f.read()
    print(intro)
```

### 3. 查看章节索引

```python
import json

with open('data/projects/PROJ_002/preprocessing/novel_chapters_index.json', 'r') as f:
    chapters = json.load(f)

for ch in chapters[:5]:  # 前5章
    print(f"第{ch['chapter_number']}章: {ch['chapter_title']}")
    print(f"  行号范围: {ch['start_line']}-{ch['end_line']}")
```

---

## 🛠️ 高级用法

### 单独重跑Hook分析

如果Hook检测结果不满意，可以单独重跑：

```python
workflow = IngestionWorkflowV3("PROJ_002")
result = await workflow.analyze_hook("ep01")
```

### 调整检测参数

```python
# 修改检测的最大时长（默认90秒）
detector = BodyStartDetector(client)
result = detector.detect_body_start(
    script_srt_text=srt_text,
    novel_chapters_text=novel_text,
    max_check_duration=120  # 检查前2分钟
)
```

### 自定义简介过滤规则

编辑 `src/modules/alignment/novel_preprocessor.py`:

```python
# 添加新的排除模式
EXCLUDE_PATTERNS = [
    r'^\[封面:',
    r'^Title:',
    # 添加自定义模式
    r'^阅读须知:',
    r'^版权声明:',
]
```

---

## 🐛 常见问题

### Q1: "未找到第1章标题"

**原因**: Novel的章节标题格式不匹配

**解决**:
```python
# 在 novel_preprocessor.py 中添加新的章节匹配模式
CHAPTER_PATTERNS = [
    r'^===?\s*第[0-9零一二三四五六七八九十百千]+章\s+.*?===?$',
    r'^第[0-9零一二三四五六七八九十百千]+章[：:\s]',
    r'^Chapter\s+\d+',
    # 添加新模式
    r'^\d+\.\s+',  # 如: "1. 第一章"
]
```

### Q2: Hook检测置信度低

**原因**: Script的叙事结构不明显

**建议**:
- 查看 `reasoning` 字段了解原因
- 如果确实没有Hook，`has_hook=false` 是正确的
- 可以手动指定 `body_start_time`（修改输出JSON）

### Q3: 分层提取节点数为0

**原因**: LLM返回格式与代码期望不匹配（已知问题）

**状态**: 待优化（不影响核心架构）

**临时方案**: 暂时跳过分层提取，直接使用Hook的原始文本

---

## 📊 性能基准

基于 PROJ_002 测试：

| Phase | 耗时 | LLM调用次数 |
|-------|------|------------|
| Phase 0 | ~0.1秒 | 0 |
| Phase 1 | ~10秒 | 1（Body检测） + 8（分层提取，可选） |
| Phase 2 | 待实现 | - |

**成本估算**（按DeepSeek定价）:
- Phase 1: ~$0.001/集（仅Body检测）
- Phase 1完整: ~$0.01/集（含分层提取）

---

## 🔗 相关文档

- [架构设计文档](./architecture/LAYERED_ALIGNMENT_DESIGN.md)
- [实施总结报告](./maintenance/HOOK_BODY_SEPARATION_IMPLEMENTATION.md)
- [开发规范](./DEV_STANDARDS.md)

---

## 💡 最佳实践

1. **首次运行新项目**:
   ```python
   # Step 1: 先运行Phase 0
   await workflow.preprocess_novel()
   
   # Step 2: 查看简介和章节索引是否正确
   # 如有问题，调整EXCLUDE_PATTERNS
   
   # Step 3: 运行Phase 1
   await workflow.analyze_hook("ep01")
   
   # Step 4: 查看Hook分析结果
   # 确认body_start_time是否合理
   
   # Step 5: 运行Phase 2
   await workflow.align_body("ep01")
   ```

2. **批量处理多集**:
   ```python
   # 推荐：一次性运行全部
   await workflow.run()  # 自动检测所有SRT文件
   ```

3. **调试模式**:
   ```python
   # 分阶段运行，便于定位问题
   # 每个Phase的输出文件都可以单独查看
   ```

---

**更新日期**: 2026-02-04  
**适用版本**: IngestionWorkflowV3 (V4.0架构)
