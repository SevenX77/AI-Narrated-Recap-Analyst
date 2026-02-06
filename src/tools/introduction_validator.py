"""
简介验证工具

使用LLM验证过滤后的简介质量，检测多删/漏删，并生成改进建议
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """验证问题"""
    type: str  # 'over_filtered' | 'under_filtered' | 'readability'
    severity: str  # 'critical' | 'warning' | 'info'
    location: str  # 问题位置描述
    content: str  # 问题内容
    reason: str  # 问题原因
    suggestion: str  # 修复建议


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    quality_score: float  # 0-100
    issues: List[ValidationIssue]
    filtered_introduction: str  # 最终过滤后的简介
    rule_suggestions: List[str]  # 规则改进建议
    
    def __str__(self):
        status = "✅ 通过" if self.is_valid else "⚠️ 需要改进"
        return f"{status} | 质量分: {self.quality_score}/100 | 问题数: {len(self.issues)}"


class IntroductionValidator(BaseTool):
    """
    简介验证工具
    
    功能：
    1. 检测过度过滤（多删）：关键故事元素被误删
    2. 检测过滤不足（漏删）：元信息残留
    3. 可读性检查：逻辑连贯性、突兀内容
    4. 生成规则改进建议
    """
    
    name = "introduction_validator"
    description = "Validate filtered introductions and suggest rule improvements"
    
    def __init__(self):
        """初始化"""
        self.llm_client = None
        self.prompt_config = None
        self._init_attempted = False
    
    def _ensure_llm_client(self):
        """确保LLM客户端已初始化（运行时检查）"""
        if self.llm_client is not None:
            return True
        
        if self._init_attempted:
            return False
        
        self._init_attempted = True
        
        try:
            if not config.llm.api_key:
                logger.error("❌ LLM API key not configured. Validator requires LLM to function.")
                logger.error("   Please set DEEPSEEK_API_KEY in .env file")
                return False
            
            self.llm_client = OpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url
            )
            self.prompt_config = load_prompts("introduction_validation")
            logger.info("✅ LLM introduction validator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM client: {e}")
            return False
    
    def execute(self, 
                original_introduction: str, 
                filtered_introduction: str,
                novel_title: str = "") -> ValidationResult:
        """
        验证过滤后的简介
        
        Args:
            original_introduction: 原始简介（包含元信息）
            filtered_introduction: 过滤后的简介
            novel_title: 小说标题（可选，用于上下文）
        
        Returns:
            ValidationResult
        """
        # 运行时确保LLM客户端可用
        if not self._ensure_llm_client():
            logger.error("❌ IntroductionValidator DISABLED: LLM client not available")
            logger.error("   Validation SKIPPED - returning unvalidated introduction")
            return ValidationResult(
                is_valid=False,  # 标记为无效，因为未经验证
                quality_score=0.0,
                issues=[ValidationIssue(
                    type="system_error",
                    severity="critical",
                    location="validator",
                    content="LLM client not available",
                    reason="API key not configured or initialization failed",
                    suggestion="Configure DEEPSEEK_API_KEY in .env file"
                )],
                filtered_introduction=filtered_introduction,
                rule_suggestions=[]
            )
        
        logger.info(f"Validating introduction for '{novel_title}'")
        
        # 调用LLM进行全面验证
        validation_data = self._validate_with_llm(
            original_introduction,
            filtered_introduction,
            novel_title
        )
        
        # 解析验证结果
        issues = self._parse_issues(validation_data)
        
        # 生成规则建议
        rule_suggestions = self._generate_rule_suggestions(issues)
        
        # 使用LLM提供的修复版本
        if 'corrected_introduction' in validation_data and validation_data['corrected_introduction']:
            fixed_introduction = validation_data['corrected_introduction'].strip()
            logger.info("Using LLM-corrected introduction")
        else:
            # 如果LLM没有提供修复版本，使用原始过滤结果
            fixed_introduction = filtered_introduction
            logger.warning("LLM did not provide corrected_introduction, using original filtered version")
        
        # 计算质量分数
        quality_score = self._calculate_quality_score(issues)
        
        result = ValidationResult(
            is_valid=quality_score >= 70.0,
            quality_score=quality_score,
            issues=issues,
            filtered_introduction=fixed_introduction,
            rule_suggestions=rule_suggestions
        )
        
        logger.info(f"Validation result: {result}")
        return result
    
    def _validate_with_llm(self,
                           original: str,
                           filtered: str,
                           title: str) -> Dict[str, Any]:
        """
        使用LLM进行全面验证并修复
        
        Returns:
            {
                "over_filtered": [...],  # 过度过滤的问题
                "under_filtered": [...],  # 过滤不足的问题
                "readability": [...],     # 可读性问题
                "overall_assessment": "...",
                "corrected_introduction": "..."  # LLM修复后的简介
            }
        """
        user_prompt = self.prompt_config["user_template"].format(
            novel_title=title,
            original_introduction=original,
            filtered_introduction=filtered
        )
        
        response = self.llm_client.chat.completions.create(
            model=self.prompt_config.get("settings", {}).get("model", "deepseek-chat"),
            messages=[
                {"role": "system", "content": self.prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.prompt_config.get("settings", {}).get("temperature", 0.2),
            max_tokens=self.prompt_config.get("settings", {}).get("max_tokens", 2000),
            response_format={"type": "json_object"}
        )
        
        import json
        validation_data = json.loads(response.choices[0].message.content)
        
        logger.debug(f"LLM validation response: {validation_data}")
        return validation_data
    
    def _parse_issues(self, validation_data: Dict[str, Any]) -> List[ValidationIssue]:
        """解析验证数据为问题列表"""
        issues = []
        
        # 过度过滤问题
        for item in validation_data.get("over_filtered", []):
            issues.append(ValidationIssue(
                type="over_filtered",
                severity=item.get("severity", "warning"),
                location=item.get("location", ""),
                content=item.get("content", ""),
                reason=item.get("reason", ""),
                suggestion=item.get("suggestion", "")
            ))
        
        # 过滤不足问题
        for item in validation_data.get("under_filtered", []):
            issues.append(ValidationIssue(
                type="under_filtered",
                severity=item.get("severity", "warning"),
                location=item.get("location", ""),
                content=item.get("content", ""),
                reason=item.get("reason", ""),
                suggestion=item.get("suggestion", "")
            ))
        
        # 可读性问题
        for item in validation_data.get("readability", []):
            issues.append(ValidationIssue(
                type="readability",
                severity=item.get("severity", "info"),
                location=item.get("location", ""),
                content=item.get("content", ""),
                reason=item.get("reason", ""),
                suggestion=item.get("suggestion", "")
            ))
        
        return issues
    
    def _generate_rule_suggestions(self, issues: List[ValidationIssue]) -> List[str]:
        """根据问题生成规则改进建议"""
        suggestions = []
        
        # 统计问题类型
        under_filtered_issues = [i for i in issues if i.type == "under_filtered"]
        
        if under_filtered_issues:
            # 提取需要过滤的模式
            patterns = []
            for issue in under_filtered_issues:
                content = issue.content.strip()
                
                # CP配对模式
                if '＊' in content or '×' in content:
                    patterns.append("配对标签（含 ＊ 或 × 符号）")
                
                # 分隔符
                if content.strip() in ['......', '。。。。。。', '———']:
                    patterns.append("装饰性分隔符")
                
                # 其他模式
                if content and not any(p in content for p in patterns):
                    patterns.append(f"'{content}' 类型的元信息")
            
            if patterns:
                unique_patterns = list(set(patterns))
                suggestions.append(
                    f"添加规则过滤以下模式：{', '.join(unique_patterns)}"
                )
        
        return suggestions
    
    
    def _calculate_quality_score(self, issues: List[ValidationIssue]) -> float:
        """
        计算质量分数
        
        - critical: -20分/个
        - warning: -10分/个
        - info: -5分/个
        """
        score = 100.0
        
        for issue in issues:
            if issue.severity == "critical":
                score -= 20
            elif issue.severity == "warning":
                score -= 10
            elif issue.severity == "info":
                score -= 5
        
        return max(0.0, min(100.0, score))
