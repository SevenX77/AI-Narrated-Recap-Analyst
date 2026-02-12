"""
Two-Pass Tool - 统一的 Two-Pass LLM 调用基础类

提供标准化的 Two-Pass 处理模式，确保输出准确性。

Two-Pass 策略：
- Pass 1: 初步处理（使用简化 Prompt）
- Pass 2: 校验修正（使用相同原则检查）

使用场景：
- 小说章节分段（NovelSegmenter）
- 脚本分段（ScriptSegmenter）
- 事件标注（NovelAnnotator）

作者：AI-Narrated Recap Analyst Team
创建时间：2026-02-10
"""

import logging
from typing import Any, Dict, Optional, Callable
from abc import ABC, abstractmethod

from src.core.interfaces import BaseTool

logger = logging.getLogger(__name__)


class TwoPassTool(BaseTool, ABC):
    """
    Two-Pass LLM 调用的基础工具类
    
    子类需要实现：
    - _execute_pass1(): Pass 1 的具体实现
    - _execute_pass2(): Pass 2 的具体实现
    - _should_use_pass2_result(): 判断是否使用 Pass 2 结果
    - _parse_result(): 解析最终结果
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """
        初始化 Two-Pass 工具
        
        Args:
            provider: LLM Provider（默认：claude）
            model: 模型名称（可选）
        """
        self.provider = provider
        self.model = model
        self.pass1_result = None
        self.pass2_result = None
    
    def execute(self, **kwargs) -> Any:
        """
        执行 Two-Pass 处理流程
        
        Args:
            **kwargs: 传递给具体实现的参数
        
        Returns:
            处理后的结果
        """
        logger.info(f"开始 Two-Pass 处理：{self.__class__.__name__}")
        
        # Pass 1: 初步处理
        logger.info("Pass 1: 初步处理")
        self.pass1_result = self._execute_pass1(**kwargs)
        
        # Pass 2: 校验修正
        logger.info("Pass 2: 校验修正")
        self.pass2_result = self._execute_pass2(
            pass1_result=self.pass1_result,
            **kwargs
        )
        
        # 判断使用哪个结果
        if self._should_use_pass2_result(self.pass2_result):
            logger.info("使用 Pass 2 修正后的结果")
            final_result = self.pass2_result
        else:
            logger.info("Pass 2 确认无需修改，使用 Pass 1 结果")
            final_result = self.pass1_result
        
        # 解析最终结果
        parsed_result = self._parse_result(final_result, **kwargs)
        
        logger.info(f"Two-Pass 处理完成")
        return parsed_result
    
    @abstractmethod
    def _execute_pass1(self, **kwargs) -> str:
        """
        执行 Pass 1：初步处理
        
        子类必须实现此方法，返回 LLM 的原始输出字符串。
        
        Args:
            **kwargs: 输入参数
        
        Returns:
            str: Pass 1 的 LLM 输出
        """
        pass
    
    @abstractmethod
    def _execute_pass2(self, pass1_result: str, **kwargs) -> str:
        """
        执行 Pass 2：校验修正
        
        子类必须实现此方法，接收 Pass 1 的结果并进行校验。
        
        Args:
            pass1_result: Pass 1 的输出
            **kwargs: 原始输入参数
        
        Returns:
            str: Pass 2 的 LLM 输出
        """
        pass
    
    @abstractmethod
    def _should_use_pass2_result(self, pass2_result: str) -> bool:
        """
        判断是否应该使用 Pass 2 的结果
        
        子类必须实现此方法，根据 Pass 2 的输出判断是否需要修正。
        
        通常的判断逻辑：
        - 如果 Pass 2 输出包含"无需修改"、"分段正确"等关键词 → False
        - 否则 → True
        
        Args:
            pass2_result: Pass 2 的输出
        
        Returns:
            bool: True 表示使用 Pass 2 结果，False 表示使用 Pass 1 结果
        """
        pass
    
    @abstractmethod
    def _parse_result(self, final_result: str, **kwargs) -> Any:
        """
        解析最终结果
        
        子类必须实现此方法，将 LLM 的文本输出解析为结构化数据。
        
        Args:
            final_result: 最终的 LLM 输出（Pass 1 或 Pass 2）
            **kwargs: 原始输入参数（可能用于解析）
        
        Returns:
            Any: 解析后的结构化结果
        """
        pass


class SimpleTwoPassTool(TwoPassTool):
    """
    简化的 Two-Pass 工具（使用函数式接口）
    
    适合不需要完整继承的场景，通过传入函数实现 Two-Pass 逻辑。
    
    Example:
        ```python
        tool = SimpleTwoPassTool(
            pass1_func=lambda **kw: llm_call(prompt1, kw['input']),
            pass2_func=lambda p1, **kw: llm_call(prompt2, kw['input'], p1),
            parse_func=lambda result, **kw: parse_output(result),
            should_use_pass2=lambda p2: "无需修改" not in p2
        )
        result = tool.execute(input=data)
        ```
    """
    
    def __init__(
        self,
        pass1_func: Callable,
        pass2_func: Callable,
        parse_func: Callable,
        should_use_pass2: Callable[[str], bool] = None,
        provider: str = "claude",
        model: Optional[str] = None
    ):
        """
        初始化简化 Two-Pass 工具
        
        Args:
            pass1_func: Pass 1 执行函数 (**kwargs) -> str
            pass2_func: Pass 2 执行函数 (pass1_result: str, **kwargs) -> str
            parse_func: 解析函数 (final_result: str, **kwargs) -> Any
            should_use_pass2: Pass 2 判断函数 (pass2_result: str) -> bool
                默认：检查是否包含"无需修改"或"分段正确"
            provider: LLM Provider
            model: 模型名称
        """
        super().__init__(provider, model)
        self.pass1_func = pass1_func
        self.pass2_func = pass2_func
        self.parse_func = parse_func
        
        if should_use_pass2 is None:
            # 默认判断逻辑
            self.should_use_pass2_func = lambda p2: not any(
                keyword in p2 for keyword in ["无需修改", "分段正确", "✅"]
            )
        else:
            self.should_use_pass2_func = should_use_pass2
    
    def _execute_pass1(self, **kwargs) -> str:
        return self.pass1_func(**kwargs)
    
    def _execute_pass2(self, pass1_result: str, **kwargs) -> str:
        return self.pass2_func(pass1_result=pass1_result, **kwargs)
    
    def _should_use_pass2_result(self, pass2_result: str) -> bool:
        return self.should_use_pass2_func(pass2_result)
    
    def _parse_result(self, final_result: str, **kwargs) -> Any:
        return self.parse_func(final_result, **kwargs)


# 便捷函数：快速创建 Two-Pass 工具
def create_two_pass_tool(
    pass1_func: Callable,
    pass2_func: Callable,
    parse_func: Callable,
    should_use_pass2: Optional[Callable[[str], bool]] = None,
    provider: str = "claude",
    model: Optional[str] = None
) -> SimpleTwoPassTool:
    """
    快速创建 Two-Pass 工具的便捷函数
    
    Args:
        pass1_func: Pass 1 执行函数
        pass2_func: Pass 2 执行函数
        parse_func: 解析函数
        should_use_pass2: Pass 2 判断函数（可选）
        provider: LLM Provider
        model: 模型名称
    
    Returns:
        SimpleTwoPassTool: 配置好的 Two-Pass 工具实例
    
    Example:
        ```python
        my_tool = create_two_pass_tool(
            pass1_func=do_pass1,
            pass2_func=do_pass2,
            parse_func=parse_result
        )
        result = my_tool.execute(input=data)
        ```
    """
    return SimpleTwoPassTool(
        pass1_func=pass1_func,
        pass2_func=pass2_func,
        parse_func=parse_func,
        should_use_pass2=should_use_pass2,
        provider=provider,
        model=model
    )
