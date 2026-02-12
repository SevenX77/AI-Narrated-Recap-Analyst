"""
项目元数据结构定义

注意：
- has_novel/has_script 应该由 ProjectManager 根据文件系统状态自动计算
- 章节数、集数等统计信息也应该动态计算
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
from pathlib import Path

class ProjectStatus(str, Enum):
    """项目状态"""
    DRAFT = "draft"  # 草稿（刚创建）
    READY = "ready"  # 就绪（已上传文件）
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    ERROR = "error"  # 错误状态

class WorkflowStageStatus(str, Enum):
    """工作流阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    LOCKED = "locked"  # 依赖未满足，禁用状态

class ProjectSources(BaseModel):
    """项目源文件信息"""
    has_novel: bool = Field(False, description="是否有原小说")
    has_script: bool = Field(False, description="是否有脚本")
    novel_chapters: int = Field(0, description="小说章节数")
    script_episodes: int = Field(0, description="脚本集数")
    other_files: int = Field(0, description="其他文件数量")

class PreprocessTask(BaseModel):
    """预处理子任务信息"""
    task_id: str = Field(..., description="任务ID，如 'novel' 或 'ep01'")
    task_type: str = Field(..., description="任务类型：'novel' 或 'script'")
    task_name: str = Field(..., description="任务显示名称")
    status: WorkflowStageStatus = WorkflowStageStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    current_step: Optional[str] = None  # 当前处理步骤
    progress: Optional[str] = None  # 进度信息

class WorkflowStageInfo(BaseModel):
    """工作流阶段信息"""
    status: WorkflowStageStatus = WorkflowStageStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    tasks: List[PreprocessTask] = Field(default_factory=list, description="子任务列表（仅预处理阶段使用）")

class WorkflowStages(BaseModel):
    """工作流各阶段状态（旧版，保留兼容性）"""
    import_stage: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="导入阶段")
    preprocess: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="预处理阶段")
    novel_segmentation: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="小说分段")
    novel_annotation: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="小说标注")
    script_segmentation: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="脚本分段")
    script_hooks: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="Hook检测")
    alignment: WorkflowStageInfo = Field(default_factory=WorkflowStageInfo, description="对齐")


# ============= Phase I Analyst Agent 工作流定义 =============

class PhaseStatus(str, Enum):
    """Phase 状态"""
    LOCKED = "locked"      # 依赖未满足
    READY = "ready"        # 可以开始
    RUNNING = "running"    # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"      # 失败
    CANCELLED = "cancelled"  # 已取消


class DependencyCheck(BaseModel):
    """依赖检查结果"""
    is_met: bool = Field(..., description="依赖是否满足")
    missing_dependencies: List[str] = Field(default_factory=list, description="缺失的依赖项")
    message: Optional[str] = Field(None, description="提示信息")


class SubTaskProgress(BaseModel):
    """子任务进度"""
    task_id: str = Field(..., description="子任务ID")
    task_name: str = Field(..., description="子任务名称")
    status: PhaseStatus = Field(PhaseStatus.LOCKED, description="子任务状态")
    progress_percentage: Optional[float] = Field(None, description="进度百分比 (0-100)")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_summary: Optional[str] = Field(None, description="结果摘要")
    

class PhaseStepState(BaseModel):
    """单个步骤的状态"""
    step_id: str = Field(..., description="步骤ID: step_1_import, step_2_script, step_3_novel, step_4_alignment")
    step_name: str = Field(..., description="步骤名称")
    status: PhaseStatus = Field(PhaseStatus.LOCKED, description="当前状态")
    
    # 依赖检查
    dependencies: DependencyCheck = Field(..., description="依赖检查结果")
    
    # 时间信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # 进度信息
    overall_progress: float = Field(0.0, description="总体进度 (0-100)")
    sub_tasks: List[SubTaskProgress] = Field(default_factory=list, description="子任务列表")
    
    # 结果信息
    error_message: Optional[str] = None
    quality_score: Optional[int] = Field(None, description="质量评分 (0-100)")
    result_path: Optional[str] = Field(None, description="结果文件路径")
    
    # 统计信息
    llm_calls_count: int = Field(0, description="LLM 调用次数")
    total_cost: float = Field(0.0, description="总成本 (USD)")
    processing_time: float = Field(0.0, description="处理时间 (秒)")
    

class Step1ImportState(PhaseStepState):
    """步骤1: 文件导入与标准化"""
    # 扩展字段
    novel_imported: bool = False
    novel_file_name: Optional[str] = None
    novel_file_size: int = 0
    novel_encoding: Optional[str] = None
    novel_chapter_count: int = 0
    
    script_imported: bool = False
    script_episodes: List[str] = Field(default_factory=list, description="已导入的集数列表")
    script_total_entries: int = Field(0, description="SRT 总条目数")
    script_total_duration: float = Field(0.0, description="总时长（秒）")


class Step2ScriptAnalysisState(PhaseStepState):
    """步骤2: Script 分析"""
    # 扩展字段：每个 episode 的处理状态
    episodes_status: Dict[str, Dict] = Field(default_factory=dict, description="每个集数的处理状态")
    # 格式: {"ep01": {"status": "completed", "phases": {...}, "quality_score": 88}}
    
    total_episodes: int = 0
    completed_episodes: int = 0
    failed_episodes: int = 0


