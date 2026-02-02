from typing import List, Optional
from pydantic import BaseModel, Field

class ScriptSegment(BaseModel):
    text: str = Field(..., description="解说文案内容")
    visual_cue: str = Field(..., description="画面提示")
    duration: int = Field(..., description="预估时长(秒)")

class Script(BaseModel):
    title: str = Field(..., description="解说标题")
    narrative_strategy: str = Field(..., description="叙事策略")
    total_duration: int = Field(..., description="总时长(秒)")
    segments: List[ScriptSegment] = Field(..., description="文案分段列表")

class AlignmentItem(BaseModel):
    script_time: str = Field(..., description="解说时间点")
    script_event: str = Field(..., description="解说事件概括")
    matched_novel_chapter: str = Field(..., description="匹配的小说章节")
    matched_novel_event: str = Field(..., description="匹配的小说事件概括")
    match_reason: str = Field(..., description="匹配理由")
    confidence: str = Field(..., description="置信度: 高/中/低")
