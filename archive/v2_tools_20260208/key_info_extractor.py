"""
Key Info Extractor Tool
关键信息提取工具

从多个章节的分段分析中提取和汇总关键信息，用于指导Script改写。
"""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from src.core.interfaces import BaseTool
from src.core.schemas_segmentation import (
    ChapterAnalysis,
    NovelKeyInfo,
    NovelSegment
)

logger = logging.getLogger(__name__)


class KeyInfoExtractor(BaseTool):
    """
    关键信息提取工具
    
    从章节分段分析中提取：
    1. P0/P1/P2分级信息
    2. 伏笔映射表
    3. 角色弧光
    4. 浓缩指导原则
    
    输出NovelKeyInfo，供Writer Agent使用。
    """
    
    name = "key_info_extractor"
    description = "Extract key information from novel chapter analyses"
    
    def execute(
        self,
        chapter_analyses: List[ChapterAnalysis],
        scope: str
    ) -> NovelKeyInfo:
        """
        执行关键信息提取
        
        Args:
            chapter_analyses: 章节分析结果列表
            scope: 范围标识（如 "ep01", "chpt_0001-0010"）
        
        Returns:
            NovelKeyInfo: 关键信息汇总
        
        Raises:
            ValueError: 当输入参数无效时
        """
        if not chapter_analyses:
            raise ValueError("chapter_analyses cannot be empty")
        
        logger.info(f"Extracting key info for scope: {scope}")
        logger.info(f"Processing {len(chapter_analyses)} chapters")
        
        # 1. 提取P0/P1/P2信息
        p0_skeleton = self._extract_priority_info(chapter_analyses, "P0-骨架")
        p1_flesh = self._extract_priority_info(chapter_analyses, "P1-血肉")
        p2_skin = self._extract_priority_info(chapter_analyses, "P2-皮肤")
        
        logger.info(f"Extracted: {len(p0_skeleton)} P0, {len(p1_flesh)} P1, {len(p2_skin)} P2")
        
        # 2. 构建伏笔映射表
        foreshadowing_map = self._build_foreshadowing_map(chapter_analyses)
        logger.info(f"Foreshadowing: {len(foreshadowing_map.get('planted', []))} planted, "
                   f"{len(foreshadowing_map.get('resolved', []))} resolved")
        
        # 3. 提取角色弧光
        character_arcs = self._extract_character_arcs(chapter_analyses)
        logger.info(f"Characters: {len(character_arcs)}")
        
        # 4. 生成浓缩指导原则
        condensation_guidelines = self._generate_guidelines(chapter_analyses)
        
        # 5. 构建NovelKeyInfo
        key_info = NovelKeyInfo(
            scope=scope,
            p0_skeleton=p0_skeleton,
            p1_flesh=p1_flesh,
            p2_skin=p2_skin,
            foreshadowing_map=foreshadowing_map,
            character_arcs=character_arcs,
            condensation_guidelines=condensation_guidelines
        )
        
        logger.info(f"Key info extraction completed for {scope}")
        return key_info
    
    def _extract_priority_info(
        self,
        chapters: List[ChapterAnalysis],
        priority: str
    ) -> List[Dict[str, Any]]:
        """提取指定优先级的信息"""
        priority_info = []
        
        for chapter in chapters:
            for segment in chapter.segments:
                if segment.tags.priority == priority:
                    info = {
                        "segment_id": segment.segment_id,
                        "chapter_id": chapter.chapter_id,
                        "content": segment.text[:100] + "..." if len(segment.text) > 100 else segment.text,
                        "full_content": segment.text,
                        "importance": self._extract_importance(segment),
                        "must_include_reason": segment.metadata.condensation_suggestion,
                        "tags": {
                            "narrative_function": segment.tags.narrative_function,
                            "structure": segment.tags.structure,
                            "character": segment.tags.character
                        },
                        "is_first_appearance": segment.metadata.is_first_appearance,
                        "word_count": segment.metadata.word_count
                    }
                    priority_info.append(info)
        
        return priority_info
    
    def _extract_importance(self, segment: NovelSegment) -> str:
        """提取重要性描述"""
        # 基于标签推断重要性
        tags = segment.tags
        
        if "核心故事设定(首次)" in tags.narrative_function:
            return "核心机制首次出现"
        elif "关键道具(首次)" in tags.narrative_function:
            return "关键道具首次登场"
        elif "钩子-悬念制造" in tags.structure:
            return "悬念制造点"
        elif "故事推进" in tags.narrative_function:
            return "情节推进"
        elif tags.character:
            return f"角色发展: {', '.join(tags.character)}"
        else:
            return "重要内容"
    
    def _build_foreshadowing_map(
        self,
        chapters: List[ChapterAnalysis]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """构建伏笔映射表"""
        foreshadowing_map = {
            "planted": [],      # 埋设的伏笔
            "resolved": [],     # 回收的伏笔
            "strengthened": [], # 强化的伏笔
            "responded": []     # 回应的伏笔
        }
        
        for chapter in chapters:
            for segment in chapter.segments:
                if segment.metadata.foreshadowing:
                    foreshadowing = segment.metadata.foreshadowing
                    info = {
                        "segment_id": segment.segment_id,
                        "chapter_id": chapter.chapter_id,
                        "content": foreshadowing.content,
                        "context": segment.text[:100] + "...",
                        "reference_id": foreshadowing.reference_id,
                        "resolution_chapter": foreshadowing.resolution_chapter
                    }
                    
                    if foreshadowing.type == "埋设":
                        foreshadowing_map["planted"].append(info)
                    elif foreshadowing.type == "回收":
                        foreshadowing_map["resolved"].append(info)
                    elif foreshadowing.type == "强化":
                        foreshadowing_map["strengthened"].append(info)
                    elif foreshadowing.type == "回应":
                        foreshadowing_map["responded"].append(info)
        
        return foreshadowing_map
    
    def _extract_character_arcs(
        self,
        chapters: List[ChapterAnalysis]
    ) -> Dict[str, Dict[str, Any]]:
        """提取角色弧光"""
        character_data = defaultdict(lambda: {
            "appearances": [],
            "key_moments": [],
            "relationships": [],
            "personality_tags": set()
        })
        
        # 收集角色信息
        for chapter in chapters:
            # 从摘要中获取首次登场的角色
            for char_name in chapter.chapter_summary.characters_introduced:
                if "initial_state" not in character_data[char_name]:
                    # 找到该角色首次登场的段落
                    for seg in chapter.segments:
                        if any(char_name in tag for tag in seg.tags.character):
                            character_data[char_name]["initial_state"] = seg.text[:50] + "..."
                            break
            
            # 收集角色的关键时刻
            for segment in chapter.segments:
                for char_tag in segment.tags.character:
                    # 解析角色标签（格式：人物塑造-角色名）
                    if "人物塑造-" in char_tag:
                        char_name = char_tag.replace("人物塑造-", "")
                        character_data[char_name]["appearances"].append(segment.segment_id)
                        
                        # 如果是关键情节，记录为key_moment
                        if segment.tags.priority == "P0-骨架":
                            character_data[char_name]["key_moments"].append({
                                "segment_id": segment.segment_id,
                                "description": segment.text[:50] + "...",
                                "chapter": chapter.chapter_id
                            })
                    
                    # 收集关系信息
                    if "对立关系-" in char_tag or "同盟关系-" in char_tag:
                        character_data[char_tag.split("-")[1]]["relationships"].append(char_tag)
        
        # 转换为标准格式
        character_arcs = {}
        for char_name, data in character_data.items():
            character_arcs[char_name] = {
                "initial_state": data.get("initial_state", "未知"),
                "key_moments": data["key_moments"],
                "relationships": list(set(data["relationships"])),
                "personality_tags": list(data["personality_tags"]),
                "appearance_count": len(data["appearances"])
            }
        
        return character_arcs
    
    def _generate_guidelines(
        self,
        chapters: List[ChapterAnalysis]
    ) -> Dict[str, List[str]]:
        """生成浓缩指导原则"""
        guidelines = {
            "must_retain": [],
            "can_simplify": [],
            "can_omit": []
        }
        
        # 统计不同类型的内容
        narrative_functions = defaultdict(int)
        structures = defaultdict(int)
        priorities = defaultdict(int)
        
        for chapter in chapters:
            for segment in chapter.segments:
                # 统计叙事功能
                for func in segment.tags.narrative_function:
                    narrative_functions[func] += 1
                
                # 统计叙事结构
                for struct in segment.tags.structure:
                    structures[struct] += 1
                
                # 统计优先级
                priorities[segment.tags.priority] += 1
        
        # 生成必须保留的内容
        must_retain_functions = ["核心故事设定(首次)", "关键道具(首次)", "故事推进"]
        must_retain_structures = ["钩子-悬念制造", "伏笔", "回应伏笔"]
        
        for func in must_retain_functions:
            if func in narrative_functions and narrative_functions[func] > 0:
                guidelines["must_retain"].append(func)
        
        for struct in must_retain_structures:
            if struct in structures and structures[struct] > 0:
                guidelines["must_retain"].append(struct)
        
        # 可以简化的内容
        can_simplify = ["背景交代", "关键信息", "重复强调"]
        for func in can_simplify:
            if func in narrative_functions and narrative_functions[func] > 0:
                guidelines["can_simplify"].append(func)
        
        # 可以省略的内容
        if priorities["P2-皮肤"] > 0:
            guidelines["can_omit"].append("P2-皮肤（氛围渲染、心理描写）")
        
        # 添加通用原则
        guidelines["must_retain"].insert(0, "所有P0-骨架内容")
        guidelines["can_simplify"].append("P1-血肉（重要细节，根据篇幅选择性保留）")
        
        return guidelines
    
    def validate_inputs(
        self,
        chapter_analyses: List[ChapterAnalysis],
        scope: str,
        **kwargs
    ) -> bool:
        """验证输入参数"""
        if not chapter_analyses:
            logger.error("chapter_analyses is empty")
            return False
        
        if not scope or not scope.strip():
            logger.error("scope is empty")
            return False
        
        return True


# 导出
__all__ = ["KeyInfoExtractor"]
