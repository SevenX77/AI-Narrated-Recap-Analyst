# Agents模块文档

Agents模块包含有状态、LLM驱动的智能代理，用于复杂的内容生成和规则学习。

## 📁 文档列表

- [writer.md](writer.md) - Writer代理（内容生成）
- [training.md](training.md) - Training代理（规则提取和验证）

## 📦 Agents模块概述

### 代码位置
```
src/agents/
├── deepseek_writer.py       # DeepSeek写作代理
├── writer.py                # 写作代理抽象
├── rule_extractor.py        # 规则提取代理
└── rule_validator.py        # 规则验证代理
```

### 文档对应
```
docs/agents/
├── README.md                # 本文件
├── writer.md                # Writer代理文档
└── training.md              # Training代理文档
```

## 🎯 核心Agent

### 1. Writer代理
**职责**: 基于分析结果生成高质量的解说内容

**包含**:
- `writer.py`: Writer基类
- `deepseek_writer.py`: DeepSeek实现

**功能**:
- 剧情改编（压缩、扩展、创作）
- 情感渲染
- 节奏控制
- 悬念设计

**相关Prompt**:
- `src/prompts/writer.yaml`

---

### 2. Training代理
**职责**: 从爆款项目中学习规则，用于评估新内容

**包含**:
- `rule_extractor.py`: 规则提取代理
- `rule_validator.py`: 规则验证代理

**功能**:
- 从GT项目提取规则
- 验证规则有效性
- 评估新生成内容
- 提供改进建议

**相关Prompt**:
- `src/prompts/rule_extraction.yaml`
- `src/prompts/rule_validation.yaml`

## 🔧 Agent接口规范

所有Agent必须继承`BaseAgent`：

```python
from src.core.interfaces import BaseAgent
from typing import Any

class MyAgent(BaseAgent):
    """
    Agent简介
    
    职责：
        - 职责1
        - 职责2
    
    状态：
        - 状态变量1
        - 状态变量2
    
    依赖：
        - LLM客户端
        - 相关工具
    """
    
    def __init__(self, llm_client: Any):
        """初始化Agent"""
        super().__init__()
        self.llm_client = llm_client
        self.state = {}
    
    def process(self, input_data: Any) -> Any:
        """
        处理输入并生成输出
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        # 实现Agent逻辑
        return result
    
    def update_state(self, key: str, value: Any):
        """更新Agent状态"""
        self.state[key] = value
```

## 📝 Agent vs Tool

### Tool（工具）
- ✅ 无状态
- ✅ 原子性操作
- ✅ 确定性输出
- ✅ 不使用LLM（或仅辅助）
- ✅ 快速执行

### Agent（代理）
- ✅ 有状态
- ✅ 复杂推理
- ✅ 创造性输出
- ✅ LLM驱动
- ✅ 可能较慢

## 🚀 开发新Agent流程

### Step 1: 设计
1. 明确Agent职责和目标
2. 定义输入输出格式
3. 设计状态管理方案
4. 设计Prompt策略

### Step 2: Prompt开发
1. 在`src/prompts/`创建YAML文件
2. 编写详细的System Prompt
3. 设计Few-shot示例
4. 测试Prompt效果

### Step 3: 实现
1. 创建Agent文件
2. 继承`BaseAgent`
3. 实现核心方法
4. 添加状态管理

### Step 4: 测试
1. 单元测试（功能测试）
2. 集成测试（与其他组件配合）
3. 质量测试（输出质量）
4. 性能测试（速度和成本）

### Step 5: 优化
1. Prompt优化
2. 状态管理优化
3. 错误处理优化
4. 性能优化

## 📚 相关文档

- [prompts/README.md](../prompts/README.md) - Prompt管理
- [workflows/README.md](../workflows/README.md) - Agent在工作流中的使用
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范

## 📈 当前状态

### Writer代理
- ✅ `writer.py` - 基类定义
- ✅ `deepseek_writer.py` - DeepSeek实现
- ✅ Prompt配置完整
- 📝 文档待完善

### Training代理
- ✅ `rule_extractor.py` - 规则提取
- ✅ `rule_validator.py` - 规则验证
- ✅ Prompt配置完整
- 📝 文档待完善

---

**最后更新**: 2026-02-08  
**维护者**: Project Team
