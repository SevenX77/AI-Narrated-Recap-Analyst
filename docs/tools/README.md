# Tools模块技术参考

Tools模块包含所有无状态、原子性的功能工具。每个工具专注做好一件事。

**本文档目的**: 技术参考，用于查找工具接口、理解实现逻辑、便于代码调用。

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

详见：[ROADMAP.md](ROADMAP.md)

### Phase I: 素材标准化（12个工具）
- **Novel处理**: 6个工具
- **Script处理**: 4个工具
- **验证工具**: 2个工具

### Phase II: 内容分析（6个工具）
- **Hook分析**: 2个工具
- **语义分析**: 2个工具
- **对齐匹配**: 2个工具

## 📋 工具技术规范

### 接口定义
所有工具必须继承 `BaseTool` (定义于 `src/core/interfaces.py`)

**基类接口**:
```python
class BaseTool(ABC):
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行工具核心功能"""
        pass
```

### 实现规范
```python
from src.core.interfaces import BaseTool
from typing import Any

class MyTool(BaseTool):
    """
    [工具名称]
    
    职责 (Responsibility):
        单一职责描述
    
    接口 (Interface):
        输入: Type - 说明
        输出: Type - 说明
    
    依赖 (Dependencies):
        - Schema: 使用的数据模型
        - Tools: 依赖的其他工具
        - Config: 需要的配置项
    
    实现逻辑 (Logic):
        1. 步骤1
        2. 步骤2
        3. 步骤3
    """
    
    def __init__(self, config_param: Any = None):
        super().__init__()
        self.config_param = config_param
    
    def execute(self, input_data: Any) -> Any:
        """核心执行逻辑"""
        # 实现
        return result
```

## 📝 工具文档模板

每个工具文档 (`docs/tools/{phase}/{tool_name}.md`) 必须包含：

### 1. 职责定义
- 单一职责描述
- 所属Phase
- 在工具链中的位置

### 2. 接口定义
```python
# 函数签名
def execute(self, input: InputType) -> OutputType
```
- 输入参数: 类型、格式、约束
- 输出结果: 类型、结构、字段说明
- 异常: 可能抛出的异常类型

### 3. 实现逻辑
- 核心算法步骤
- 调用的子工具/函数
- 关键决策逻辑

### 4. 依赖关系
- Schema: `src/core/schemas.py` 中使用的模型
- Tools: 依赖的其他工具（文件路径）
- Config: `src/core/config.py` 中需要的配置项

### 5. 代码示例
```python
# 仅展示接口调用，不是完整流程
tool = ToolName(config)
result = tool.execute(input_data)
# result.field1, result.field2
```

## 🔧 开发新工具流程

### Step 1: 设计与文档
1. 在 `docs/tools/{phase}/` 创建工具文档
2. 定义：职责、接口、实现逻辑、依赖
3. 确认设计无误后开始编码

### Step 2: 实现代码
1. 在 `src/tools/` 创建工具文件
2. 继承 `BaseTool`，实现 `execute()`
3. Docstring 必须与文档一致
4. 添加类型注解

### Step 3: 验证
1. 创建测试脚本 `scripts/test/{tool_name}_test.py`
2. 验证功能正确性和边界情况
3. 记录测试结果

### Step 4: 集成
1. 更新 `docs/tools/README.md` 工具列表
2. 如有新Schema，更新 `docs/core/schemas.md`
3. 提交代码和文档

## 📚 开发参考

### 归档工具参考
可以参考但不要直接复制：
- `archive/v2_tools_20260208/novel_processor.py`
- `archive/v2_tools_20260208/srt_processor.py`

### 相关文档
- [ROADMAP.md](ROADMAP.md) - 工具路线图
- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [interfaces.md](../core/interfaces.md) - 接口定义

## 📈 进度追踪

查看 [ROADMAP.md](ROADMAP.md) 了解：
- 已完成工具列表
- 进行中的工具
- 待开发工具
- 优先级排序

---

**最后更新**: 2026-02-08  
**当前进度**: 0/18 工具完成
