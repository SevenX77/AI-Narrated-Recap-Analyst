# Utils模块文档

Utils模块提供通用的工具函数和辅助类。

## 📦 Utils概述

### 代码位置
```
src/utils/
├── logger.py              # 日志工具
├── prompt_loader.py       # Prompt加载器
└── text_processing.py     # 文本处理工具
```

## 🎯 工具函数

### 1. logger.py - 日志工具
**职责**: 统一的日志管理

**功能**:
- 配置日志格式
- 设置日志级别
- 文件日志输出
- 控制台日志输出

**使用**:
```python
from src.utils.logger import logger

logger.info("信息日志")
logger.warning("警告日志")
logger.error("错误日志")
```

---

### 2. prompt_loader.py - Prompt加载器
**职责**: 从YAML文件加载Prompt配置

**功能**:
- 加载YAML文件
- 解析Prompt配置
- 缓存已加载的Prompt
- 模板变量替换

**使用**:
```python
from src.utils.prompt_loader import load_prompt

# 加载prompt配置
config = load_prompt("writer")

# 获取system prompt
system = config["system"]

# 使用模板
user = config["user_template"].format(content="...")
```

---

### 3. text_processing.py - 文本处理工具
**职责**: 通用的文本处理函数

**功能**:
- 文本清理
- 编码转换
- 分句分段
- 正则匹配

**使用**:
```python
from src.utils.text_processing import (
    normalize_text,
    split_sentences,
    clean_whitespace
)

# 规范化文本
text = normalize_text(raw_text)

# 分句
sentences = split_sentences(text)

# 清理空白
clean = clean_whitespace(text)
```

## 📝 开发规范

### 添加新工具函数

#### 1. 确定位置
- 日志相关 → `logger.py`
- Prompt相关 → `prompt_loader.py`
- 文本处理 → `text_processing.py`
- 新类别 → 创建新文件

#### 2. 编写函数
```python
def my_util_function(param1: str, param2: int) -> str:
    """
    函数简介
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
        
    Raises:
        ValueError: 错误情况说明
    """
    # 实现函数逻辑
    return result
```

#### 3. 添加测试
在`scripts/test/`创建测试脚本

#### 4. 更新文档
在本文档中添加说明和使用示例

## 🔧 工具函数设计原则

### 1. 纯函数
- 无副作用
- 相同输入返回相同输出
- 不依赖外部状态

### 2. 单一职责
- 一个函数只做一件事
- 函数名清晰表达意图

### 3. 可测试
- 易于编写单元测试
- 边界情况处理完善

### 4. 可复用
- 通用性强
- 接口清晰
- 文档完整

## 📚 相关文档

- [DEV_STANDARDS.md](../DEV_STANDARDS.md) - 开发规范
- [core/README.md](../core/README.md) - Core模块

---

**最后更新**: 2026-02-08  
**当前工具**: 3个文件
