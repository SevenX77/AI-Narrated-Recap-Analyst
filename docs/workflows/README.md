# Workflows模块文档

Workflows模块编排工具和代理的执行流程，实现完整的业务逻辑。

## 📁 文档列表

- [ROADMAP.md](ROADMAP.md) - Workflow 开发路线图
- [training_workflow.md](training_workflow.md) - Training工作流
- [novel_processing_workflow.md](novel_processing_workflow.md) - Novel处理工作流

## 📦 Workflows模块概述

### 代码位置
```
src/workflows/
├── novel_processing_workflow.py      # 小说处理工作流 ⭐
├── script_processing_workflow.py     # 脚本处理工作流 ⭐
├── preprocess_service.py             # 预处理服务（后台任务）⭐
├── report_generator.py               # 报告生成器
└── training_workflow_v2.py           # 热度驱动训练工作流
```

### 文档对应
```
docs/workflows/
├── README.md                          # 本文件
├── novel_processing_workflow.md      # Novel处理工作流文档
├── script_processing_workflow.md     # Script处理工作流文档
└── training_workflow.md              # Training工作流文档
```

## 🎯 当前工作流

### Novel Processing Workflow（小说处理工作流）✅
**文件**: `src/workflows/novel_processing_workflow.py`

**职责**: 从原始小说到完整章节分析

**流程**:
1. **小说导入与规范化**
2. **提取小说元数据**
3. **检测章节边界**
4. **章节并行分段（Two-Pass）**
5. **章节并行标注（Three-Pass）**
6. **全书系统元素分析（可选）**
7. **章节系统元素检测与追踪（可选）**
8. **质量验证与报告生成**

**关键特性**:
- 并行处理章节（线程池）
- 错误恢复与断点续传
- 实时进度监控
- LLM rate limiting 集成
- 质量门禁（≥80分）

**详细文档**: [novel_processing_workflow.md](novel_processing_workflow.md)

---

### Script Processing Workflow（脚本处理工作流）✅
**文件**: `src/workflows/script_processing_workflow.py`

**职责**: 从原始SRT字幕到完整脚本分析

**流程**:
1. **SRT导入与验证**
2. **文本提取与清洗**
3. **脚本ABC分段（Two-Pass）**
4. **质量验证与报告生成**

**关键特性**:
- 并行处理多个SRT文件
- 智能文本合并
- ABC分类分段（A-旁白，B-事件，C-系统）
- 质量门禁

**详细文档**: [script_processing_workflow.md](script_processing_workflow.md)

---

### Preprocess Service（预处理服务）✅ ⭐
**文件**: `src/workflows/preprocess_service.py`

**职责**: 后台异步预处理服务，自动识别文件类型并执行相应处理

**特性**:
- 自动识别文件类型（.txt → Novel, .srt → Script）
- 异步后台执行（不阻塞API响应）
- 状态追踪（pending, running, completed, failed）
- 错误恢复和详细日志
- 支持增量处理（追加文件）

**使用场景**:
- API V2 文件上传后自动触发
- 前端实时监控预处理进度
- 支持文件追加和重新处理

**流程**:
```python
# 用户上传文件 → API接收 → PreprocessService异步执行
async def process_project_files(project_id: str):
    # 1. 检测文件类型
    # 2. 执行对应工作流（Novel/Script）
    # 3. 更新项目元数据
    # 4. 记录状态和错误
```

---

### Training Workflow（热度驱动训练）✅
**文件**: `src/workflows/training_workflow_v2.py`

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

详细规划请参考 [ROADMAP.md](ROADMAP.md)

### Script Processing Workflow（脚本处理工作流）✅
**状态**: 已完成 (2026-02-10)  
**文件**: `script_processing_workflow.py`

**流程**:
1. SRT 导入与规范化
2. 文本提取与智能修复
3. Hook 边界检测（ep01）
4. Hook 内容分析（可选）
5. 脚本语义分段（ABC 分类）
6. 质量验证

**关键特性**:
- Hook智能检测与分析
- Three-Pass分段（Two-Pass + ABC分类）
- 质量门禁（≥75分）
- 成本透明（$0.08-0.20/集）

**详细文档**: [script_processing_workflow.md](script_processing_workflow.md)

### Alignment Workflow（对齐分析工作流）🚧
**状态**: 待开发 (预计 2026-02-17)

**流程**:
1. 数据加载与验证
2. Hook-Body 分离策略
3. 句子级对齐分析
4. ABC 类型匹配分析
5. 覆盖率与改编分析
6. 质量评估与报告生成

### Full Pipeline Workflow（完整流程工作流）🚧
**状态**: 待开发 (预计 2026-02-20)

**流程**:
1. 项目初始化
2. 串行处理 Novel 和 Script
3. 质量门禁检查（≥80/≥75分）
4. 对齐分析
5. 综合报告生成（HTML + JSON）
6. 工件归档

### Batch Processing Workflow（批量处理工作流）🔜
**状态**: P2 优先级

**流程**:
1. 批量任务规划
2. 并行处理（动态调度）
3. 结果汇总与统计

### Quality Optimization Workflow（质量优化工作流）🔜
**状态**: P2 优先级

**流程**:
1. 质量问题诊断
2. 针对性修复
3. 验证与对比

### Generation Workflow（内容生成工作流）🔮
**状态**: P3 优先级，未来规划

**流程**:
1. Phase 1: 内容规划
2. Phase 2: Writer生成
3. Phase 3: 质量评估与优化

## 📚 相关文档

- [tools/README.md](../tools/README.md) - 工具模块
- [agents/README.md](../agents/README.md) - 代理模块
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范

---

## 📊 开发进度

**当前进度**: 3/7 workflows (43%)
- ✅ NovelProcessingWorkflow (测试中)
- ✅ ScriptProcessingWorkflow (已完成，待测试)
- ✅ TrainingWorkflow (已上线)
- 🚧 AlignmentWorkflow (待开发)
- 🚧 FullPipelineWorkflow (待开发)
- 🔜 BatchProcessingWorkflow (P2)
- 🔜 QualityOptimizationWorkflow (P2)
- 🔮 GenerationWorkflow (P3)

**下一步**: 开发 AlignmentWorkflow（预计 4-5 天）

---

**最后更新**: 2026-02-10  
**当前工作流**: 3个（Novel Processing, Script Processing, Training）  
**计划工作流**: 4个（Alignment, Full Pipeline, Batch Processing, Quality Optimization）
