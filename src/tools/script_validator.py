"""
ScriptValidator - 脚本处理质量验证工具

验证脚本处理的各个环节质量，生成质量报告。
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import re

from src.core.interfaces import BaseTool
from src.core.schemas_script import (
    SrtEntry,
    SrtTextExtractionResult,
    ScriptSegmentationResult,
    ScriptValidationReport,
    ScriptValidationIssue
)

logger = logging.getLogger(__name__)


class ScriptValidator(BaseTool):
    """
    脚本处理质量验证工具
    
    职责 (Responsibility):
        验证脚本处理的各个环节质量，确保数据准确性和合理性。
    
    检查项:
        1. 时间轴连续性: 检查时间跳跃、重叠
        2. 文本完整性: 验证SRT覆盖率
        3. 分段合理性: 分段数量、段落长度
    
    接口 (Interface):
        输入:
            - srt_entries: List[SrtEntry]
            - text_extraction: SrtTextExtractionResult
            - segmentation: ScriptSegmentationResult
        
        输出:
            - ScriptValidationReport: 验证报告
    """
    
    name = "script_validator"
    description = "验证脚本处理质量"
    
    def __init__(self):
        """初始化验证器"""
        super().__init__()
        self.quality_weights = {
            "timeline": 0.3,      # 时间轴权重
            "text": 0.4,          # 文本完整性权重
            "segmentation": 0.3   # 分段合理性权重
        }
    
    def execute(
        self,
        srt_entries: List[SrtEntry],
        text_extraction: SrtTextExtractionResult = None,
        segmentation: ScriptSegmentationResult = None,
        episode_name: str = "ep01",
        **kwargs
    ) -> ScriptValidationReport:
        """
        执行脚本质量验证
        
        Args:
            srt_entries: SRT条目列表
            text_extraction: 文本提取结果（可选）
            segmentation: 分段结果（可选）
            episode_name: 集数名称
        
        Returns:
            ScriptValidationReport: 验证报告
        """
        logger.info(f"🔍 开始验证脚本处理质量: {episode_name}")
        
        issues: List[ScriptValidationIssue] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        
        # 1. 时间轴连续性检查
        timeline_check = self._check_timeline(srt_entries, issues, warnings)
        
        # 2. 文本完整性检查
        text_check = {}
        if text_extraction:
            text_check = self._check_text_completeness(
                srt_entries, text_extraction, issues, warnings
            )
        
        # 3. 分段合理性检查
        segmentation_check = {}
        if segmentation:
            segmentation_check = self._check_segmentation(
                segmentation, srt_entries, issues, warnings, recommendations
            )
        
        # 计算总体质量评分
        quality_score = self._calculate_quality_score(
            timeline_check,
            text_check,
            segmentation_check
        )
        
        # 生成统计信息
        statistics = self._generate_statistics(
            srt_entries, text_extraction, segmentation
        )
        
        # 生成报告
        report = ScriptValidationReport(
            episode_name=episode_name,
            validation_time=datetime.now(),
            quality_score=quality_score,
            is_valid=quality_score >= 70.0,
            timeline_check=timeline_check,
            text_check=text_check,
            segmentation_check=segmentation_check,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            statistics=statistics
        )
        
        logger.info(f"✅ 验证完成: 质量评分 {quality_score:.1f}/100")
        logger.info(f"   问题数: {len(issues)}, 警告数: {len(warnings)}")
        
        return report
    
    def _parse_time(self, time_str: str) -> timedelta:
        """解析SRT时间格式为timedelta"""
        # 格式: HH:MM:SS,mmm
        parts = re.match(r'(\d+):(\d+):(\d+),(\d+)', time_str)
        if parts:
            hours, minutes, seconds, milliseconds = map(int, parts.groups())
            return timedelta(
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                milliseconds=milliseconds
            )
        return timedelta(0)
    
    def _check_timeline(
        self,
        srt_entries: List[SrtEntry],
        issues: List[ScriptValidationIssue],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """检查时间轴连续性"""
        logger.info("   检查时间轴连续性...")
        
        if not srt_entries:
            issues.append(ScriptValidationIssue(
                severity="error",
                category="timeline",
                description="未检测到任何SRT条目",
                recommendation="检查SRT文件格式"
            ))
            return {"passed": False, "total_entries": 0}
        
        gaps = []
        overlaps = []
        
        for i in range(len(srt_entries) - 1):
            current = srt_entries[i]
            next_entry = srt_entries[i + 1]
            
            current_end = self._parse_time(current.end_time)
            next_start = self._parse_time(next_entry.start_time)
            
            # 检查间隔（>1秒为异常）
            gap = (next_start - current_end).total_seconds()
            if gap > 1.0:
                gaps.append({
                    "entries": f"{current.index}-{next_entry.index}",
                    "gap_seconds": round(gap, 2),
                    "time_range": f"{current.end_time} → {next_entry.start_time}"
                })
            
            # 检查重叠
            if next_start < current_end:
                overlaps.append({
                    "entries": f"{current.index}-{next_entry.index}",
                    "overlap_seconds": round((current_end - next_start).total_seconds(), 2),
                    "time_range": f"{next_entry.start_time} → {current.end_time}"
                })
        
        # 添加问题和警告
        if gaps:
            for gap_info in gaps[:3]:  # 只报告前3个
                issues.append(ScriptValidationIssue(
                    severity="warning",
                    category="timeline",
                    description=f"时间轴间隔: {gap_info['time_range']} ({gap_info['gap_seconds']}秒)",
                    location=f"srt_entry_{gap_info['entries']}",
                    recommendation="检查是否存在缺失字幕"
                ))
            if len(gaps) > 3:
                warnings.append(f"共发现 {len(gaps)} 个时间轴间隔")
        
        if overlaps:
            issues.append(ScriptValidationIssue(
                severity="error",
                category="timeline",
                description=f"时间轴重叠: {len(overlaps)} 处",
                recommendation="检查SRT文件时间戳"
            ))
        
        passed = len(gaps) <= 5 and len(overlaps) == 0
        
        return {
            "passed": passed,
            "total_entries": len(srt_entries),
            "gaps": gaps,
            "overlaps": overlaps
        }
    
    def _check_text_completeness(
        self,
        srt_entries: List[SrtEntry],
        text_extraction: SrtTextExtractionResult,
        issues: List[ScriptValidationIssue],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """检查文本完整性"""
        logger.info("   检查文本完整性...")
        
        # 计算原始SRT文本总长度
        srt_text_total = sum(len(e.text) for e in srt_entries)
        
        # 提取后的文本长度
        extracted_text_length = len(text_extraction.processed_text)
        
        # 计算覆盖率
        coverage = extracted_text_length / srt_text_total if srt_text_total > 0 else 0
        
        missing_chars = srt_text_total - extracted_text_length
        
        passed = coverage >= 0.95
        
        if not passed:
            issues.append(ScriptValidationIssue(
                severity="warning",
                category="text",
                description=f"文本覆盖率低: {coverage:.1%} (缺失 {missing_chars} 字符)",
                recommendation="检查文本提取逻辑"
            ))
        
        return {
            "passed": passed,
            "coverage": round(coverage, 3),
            "srt_text_length": srt_text_total,
            "extracted_text_length": extracted_text_length,
            "missing_chars": missing_chars
        }
    
    def _check_segmentation(
        self,
        segmentation: ScriptSegmentationResult,
        srt_entries: List[SrtEntry],
        issues: List[ScriptValidationIssue],
        warnings: List[str],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """检查分段合理性"""
        logger.info("   检查分段合理性...")
        
        total_segments = segmentation.total_segments
        
        # 检查分段数量（5-20段/集为正常范围）
        segments_ok = 5 <= total_segments <= 20
        
        if total_segments < 5:
            warnings.append(f"分段数量过少: {total_segments}段 (建议5-20段)")
        elif total_segments > 20:
            warnings.append(f"分段数量过多: {total_segments}段 (建议5-20段)")
        
        # 计算平均段落时长
        segment_durations = []
        for seg in segmentation.segments:
            start = self._parse_time(seg.start_time)
            end = self._parse_time(seg.end_time)
            duration = (end - start).total_seconds()
            segment_durations.append(duration)
        
        avg_duration = sum(segment_durations) / len(segment_durations) if segment_durations else 0
        
        # 检查是否有异常短或异常长的段落
        short_segments = [i for i, d in enumerate(segment_durations, 1) if d < 10]
        long_segments = [i for i, d in enumerate(segment_durations, 1) if d > 180]
        
        if short_segments:
            warnings.append(f"存在过短段落(<10秒): 段落 {short_segments[:3]}")
        
        if long_segments:
            warnings.append(f"存在过长段落(>3分钟): 段落 {long_segments[:3]}")
        
        # 生成建议
        if segments_ok and len(short_segments) == 0 and len(long_segments) == 0:
            recommendations.append("分段质量优秀，建议保持当前策略")
        
        return {
            "passed": segments_ok,
            "total_segments": total_segments,
            "avg_duration_seconds": round(avg_duration, 1),
            "avg_sentence_count": segmentation.avg_sentence_count,
            "short_segments": short_segments,
            "long_segments": long_segments
        }
    
    def _calculate_quality_score(
        self,
        timeline_check: Dict,
        text_check: Dict,
        segmentation_check: Dict
    ) -> float:
        """计算总体质量评分"""
        scores = {}
        
        # 时间轴评分
        scores["timeline"] = 100.0 if timeline_check.get("passed") else 70.0
        
        # 文本完整性评分
        if text_check:
            coverage = text_check.get("coverage", 0)
            scores["text"] = coverage * 100
        else:
            scores["text"] = 100.0  # 无文本提取结果，不扣分
        
        # 分段评分
        if segmentation_check:
            scores["segmentation"] = 100.0 if segmentation_check.get("passed") else 80.0
        else:
            scores["segmentation"] = 100.0  # 无分段结果，不扣分
        
        # 加权平均
        total_score = sum(
            scores[key] * weight 
            for key, weight in self.quality_weights.items()
        )
        
        return round(total_score, 1)
    
    def _generate_statistics(
        self,
        srt_entries: List[SrtEntry],
        text_extraction: SrtTextExtractionResult,
        segmentation: ScriptSegmentationResult
    ) -> Dict[str, Any]:
        """生成统计信息"""
        stats = {
            "total_srt_entries": len(srt_entries),
        }
        
        if srt_entries:
            total_duration = self._parse_time(srt_entries[-1].end_time)
            stats["total_duration_seconds"] = total_duration.total_seconds()
            stats["total_duration_formatted"] = str(total_duration)
        
        if text_extraction:
            stats["text_length"] = len(text_extraction.processed_text)
        
        if segmentation:
            stats["total_segments"] = segmentation.total_segments
            stats["avg_sentence_count"] = segmentation.avg_sentence_count
        
        return stats
