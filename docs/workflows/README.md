# Workflows模块文档

Workflows模块编排工具和代理的执行流程，实现完整的业务逻辑。

## 📁 文档列表

- [training_workflow.md](training_workflow.md) - Training工作流

## 📦 Workflows模块概述

### 代码位置
```
src/workflows/
└── training_workflow_v2.py      # 热度驱动训练工作流
```

### 文档对应
```
docs/workflows/
├── README.md                    # 本文件
└── training_workflow.md         # Training工作流文档
```

## 🎯 当前工作流

### Training Workflow（热度驱动训练）
**文件**: `training_workflow_v2.py`

**职责**: 基于真实热度数据的规则学习和内容评估系统

**流程**:
1. **规则提取**: 从多个GT项目中提取爆款规则
2. **规则验证**: 验证规则能否预测GT项目的热度
3. **规则优化**: 根据验证结果调整规则权重
4. **内容评估**: 用优化后的规则评估新生成的内容

**使用的组件**:
- `RuleExtractorAgent`: 规则提取
- `RuleValidatorAgent`: 规则验证
- `ComparativeEvaluatorAgent`: 对比评估

**详细文档**: [training_workflow.md](training_workflow.md)

## 🔧 Workflow接口规范

所有Workflow必须继承`BaseWorkflow`：

```python
from src.core.interfaces import BaseWorkflow
from typing import Dict, Any

class MyWorkflow(BaseWorkflow):
    """
    工作流简介
    
    流程：
        Phase 1: 阶段1描述
        Phase 2: 阶段2描述
        Phase 3: 阶段3描述
    
    输入：
        - 参数1: 描述
        - 参数2: 描述
    
    输出：
        Dict包含：
        - result1: 描述
        - result2: 描述
    """
    
    name = "my_workflow"
    
    def __init__(self):
        """初始化工作流"""
        super().__init__()
        # 初始化工具和代理
        self.tool1 = Tool1()
        self.agent1 = Agent1()
        
        # 注册组件
        self.register_tool(self.tool1)
        self.register_agent(self.agent1)
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        运行工作流
        
        Args:
            **kwargs: 工作流参数
            
        Returns:
            工作流执行结果
        """
        # Phase 1
        result1 = await self._phase1(**kwargs)
        
        # Phase 2
        result2 = await self._phase2(result1)
        
        # Phase 3
        result3 = await self._phase3(result2)
        
        return {
            "success": True,
            "results": result3
        }
    
    async def _phase1(self, **kwargs):
        """执行Phase 1"""
        pass
    
    async def _phase2(self, input_data):
        """执行Phase 2"""
        pass
    
    async def _phase3(self, input_data):
        """执行Phase 3"""
        pass
```

## 📝 Workflow设计原则

### 1. 模块化
每个Phase独立，可以单独测试和优化

### 2. 可恢复
支持断点续传，失败后可从中断处继续

### 3. 可监控
记录详细的执行日志，便于调试和优化

### 4. 可配置
关键参数可通过配置文件或参数传入

### 5. 错误处理
完善的异常捕获和错误恢复机制

## 🚀 开发新Workflow流程

### Step 1: 设计
1. 分析业务需求
2. 拆分为多个Phase
3. 确定需要的工具和代理
4. 设计数据流

### Step 2: 实现
1. 创建Workflow文件
2. 继承`BaseWorkflow`
3. 实现各个Phase
4. 添加日志和错误处理

### Step 3: 测试
1. 单元测试（各Phase独立测试）
2. 集成测试（完整流程测试）
3. 性能测试（执行时间、资源占用）
4. 边界测试（异常情况）

### Step 4: 文档
1. 编写Workflow文档
2. 绘制流程图
3. 提供使用示例
4. 记录注意事项

### Step 5: 优化
1. 性能优化（并发、缓存）
2. 用户体验优化（进度提示）
3. 错误处理优化
4. 文档完善

## 📊 Workflow vs Tool vs Agent

### Tool（工具）
- 单一功能
- 无状态
- 快速执行

### Agent（代理）
- 复杂推理
- 有状态
- LLM驱动

### Workflow（工作流）
- 编排多个工具和代理
- 实现完整业务逻辑
- 管理执行流程

## 🔄 未来Workflow规划

### Ingestion Workflow（素材摄入）
**待开发**

**流程**:
1. Phase 1: 素材导入与验证
2. Phase 2: 素材标准化处理
3. Phase 3: 质量检查与报告

### Analysis Workflow（内容分析）
**待开发**

**流程**:
1. Phase 1: Hook检测与分析
2. Phase 2: 语义提取与标注
3. Phase 3: 对齐匹配与验证

### Generation Workflow（内容生成）
**待开发**

**流程**:
1. Phase 1: 内容规划
2. Phase 2: Writer生成
3. Phase 3: 质量评估与优化

## 📚 相关文档

- [tools/README.md](../tools/README.md) - 工具模块
- [agents/README.md](../agents/README.md) - 代理模块
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范

---

**最后更新**: 2026-02-08  
**当前工作流**: 1个（Training）  
**计划工作流**: 3个（Ingestion、Analysis、Generation）
