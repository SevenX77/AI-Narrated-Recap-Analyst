"""
NovelValidator - 小说处理质量验证工具

验证小说处理的各个环节质量，生成质量报告。
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from src.core.interfaces import BaseTool
from src.core.schemas_novel import (
    NovelImportResult,
    ChapterInfo,
    ParagraphSegmentationResult,
    AnnotatedChapter,
    NovelValidationReport,
    ValidationIssue
)

logger = logging.getLogger(__name__)


class NovelValidator(BaseTool):
    """
    小说处理质量验证工具
    
    职责 (Responsibility):
        验证小说处理的各个环节质量，确保数据准确性和合理性。
    
    检查项:
        1. 编码正确性: 检测乱码字符
        2. 章节完整性: 验证章节连续性
        3. 分段合理性: ABC类分布、过度分段
        4. 标注合理性: 事件数量、设定数量
    
    接口 (Interface):
        输入:
            - import_result: NovelImportResult
            - chapter_infos: List[ChapterInfo]
            - segmentation_results: List[ParagraphSegmentationResult]
            - annotation_results: List[AnnotatedChapter]
        
        输出:
            - NovelValidationReport: 验证报告
    """
    
    name = "novel_validator"
    description = "验证小说处理质量"
    
    def __init__(self):
        """初始化验证器"""
        super().__init__()
        self.quality_weights = {
            "encoding": 0.2,      # 编码正确性权重
            "chapter": 0.25,      # 章节完整性权重
            "segmentation": 0.3,  # 分段合理性权重
            "annotation": 0.25    # 标注合理性权重
        }
    
    def execute(
        self,
        import_result: NovelImportResult,
        chapter_infos: List[ChapterInfo],
        segmentation_results: List[ParagraphSegmentationResult] = None,
        annotation_results: List[AnnotatedChapter] = None,
        **kwargs
    ) -> NovelValidationReport:
        """
        执行小说质量验证
        
        Args:
            import_result: 小说导入结果
            chapter_infos: 章节信息列表
            segmentation_results: 分段结果列表（可选）
            annotation_results: 标注结果列表（可选）
        
        Returns:
            NovelValidationReport: 验证报告
        """
        logger.info(f"🔍 开始验证小说处理质量: {import_result.project_name}")
        
        issues: List[ValidationIssue] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        
        # 1. 编码正确性检查
        encoding_check = self._check_encoding(import_result, issues, warnings)
        
        # 2. 章节完整性检查
        chapter_check = self._check_chapters(chapter_infos, issues, warnings)
        
        # 3. 分段合理性检查
        segmentation_check = {}
        if segmentation_results:
            segmentation_check = self._check_segmentation(
                segmentation_results, issues, warnings, recommendations
            )
        
        # 4. 标注合理性检查
        annotation_check = {}
        if annotation_results:
            annotation_check = self._check_annotation(
                annotation_results, issues, warnings, recommendations
            )
        
        # 计算总体质量评分
        quality_score = self._calculate_quality_score(
            encoding_check,
            chapter_check,
            segmentation_check,
            annotation_check
        )
        
        # 生成统计信息
        statistics = self._generate_statistics(
            import_result,
            chapter_infos,
            segmentation_results,
            annotation_results
        )
        
        # 生成报告
        report = NovelValidationReport(
            project_name=import_result.project_name,
            validation_time=datetime.now(),
            quality_score=quality_score,
            is_valid=quality_score >= 70.0,
            encoding_check=encoding_check,
            chapter_check=chapter_check,
            segmentation_check=segmentation_check,
            annotation_check=annotation_check,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            statistics=statistics
        )
        
        logger.info(f"✅ 验证完成: 质量评分 {quality_score:.1f}/100")
        logger.info(f"   问题数: {len(issues)}, 警告数: {len(warnings)}")
        
        return report
    
    def _check_encoding(
        self,
        import_result: NovelImportResult,
        issues: List[ValidationIssue],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """检查编码正确性"""
        logger.info("   检查编码正确性...")
        
        # 读取文件内容检查乱码
        invalid_chars = ['�', '\ufffd']
        invalid_count = 0
        
        try:
            with open(import_result.saved_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for char in invalid_chars:
                    invalid_count += content.count(char)
            
            passed = invalid_count == 0
            
            if not passed:
                issues.append(ValidationIssue(
                    severity="error",
                    category="encoding",
                    description=f"检测到 {invalid_count} 个乱码字符",
                    location="novel_content",
                    recommendation="重新导入文件，检查原始文件编码"
                ))
            
            return {
                "passed": passed,
                "invalid_chars_count": invalid_count,
                "encoding": import_result.encoding
            }
            
        except Exception as e:
            logger.error(f"编码检查失败: {e}")
            issues.append(ValidationIssue(
                severity="error",
                category="encoding",
                description=f"无法读取文件: {str(e)}",
                location="novel_file"
            ))
            return {"passed": False, "error": str(e)}
    
    def _check_chapters(
        self,
        chapter_infos: List[ChapterInfo],
        issues: List[ValidationIssue],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """检查章节完整性"""
        logger.info("   检查章节完整性...")
        
        if not chapter_infos:
            issues.append(ValidationIssue(
                severity="error",
                category="chapter",
                description="未检测到任何章节",
                recommendation="检查章节标题格式"
            ))
            return {"passed": False, "total_chapters": 0}
        
        # 检查章节连续性
        chapter_numbers = [ch.number for ch in chapter_infos]
        expected = list(range(1, len(chapter_infos) + 1))
        missing = set(expected) - set(chapter_numbers)
        duplicates = [num for num in chapter_numbers if chapter_numbers.count(num) > 1]
        
        passed = len(missing) == 0 and len(duplicates) == 0
        
        if missing:
            issues.append(ValidationIssue(
                severity="error",
                category="chapter",
                description=f"缺失章节: {sorted(missing)}",
                recommendation="检查章节标题是否完整"
            ))
        
        if duplicates:
            issues.append(ValidationIssue(
                severity="error",
                category="chapter",
                description=f"重复章节: {sorted(set(duplicates))}",
                recommendation="检查章节检测逻辑"
            ))
        
        return {
            "passed": passed,
            "total_chapters": len(chapter_infos),
            "missing_chapters": sorted(missing),
            "duplicate_chapters": sorted(set(duplicates))
        }
    
    def _check_segmentation(
        self,
        segmentation_results: List[ParagraphSegmentationResult],
        issues: List[ValidationIssue],
        warnings: List[str],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """检查分段合理性"""
        logger.info("   检查分段合理性...")
        
        if not segmentation_results:
            return {"passed": True, "message": "无分段结果"}
        
        # 统计ABC类分布
        total_paragraphs = 0
        type_counts = {"A": 0, "B": 0, "C": 0}
        paragraph_counts = []
        
        for seg in segmentation_results:
            total_paragraphs += len(seg.paragraphs)
            paragraph_counts.append(len(seg.paragraphs))
            
            for p in seg.paragraphs:
                type_counts[p.type] = type_counts.get(p.type, 0) + 1
        
        # 计算分布比例
        type_ratios = {t: c / total_paragraphs for t, c in type_counts.items()}
        
        # 检查ABC类分布是否合理
        # 正常范围: A:10-30%, B:60-80%, C:0-10%
        distribution_ok = True
        
        if type_ratios.get("A", 0) < 0.10 or type_ratios.get("A", 0) > 0.30:
            warnings.append(f"A类比例异常: {type_ratios.get('A', 0):.1%} (正常范围: 10%-30%)")
            distribution_ok = False
        
        if type_ratios.get("B", 0) < 0.60 or type_ratios.get("B", 0) > 0.80:
            warnings.append(f"B类比例异常: {type_ratios.get('B', 0):.1%} (正常范围: 60%-80%)")
            distribution_ok = False
        
        if type_ratios.get("C", 0) > 0.10:
            warnings.append(f"C类比例过高: {type_ratios.get('C', 0):.1%} (正常范围: 0%-10%)")
            distribution_ok = False
        
        # 检查过度分段
        avg_paragraphs = sum(paragraph_counts) / len(paragraph_counts)
        max_paragraphs = max(paragraph_counts)
        
        if max_paragraphs > 50:
            chapter_idx = paragraph_counts.index(max_paragraphs) + 1
            issues.append(ValidationIssue(
                severity="warning",
                category="segmentation",
                description=f"第{chapter_idx}章分段数量过多（{max_paragraphs}段）",
                location=f"chapter_{chapter_idx}",
                recommendation="检查分段逻辑，考虑合并相似段落"
            ))
        
        # 生成建议
        if distribution_ok and avg_paragraphs >= 8 and avg_paragraphs <= 15:
            recommendations.append("分段质量优秀，建议保持当前策略")
        elif not distribution_ok:
            recommendations.append("ABC类分布不均，建议review分段Prompt")
        
        return {
            "passed": distribution_ok,
            "total_paragraphs": total_paragraphs,
            "avg_paragraphs_per_chapter": avg_paragraphs,
            "max_paragraphs": max_paragraphs,
            "abc_distribution": type_ratios
        }
    
    def _check_annotation(
        self,
        annotation_results: List[AnnotatedChapter],
        issues: List[ValidationIssue],
        warnings: List[str],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """检查标注合理性"""
        logger.info("   检查标注合理性...")
        
        if not annotation_results:
            return {"passed": True, "message": "无标注结果"}
        
        # 统计事件和设定数量
        total_events = sum(ann.event_timeline.total_events for ann in annotation_results)
        total_settings = sum(ann.setting_library.total_settings for ann in annotation_results)
        
        avg_events = total_events / len(annotation_results)
        avg_settings = total_settings / len(annotation_results)
        
        # 检查是否合理（每章应该有3-15个事件）
        annotation_ok = True
        
        if avg_events < 3:
            warnings.append(f"平均事件数量过少: {avg_events:.1f}/章 (建议>3)")
            annotation_ok = False
        elif avg_events > 15:
            warnings.append(f"平均事件数量过多: {avg_events:.1f}/章 (建议<15)")
            annotation_ok = False
        
        if avg_settings < 1:
            warnings.append(f"平均设定数量过少: {avg_settings:.1f}/章 (建议>1)")
        
        if annotation_ok:
            recommendations.append("标注质量良好，事件和设定数量合理")
        
        return {
            "passed": annotation_ok,
            "total_events": total_events,
            "total_settings": total_settings,
            "avg_events_per_chapter": avg_events,
            "avg_settings_per_chapter": avg_settings
        }
    
    def _calculate_quality_score(
        self,
        encoding_check: Dict,
        chapter_check: Dict,
        segmentation_check: Dict,
        annotation_check: Dict
    ) -> float:
        """计算总体质量评分"""
        scores = {}
        
        # 编码评分
        scores["encoding"] = 100.0 if encoding_check.get("passed") else 0.0
        
        # 章节评分
        scores["chapter"] = 100.0 if chapter_check.get("passed") else 50.0
        
        # 分段评分
        if segmentation_check:
            scores["segmentation"] = 100.0 if segmentation_check.get("passed") else 70.0
        else:
            scores["segmentation"] = 100.0  # 无分段结果，不扣分
        
        # 标注评分
        if annotation_check:
            scores["annotation"] = 100.0 if annotation_check.get("passed") else 70.0
        else:
            scores["annotation"] = 100.0  # 无标注结果，不扣分
        
        # 加权平均
        total_score = sum(
            scores[key] * weight 
            for key, weight in self.quality_weights.items()
        )
        
        return round(total_score, 1)
    
    def _generate_statistics(
        self,
        import_result: NovelImportResult,
        chapter_infos: List[ChapterInfo],
        segmentation_results: List[ParagraphSegmentationResult],
        annotation_results: List[AnnotatedChapter]
    ) -> Dict[str, Any]:
        """生成统计信息"""
        stats = {
            "file_size": import_result.file_size,
            "char_count": import_result.char_count,
            "chapter_count": len(chapter_infos),
        }
        
        if segmentation_results:
            stats["total_paragraphs"] = sum(len(s.paragraphs) for s in segmentation_results)
            stats["avg_paragraphs_per_chapter"] = stats["total_paragraphs"] / len(segmentation_results)
        
        if annotation_results:
            stats["total_events"] = sum(a.event_timeline.total_events for a in annotation_results)
            stats["total_settings"] = sum(a.setting_library.total_settings for a in annotation_results)
        
        return stats
