# Prompts模块文档

Prompts模块管理所有LLM的Prompt配置，采用YAML格式统一管理。

## 📦 Prompts概述

### 代码位置
```
src/prompts/
├── writer.yaml                          # Writer代理prompts
├── rule_extraction.yaml                 # 规则提取prompts
├── rule_validation.yaml                 # 规则验证prompts
├── novel_segmentation.yaml              # 小说分段prompts
├── novel_chapter_functional_analysis.yaml
├── srt_script_processing_with_novel.yaml
├── srt_script_processing_without_novel.yaml
└── ... (共16个yaml文件)
```

## 🎯 Prompt管理原则

### 1. YAML格式
所有Prompt使用YAML格式存储，便于版本控制和diff

### 2. 分类管理
按功能模块分类：
- Writer相关
- Training相关
- 素材处理相关
- 分析对齐相关

### 3. 版本控制
- 使用Git跟踪Prompt变更
- 重大变更记录在CHANGELOG
- 保留历史版本用于回滚

### 4. 提取硬编码
- ❌ 禁止在代码中硬编码Prompt
- ✅ 所有Prompt统一在此目录管理

## 📝 Prompt YAML格式

### 基本结构
```yaml
# Prompt名称和描述
name: "prompt_name"
description: "Prompt用途说明"
version: "1.0"

# System Prompt
system: |
  你是一个...
  
  你的任务是...
  
  规则：
  1. 规则1
  2. 规则2

# User Prompt模板
user_template: |
  请分析以下内容：
  
  {{content}}
  
  要求：
  {{requirements}}

# Few-shot示例（可选）
examples:
  - user: "示例输入1"
    assistant: "示例输出1"
  - user: "示例输入2"
    assistant: "示例输出2"

# 参数说明
parameters:
  temperature: 0.7
  max_tokens: 4096
  top_p: 0.95
```

## 🔧 Prompt使用

### 加载Prompt
```python
from src.utils.prompt_loader import load_prompt

# 加载完整prompt配置
prompt_config = load_prompt("writer")

# 获取system prompt
system_prompt = prompt_config["system"]

# 使用模板
user_prompt = prompt_config["user_template"].format(
    content=content,
    requirements=requirements
)
```

### 在Agent中使用
```python
class MyAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__()
        self.llm_client = llm_client
        self.prompt_config = load_prompt("my_prompt")
    
    def process(self, input_data):
        messages = [
            {"role": "system", "content": self.prompt_config["system"]},
            {"role": "user", "content": self._format_user_prompt(input_data)}
        ]
        
        response = self.llm_client.chat(
            messages=messages,
            **self.prompt_config.get("parameters", {})
        )
        
        return response
```

## 📚 Prompt分类

### Writer相关
- `writer.yaml` - 主要的写作prompt

### Training相关
- `rule_extraction.yaml` - 从GT项目提取规则
- `rule_validation.yaml` - 验证规则有效性
- `comparative_evaluation.yaml` - 对比评估

### 素材处理相关
- `novel_segmentation.yaml` - 小说分段
- `novel_segmentation_analysis.yaml` - 分段分析
- `novel_chapter_functional_analysis.yaml` - 章节功能分析
- `introduction_extraction.yaml` - 简介提取
- `introduction_validation.yaml` - 简介验证

### Script处理相关
- `srt_script_processing_with_novel.yaml` - 有小说参考的SRT处理
- `srt_script_processing_without_novel.yaml` - 无小说参考的SRT处理

### 分析对齐相关
- `alignment.yaml` - 对齐分析
- `script_alignment_analysis.yaml` - 脚本对齐分析
- `layered_extraction.yaml` - 分层提取

## 🚀 开发新Prompt

### Step 1: 创建YAML文件
```yaml
name: "new_prompt"
description: "新Prompt的用途"
version: "1.0"

system: |
  编写详细的system prompt
  
user_template: |
  编写user prompt模板
```

### Step 2: 测试Prompt
1. 使用测试脚本验证
2. 调整参数（temperature、max_tokens等）
3. 添加Few-shot示例
4. 验证输出质量

### Step 3: 优化
1. 收集实际使用反馈
2. 优化Prompt措辞
3. 调整参数
4. 版本升级

### Step 4: 文档化
1. 在本文档中添加说明
2. 记录使用场景
3. 提供代码示例

## 📊 Prompt优化策略

### 1. 明确性
- 清晰定义任务目标
- 提供具体的输出格式
- 列出详细的规则

### 2. 示例驱动
- 提供Few-shot示例
- 示例要覆盖典型场景
- 示例要展示期望格式

### 3. 约束条件
- 明确输出长度限制
- 指定格式要求
- 说明禁止行为

### 4. 迭代优化
- 从简单开始
- 根据反馈改进
- A/B测试对比

## ⚠️ 注意事项

### 禁止事项
- ❌ 在代码中硬编码Prompt
- ❌ 随意修改Prompt不记录
- ❌ 不测试就上线新Prompt

### 推荐做法
- ✅ 所有Prompt统一管理
- ✅ 版本变更记录在Git
- ✅ 重大变更先测试后上线
- ✅ 保留历史版本用于回滚

## 📈 Prompt版本管理

### 版本号规则
- 大版本号：重大改动（v1.0 → v2.0）
- 小版本号：优化改进（v1.0 → v1.1）
- 补丁版本：Bug修复（v1.0.0 → v1.0.1）

### 变更记录
在Prompt文件中记录变更历史：
```yaml
changelog:
  - version: "1.1"
    date: "2026-02-08"
    changes:
      - "优化System Prompt的措辞"
      - "添加2个Few-shot示例"
  - version: "1.0"
    date: "2026-01-01"
    changes:
      - "初始版本"
```

---

**最后更新**: 2026-02-08  
**当前Prompts**: 16个YAML文件
