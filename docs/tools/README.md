# Tools模块文档

Tools模块包含所有无状态、原子性的功能工具。每个工具专注做好一件事。

## 📁 文档组织

```
docs/tools/
├── README.md                    # 本文件：Tools概述
│
├── phase1_novel/                # Phase I: Novel处理工具
│   ├── README.md
│   ├── novel_importer.md       # 小说导入
│   ├── novel_metadata_extractor.md
│   ├── novel_chapter_detector.md
│   ├── novel_segmenter.md
│   ├── novel_chapter_splitter.md
│   └── novel_validator.md
│
├── phase1_script/               # Phase I: Script处理工具
│   ├── README.md
│   ├── srt_importer.md
│   ├── srt_text_extractor.md
│   ├── script_segmenter.md
│   └── script_validator.md
│
└── phase2_analysis/             # Phase II: 分析对齐工具
    ├── README.md
    ├── hook_detector.md
    ├── hook_content_analyzer.md
    ├── novel_semantic_analyzer.md
    ├── script_semantic_analyzer.md
    ├── semantic_matcher.md
    ├── alignment_validator.md
    ├── novel_tagger.md
    └── script_tagger.md
```

## 🎯 工具设计原则

### 1. 单一职责
每个工具只做一件事，做好一件事。

### 2. 无状态
工具不保存状态，每次调用独立。

### 3. 原子性
工具执行要么成功，要么失败，不会有中间状态。

### 4. 可测试
每个工具都有对应的测试脚本。

### 5. 文档完整
每个工具都有详细的文档和使用示例。

## 📊 工具开发路线图

详见：[TOOLS_ROADMAP.md](../TOOLS_ROADMAP.md)

### Phase I: 素材标准化（12个工具）
- **Novel处理**: 6个工具
- **Script处理**: 4个工具
- **验证工具**: 2个工具

### Phase II: 内容分析（6个工具）
- **Hook分析**: 2个工具
- **语义分析**: 2个工具
- **对齐匹配**: 2个工具

## 🔧 工具接口规范

所有工具必须继承`BaseTool`：

```python
from src.core.interfaces import BaseTool
from typing import Any

class MyTool(BaseTool):
    """
    工具简介
    
    职责：
        - 职责1
        - 职责2
    
    输入：
        input_type: 输入描述
    
    输出：
        output_type: 输出描述
    
    依赖：
        - DependencyTool1
        - DependencyTool2
    """
    
    def __init__(self, config_param: Any = None):
        """初始化工具"""
        super().__init__()
        self.config_param = config_param
    
    def execute(self, input_data: Any) -> Any:
        """
        执行工具的核心功能
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理后的数据
            
        Raises:
            ValueError: 输入数据无效
            RuntimeError: 处理失败
        """
        # 实现工具逻辑
        return result
```

## 📝 工具文档模板

每个工具的文档应包含：

### 1. 基本信息
- 工具名称
- 职责描述
- 所属Phase
- 优先级

### 2. 接口说明
- 输入参数
- 输出格式
- 异常处理

### 3. 依赖关系
- 依赖的工具
- 依赖的Schema
- 依赖的配置

### 4. 使用示例
- 基本用法
- 高级用法
- 错误处理

### 5. 测试方法
- 测试脚本位置
- 测试数据准备
- 预期结果

## 🚀 开发新工具流程

### Step 1: 设计
1. 明确工具职责（单一职责）
2. 定义输入输出
3. 确定依赖关系
4. 编写文档（在`docs/tools/`对应目录）

### Step 2: 实现
1. 创建工具文件（在`src/tools/`）
2. 继承`BaseTool`
3. 实现`execute()`方法
4. 添加完整的docstring

### Step 3: 测试
1. 创建测试脚本（在`scripts/test/`）
2. 准备测试数据
3. 验证功能正确性
4. 测试边界情况

### Step 4: 文档
1. 更新工具文档
2. 添加使用示例
3. 记录已知问题
4. 更新本README

### Step 5: 集成
1. 提交代码审查
2. 运行CI测试
3. 合并到主分支
4. 标记版本

## 📚 开发参考

### 归档工具参考
可以参考但不要直接复制：
- `archive/v2_tools_20260208/novel_processor.py`
- `archive/v2_tools_20260208/srt_processor.py`

### 相关文档
- [TOOLS_ROADMAP.md](../TOOLS_ROADMAP.md) - 工具路线图
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [interfaces.md](../core/interfaces.md) - 接口定义

## 📈 进度追踪

查看 [TOOLS_ROADMAP.md](../TOOLS_ROADMAP.md) 了解：
- 已完成工具列表
- 进行中的工具
- 待开发工具
- 优先级排序

---

**最后更新**: 2026-02-08  
**当前进度**: 0/18 工具完成
