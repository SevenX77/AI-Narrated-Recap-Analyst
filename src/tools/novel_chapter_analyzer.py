"""
Novel Chapter Functional Analyzer
小说章节功能段分析工具 - 使用LLM进行叙事功能级别的分段和标注
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from openai import OpenAI

from src.core.interfaces import BaseTool
from src.core.config import config
from src.core.schemas_novel_analysis import (
    ChapterFunctionalAnalysis,
    FunctionalSegment,
    ChapterSummary,
    ChapterStructureInsight
)
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class NovelChapterAnalyzer(BaseTool):
    """
    小说章节功能段分析工具
    
    功能：
    1. 使用LLM按叙事功能将章节分段（功能段级别，非自然段）
    2. 为每个功能段标注多维度标签（叙事功能、结构、角色、优先级）
    3. 提供浓缩建议
    4. 生成章节摘要和结构洞察
    5. 输出Markdown和JSON两种格式
    
    与 NovelSegmentationAnalyzer 的区别：
    - NovelSegmentationAnalyzer：自然段级别（24个段落/章），适合精确对齐
    - NovelChapterAnalyzer：功能段级别（11个段落/章），适合人类理解
    """
    
    name = "novel_chapter_analyzer"
    description = "Analyze novel chapters by narrative function (functional segments)"
    
    def __init__(self):
        """初始化工具"""
        self.llm_client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url
        )
        self.prompt_config = load_prompts("novel_chapter_functional_analysis")
        logger.info(f"Initialized {self.name} with model: {config.llm.model}")
    
    def execute(self,
                chapter_content: str,
                chapter_number: int,
                chapter_title: str,
                novel_title: str = "",
                known_characters: List[str] = None,
                known_world_settings: Dict[str, str] = None,
                previous_foreshadowing: List[str] = None) -> ChapterFunctionalAnalysis:
        """
        执行章节功能段分析
        
        Args:
            chapter_content: 章节原文内容
            chapter_number: 章节序号
            chapter_title: 章节标题
            novel_title: 小说标题
            known_characters: 已知角色列表（可选，用于上下文）
            known_world_settings: 已知世界观设定（可选）
            previous_foreshadowing: 前文伏笔列表（可选）
        
        Returns:
            ChapterFunctionalAnalysis: 章节功能段分析结果
        """
        logger.info(f"Starting functional analysis for Chapter {chapter_number}: {chapter_title}")
        
        # 1. 准备上下文
        context = self._prepare_context(
            known_characters or [],
            known_world_settings or {},
            previous_foreshadowing or []
        )
        
        # 2. 构建Prompt
        prompt = self._build_prompt(
            novel_title=novel_title,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            **context
        )
        
        # 3. 调用LLM（支持V3 -> R1 fallback）
        logger.info("Calling LLM for functional analysis...")
        analysis_result, used_model = self._call_llm_with_fallback(prompt)
        
        # 4. 解析结果
        try:
            chapter_analysis = self._parse_result(analysis_result, chapter_number)
            logger.info(f"Analysis successful with {used_model}: {len(chapter_analysis.segments)} functional segments")
            return chapter_analysis
        except Exception as e:
            logger.error(f"Failed to parse LLM result for chapter {chapter_number}: {e}")
            raise RuntimeError(f"Result parsing failed: {e}")
    
    def _prepare_context(self,
                        known_characters: List[str],
                        known_world_settings: Dict[str, str],
                        previous_foreshadowing: List[str]) -> Dict[str, str]:
        """准备上下文信息"""
        return {
            "known_characters": ", ".join(known_characters) if known_characters else "无",
            "known_world_settings": json.dumps(known_world_settings, ensure_ascii=False) if known_world_settings else "无",
            "previous_foreshadowing": ", ".join(previous_foreshadowing) if previous_foreshadowing else "无"
        }
    
    def _build_prompt(self,
                     novel_title: str,
                     chapter_number: int,
                     chapter_title: str,
                     chapter_content: str,
                     **context) -> str:
        """构建LLM Prompt"""
        system_prompt = self.prompt_config.get("novel_chapter_functional_analysis", {}).get("system", "")
        user_template = self.prompt_config.get("novel_chapter_functional_analysis", {}).get("user", "")
        
        user_prompt = user_template.format(
            novel_title=novel_title or "未知",
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            chapter_id=f"{chapter_number:04d}",
            **context
        )
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def _call_llm_with_fallback(self, prompt: str) -> tuple[str, str]:
        """
        调用LLM进行分析，支持多提供商和fallback
        
        - Claude: 直接调用，无fallback
        - DeepSeek: 支持 V3 -> R1 fallback
        
        Returns:
            tuple: (LLM输出, 使用的模型名称)
        """
        # 如果是 Claude，直接调用（不使用 fallback 逻辑）
        if config.llm.provider == "claude":
            return self._call_claude_model(prompt)
        
        # DeepSeek: 使用双模型逻辑
        # 尝试主模型 (R1)
        try:
            logger.info(f"Trying primary model: {config.llm.primary_model}")
            response = self.llm_client.chat.completions.create(
                model=config.llm.primary_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,  # R1 推荐使用 1.0
                max_tokens=8000
            )
            result = response.choices[0].message.content
            
            # 验证结果（检查是否过度聚合）
            if config.llm.enable_fallback and config.llm.fallback_on_validation_fail:
                if self._should_fallback(result):
                    logger.warning(f"Primary model result failed validation, falling back to {config.llm.fallback_model}")
                    return self._call_fallback_model(prompt)
            
            return result, config.llm.primary_model
            
        except Exception as e:
            logger.error(f"Primary model ({config.llm.primary_model}) failed: {e}")
            
            if config.llm.enable_fallback and config.llm.fallback_on_error:
                logger.info(f"Falling back to {config.llm.fallback_model}")
                return self._call_fallback_model(prompt)
            else:
                raise RuntimeError(f"LLM API error: {e}")
    
    def _call_claude_model(self, prompt: str) -> tuple[str, str]:
        """调用 Claude 模型"""
        try:
            logger.info(f"Calling Claude model: {config.llm.model_name}")
            response = self.llm_client.chat.completions.create(
                model=config.llm.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=config.llm.claude_temperature,
                max_tokens=config.llm.claude_max_tokens
            )
            
            result = response.choices[0].message.content
            logger.info(f"Claude response received: {len(result)} characters")
            
            return result, config.llm.model_name
            
        except Exception as e:
            logger.error(f"Claude model ({config.llm.model_name}) failed: {e}")
            raise RuntimeError(f"Claude API error: {e}")
    
    def _call_fallback_model(self, prompt: str) -> tuple[str, str]:
        """调用 fallback 模型 (R1)"""
        try:
            response = self.llm_client.chat.completions.create(
                model=config.llm.fallback_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,  # R1 推荐使用 1.0
                max_tokens=8000
            )
            
            # R1 返回推理过程和最终内容
            if hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning = response.choices[0].message.reasoning_content
                logger.info(f"R1 reasoning: {reasoning[:200]}...")
            
            return response.choices[0].message.content, config.llm.fallback_model
            
        except Exception as e:
            logger.error(f"Fallback model ({config.llm.fallback_model}) also failed: {e}")
            raise RuntimeError(f"Both primary and fallback models failed: {e}")
    
    def _should_fallback(self, llm_output: str) -> bool:
        """
        判断是否应该fallback到R1
        
        检查V3的输出是否有明显问题：
        1. 段落1字数 < 120 (只有广播，没有反应)
        2. 段落1字数 > 400 (过度聚合)
        3. JSON解析失败
        """
        try:
            # 尝试提取第一个段落的字数
            if "```json" in llm_output:
                json_text = llm_output.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_output:
                json_text = llm_output.split("```")[1].split("```")[0].strip()
            else:
                json_text = llm_output
            
            data = json.loads(json_text)
            segments = data.get("segments", [])
            
            if segments:
                first_seg_word_count = segments[0].get("metadata", {}).get("word_count", 0)
                
                # 段落1字数异常
                if first_seg_word_count < 120:
                    logger.warning(f"First segment too short: {first_seg_word_count} < 120")
                    return True
                if first_seg_word_count > 400:
                    logger.warning(f"First segment too long: {first_seg_word_count} > 400 (over-aggregation)")
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Validation check failed: {e}, will not fallback")
            return False
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM进行分析（旧接口，保留兼容性）"""
        result, _ = self._call_llm_with_fallback(prompt)
        return result
    
    def _parse_result(self, llm_output: str, chapter_number: int) -> ChapterFunctionalAnalysis:
        """解析LLM输出的JSON结果"""
        # 提取JSON内容（可能被包裹在```json```中）
        json_text = llm_output
        if "```json" in llm_output:
            json_text = llm_output.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_output:
            json_text = llm_output.split("```")[1].split("```")[0].strip()
        
        # 解析JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"LLM output: {llm_output[:500]}...")
            raise ValueError(f"Invalid JSON output from LLM: {e}")
        
        # 构建Pydantic模型
        try:
            return ChapterFunctionalAnalysis(**data)
        except Exception as e:
            logger.error(f"Pydantic validation error: {e}")
            raise ValueError(f"Failed to validate analysis result: {e}")
    
    def save_markdown(self,
                     analysis: ChapterFunctionalAnalysis,
                     output_path: Path) -> Path:
        """
        将分析结果保存为Markdown格式
        
        Args:
            analysis: 章节分析结果
            output_path: 输出文件路径
        
        Returns:
            保存的文件路径
        """
        logger.info(f"Saving Markdown to {output_path}")
        
        markdown_content = self._generate_markdown(analysis)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown saved successfully")
        return output_path
    
    def save_json(self,
                 analysis: ChapterFunctionalAnalysis,
                 output_path: Path) -> Path:
        """
        将分析结果保存为JSON格式
        
        Args:
            analysis: 章节分析结果
            output_path: 输出文件路径
        
        Returns:
            保存的文件路径
        """
        logger.info(f"Saving JSON to {output_path}")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON saved successfully")
        return output_path
    
    def _generate_markdown(self, analysis: ChapterFunctionalAnalysis) -> str:
        """生成Markdown格式的分析报告"""
        md = []
        
        # 标题和元信息
        md.append(f"# 第{analysis.chapter_number}章完整分段分析\n")
        md.append(f"> **章节**: 第{analysis.chapter_number}章 - {analysis.chapter_title}")
        md.append(f"> **分析方法**: [小说叙事分段分析方法论](../../../../docs/NOVEL_SEGMENTATION_METHODOLOGY.md)")
        md.append(f"> **分析日期**: {analysis.analyzed_at.strftime('%Y-%m-%d')}")
        md.append(f"> **分析版本**: {analysis.version}\n")
        md.append("---\n")
        
        # 各功能段
        for i, seg in enumerate(analysis.segments, 1):
            md.append(f"## {seg.title}\n")
            md.append("```")
            md.append(seg.content)
            md.append("```\n")
            
            # 叙事功能
            md.append("**[叙事功能]**")
            for func in seg.tags.narrative_function:
                md.append(f"- {func}")
            md.append("")
            
            # 叙事结构
            if seg.tags.structure:
                md.append("**[叙事结构]**")
                for struct in seg.tags.structure:
                    md.append(f"- {struct}")
                md.append("")
            
            # 角色与关系
            if seg.tags.character:
                md.append("**[角色与关系]**")
                for char in seg.tags.character:
                    md.append(f"- {char}")
                md.append("")
            
            # 浓缩优先级
            md.append("**[浓缩优先级]**")
            md.append(f"- {seg.tags.priority}")
            md.append("")
            
            # 浓缩建议
            md.append("**[浓缩建议]**")
            md.append(f"- {seg.condensation_suggestion}")
            md.append("")
            
            # 时空
            if seg.tags.location or seg.tags.time:
                md.append("**[时空]**")
                if seg.tags.location:
                    md.append(f"- 地点：{seg.tags.location}")
                if seg.tags.time:
                    md.append(f"- 时间：{seg.tags.time}")
                md.append("")
            
            # 元数据
            if seg.metadata.contains_first_appearance or seg.metadata.repetition_items or seg.metadata.foreshadowing:
                md.append("**[元数据]**")
                if seg.metadata.contains_first_appearance:
                    md.append("- 包含首次出现的设定/道具")
                if seg.metadata.repetition_items:
                    md.append(f"- 重复强调：{', '.join(seg.metadata.repetition_items)}")
                if seg.metadata.foreshadowing:
                    fh = seg.metadata.foreshadowing
                    md.append(f"- 伏笔：{fh.get('type', '')} - {fh.get('content', '')}")
                md.append("")
            
            md.append("---\n")
        
        # 章节整体分析
        md.append(f"## 📊 第{analysis.chapter_number}章整体分析\n")
        
        # 核心功能统计
        md.append("### 核心功能统计\n")
        md.append("| 功能类型 | 数量 | 关键段落 |")
        md.append("|---------|------|---------|")
        
        story_segments = [s.segment_id for s in analysis.segments if "故事推进" in s.tags.narrative_function]
        md.append(f"| **故事推进** | {len(story_segments)}次 | {', '.join(story_segments[:3])}{'...' if len(story_segments) > 3 else ''} |")
        
        first_appearance_segments = [s.segment_id for s in analysis.segments if s.metadata.contains_first_appearance]
        md.append(f"| **核心设定（首次）** | {len(first_appearance_segments)}项 | {', '.join(first_appearance_segments[:3])}{'...' if len(first_appearance_segments) > 3 else ''} |")
        
        md.append("")
        
        # 优先级分布
        md.append("### 优先级分布\n")
        md.append(f"- **P0-骨架**（{analysis.chapter_summary.p0_count}处）：{', '.join(analysis.chapter_summary.key_events)}")
        md.append(f"- **P1-血肉**（{analysis.chapter_summary.p1_count}处）：重要细节")
        md.append(f"- **P2-皮肤**（{analysis.chapter_summary.p2_count}处）：氛围渲染\n")
        
        # 时空轨迹
        locations = [s.tags.location for s in analysis.segments if s.tags.location]
        times = [s.tags.time for s in analysis.segments if s.tags.time]
        if locations or times:
            md.append("### 时空轨迹\n")
            md.append("```")
            if times:
                md.append(" → ".join(times[:3]) + ("..." if len(times) > 3 else ""))
            if locations:
                md.append(" → ".join(locations[:3]) + ("..." if len(locations) > 3 else ""))
            md.append("```\n")
        
        # 结构特点
        if analysis.structure_insight.opening_style:
            md.append("### 结构特点\n")
            if analysis.structure_insight.opening_style:
                md.append(f"1. **开篇方式**：{analysis.structure_insight.opening_style}")
            if analysis.structure_insight.turning_point:
                md.append(f"2. **转折点**：{analysis.structure_insight.turning_point}")
            if analysis.structure_insight.climax:
                md.append(f"3. **高潮**：{analysis.structure_insight.climax}")
            if analysis.structure_insight.ending_hook:
                md.append(f"4. **章节钩子**：{analysis.structure_insight.ending_hook}")
            md.append("")
        
        # 浓缩建议
        if analysis.chapter_summary.condensed_version:
            md.append("### 浓缩建议（500字版本）\n")
            md.append("```")
            md.append(analysis.chapter_summary.condensed_version)
            md.append("```\n")
        
        # 方法论验证
        if analysis.methodology_notes:
            md.append("---\n")
            md.append("## 🎯 方法论验证\n")
            for note in analysis.methodology_notes:
                md.append(f"✅ {note}")
            md.append("")
        
        # 分析完成信息
        md.append("---\n")
        md.append(f"**分析完成时间**: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**分析版本**: {analysis.version}")
        md.append(f"**下一步**: 分析第{analysis.chapter_number + 1}章，验证伏笔回收情况\n")
        
        return "\n".join(md)
