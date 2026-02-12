"""
Project Exceptions - 统一的异常处理体系

定义项目中使用的所有异常类型，确保错误处理的一致性。

异常层级：
- ProjectBaseException (基础异常)
  ├── ToolExecutionError (工具执行错误)
  ├── LLMCallError (LLM 调用错误)
  ├── ValidationError (数据验证错误)
  ├── ConfigurationError (配置错误)
  ├── FileOperationError (文件操作错误)
  └── WorkflowError (工作流错误)

作者：AI-Narrated Recap Analyst Team
创建时间：2026-02-10
"""

from typing import Optional, Any, Dict


class ProjectBaseException(Exception):
    """
    项目基础异常类
    
    所有自定义异常都应该继承此类。
    
    Attributes:
        message: 错误消息
        details: 额外的错误详情（可选）
        original_error: 原始异常（如果是封装异常）
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化异常
        
        Args:
            message: 错误消息
            details: 错误详情字典
            original_error: 原始异常对象
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        """返回格式化的错误信息"""
        base_msg = self.message
        
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg += f" ({details_str})"
        
        if self.original_error:
            base_msg += f" [原因: {self.original_error}]"
        
        return base_msg


class ToolExecutionError(ProjectBaseException):
    """
    工具执行错误
    
    当工具类执行失败时抛出。
    
    Example:
        ```python
        try:
            result = tool.execute(**kwargs)
        except Exception as e:
            raise ToolExecutionError(
                message="工具执行失败",
                details={"tool_name": "NovelSegmenter", "chapter": 1},
                original_error=e
            )
        ```
    """
    
    def __init__(
        self,
        tool_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化工具执行错误
        
        Args:
            tool_name: 工具名称
            message: 错误消息
            details: 错误详情
            original_error: 原始异常
        """
        self.tool_name = tool_name
        super().__init__(
            message=f"[{tool_name}] {message}",
            details=details,
            original_error=original_error
        )


class LLMCallError(ProjectBaseException):
    """
    LLM 调用错误
    
    当 LLM API 调用失败时抛出。
    
    Example:
        ```python
        try:
            response = llm_client.call(...)
        except Exception as e:
            raise LLMCallError(
                message="LLM API 调用失败",
                details={"provider": "claude", "model": "sonnet-4"},
                original_error=e
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化 LLM 调用错误
        
        Args:
            message: 错误消息
            provider: LLM Provider 名称
            model: 模型名称
            details: 错误详情
            original_error: 原始异常
        """
        self.provider = provider
        self.model = model
        
        error_details = details or {}
        if provider:
            error_details["provider"] = provider
        if model:
            error_details["model"] = model
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )


class ValidationError(ProjectBaseException):
    """
    数据验证错误
    
    当输入或输出数据验证失败时抛出。
    
    Example:
        ```python
        if not input_data:
            raise ValidationError(
                message="输入数据为空",
                details={"field": "novel_path", "value": None}
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化验证错误
        
        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 字段的实际值
            expected_type: 期望的类型
            details: 错误详情
            original_error: 原始异常
        """
        self.field = field
        self.value = value
        self.expected_type = expected_type
        
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)
        if expected_type:
            error_details["expected_type"] = expected_type
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )


class ConfigurationError(ProjectBaseException):
    """
    配置错误
    
    当配置不完整或无效时抛出。
    
    Example:
        ```python
        if not api_key:
            raise ConfigurationError(
                message="API Key 未配置",
                config_key="CLAUDE_API_KEY"
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化配置错误
        
        Args:
            message: 错误消息
            config_key: 配置项的键名
            details: 错误详情
            original_error: 原始异常
        """
        self.config_key = config_key
        
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )


class FileOperationError(ProjectBaseException):
    """
    文件操作错误
    
    当文件读写操作失败时抛出。
    
    Example:
        ```python
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except IOError as e:
            raise FileOperationError(
                message="文件读取失败",
                file_path=file_path,
                operation="read",
                original_error=e
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化文件操作错误
        
        Args:
            message: 错误消息
            file_path: 文件路径
            operation: 操作类型（read/write/delete等）
            details: 错误详情
            original_error: 原始异常
        """
        self.file_path = file_path
        self.operation = operation
        
        error_details = details or {}
        if file_path:
            error_details["file_path"] = file_path
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )


class WorkflowError(ProjectBaseException):
    """
    工作流错误
    
    当工作流执行失败时抛出。
    
    Example:
        ```python
        try:
            result = await workflow.run(...)
        except Exception as e:
            raise WorkflowError(
                message="工作流执行失败",
                workflow_name="NovelProcessingWorkflow",
                step=4,
                original_error=e
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        workflow_name: Optional[str] = None,
        step: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化工作流错误
        
        Args:
            message: 错误消息
            workflow_name: 工作流名称
            step: 失败的步骤编号
            details: 错误详情
            original_error: 原始异常
        """
        self.workflow_name = workflow_name
        self.step = step
        
        error_details = details or {}
        if workflow_name:
            error_details["workflow"] = workflow_name
        if step is not None:
            error_details["step"] = step
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )


class ParsingError(ProjectBaseException):
    """
    解析错误
    
    当 LLM 输出解析失败时抛出。
    
    Example:
        ```python
        try:
            parsed = parse_llm_output(llm_result)
        except Exception as e:
            raise ParsingError(
                message="LLM 输出解析失败",
                parser_name="SegmentationParser",
                raw_output=llm_result[:100],
                original_error=e
            )
        ```
    """
    
    def __init__(
        self,
        message: str,
        parser_name: Optional[str] = None,
        raw_output: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初始化解析错误
        
        Args:
            message: 错误消息
            parser_name: 解析器名称
            raw_output: 原始输出（截断版本）
            details: 错误详情
            original_error: 原始异常
        """
        self.parser_name = parser_name
        self.raw_output = raw_output
        
        error_details = details or {}
        if parser_name:
            error_details["parser"] = parser_name
        if raw_output:
            error_details["raw_output_preview"] = raw_output[:100] + "..." if len(raw_output) > 100 else raw_output
        
        super().__init__(
            message=message,
            details=error_details,
            original_error=original_error
        )
