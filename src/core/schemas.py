from typing import List, Optional, Dict, Any, Tuple
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

class EpisodeCoverage(BaseModel):
    """
    单集SRT的覆盖情况
    """
    episode_name: str = Field(..., description="集数名称，如 'ep01'")
    total_events: int = Field(..., description="该集的总事件数")
    matched_events: int = Field(..., description="成功匹配的事件数")
    coverage_ratio: float = Field(..., description="覆盖率 (0.0-1.0)")
    max_matched_chapter: Optional[str] = Field(None, description="匹配到的最大章节，如 '第10章'")
    min_matched_chapter: Optional[str] = Field(None, description="匹配到的最小章节，如 '第1章'")

class AlignmentQualityReport(BaseModel):
    """
    对齐质量评估报告
    
    用于评估当前对齐结果的质量，决定是否需要继续提取更多章节
    """
    overall_score: float = Field(..., description="整体质量得分 (0-100)")
    avg_confidence: float = Field(..., description="平均置信度 (0.0-1.0)")
    coverage_ratio: float = Field(..., description="整体覆盖率 (0.0-1.0)")
    continuity_score: float = Field(..., description="章节连续性得分 (0.0-1.0)")
    
    episode_coverage: List[EpisodeCoverage] = Field(..., description="各集覆盖情况")
    
    is_qualified: bool = Field(..., description="是否达到合格标准")
    needs_more_chapters: bool = Field(..., description="是否需要提取更多章节")
    
    details: Dict[str, Any] = Field(default_factory=dict, description="详细统计信息")


# ==================== 新的三层数据模型 (v2) ====================

class TimeRange(BaseModel):
    """时间范围 (用于Script的SRT时间轴)"""
    start: str = Field(..., description="开始时间，如 '00:00:14,000'")
    end: str = Field(..., description="结束时间，如 '00:00:30,900'")


class Sentence(BaseModel):
    """
    句子 - 最小文本单元
    
    从SRT碎片化文本或小说文本中还原出的完整句子
    """
    text: str = Field(..., description="完整句子文本")
    time_range: Optional[TimeRange] = Field(None, description="SRT时间范围（仅Script有）")
    index: int = Field(..., description="在原文中的位置索引")


class SemanticBlock(BaseModel):
    """
    意思块 - 情节步骤级
    
    围绕单一主题的语义连贯段落，包含1-N个句子
    是匹配的核心单元
    """
    block_id: str = Field(..., description="意思块唯一标识，如 'block_ep01_001'")
    theme: str = Field(..., description="意思块的主题，如 '发现敌人'、'准备逃跑'")
    sentences: List[Sentence] = Field(..., description="构成该意思块的句子列表")
    
    # 关键维度（用于匹配验证）
    characters: List[str] = Field(default_factory=list, description="涉及的角色，如 ['我', '剪刀女']")
    location: Optional[str] = Field(None, description="地点，如 '超市'。注意：只提取实际发生的地点，忽略假设性描述")
    time_context: Optional[str] = Field(None, description="时间，如 '晚上'、'深夜'。注意：只提取实际发生的时间，忽略假设性描述（如'如果等到白天'）")
    
    # Script特有
    time_range: Optional[TimeRange] = Field(None, description="SRT时间范围（仅Script有）")
    
    # 匹配用
    summary: str = Field(..., description="对这个意思块的简短概括（50字以内）")


class Event(BaseModel):
    """
    事件 - 完整情节单元
    
    高层次的故事情节单元，包含一个完整的"意思块链"
    可能跨越多章（Novel）或多个时间段（Script）
    """
    event_id: str = Field(..., description="事件唯一标识，如 'event_ep01_001'")
    title: str = Field(..., description="事件标题，如 '超市中与剪刀女战斗'")
    semantic_blocks: List[SemanticBlock] = Field(..., description="包含的意思块列表（按顺序）")
    
    # Event级元信息
    characters: List[str] = Field(default_factory=list, description="主要角色列表")
    location: Optional[str] = Field(None, description="主要地点")
    time_context: Optional[str] = Field(None, description="时间背景")
    
    # Novel特有
    chapter_range: Optional[Tuple[int, int]] = Field(None, description="章节范围，如 (1, 3) 表示第1-3章")
    
    # Script特有
    time_range: Optional[TimeRange] = Field(None, description="视频时间范围（仅Script有）")
    episode: Optional[str] = Field(None, description="所属集数，如 'ep01'（仅Script有）")


