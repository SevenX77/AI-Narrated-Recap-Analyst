"""
NovelScriptAligner - Novel与Script对齐工具

基于NovelAnnotator的事件/设定标注结果和ScriptSegmenter的分段结果，
进行句子级语义对齐分析。

核心功能：
1. Script片段提取：从Script分段结果中提取片段
2. LLM对齐分析：使用LLM分析每个片段与Novel事件/设定的对应关系
3. 改写策略识别：识别exact、paraphrase、summarize、expand等改写类型
4. 覆盖率统计：计算事件/设定的覆盖率
5. 质量评估：生成对齐质量报告

设计原则：
- 基于Annotation结构（事件+设定），不直接读取Novel原文
- 输入高效：只需事件/设定摘要，可处理长篇Novel
- 输出结构化：提供改写策略、置信度、覆盖率等分析
"""

import logging
import re
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter

from src.core.interfaces import BaseTool
from src.core.schemas_novel import AnnotatedChapter
from src.core.schemas_script import ScriptSegmentationResult
from src.core.schemas_alignment import (
    AlignmentResult,
    ScriptFragmentAlignment,
    EventAlignment,
    SettingAlignment,
    SkippedContent,
    CoverageStatistics,
    RewriteStrategyStatistics,
    AlignmentQualityMetrics,
    AlignmentReport
)
from src.core.llm_client_manager import get_llm_client, get_model_name
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelScriptAligner(BaseTool):
    """
    Novel-Script对齐工具
    
    基于Annotation结构（事件+设定）进行句子级对齐分析。
    
    Args:
        provider: LLM Provider（默认："claude"）
        model: 模型名称（可选，默认使用provider的默认模型）
    
    Returns:
        AlignmentResult: 完整的对齐分析结果
    """
    
    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """初始化对齐工具"""
        self.provider = provider
        self.model = model or get_model_name(provider)
        self.llm_client = get_llm_client(provider)
        
        # 加载Prompt
        self.prompts = load_prompts("novel_script_alignment")
        
        logger.info(f"NovelScriptAligner initialized with {provider}/{self.model}")
    
    def execute(
        self,
        novel_annotation: AnnotatedChapter,
        script_result: ScriptSegmentationResult,
        project_name: str,
        **kwargs
    ) -> AlignmentResult:
        """
        执行Novel-Script对齐分析
        
        Args:
            novel_annotation: Novel章节标注结果（来自NovelAnnotator）
            script_result: Script分段结果（来自ScriptSegmenter）
            project_name: 项目名称
            **kwargs: 其他参数
        
        Returns:
            AlignmentResult: 完整的对齐分析结果
        """
        logger.info("=" * 80)
        logger.info("Starting Novel-Script Alignment")
        logger.info("=" * 80)
        logger.info(f"Project: {project_name}")
        logger.info(f"Novel Chapter: {novel_annotation.chapter_number}")
        logger.info(f"Script Episode: (from result)")
        logger.info(f"Novel Events: {novel_annotation.event_timeline.total_events}")
        logger.info(f"Novel Settings: {novel_annotation.setting_library.total_settings}")
        logger.info(f"Script Segments: {len(script_result.segments)}")
        
        start_time = time.time()
        
        # Step 1: 准备Novel事件和设定文本
        logger.info("\nStep 1: Preparing Novel events and settings")
        events_text = self._prepare_events_text(novel_annotation.event_timeline.events)
        settings_text = self._prepare_settings_text(novel_annotation.setting_library.settings)
        
        # Step 2: 提取Script片段
        logger.info("\nStep 2: Extracting Script fragments")
        script_fragments = self._extract_script_fragments(script_result)
        logger.info(f"  Total fragments: {len(script_fragments)}")
        
        # Step 3: LLM对齐分析
        logger.info("\nStep 3: LLM alignment analysis")
        alignments = self._align_fragments(
            script_fragments,
            events_text,
            settings_text,
            novel_annotation
        )
        
        # Step 4: 计算统计信息
        logger.info("\nStep 4: Computing statistics")
        coverage_stats = self._compute_coverage_stats(
            alignments,
            novel_annotation.event_timeline.events,
            novel_annotation.setting_library.settings
        )
        rewrite_stats = self._compute_rewrite_stats(alignments)
        
        processing_time = time.time() - start_time
        
        # Step 5: 构建结果
        alignment_result = AlignmentResult(
            project_name=project_name,
            novel_chapter_id=f"chpt_{novel_annotation.chapter_number:04d}",
            script_episode_id=kwargs.get("episode_id", "unknown"),
            alignments=alignments,
            coverage_stats=coverage_stats,
            rewrite_stats=rewrite_stats,
            total_fragments=len(script_fragments),
            llm_provider=self.provider,
            llm_model=self.model
        )
        
        logger.info("=" * 80)
        logger.info("Alignment Complete!")
        logger.info("=" * 80)
        logger.info(f"Total fragments: {len(script_fragments)}")
        logger.info(f"Event coverage: {coverage_stats.event_coverage * 100:.1f}%")
        logger.info(f"Setting coverage: {coverage_stats.setting_coverage * 100:.1f}%")
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info("=" * 80)
        
        return alignment_result
    
    def _prepare_events_text(self, events: List[Any]) -> str:
        """准备Novel事件列表文本"""
        events_text = []
        for event in events:
            event_text = f"""【事件{event.event_id}】{event.event_summary}
类型: {event.event_type}类
包含段落: {event.paragraph_indices}
时间: {event.time}
地点: {event.location}"""
            events_text.append(event_text)
        
        return "\n\n".join(events_text)
    
    def _prepare_settings_text(self, settings: List[Any]) -> str:
        """准备Novel设定列表文本"""
        settings_text = []
        for setting in settings:
            setting_text = f"""【设定{setting.setting_id}】{setting.setting_title}
内容: {setting.setting_summary}
段落: {setting.paragraph_index}"""
            settings_text.append(setting_text)
        
        return "\n\n".join(settings_text)
    
    def _extract_script_fragments(
        self,
        script_result: ScriptSegmentationResult
    ) -> List[Dict[str, Any]]:
        """
        从Script分段结果中提取片段
        
        Args:
            script_result: Script分段结果
        
        Returns:
            List[Dict]: Script片段列表
        """
        fragments = []
        
        for idx, segment in enumerate(script_result.segments, 1):
            # 构建时间范围字符串
            time_range = f"{segment.start_time} --> {segment.end_time}"
            
            fragments.append({
                "index": idx,
                "time_range": time_range,
                "content": segment.content,
                "start_time": segment.start_time,
                "end_time": segment.end_time
            })
        
        return fragments
    
    def _align_fragments(
        self,
        fragments: List[Dict[str, Any]],
        events_text: str,
        settings_text: str,
        novel_annotation: AnnotatedChapter
    ) -> List[ScriptFragmentAlignment]:
        """
        使用LLM对齐Script片段
        
        Args:
            fragments: Script片段列表
            events_text: Novel事件文本
            settings_text: Novel设定文本
            novel_annotation: Novel标注结果
        
        Returns:
            List[ScriptFragmentAlignment]: 对齐结果列表
        """
        alignments = []
        
        for fragment in fragments:
            logger.info(f"  Aligning fragment {fragment['index']}/{len(fragments)}")
            logger.info(f"    Time: {fragment['time_range']}")
            logger.info(f"    Content: {fragment['content'][:80]}...")
            
            try:
                # 准备Prompt
                user_prompt = self.prompts['user_template'].format(
                    time_range=fragment['time_range'],
                    script_content=fragment['content'],
                    events_text=events_text,
                    settings_text=settings_text
                )
                
                # 调用LLM
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompts['system']},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                result_text = response.choices[0].message.content.strip()
                
                # 解析LLM输出
                alignment = self._parse_alignment_result(
                    fragment,
                    result_text,
                    novel_annotation
                )
                
                alignments.append(alignment)
                
                # 记录匹配结果
                logger.info(f"    Matched events: {len(alignment.matched_events)}")
                logger.info(f"    Matched settings: {len(alignment.matched_settings)}")
                if alignment.skipped_content:
                    logger.info(f"    Skipped: {len(alignment.skipped_content)}")
            
            except Exception as e:
                logger.error(f"  Error aligning fragment {fragment['index']}: {e}")
                # 创建空对齐结果
                alignment = ScriptFragmentAlignment(
                    fragment_index=fragment['index'],
                    time_range=fragment['time_range'],
                    content=fragment['content'],
                    content_preview=fragment['content'][:100]
                )
                alignments.append(alignment)
        
        return alignments
    
    def _parse_alignment_result(
        self,
        fragment: Dict[str, Any],
        llm_output: str,
        novel_annotation: AnnotatedChapter
    ) -> ScriptFragmentAlignment:
        """
        解析LLM对齐结果
        
        Args:
            fragment: Script片段
            llm_output: LLM输出文本
            novel_annotation: Novel标注结果
        
        Returns:
            ScriptFragmentAlignment: 解析后的对齐结果
        """
        # 初始化结果
        matched_events = []
        matched_settings = []
        skipped_content = []
        
        # 解析匹配的事件
        event_section = self._extract_section(llm_output, "### 1. 匹配的Novel事件", "### 2. 匹配的Novel设定")
        if event_section and "无匹配事件" not in event_section:
            matched_events = self._parse_event_matches(event_section)
        
        # 解析匹配的设定
        setting_section = self._extract_section(llm_output, "### 2. 匹配的Novel设定", "### 3. Script跳过的内容")
        if setting_section and "无匹配设定" not in setting_section:
            matched_settings = self._parse_setting_matches(setting_section)
        
        # 解析跳过的内容
        skip_section = self._extract_section(llm_output, "### 3. Script跳过的内容", None)
        if skip_section and "无明显跳过" not in skip_section:
            skipped_content = self._parse_skipped_content(skip_section)
        
        return ScriptFragmentAlignment(
            fragment_index=fragment['index'],
            time_range=fragment['time_range'],
            content=fragment['content'],
            content_preview=fragment['content'][:100],
            matched_events=matched_events,
            matched_settings=matched_settings,
            skipped_content=skipped_content
        )
    
    def _extract_section(
        self,
        text: str,
        start_marker: str,
        end_marker: Optional[str]
    ) -> str:
        """提取文本中的特定章节"""
        start_pos = text.find(start_marker)
        if start_pos == -1:
            return ""
        
        start_pos += len(start_marker)
        
        if end_marker:
            end_pos = text.find(end_marker, start_pos)
            if end_pos == -1:
                return text[start_pos:].strip()
            return text[start_pos:end_pos].strip()
        else:
            return text[start_pos:].strip()
    
    def _parse_event_matches(self, text: str) -> List[EventAlignment]:
        """解析事件匹配结果"""
        events = []
        
        # 匹配格式：事件ID: 000100001B | 类型: summarize | 置信度: 0.9 | 说明: ...
        pattern = r'事件ID:\s*(\S+)\s*\|\s*类型:\s*(\w+)\s*\|\s*置信度:\s*([\d.]+)\s*\|\s*说明:\s*(.+?)(?=\n事件ID:|\n\n|$)'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            event_id = match.group(1).strip()
            match_type = match.group(2).strip()
            confidence = float(match.group(3).strip())
            explanation = match.group(4).strip()
            
            events.append(EventAlignment(
                event_id=event_id,
                match_type=match_type,
                confidence=confidence,
                explanation=explanation
            ))
        
        return events
    
    def _parse_setting_matches(self, text: str) -> List[SettingAlignment]:
        """解析设定匹配结果"""
        settings = []
        
        # 匹配格式：设定ID: S00010001 | 类型: paraphrase | 置信度: 0.95 | 说明: ...
        pattern = r'设定ID:\s*(\S+)\s*\|\s*类型:\s*(\w+)\s*\|\s*置信度:\s*([\d.]+)\s*\|\s*说明:\s*(.+?)(?=\n设定ID:|\n\n|$)'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            setting_id = match.group(1).strip()
            match_type = match.group(2).strip()
            confidence = float(match.group(3).strip())
            explanation = match.group(4).strip()
            
            settings.append(SettingAlignment(
                setting_id=setting_id,
                match_type=match_type,
                confidence=confidence,
                explanation=explanation
            ))
        
        return settings
    
    def _parse_skipped_content(self, text: str) -> List[SkippedContent]:
        """解析跳过的内容"""
        skipped = []
        
        # 匹配格式：跳过类型: event | ID: 000100003B | 原因: ...
        pattern = r'跳过类型:\s*(\w+)\s*\|\s*ID:\s*(\S+)\s*\|\s*原因:\s*(.+?)(?=\n跳过类型:|\n\n|$)'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            content_type = match.group(1).strip()
            content_id = match.group(2).strip()
            reason = match.group(3).strip()
            
            skipped.append(SkippedContent(
                content_type=content_type,
                content_id=content_id,
                reason=reason
            ))
        
        return skipped
    
    def _compute_coverage_stats(
        self,
        alignments: List[ScriptFragmentAlignment],
        events: List[Any],
        settings: List[Any]
    ) -> CoverageStatistics:
        """计算覆盖率统计"""
        # 收集所有匹配的事件和设定ID
        matched_event_ids = set()
        matched_setting_ids = set()
        
        for alignment in alignments:
            for event_match in alignment.matched_events:
                matched_event_ids.add(event_match.event_id)
            for setting_match in alignment.matched_settings:
                matched_setting_ids.add(setting_match.setting_id)
        
        # 所有事件和设定的ID
        all_event_ids = {e.event_id for e in events}
        all_setting_ids = {s.setting_id for s in settings}
        
        # 未匹配的ID
        unmatched_event_ids = list(all_event_ids - matched_event_ids)
        unmatched_setting_ids = list(all_setting_ids - matched_setting_ids)
        
        return CoverageStatistics(
            total_events=len(events),
            matched_events=len(matched_event_ids),
            event_coverage=len(matched_event_ids) / len(events) if events else 0,
            total_settings=len(settings),
            matched_settings=len(matched_setting_ids),
            setting_coverage=len(matched_setting_ids) / len(settings) if settings else 0,
            matched_event_ids=sorted(list(matched_event_ids)),
            matched_setting_ids=sorted(list(matched_setting_ids)),
            unmatched_event_ids=sorted(unmatched_event_ids),
            unmatched_setting_ids=sorted(unmatched_setting_ids)
        )
    
    def _compute_rewrite_stats(
        self,
        alignments: List[ScriptFragmentAlignment]
    ) -> RewriteStrategyStatistics:
        """计算改写策略统计"""
        match_types = []
        
        for alignment in alignments:
            for event_match in alignment.matched_events:
                match_types.append(event_match.match_type)
            for setting_match in alignment.matched_settings:
                match_types.append(setting_match.match_type)
        
        type_counter = Counter(match_types)
        
        # 找出主要策略
        dominant_strategy = type_counter.most_common(1)[0][0] if type_counter else "none"
        
        return RewriteStrategyStatistics(
            exact_count=type_counter.get("exact", 0),
            paraphrase_count=type_counter.get("paraphrase", 0),
            summarize_count=type_counter.get("summarize", 0),
            expand_count=type_counter.get("expand", 0),
            none_count=type_counter.get("none", 0),
            dominant_strategy=dominant_strategy
        )
    
    def generate_report(
        self,
        alignment_result: AlignmentResult,
        output_path: Optional[Path] = None
    ) -> AlignmentReport:
        """
        生成对齐质量报告
        
        Args:
            alignment_result: 对齐结果
            output_path: 输出路径（可选）
        
        Returns:
            AlignmentReport: 完整的质量报告
        """
        logger.info("Generating alignment quality report")
        
        # 计算质量指标
        quality_metrics = self._compute_quality_metrics(alignment_result.alignments)
        
        # 生成建议
        recommendations = self._generate_recommendations(
            alignment_result,
            quality_metrics
        )
        
        report = AlignmentReport(
            alignment_result=alignment_result,
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
        
        # 如果指定了输出路径，保存报告
        if output_path:
            self._save_report(report, output_path)
        
        return report
    
    def _compute_quality_metrics(
        self,
        alignments: List[ScriptFragmentAlignment]
    ) -> AlignmentQualityMetrics:
        """计算质量指标"""
        all_confidences = []
        high_count = 0
        medium_count = 0
        low_count = 0
        empty_count = 0
        
        for alignment in alignments:
            has_match = False
            
            for event_match in alignment.matched_events:
                all_confidences.append(event_match.confidence)
                has_match = True
                if event_match.confidence > 0.9:
                    high_count += 1
                elif event_match.confidence >= 0.7:
                    medium_count += 1
                else:
                    low_count += 1
            
            for setting_match in alignment.matched_settings:
                all_confidences.append(setting_match.confidence)
                has_match = True
                if setting_match.confidence > 0.9:
                    high_count += 1
                elif setting_match.confidence >= 0.7:
                    medium_count += 1
                else:
                    low_count += 1
            
            if not has_match:
                empty_count += 1
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return AlignmentQualityMetrics(
            avg_confidence=round(avg_confidence, 3),
            high_confidence_count=high_count,
            medium_confidence_count=medium_count,
            low_confidence_count=low_count,
            empty_alignment_count=empty_count
        )
    
    def _generate_recommendations(
        self,
        alignment_result: AlignmentResult,
        quality_metrics: AlignmentQualityMetrics
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 覆盖率建议
        if alignment_result.coverage_stats.event_coverage < 0.8:
            recommendations.append(
                f"事件覆盖率较低（{alignment_result.coverage_stats.event_coverage*100:.1f}%），"
                f"建议检查Script是否遗漏了关键事件"
            )
        
        if alignment_result.coverage_stats.setting_coverage < 0.7:
            recommendations.append(
                f"设定覆盖率较低（{alignment_result.coverage_stats.setting_coverage*100:.1f}%），"
                f"建议检查Script是否充分展示了世界观设定"
            )
        
        # 质量建议
        if quality_metrics.low_confidence_count > quality_metrics.high_confidence_count:
            recommendations.append(
                f"低置信度匹配较多（{quality_metrics.low_confidence_count}个），"
                f"建议人工审核对齐结果"
            )
        
        if quality_metrics.empty_alignment_count > len(alignment_result.alignments) * 0.2:
            recommendations.append(
                f"无匹配的片段较多（{quality_metrics.empty_alignment_count}个），"
                f"可能Script包含大量原创内容"
            )
        
        # 改写策略建议
        if alignment_result.rewrite_stats.summarize_count > alignment_result.rewrite_stats.paraphrase_count * 2:
            recommendations.append(
                f"Script主要采用压缩策略，建议检查是否过度简化关键情节"
            )
        
        if not recommendations:
            recommendations.append("对齐质量良好，覆盖率和置信度均达标")
        
        return recommendations
    
    def _save_report(self, report: AlignmentReport, output_path: Path):
        """保存报告到文件"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Report saved: {json_path}")
        
        # 保存Markdown
        md_path = output_path.with_suffix('.md')
        self._save_markdown_report(report, md_path)
        logger.info(f"Report saved: {md_path}")
    
    def _save_markdown_report(self, report: AlignmentReport, md_path: Path):
        """保存Markdown格式报告"""
        with open(md_path, 'w', encoding='utf-8') as f:
            result = report.alignment_result
            metrics = report.quality_metrics
            
            f.write("# Novel-Script对齐分析报告\n\n")
            
            # 基本信息
            f.write("## 基本信息\n\n")
            f.write(f"- **项目**: {result.project_name}\n")
            f.write(f"- **Novel章节**: {result.novel_chapter_id}\n")
            f.write(f"- **Script集数**: {result.script_episode_id}\n")
            f.write(f"- **分析时间**: {result.aligned_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **使用模型**: {result.llm_provider}/{result.llm_model}\n\n")
            
            # 覆盖率统计
            f.write("## 覆盖率统计\n\n")
            f.write(f"### 事件覆盖率\n\n")
            f.write(f"- 总事件数: {result.coverage_stats.total_events}\n")
            f.write(f"- 已匹配: {result.coverage_stats.matched_events}\n")
            f.write(f"- 覆盖率: {result.coverage_stats.event_coverage*100:.1f}%\n\n")
            
            f.write(f"### 设定覆盖率\n\n")
            f.write(f"- 总设定数: {result.coverage_stats.total_settings}\n")
            f.write(f"- 已匹配: {result.coverage_stats.matched_settings}\n")
            f.write(f"- 覆盖率: {result.coverage_stats.setting_coverage*100:.1f}%\n\n")
            
            # 改写策略统计
            f.write("## 改写策略统计\n\n")
            f.write(f"- **原文保留** (exact): {result.rewrite_stats.exact_count}\n")
            f.write(f"- **改写** (paraphrase): {result.rewrite_stats.paraphrase_count}\n")
            f.write(f"- **压缩** (summarize): {result.rewrite_stats.summarize_count}\n")
            f.write(f"- **扩写** (expand): {result.rewrite_stats.expand_count}\n")
            f.write(f"- **无对应** (none): {result.rewrite_stats.none_count}\n")
            f.write(f"- **主要策略**: {result.rewrite_stats.dominant_strategy}\n\n")
            
            # 质量指标
            f.write("## 质量指标\n\n")
            f.write(f"- 平均置信度: {metrics.avg_confidence:.3f}\n")
            f.write(f"- 高置信度匹配 (>0.9): {metrics.high_confidence_count}\n")
            f.write(f"- 中等置信度匹配 (0.7-0.9): {metrics.medium_confidence_count}\n")
            f.write(f"- 低置信度匹配 (<0.7): {metrics.low_confidence_count}\n")
            f.write(f"- 无匹配片段: {metrics.empty_alignment_count}\n\n")
            
            # 建议
            f.write("## 改进建议\n\n")
            for idx, rec in enumerate(report.recommendations, 1):
                f.write(f"{idx}. {rec}\n")
            f.write("\n")
            
            # 详细对齐结果
            f.write("## 详细对齐结果\n\n")
            for alignment in result.alignments:
                f.write(f"### Script片段 {alignment.fragment_index}\n\n")
                f.write(f"**时间**: `{alignment.time_range}`\n\n")
                f.write(f"**内容预览**: {alignment.content_preview}...\n\n")
                
                if alignment.matched_events:
                    f.write("**匹配事件**:\n\n")
                    for event in alignment.matched_events:
                        f.write(f"- `{event.event_id}` ({event.match_type}, 置信度: {event.confidence})\n")
                        f.write(f"  - {event.explanation}\n")
                    f.write("\n")
                
                if alignment.matched_settings:
                    f.write("**匹配设定**:\n\n")
                    for setting in alignment.matched_settings:
                        f.write(f"- `{setting.setting_id}` ({setting.match_type}, 置信度: {setting.confidence})\n")
                        f.write(f"  - {setting.explanation}\n")
                    f.write("\n")
                
                if alignment.skipped_content:
                    f.write("**跳过内容**:\n\n")
                    for skip in alignment.skipped_content:
                        f.write(f"- {skip.content_type}: `{skip.content_id}` - {skip.reason}\n")
                    f.write("\n")
                
                f.write("---\n\n")
