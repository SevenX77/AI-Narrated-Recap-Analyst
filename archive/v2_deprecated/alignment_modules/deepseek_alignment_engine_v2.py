"""
DeepSeek对齐引擎 v2 - 基于两级匹配策略

新的三层数据模型：Sentence -> SemanticBlock -> Event
两级匹配策略：Event级粗匹配 + SemanticBlock链细验证
"""

import json
import re
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from src.core.schemas import (
    Sentence, SemanticBlock, Event, EventAlignment,
    BlockChainValidation, TimeRange, AlignmentQualityReport
)
from src.utils.logger import logger
from src.utils.prompt_loader import load_prompts
from src.modules.alignment.hook_detector import HookDetector
from .alignment_engine import AlignmentEngine


class DeepSeekAlignmentEngineV2(AlignmentEngine):
    """
    DeepSeek对齐引擎 v2
    
    实现新的两级匹配策略：
    1. Level 1: Event级粗匹配（快速定位候选）
    2. Level 2: SemanticBlock链细验证（精确确认）
    """
    
    def __init__(self, client=None, model_name: str = "deepseek-chat"):
        super().__init__(client, model_name)
        self.prompts = load_prompts("alignment")
        self.hook_detector = HookDetector(client, model_name)
        self.semaphore = asyncio.Semaphore(5)  # 并发控制
        self.last_hook_result = None  # 保存最后一次Hook检测结果
    
    # ==================== Step 1: 文本预处理 ====================
    
    async def restore_sentences_from_srt_async(self, srt_blocks: List[Dict]) -> List[Sentence]:
        """
        将SRT字幕块还原为完整句子（异步版本）
        
        Args:
            srt_blocks: SRT块列表，每个块包含 {index, start, end, text}
            
        Returns:
            List[Sentence]: 句子列表
        """
        logger.info(f"📝 还原SRT句子: {len(srt_blocks)} blocks")
        logger.info(f"   → 调用LLM进行句子还原...")
        
        # 格式化SRT blocks为文本
        srt_text = self._format_srt_blocks(srt_blocks)
        
        # 构造prompt
        system_prompt = self.prompts["srt_sentence_restoration"]["system"]
        user_prompt = self.prompts["srt_sentence_restoration"]["user"].format(
            srt_blocks=srt_text
        )
        
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as json_err:
                logger.error(f"❌ SRT句子还原 - JSON解析失败")
                logger.error(f"   错误类型: {type(json_err).__name__}")
                logger.error(f"   错误信息: {json_err}")
                logger.error(f"   错误位置: line {json_err.lineno}, column {json_err.colno}")
                logger.error(f"   LLM返回内容长度: {len(content)} 字符")
                logger.error(f"   LLM返回内容前500字符:")
                logger.error(f"   {content[:500]}")
                logger.error(f"   LLM返回内容后500字符:")
                logger.error(f"   {content[-500:]}")
                logger.warning(f"   → 使用降级方案：每个SRT块作为一个句子")
                return self._fallback_srt_to_sentences(srt_blocks)
            
            # 解析为Sentence对象
            sentences_list = data.get("sentences", data) if isinstance(data, dict) else data
            
            if not isinstance(sentences_list, list):
                logger.error(f"❌ SRT句子还原 - 返回数据格式错误")
                logger.error(f"   期望: list")
                logger.error(f"   实际: {type(sentences_list).__name__}")
                logger.error(f"   数据内容: {sentences_list}")
                logger.warning(f"   → 使用降级方案：每个SRT块作为一个句子")
                return self._fallback_srt_to_sentences(srt_blocks)
            
            sentences = []
            
            for idx, item in enumerate(sentences_list):
                try:
                    time_range = None
                    if "time_range" in item:
                        time_range = TimeRange(**item["time_range"])
                    
                    sentences.append(Sentence(
                        text=item["text"],
                        time_range=time_range,
                        index=item.get("index", len(sentences))
                    ))
                except Exception as item_err:
                    logger.error(f"❌ 解析第 {idx+1} 个句子失败")
                    logger.error(f"   错误: {item_err}")
                    logger.error(f"   数据: {item}")
                    # 继续处理下一个
                    continue
            
            if not sentences:
                logger.error(f"❌ SRT句子还原 - 未成功解析任何句子")
                logger.warning(f"   → 使用降级方案：每个SRT块作为一个句子")
                return self._fallback_srt_to_sentences(srt_blocks)
            
            logger.info(f"✅ 还原完成: {len(sentences)} 句子")
            return sentences
            
        except Exception as e:
            logger.error(f"❌ SRT句子还原失败 - 未预期的错误")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            import traceback
            logger.error(f"   堆栈追踪:\n{traceback.format_exc()}")
            logger.warning(f"   → 使用降级方案：每个SRT块作为一个句子")
            # 降级：每个SRT块作为一个句子
            return self._fallback_srt_to_sentences(srt_blocks)
    
    def restore_sentences_from_novel(self, novel_text: str, chapter_id: str) -> List[Sentence]:
        """
        将小说文本分割为句子
        
        Args:
            novel_text: 小说文本
            chapter_id: 章节ID
            
        Returns:
            List[Sentence]: 句子列表
        """
        # 简单实现：按句号、问号、感叹号分割
        sentences = []
        pattern = r'([^。！？]+[。！？])'
        matches = re.findall(pattern, novel_text)
        
        for i, text in enumerate(matches):
            if text.strip():
                sentences.append(Sentence(
                    text=text.strip(),
                    time_range=None,
                    index=i
                ))
        
        logger.info(f"📖 小说句子分割: {chapter_id} -> {len(sentences)} 句子")
        return sentences
    
    def _format_srt_blocks(self, srt_blocks: List[Dict]) -> str:
        """格式化SRT blocks为可读文本"""
        lines = []
        for block in srt_blocks:
            lines.append(f"[{block['start']} --> {block['end']}]")
            lines.append(f"{block['text']}")
            lines.append("")
        return "\n".join(lines)
    
    def _fallback_srt_to_sentences(self, srt_blocks: List[Dict]) -> List[Sentence]:
        """降级方案：每个SRT块作为一个句子"""
        sentences = []
        for i, block in enumerate(srt_blocks):
            sentences.append(Sentence(
                text=block['text'],
                time_range=TimeRange(start=block['start'], end=block['end']),
                index=i
            ))
        return sentences
    
    # ==================== Step 2: 意思块划分 ====================
    
    async def segment_semantic_blocks_async(
        self,
        sentences: List[Sentence],
        source_type: str,
        context_info: str = ""
    ) -> List[SemanticBlock]:
        """
        将句子划分为意思块（异步版本）
        
        Args:
            sentences: 句子列表
            source_type: "script" 或 "novel"
            context_info: 额外上下文信息
            
        Returns:
            List[SemanticBlock]: 意思块列表
        """
        logger.info(f"🧩 划分意思块: {len(sentences)} 句子 ({source_type})")
        logger.info(f"   → 调用LLM进行意思块划分...")
        
        # 格式化sentences为文本
        sentences_text = self._format_sentences(sentences)
        
        # 构造prompt
        system_prompt = self.prompts["semantic_block_segmentation"]["system"]
        user_prompt = self.prompts["semantic_block_segmentation"]["user"].format(
            sentences=sentences_text,
            source_type=source_type,
            context_info=context_info
        )
        
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 解析为SemanticBlock对象
            blocks_list = data.get("blocks", data) if isinstance(data, dict) else data
            semantic_blocks = []
            
            for item in blocks_list:
                # 提取对应的句子
                sentence_indices = item.get("sentence_indices", [])
                block_sentences = [sentences[i] for i in sentence_indices if i < len(sentences)]
                
                # 计算time_range（仅script有）
                time_range = None
                if source_type == "script" and block_sentences:
                    first_sentence = block_sentences[0]
                    last_sentence = block_sentences[-1]
                    if first_sentence.time_range and last_sentence.time_range:
                        time_range = TimeRange(
                            start=first_sentence.time_range.start,
                            end=last_sentence.time_range.end
                        )
                
                semantic_blocks.append(SemanticBlock(
                    block_id=item["block_id"],
                    theme=item["theme"],
                    sentences=block_sentences,
                    characters=item.get("characters", []),
                    location=item.get("location"),
                    time_context=item.get("time_context"),
                    summary=item["summary"],
                    time_range=time_range
                ))
            
            logger.info(f"✅ 意思块划分完成: {len(semantic_blocks)} blocks")
            return semantic_blocks
            
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ 意思块划分 - JSON解析失败")
            logger.error(f"   错误: {json_err}")
            logger.error(f"   位置: line {json_err.lineno}, column {json_err.colno}")
            if 'content' in locals():
                logger.error(f"   LLM返回内容长度: {len(content)} 字符")
                logger.error(f"   前500字符: {content[:500]}")
            return []
        except Exception as e:
            logger.error(f"❌ 意思块划分失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            import traceback
            logger.error(f"   堆栈追踪:\n{traceback.format_exc()}")
            return []
    
    def _format_sentences(self, sentences: List[Sentence]) -> str:
        """格式化句子为可读文本"""
        lines = []
        for i, sentence in enumerate(sentences):
            if sentence.time_range:
                lines.append(f"{i}. [{sentence.time_range.start}] {sentence.text}")
            else:
                lines.append(f"{i}. {sentence.text}")
        return "\n".join(lines)
    
    # ==================== Step 3: 事件聚合 ====================
    
    async def aggregate_events_async(
        self,
        semantic_blocks: List[SemanticBlock],
        source_type: str,
        context_info: str = ""
    ) -> List[Event]:
        """
        将意思块聚合为事件（异步版本）
        
        Args:
            semantic_blocks: 意思块列表
            source_type: "script" 或 "novel"
            context_info: 额外上下文信息
            
        Returns:
            List[Event]: 事件列表
        """
        logger.info(f"📦 聚合事件: {len(semantic_blocks)} blocks ({source_type})")
        logger.info(f"   → 调用LLM进行事件聚合...")
        
        # 格式化blocks为文本
        blocks_text = self._format_blocks_for_aggregation(semantic_blocks)
        
        # 构造prompt
        system_prompt = self.prompts["event_aggregation"]["system"]
        user_prompt = self.prompts["event_aggregation"]["user"].format(
            semantic_blocks=blocks_text,
            source_type=source_type,
            context_info=context_info
        )
        
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 解析为Event对象
            events_list = data.get("events", data) if isinstance(data, dict) else data
            events = []
            
            # 创建block_id到block对象的映射
            block_map = {block.block_id: block for block in semantic_blocks}
            
            for item in events_list:
                # 提取对应的blocks
                block_ids = item.get("block_ids", [])
                event_blocks = [block_map[bid] for bid in block_ids if bid in block_map]
                
                # 计算time_range（仅script有）
                time_range = None
                if source_type == "script" and event_blocks:
                    first_block = event_blocks[0]
                    last_block = event_blocks[-1]
                    if first_block.time_range and last_block.time_range:
                        time_range = TimeRange(
                            start=first_block.time_range.start,
                            end=last_block.time_range.end
                        )
                
                # 解析chapter_range
                chapter_range = None
                if "chapter_range" in item and item["chapter_range"]:
                    cr = item["chapter_range"]
                    if isinstance(cr, list) and len(cr) == 2:
                        chapter_range = tuple(cr)
                
                events.append(Event(
                    event_id=item["event_id"],
                    title=item["title"],
                    semantic_blocks=event_blocks,
                    characters=item.get("characters", []),
                    location=item.get("location"),
                    time_context=item.get("time_context"),
                    chapter_range=chapter_range,
                    time_range=time_range,
                    episode=item.get("episode")
                ))
            
            logger.info(f"✅ 事件聚合完成: {len(events)} events")
            return events
            
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ 事件聚合 - JSON解析失败")
            logger.error(f"   错误: {json_err}")
            logger.error(f"   位置: line {json_err.lineno}, column {json_err.colno}")
            if 'content' in locals():
                logger.error(f"   LLM返回内容长度: {len(content)} 字符")
                logger.error(f"   前500字符: {content[:500]}")
            return []
        except Exception as e:
            logger.error(f"❌ 事件聚合失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            import traceback
            logger.error(f"   堆栈追踪:\n{traceback.format_exc()}")
            return []
    
    def _format_blocks_for_aggregation(self, blocks: List[SemanticBlock]) -> str:
        """格式化意思块为可读文本"""
        lines = []
        for block in blocks:
            lines.append(f"Block ID: {block.block_id}")
            lines.append(f"  主题: {block.theme}")
            lines.append(f"  概括: {block.summary}")
            lines.append(f"  角色: {', '.join(block.characters) if block.characters else '无'}")
            lines.append(f"  地点: {block.location or '未知'}")
            lines.append(f"  时间: {block.time_context or '未知'}")
            lines.append("")
        return "\n".join(lines)
    
    # ==================== Step 4: 两级匹配 ====================
    
    async def match_events_two_level_async(
        self,
        script_events: List[Event],
        novel_events: List[Event],
        episode_name: str = "ep01"
    ) -> List[EventAlignment]:
        """
        两级匹配（优化版）：批量Event级匹配 + 批量Block链验证
        
        Args:
            script_events: Script的事件列表
            novel_events: Novel的事件列表
            episode_name: 集数名称
            
        Returns:
            List[EventAlignment]: 对齐结果列表
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔗 开始两级匹配: {episode_name}")
        logger.info(f"   Script Events: {len(script_events)}")
        logger.info(f"   Novel Events: {len(novel_events)}")
        logger.info(f"{'='*60}\n")
        
        # 如果是ep01，先进行Hook检测
        linear_start_index = 0
        if episode_name == "ep01" and script_events:
            logger.info("🎣 执行Hook检测...")
            # 使用SemanticBlocks进行Hook检测
            script_blocks = []
            for event in script_events[:5]:  # 只检查前5个事件
                script_blocks.extend(event.semantic_blocks)
            
            novel_blocks = []
            for event in novel_events[:10]:  # 检查前10个事件
                novel_blocks.extend(event.semantic_blocks)
            
            hook_result = self.hook_detector.detect_hook_boundary(
                script_blocks[:20],
                novel_blocks[:50]
            )
            
            # 保存Hook检测结果供workflow使用
            self.last_hook_result = hook_result
            
            logger.info(f"   结果: has_hook={hook_result.has_hook}, confidence={hook_result.confidence:.2f}")
            logger.info(f"   推理: {hook_result.reasoning}")
            
            # 找到linear_start_index对应的event索引
            if hook_result.has_hook:
                block_count = 0
                for i, event in enumerate(script_events):
                    block_count += len(event.semantic_blocks)
                    if block_count > hook_result.linear_start_index:
                        linear_start_index = i
                        break
                logger.info(f"   ✅ 线性叙事起点: Event索引 {linear_start_index}\n")
        
        # 从线性起点开始匹配
        alignments = []
        last_matched_novel_index = 0
        events_to_match = script_events[linear_start_index:]
        
        logger.info(f"📊 Level 1: 批量Event级粗匹配")
        logger.info(f"   待匹配Script Events: {len(events_to_match)}")
        
        # 批量Event级匹配
        batch_matching_results = await self._batch_match_events_async(
            events_to_match,
            novel_events,
            last_matched_novel_index
        )
        
        logger.info(f"   ✅ 批量匹配完成\n")
        
        # 处理每个Script Event的匹配结果
        for i, script_event in enumerate(events_to_match):
            matching_result = batch_matching_results.get(script_event.event_id, {})
            candidates = matching_result.get("candidates", [])
            
            logger.info(f"{'─'*60}")
            logger.info(f"📌 处理Script Event #{i+1}: {script_event.event_id}")
            logger.info(f"   标题: {script_event.title}")
            logger.info(f"   角色: {', '.join(script_event.characters) if script_event.characters else '无'}")
            logger.info(f"   地点: {script_event.location or '未知'}")
            logger.info(f"   意思块数: {len(script_event.semantic_blocks)}")
            logger.info(f"   候选数: {len(candidates)}")
            
            if not candidates:
                logger.warning(f"   ⚠️  未找到候选\n")
                continue
            
            # 过滤高分候选（阈值0.75）
            EVENT_THRESHOLD_HIGH = 0.75
            EVENT_THRESHOLD_LOW = 0.6
            
            high_score_candidates = [c for c in candidates if c["match_score"] >= EVENT_THRESHOLD_HIGH]
            
            logger.info(f"   📏 Event级阈值: {EVENT_THRESHOLD_HIGH} (降级阈值: {EVENT_THRESHOLD_LOW})")
            
            if not high_score_candidates:
                max_score = max([c['match_score'] for c in candidates]) if candidates else 0
                logger.info(f"   ⚠️  无候选达到阈值{EVENT_THRESHOLD_HIGH}（最高分: {max_score:.3f}）")
                # 降级：使用阈值0.6
                high_score_candidates = [c for c in candidates if c["match_score"] >= EVENT_THRESHOLD_LOW]
                if high_score_candidates:
                    logger.info(f"   → 使用降级阈值{EVENT_THRESHOLD_LOW}，找到 {len(high_score_candidates)} 个候选")
            
            if not high_score_candidates:
                logger.warning(f"   ⚠️  未找到合适候选（最高分 < 0.6）\n")
                continue
            
            # 显示候选信息
            for j, cand in enumerate(high_score_candidates[:3]):  # 最多显示3个
                logger.info(f"   候选#{j+1}: {cand['novel_event_id']} (评分: {cand['match_score']:.3f})")
                logger.info(f"      推理: {cand.get('reasoning', 'N/A')}")
            
            # Level 2: 批量Block链验证
            logger.info(f"\n   🔍 Level 2: 批量Block链验证（{len(high_score_candidates)}个候选）")
            
            # 获取Novel Event对象
            novel_event_objs = []
            for cand in high_score_candidates:
                novel_event = next(
                    (e for e in novel_events if e.event_id == cand["novel_event_id"]),
                    None
                )
                if novel_event:
                    novel_event_objs.append((cand, novel_event))
            
            if not novel_event_objs:
                logger.warning(f"   ⚠️  无法找到Novel Event对象\n")
                continue
            
            # 批量验证
            validation_results = await self._batch_validate_block_chains_async(
                script_event,
                novel_event_objs
            )
            
            # 选择最佳匹配
            best_alignment = None
            best_score = 0.0
            
            for (cand, novel_event), validation in zip(novel_event_objs, validation_results):
                # 计算最终置信度
                final_confidence = (
                    cand["match_score"] * 0.4 +
                    validation.validation_score * 0.6
                )
                
                logger.info(f"      Novel Event: {novel_event.title}")
                logger.info(f"         Event匹配分: {cand['match_score']:.3f}")
                logger.info(f"         Block链验证分: {validation.validation_score:.3f}")
                logger.info(f"         最终置信度: {final_confidence:.3f}")
                logger.info(f"         覆盖率: {validation.coverage_rate:.1%}, 顺序一致性: {validation.order_consistency:.1%}")
                
                if final_confidence > best_score:
                    best_score = final_confidence
                    best_alignment = EventAlignment(
                        script_event=script_event,
                        novel_event=novel_event,
                        event_match_score=cand["match_score"],
                        block_chain_validation=validation,
                        final_confidence=final_confidence,
                        reasoning=f"Event匹配: {cand.get('reasoning', '')}; Block链验证: {validation.reasoning}"
                    )
                    
                    # 更新last_matched_novel_index
                    novel_index = novel_events.index(novel_event)
                    last_matched_novel_index = max(last_matched_novel_index, novel_index)
            
            if best_alignment:
                alignments.append(best_alignment)
                logger.info(f"\n   ✅ 最佳匹配: {best_alignment.novel_event.title}")
                logger.info(f"      最终置信度: {best_score:.3f}\n")
            else:
                logger.warning(f"   ⚠️  验证失败，无最佳匹配\n")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 两级匹配完成: {episode_name}")
        logger.info(f"   成功匹配: {len(alignments)} / {len(events_to_match)}")
        logger.info(f"   匹配率: {len(alignments)/len(events_to_match)*100:.1f}%" if events_to_match else "   匹配率: N/A")
        avg_conf = sum(a.final_confidence for a in alignments)/len(alignments) if alignments else 0.0
        logger.info(f"   平均置信度: {avg_conf:.3f}")
        logger.info(f"{'='*60}\n")
        
        return alignments
    
    async def _batch_match_events_async(
        self,
        script_events: List[Event],
        novel_events: List[Event],
        last_matched_index: int
    ) -> Dict[str, Dict]:
        """
        批量Event级粗匹配（一次LLM调用处理所有Script Events）
        
        Args:
            script_events: Script事件列表
            novel_events: Novel事件列表
            last_matched_index: 上次匹配的Novel索引
            
        Returns:
            Dict[str, Dict]: {script_event_id: {"candidates": [...]}, ...}
        """
        # 格式化所有Script Events
        script_events_text = "\n\n".join([
            f"Script Event #{i+1}:\n" + self._format_event_for_matching(e)
            for i, e in enumerate(script_events)
        ])
        
        # 格式化Novel Events（从last_matched_index往后）
        novel_events_window = novel_events[last_matched_index:last_matched_index+100]  # 限制窗口
        novel_events_text = "\n\n".join([
            f"Novel Event #{i+last_matched_index}:\n" + self._format_event_for_matching(e)
            for i, e in enumerate(novel_events_window)
        ])
        
        # 构造prompt
        system_prompt = self.prompts["event_level_matching"]["system"]
        user_prompt = self.prompts["event_level_matching"]["user"].format(
            script_events=script_events_text,
            novel_events=novel_events_text,
            last_matched_index=last_matched_index
        )
        
        logger.info(f"   → 调用LLM批量匹配 {len(script_events)} 个Script Events (Novel窗口: {len(novel_events_window)} events)...")
        
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 解析results
            results = data.get("results", [])
            
            # 构建返回字典
            result_dict = {}
            for result in results:
                script_event_id = result.get("script_event_id")
                if script_event_id:
                    result_dict[script_event_id] = {
                        "candidates": result.get("candidates", [])
                    }
            
            return result_dict
            
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ 批量Event级匹配 - JSON解析失败")
            logger.error(f"   错误: {json_err}")
            logger.error(f"   位置: line {json_err.lineno}, column {json_err.colno}")
            if 'content' in locals():
                logger.error(f"   LLM返回内容长度: {len(content)} 字符")
                logger.error(f"   前500字符: {content[:500]}")
                logger.error(f"   后500字符: {content[-500:]}")
            return {}
        except Exception as e:
            logger.error(f"❌ 批量Event级匹配失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            import traceback
            logger.error(f"   堆栈追踪:\n{traceback.format_exc()}")
            return {}
    
    async def _batch_validate_block_chains_async(
        self,
        script_event: Event,
        novel_candidates: List[Tuple[Dict, Event]]
    ) -> List[BlockChainValidation]:
        """
        批量Block链验证（一次LLM调用验证多个候选）
        
        Args:
            script_event: Script事件
            novel_candidates: [(candidate_dict, novel_event), ...] 列表
            
        Returns:
            List[BlockChainValidation]: 验证结果列表（与输入顺序一致）
        """
        if not novel_candidates:
            return []
        
        # 格式化Script Event的blocks
        script_blocks_text = self._format_blocks_for_validation(script_event.semantic_blocks)
        
        # 格式化所有Novel Event候选
        novel_candidates_text = []
        for i, (cand, novel_event) in enumerate(novel_candidates):
            novel_text = f"""
Candidate #{i+1}:
Novel Event ID: {novel_event.event_id}
Title: {novel_event.title}
Semantic Blocks:
{self._format_blocks_for_validation(novel_event.semantic_blocks)}
"""
            novel_candidates_text.append(novel_text.strip())
        
        # 构造prompt
        system_prompt = self.prompts["block_chain_validation_batch"]["system"]
        user_prompt = self.prompts["block_chain_validation_batch"]["user"].format(
            script_event_id=script_event.event_id,
            script_event_title=script_event.title,
            script_blocks=script_blocks_text,
            novel_candidates="\n\n".join(novel_candidates_text)
        )
        
        logger.info(f"      → 调用LLM批量验证Block链 ({len(novel_candidates)} 个候选)...")
        
        try:
            async with self.semaphore:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 解析validations
            validations = data.get("validations", [])
            
            # 构建返回列表（按novel_event_id匹配）
            results = []
            for cand, novel_event in novel_candidates:
                # 查找对应的validation
                validation_data = next(
                    (v for v in validations if v.get("novel_event_id") == novel_event.event_id),
                    None
                )
                
                if validation_data:
                    matched_pairs = [tuple(pair) for pair in validation_data.get("matched_pairs", [])]
                    results.append(BlockChainValidation(
                        script_chain=validation_data.get("script_chain", []),
                        novel_chain=validation_data.get("novel_chain", []),
                        matched_pairs=matched_pairs,
                        coverage_rate=validation_data.get("coverage_rate", 0.0),
                        order_consistency=validation_data.get("order_consistency", 0.0),
                        validation_score=validation_data.get("validation_score", 0.0),
                        reasoning=validation_data.get("reasoning", "")
                    ))
                else:
                    # 默认失败结果
                    script_chain = [b.theme for b in script_event.semantic_blocks]
                    novel_chain = [b.theme for b in novel_event.semantic_blocks]
                    results.append(BlockChainValidation(
                        script_chain=script_chain,
                        novel_chain=novel_chain,
                        matched_pairs=[],
                        coverage_rate=0.0,
                        order_consistency=0.0,
                        validation_score=0.0,
                        reasoning="未找到验证结果"
                    ))
            
            return results
            
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ 批量Block链验证 - JSON解析失败")
            logger.error(f"   错误: {json_err}")
            logger.error(f"   位置: line {json_err.lineno}, column {json_err.colno}")
            if 'content' in locals():
                logger.error(f"   LLM返回内容长度: {len(content)} 字符")
                logger.error(f"   前500字符: {content[:500]}")
                logger.error(f"   后500字符: {content[-500:]}")
            # 返回默认失败结果
            results = []
            for cand, novel_event in novel_candidates:
                script_chain = [b.theme for b in script_event.semantic_blocks]
                novel_chain = [b.theme for b in novel_event.semantic_blocks]
                results.append(BlockChainValidation(
                    script_chain=script_chain,
                    novel_chain=novel_chain,
                    matched_pairs=[],
                    coverage_rate=0.0,
                    order_consistency=0.0,
                    validation_score=0.0,
                    reasoning=f"JSON解析失败: {str(json_err)}"
                ))
            return results
        except Exception as e:
            logger.error(f"❌ 批量Block链验证失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            import traceback
            logger.error(f"   堆栈追踪:\n{traceback.format_exc()}")
            # 返回默认失败结果
            results = []
            for cand, novel_event in novel_candidates:
                script_chain = [b.theme for b in script_event.semantic_blocks]
                novel_chain = [b.theme for b in novel_event.semantic_blocks]
                results.append(BlockChainValidation(
                    script_chain=script_chain,
                    novel_chain=novel_chain,
                    matched_pairs=[],
                    coverage_rate=0.0,
                    order_consistency=0.0,
                    validation_score=0.0,
                    reasoning=f"验证失败: {str(e)}"
                ))
            return results
    
    
    def _format_event_for_matching(self, event: Event) -> str:
        """格式化事件为可读文本（用于匹配）"""
        lines = [
            f"Event ID: {event.event_id}",
            f"Title: {event.title}",
            f"Characters: {', '.join(event.characters) if event.characters else '无'}",
            f"Location: {event.location or '未知'}",
            f"Time: {event.time_context or '未知'}",
            f"Blocks: {len(event.semantic_blocks)} blocks",
            "Block Themes: " + " → ".join([b.theme for b in event.semantic_blocks])
        ]
        return "\n".join(lines)
    
    def _format_blocks_for_validation(self, blocks: List[SemanticBlock]) -> str:
        """格式化意思块为可读文本（用于验证）"""
        lines = []
        for i, block in enumerate(blocks):
            lines.append(f"{i}. {block.theme}")
            lines.append(f"   概括: {block.summary}")
        return "\n".join(lines)
    
    # ==================== 兼容旧接口 ====================
    
    def align_script_with_novel(
        self,
        novel_events_data: List[Dict],
        script_events_data: List[Dict]
    ) -> List[EventAlignment]:
        """
        兼容旧接口（暂时不实现，需要在workflow中使用新的流程）
        """
        raise NotImplementedError("请使用新的两级匹配流程")
    
    def aggregate_context(self, alignment_results, novel_chapters):
        """兼容旧接口"""
        raise NotImplementedError("使用新的Event对齐结果")
    
    def evaluate_alignment_quality(
        self,
        alignment_results: List[EventAlignment],
        quality_threshold: float = 70.0
    ) -> AlignmentQualityReport:
        """
        评估对齐质量（简化版本，基于新的EventAlignment）
        
        TODO: 完善评估逻辑
        """
        if not alignment_results:
            return AlignmentQualityReport(
                overall_score=0.0,
                avg_confidence=0.0,
                coverage_ratio=0.0,
                continuity_score=0.0,
                episode_coverage=[],
                is_qualified=False,
                needs_more_chapters=True,
                details={}
            )
        
        # 计算平均置信度
        avg_confidence = sum(a.final_confidence for a in alignment_results) / len(alignment_results)
        
        # 简化的评分
        overall_score = avg_confidence * 100
        
        return AlignmentQualityReport(
            overall_score=overall_score,
            avg_confidence=avg_confidence,
            coverage_ratio=1.0,  # TODO: 计算实际覆盖率
            continuity_score=1.0,  # TODO: 计算章节连续性
            episode_coverage=[],  # TODO: 计算各集覆盖
            is_qualified=overall_score >= quality_threshold,
            needs_more_chapters=overall_score < quality_threshold,
            details={
                "total_alignments": len(alignment_results),
                "avg_event_match_score": sum(a.event_match_score for a in alignment_results) / len(alignment_results),
                "avg_validation_score": sum(a.block_chain_validation.validation_score for a in alignment_results) / len(alignment_results)
            }
        )