class BlockChainValidation(BaseModel):
    """
    意思块链验证结果
    
    用于验证Script Event和Novel Event的意思块链是否匹配
    """
    script_chain: List[str] = Field(..., description="Script的意思块主题链，如 ['发现敌人', '准备逃跑', '扔罐头', '逃脱']")
    novel_chain: List[str] = Field(..., description="Novel的意思块主题链，如 ['潜入', '发现敌人', '观察', '准备逃跑', '扔罐头', '逃跑中', '成功逃脱', '返回']")
    
    matched_pairs: List[Tuple[int, int]] = Field(default_factory=list, description="匹配的索引对，如 [(0, 1), (1, 3), (2, 4), (3, 6)]")
    coverage_rate: float = Field(..., description="Script链的覆盖率 (0.0-1.0)，即Script链中有多少比例的block在Novel链中找到了对应")
    order_consistency: float = Field(..., description="顺序一致性 (0.0-1.0)，验证匹配的block是否按顺序出现")
    validation_score: float = Field(..., description="综合验证分数 (0.0-1.0)")
    
    reasoning: str = Field(..., description="验证推理过程")


class EventAlignment(BaseModel):
    """
    Event级对齐结果
    
    两级匹配的最终结果：Event级粗匹配 + SemanticBlock链细验证
    """
    script_event: Event = Field(..., description="Script的事件")
    novel_event: Event = Field(..., description="Novel的事件")
    
    # Level 1: Event级匹配分数
    event_match_score: float = Field(..., description="Event级匹配分数 (0.0-1.0)")
    
    # Level 2: SemanticBlock链验证结果
    block_chain_validation: BlockChainValidation = Field(..., description="意思块链验证结果")
    
    # 最终结果
    final_confidence: float = Field(..., description="最终置信度 (0.0-1.0)，综合Event级和Block链级的分数")
    reasoning: str = Field(..., description="匹配推理过程")


# ==================== Hook-Body分离架构的新Schema ====================

class BodyStartDetection(BaseModel):
    """
    Body起点检测结果
    """
    has_hook: bool = Field(..., description="是否存在Hook")
    body_start_time: str = Field(..., description="Body开始的时间戳，如 '00:00:30,900'")
    hook_end_time: Optional[str] = Field(None, description="Hook结束的时间戳（如has_hook=True）")
    confidence: float = Field(..., description="检测置信度 (0.0-1.0)")
    reasoning: str = Field(..., description="判断理由")


class LayeredNode(BaseModel):
    """
    分层节点（用于分层对齐模型）
    """
    node_type: str = Field(..., description="节点类型：world_building/game_mechanics/items_equipment/plot_events")
    content: str = Field(..., description="原文内容")
    summary: str = Field(..., description="简要概括（20字以内）")
    source_time: Optional[str] = Field(None, description="来源时间戳（如果来自Script）")
    source_chapter: Optional[str] = Field(None, description="来源章节（如果来自Novel）")


class HookLayeredContent(BaseModel):
    """
    Hook的分层内容
    """
    time_range: str = Field(..., description="Hook的时间范围，如 '00:00:00,000 - 00:00:30,900'")
    raw_text: str = Field(..., description="Hook的原始文本")
    world_building: List[LayeredNode] = Field(default_factory=list, description="世界观设定节点")
    game_mechanics: List[LayeredNode] = Field(default_factory=list, description="游戏机制节点")
    items_equipment: List[LayeredNode] = Field(default_factory=list, description="道具装备节点")
    plot_events: List[LayeredNode] = Field(default_factory=list, description="情节事件节点")


class HookAnalysisResult(BaseModel):
    """
    Hook分析完整结果（Phase 1输出）
    """
    episode: str = Field(..., description="集数，如 'ep01'")
    detection: BodyStartDetection = Field(..., description="Body起点检测结果")
    hook_content: Optional[HookLayeredContent] = Field(None, description="Hook的分层内容（如has_hook=True）")
    intro_similarity: float = Field(0.0, description="Hook与Novel简介的相似度 (0.0-1.0)")
    source_analysis: Dict[str, Any] = Field(default_factory=dict, description="来源分析（简介/章节/独立内容）")
    status: str = Field("completed", description="处理状态")
    timestamp: str = Field(..., description="处理时间戳")


class NovelPreprocessingResult(BaseModel):
    """
    Novel预处理结果
    """
    novel_path: str = Field(..., description="Novel原始文件路径")
    introduction_length: int = Field(..., description="简介长度（字符数）")
    chapter_1_line: int = Field(..., description="第1章起始行号")
    total_chapters: int = Field(..., description="总章节数")
    output_intro: str = Field(..., description="输出简介文件路径")
    output_index: str = Field(..., description="输出章节索引文件路径")


class ChapterInfo(BaseModel):
    """
    章节信息
    """
    chapter_number: int = Field(..., description="章节号")
    chapter_title: str = Field(..., description="章节标题")
    start_line: int = Field(..., description="起始行号")
    end_line: int = Field(..., description="结束行号")
    line_count: int = Field(..., description="行数")


# ==================== 自反馈优化系统 Schema ====================

from datetime import datetime