class Step3NovelAnalysisState(PhaseStepState):
    """步骤3: Novel 分析"""
    # 扩展字段：8 个 Step 的状态
    novel_steps: Dict[str, Dict] = Field(default_factory=dict, description="Novel 处理的 8 个 Step 状态")
    # 格式: {"step_1_import": {"status": "completed", ...}, ...}
    
    total_chapters: int = 0
    total_paragraphs: int = 0
    total_events: int = 0
    total_settings: int = 0
    total_system_elements: int = 0


class Step4AlignmentState(PhaseStepState):
    """步骤4: Script-Novel 对齐"""
    # 扩展字段
    alignment_pairs: List[Dict] = Field(default_factory=list, description="对齐对列表")
    # 格式: [{"episode_id": "ep01", "chapter_ids": [1, 2, 3], "status": "completed"}]
    
    total_alignments: int = 0
    average_match_confidence: Optional[float] = None
    event_coverage_rate: Optional[float] = None
    setting_coverage_rate: Optional[float] = None


class PhaseIAnalystState(BaseModel):
    """Phase I: Analyst Agent 完整状态"""
    phase_name: str = "Phase I: Analyst Agent"
    overall_status: PhaseStatus = PhaseStatus.LOCKED
    overall_progress: float = Field(0.0, description="整体进度 (0-100)")
    
    # 4 个步骤
    step_1_import: Step1ImportState
    step_2_script: Step2ScriptAnalysisState
    step_3_novel: Step3NovelAnalysisState
    step_4_alignment: Step4AlignmentState
    
    # 统计信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_llm_calls: int = 0
    total_cost: float = 0.0
    total_processing_time: float = 0.0
    
    def calculate_overall_progress(self) -> float:
        """计算整体进度"""
        steps = [
            self.step_1_import,
            self.step_2_script,
            self.step_3_novel,
            self.step_4_alignment
        ]
        total_progress = sum(step.overall_progress for step in steps)
        return total_progress / 4.0
    
    def get_current_step(self) -> Optional[PhaseStepState]:
        """获取当前正在处理的步骤"""
        for step in [self.step_1_import, self.step_2_script, self.step_3_novel, self.step_4_alignment]:
            if step.status == PhaseStatus.RUNNING:
                return step
        return None

class ProjectStats(BaseModel):
    """项目统计信息"""
    total_size: int = Field(0, description="总大小（字节）")
    raw_files_count: int = Field(0, description="原始文件数量")
    processed_files_count: int = Field(0, description="处理后文件数量")
    last_processed: Optional[str] = None

class ProjectMeta(BaseModel):
    """项目元数据"""
    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    status: ProjectStatus = Field(ProjectStatus.DRAFT, description="项目状态")
    
    sources: ProjectSources = Field(default_factory=ProjectSources, description="源文件信息")
    # 工作流系统（两个独立系统）
    workflow_stages: WorkflowStages = Field(
        default_factory=WorkflowStages,
        description="通用工作流阶段（预处理、分段、标注等）"
    )
    
    phase_i_analyst: Optional[PhaseIAnalystState] = Field(
        None,
        description="Phase I Analyst Agent 专用工作流（深度分析、对齐等）- 可选功能"
    )
    
    stats: ProjectStats = Field(default_factory=ProjectStats, description="统计信息")
    
    def to_dict(self) -> dict:
        """转换为字典（JSON可序列化格式）"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProjectMeta":
        """从字典创建"""
        return cls(**data)
    
    def initialize_phase_i(self):
        """初始化 Phase I 工作流状态"""
        if self.phase_i_analyst is None:
            self.phase_i_analyst = PhaseIAnalystState(
                step_1_import=Step1ImportState(
                    step_id="step_1_import",
                    step_name="文件导入与标准化",
                    status=PhaseStatus.READY,  # 第一步默认 READY
                    dependencies=DependencyCheck(is_met=True, message="无前置依赖")
                ),
                step_2_script=Step2ScriptAnalysisState(
                    step_id="step_2_script",
                    step_name="Script 分析",
                    status=PhaseStatus.LOCKED,
                    dependencies=DependencyCheck(
                        is_met=False,
                        missing_dependencies=["step_1_import"],
                        message="需要先完成文件导入"
                    )
                ),
                step_3_novel=Step3NovelAnalysisState(
                    step_id="step_3_novel",
                    step_name="Novel 分析",
                    status=PhaseStatus.LOCKED,
                    dependencies=DependencyCheck(
                        is_met=False,
                        missing_dependencies=["step_1_import"],
                        message="需要先完成文件导入"
                    )
                ),
                step_4_alignment=Step4AlignmentState(
                    step_id="step_4_alignment",
                    step_name="Script-Novel 对齐",
                    status=PhaseStatus.LOCKED,
                    dependencies=DependencyCheck(
                        is_met=False,
                        missing_dependencies=["step_2_script", "step_3_novel"],
                        message="需要先完成 Script 和 Novel 分析"
                    )
                )
            )
