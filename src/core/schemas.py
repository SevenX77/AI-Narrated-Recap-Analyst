from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Character(BaseModel):
    name: str = Field(..., description="角色名称")
    role: str = Field(..., description="角色在当前片段中的定位，如：主角、反派、配角、路人")
    status: str = Field(..., description="角色当前状态，如：受伤、震惊、得意")

class NarrativeBeat(BaseModel):
    event_type: str = Field(..., description="事件类型：冲突(Conflict)、转折(Twist)、升级(Upgrade)、铺垫(Setup)、高潮(Climax)")
    description: str = Field(..., description="事件简述，一句话概括")
    intensity: int = Field(..., description="紧张/爽感程度，1-10分")

class NarrativeEvent(BaseModel):
    """
    最小叙事单元 (SVO + Context)，用于细粒度对齐和逻辑分析
    """
    subject: str = Field(..., description="主语 (Who)")
    action: str = Field(..., description="谓语/动作 (Did what)")
    outcome: str = Field(..., description="宾语/结果 (To whom/what)")
    
    # --- 新增核心上下文信息 ---
    location: Optional[str] = Field(None, description="地点 (Where) - 例如：'破败的超市', '车队末尾'")
    time_context: Optional[str] = Field(None, description="时间/时机 (When) - 例如：'广播响起后', '深夜'")
    method: Optional[str] = Field(None, description="手段/工具 (How) - 例如：'用十字弩', '偷偷地'")
    # -----------------------

    original_text: Optional[str] = Field(None, description="原文摘录")
    event_type: str = Field("plot", description="类型：plot(剧情), setting(设定), emotion(情绪)")

class SceneAnalysis(BaseModel):
    """
    对小说片段的结构化分析结果 (用于生成解说)
    """
    summary: str = Field(..., description="本片段的剧情梗概，100字以内")
    scene_type: str = Field(..., description="场景类型：战斗、对话、内心独白、环境描写")
    characters: List[Character] = Field(..., description="出场角色列表")
    beats: List[NarrativeBeat] = Field(..., description="剧情节拍列表")
    potential_hooks: List[str] = Field(..., description="适合做开头钩子的关键句或情节")
    narrative_pattern: str = Field(..., description="本段落的抽象叙事模式（不包含具体人名物名）")
    flashback_candidate: Optional[str] = Field(None, description="【关键】适合用于倒叙开场的最高爽点/最大悬念事件。如果本段落平淡无奇，可为空。")
    protagonist_name: str = Field(..., description="主角在小说中的原名（用于后续替换为第一人称）")

class AlignmentItem(BaseModel):
    """
    解说文案与小说原文的对齐项 (用于反馈学习)
    """
    script_time: str = Field(..., description="解说时间轴")
    script_event: str = Field(..., description="解说事件概括")
    matched_novel_chapter: str = Field(..., description="对应小说章节")
    matched_novel_event: str = Field(..., description="对应小说事件概括")
    match_reason: str = Field(..., description="匹配/改编理由")
    confidence: str = Field(..., description="置信度: 高/中/低")

class FeedbackReport(BaseModel):
    """
    反馈分析报告
    """
    score: float = Field(..., description="总体评分 (0-100)")
    issues: List[str] = Field(..., description="发现的问题列表")
    suggestions: List[str] = Field(..., description="改进建议列表")
    methodology_update: str = Field(..., description="提炼出的方法论/策略更新建议")