class AlignmentAnnotation(BaseModel):
    """
    对齐标注（用于标记错误和提供反馈）
    """
    annotation_id: str = Field(..., description="标注ID")
    project_id: str = Field(..., description="项目ID")
    episode: str = Field(..., description="集数")
    layer: str = Field(..., description="层级（world_building/game_mechanics/items_equipment/plot_events）")
    
    # 对齐内容
    script_node_id: str = Field(..., description="Script节点ID")
    novel_node_id: str = Field(..., description="Novel节点ID")
    script_content: str = Field(..., description="Script内容")
    novel_content: str = Field(..., description="Novel内容")
    
    # 系统判断
    system_similarity: float = Field(..., description="系统计算的相似度")
    system_confidence: str = Field(..., description="系统置信度")
    
    # 人工标注
    is_correct_match: bool = Field(..., description="是否正确匹配")
    error_type: Optional[str] = Field(None, description="错误类型：missing/incomplete/wrong_match/similarity_wrong")
    human_similarity: Optional[float] = Field(None, description="人类评估的相似度")
    human_feedback: Optional[str] = Field(None, description="人类反馈说明")
    correction: Optional[str] = Field(None, description="正确答案")
    
    # Heat分数（问题严重程度）
    heat_score: float = Field(0.0, description="Heat分数（0-100），越高越严重")
    
    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now, description="标注时间")
    annotator: Optional[str] = Field(None, description="标注人")


class PromptVersion(BaseModel):
    """
    Prompt版本信息
    """
    version: str = Field(..., description="版本号（如v1.1）")
    layer: str = Field(..., description="层级")
    parent_version: Optional[str] = Field(None, description="父版本")
    
    # Prompt内容
    prompt_content: str = Field(..., description="完整的Prompt内容")
    
    # 优化信息
    change_summary: str = Field(..., description="变更摘要")
    optimized_for: List[str] = Field(default_factory=list, description="针对的错误类型")
    heat_addressed: List[float] = Field(default_factory=list, description="解决的Heat分数列表")
    
    # 性能指标
    metrics: Optional[Dict[str, float]] = Field(None, description="性能指标")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="system", description="创建方式（system/manual）")


class OptimizationRound(BaseModel):
    """
    优化轮次记录
    """
    round_number: int = Field(..., description="轮次编号")
    project_id: str = Field(..., description="项目ID")
    episode: str = Field(..., description="集数")
    
    # Prompt版本
    prompt_versions: Dict[str, str] = Field(..., description="各层使用的Prompt版本")
    
    # 对齐结果
    alignment_result_path: str = Field(..., description="对齐结果文件路径")
    overall_score: float = Field(..., description="Overall Score")
    layer_scores: Dict[str, float] = Field(..., description="各层得分")
    
    # 标注数据
    annotations: List[AlignmentAnnotation] = Field(default_factory=list)
    total_annotations: int = Field(0, description="标注总数")
    error_count: int = Field(0, description="错误数量")
    total_heat: float = Field(0.0, description="总Heat分数")
    avg_heat: float = Field(0.0, description="平均Heat分数")
    
    # 决策
    adopted: bool = Field(..., description="是否采用新Prompt")
    adoption_reason: Optional[str] = Field(None, description="采用/拒绝理由")
    
    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_seconds: Optional[float] = Field(None, description="耗时（秒）")


class FinalOptimizationReport(BaseModel):
    """
    最终优化报告（5轮综合）
    """
    project_id: str = Field(..., description="项目ID")
    episode: str = Field(..., description="集数")
    
    # 轮次汇总
    rounds: List[OptimizationRound] = Field(..., description="所有轮次数据")
    total_rounds: int = Field(..., description="总轮次数")
    
    # 改进轨迹
    score_trajectory: List[float] = Field(..., description="Overall Score轨迹")
    heat_trajectory: List[float] = Field(..., description="总Heat轨迹")
    
    # 最终结果
    initial_score: float = Field(..., description="初始Overall Score")
    final_score: float = Field(..., description="最终Overall Score")
    improvement: float = Field(..., description="改进幅度")
    improvement_percentage: float = Field(..., description="改进百分比")
    
    initial_heat: float = Field(..., description="初始总Heat")
    final_heat: float = Field(..., description="最终总Heat")
    heat_reduction: float = Field(..., description="Heat降低幅度")
    heat_reduction_percentage: float = Field(..., description="Heat降低百分比")
    
    # LLM综合评估
    llm_evaluation: Optional[str] = Field(None, description="LLM综合评估报告")
    convergence_status: Optional[str] = Field(None, description="收敛状态（converged/improving/unstable）")
    production_ready: Optional[bool] = Field(None, description="是否达到生产可用水平")
    
    # 建议
    recommendations: List[str] = Field(default_factory=list, description="下一步建议")
    
    # 元数据
    generated_at: datetime = Field(default_factory=datetime.now)
    total_duration_seconds: Optional[float] = Field(None, description="总耗时")
