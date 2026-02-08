# Core模块文档

Core模块提供项目的核心基础设施，包括配置管理、接口定义、数据模型和管理器。

## 📁 文档列表

- [config.md](config.md) - 配置系统（LLM、路径、日志等）
- [interfaces.md](interfaces.md) - 基础接口（BaseTool、BaseAgent、BaseWorkflow）
- [schemas.md](schemas.md) - 数据模型（Pydantic schemas）
- [managers.md](managers.md) - 管理器（ProjectManager、ArtifactManager）

## 📦 Core模块概述

### 代码位置
```
src/core/
├── __init__.py
├── config.py                # 配置管理
├── interfaces.py            # 接口定义
├── schemas.py               # 基础数据模型
├── schemas_*.py             # 分类数据模型
├── project_manager.py       # 项目管理器
└── artifact_manager.py      # 输出管理器
```

### 文档对应
```
docs/core/
├── README.md               # 本文件
├── config.md               # config.py文档
├── interfaces.md           # interfaces.py文档
├── schemas.md              # schemas相关文档
└── managers.md             # managers相关文档
```

## 🎯 核心职责

### 1. 配置管理（config.py）
- LLM配置（DeepSeek、Claude）
- 路径配置（data、logs、projects）
- 日志级别配置
- 全局配置实例

### 2. 接口定义（interfaces.py）
- `BaseTool`: 工具基类（无状态、原子性）
- `BaseAgent`: 代理基类（有状态、LLM驱动）
- `BaseWorkflow`: 工作流基类（编排工具和代理）

### 3. 数据模型（schemas_*.py）
- `schemas.py`: 基础数据模型
- `schemas_novel_analysis.py`: 小说分析相关
- `schemas_segmentation.py`: 分段相关
- `schemas_writer.py`: Writer相关
- `schemas_feedback.py`: Training反馈相关

### 4. 管理器
- `ProjectManager`: 项目目录管理、元数据管理
- `ArtifactManager`: 输出文件管理、版本控制

## 🔧 使用示例

### 使用配置
```python
from src.core.config import config

# 获取LLM配置
llm_config = config.llm
api_key = llm_config.api_key

# 获取路径
data_dir = config.data_dir
```

### 继承接口
```python
from src.core.interfaces import BaseTool

class MyTool(BaseTool):
    def execute(self, input_data):
        # 实现工具逻辑
        return result
```

### 使用数据模型
```python
from src.core.schemas import NovelMetadata

metadata = NovelMetadata(
    title="示例小说",
    author="作者",
    intro="简介..."
)
```

### 使用管理器
```python
from src.core.project_manager import project_manager

# 获取项目路径
paths = project_manager.get_project_paths("PROJ_001")

# 创建新项目
project_manager.create_project("新项目")
```

## 📝 开发规范

### 添加新配置
1. 在`config.py`中添加配置类
2. 在`AppConfig`中注册
3. 更新`config.md`文档
4. 提供使用示例

### 添加新接口
1. 在`interfaces.py`中定义抽象基类
2. 使用`@abstractmethod`标注必需方法
3. 更新`interfaces.md`文档
4. 提供继承示例

### 添加新Schema
1. 根据功能选择合适的`schemas_*.py`文件
2. 使用Pydantic `BaseModel`
3. 添加完整的Field描述
4. 更新`schemas.md`文档

### 修改管理器
1. 保持向后兼容
2. 添加单元测试
3. 更新`managers.md`文档
4. 记录breaking changes

## 🔗 相关文档

- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - 项目结构

---

**最后更新**: 2026-02-08
