# SRT字幕处理快速入门

## 快速开始

### 1. 单独处理SRT文件

```python
from pathlib import Path
from src.tools.srt_processor import SrtScriptProcessor

# 创建处理器
processor = SrtScriptProcessor(use_llm=True)

# 有小说参考模式
with open("novel/chpt_0000.txt", "r", encoding="utf-8") as f:
    novel_reference = f.read()

report = processor.execute(
    srt_file_path=Path("raw/ep01.srt"),
    output_dir=Path("script/"),
    novel_reference=novel_reference,
    episode_name="ep01"
)

# 无小说参考模式
report = processor.execute(
    srt_file_path=Path("raw/ep01.srt"),
    output_dir=Path("script/"),
    novel_reference=None,  # 关键：无参考
    episode_name="ep01"
)

print(f"处理完成！输出文件: {report['output_file']}")
```

### 2. 通过迁移工作流批量处理

```bash
# 运行迁移脚本（会自动处理所有SRT文件）
python scripts/run_migration.py
```

### 3. 测试SRT处理功能

```bash
# 运行测试脚本
python scripts/test_srt_processing.py
```

## 输出说明

### 处理后的脚本文件

**位置**: `data/projects/{category}/{project_name}/script/ep01.txt`

**格式**: 自然段落，段间双换行

```
只因我出生时，一身红绿胎记将母妃吓晕。而在皇室，非龙凤胎的双生子被视为不祥。

于是原本能留下的我，被母妃点名要送走。走之前，皇帝特意见了我一面。

...
```

### 处理报告

**位置**: `data/projects/{category}/{project_name}/script/ep01_processing_report.json`

**内容示例**:
```json
{
  "episode": "ep01",
  "processing_mode": "without_novel",
  "stats": {
    "original_chars": 3908,
    "processed_chars": 3887,
    "paragraphs": 14,
    "srt_entries": 358,
    "processing_time_seconds": 102.39
  },
  "entity_standardization": {
    "locations": {
      "上沪": {
        "variants": ["上沪", "上户", "上"],
        "standard_form": "上沪",
        "reasoning": "指代上海，沪是上海简称"
      }
    }
  }
}
```

## 两种处理模式对比

| 特性 | 有小说参考 | 无小说参考 |
|------|-----------|-----------|
| **实体来源** | 从小说提取 | 从字幕自身识别 |
| **名称对齐** | 对齐到小说标准 | 智能推断标准形式 |
| **适用场景** | with_novel项目 | without_novel项目 |
| **处理速度** | 较快（~80s/集） | 稍慢（~100s/集） |
| **准确性** | 高（有参考） | 高（智能推断） |

## 常见问题

### Q1: 如何调整段落长度？

```python
processor = SrtScriptProcessor(
    use_llm=True,
    min_paragraph_length=50,   # 最小段落长度
    max_paragraph_length=300   # 最大段落长度
)
```

### Q2: LLM不可用时会怎样？

系统会自动降级到基于规则的处理：
- 简单标点添加
- 基本句子合并
- 不会完全失败

### Q3: 如何查看实体标准化详情？

查看处理报告中的`entity_standardization`字段，包含：
- 识别的所有实体
- 每个实体的变体列表
- 选择标准形式的推理依据

### Q4: 处理速度慢怎么办？

当前瓶颈是LLM API调用。优化建议：
1. 使用更快的模型
2. 批量处理多个集数
3. 缓存实体标准化结果

## 配置说明

### Prompt配置

**有小说参考**: `src/prompts/srt_script_processing_with_novel.yaml`
**无小说参考**: `src/prompts/srt_script_processing_without_novel.yaml`

可调整参数：
- `model`: LLM模型名称（默认: deepseek-chat）
- `temperature`: 温度参数（默认: 0.2）
- `max_tokens`: 最大token数（默认: 3000-4000）

### API配置

在`.env`文件中配置：
```
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

## 最佳实践

1. **先测试再批量**: 使用测试脚本验证效果后再批量处理
2. **检查报告**: 处理后查看报告，确认实体标准化是否合理
3. **人工审核**: 对关键集数进行人工审核，确保质量
4. **保留原文件**: 原始SRT文件保存在`raw/`目录，便于重新处理

## 相关文档

- **设计文档**: `docs/architecture/SRT_PROCESSING_DESIGN.md`
- **实现报告**: `docs/maintenance/SRT_PROCESSING_IMPLEMENTATION.md`
- **架构文档**: `docs/architecture/logic_flows.md`

---

**更新时间**: 2026-02-05  
**版本**: v1.0
