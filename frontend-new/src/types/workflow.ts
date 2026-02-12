/**
 * Phase I Analyst Agent 工作流类型定义
 */

export type PhaseStatus =
  | 'locked'      // 依赖未满足
  | 'ready'       // 可以开始
  | 'running'     // 进行中
  | 'completed'   // 已完成
  | 'failed'      // 失败
  | 'cancelled'   // 已取消

export interface DependencyCheck {
  is_met: boolean
  missing_dependencies: string[]
  message?: string
}

export interface SubTaskProgress {
  task_id: string
  task_name: string
  status: PhaseStatus
  progress_percentage?: number
  started_at?: string
  completed_at?: string
  error_message?: string
  result_summary?: string
}

export interface PhaseStepState {
  step_id: string
  step_name: string
  status: PhaseStatus
  dependencies: DependencyCheck
  started_at?: string
  completed_at?: string
  last_updated?: string
  overall_progress: number
  sub_tasks: SubTaskProgress[]
  error_message?: string
  quality_score?: number
  result_path?: string
  llm_calls_count: number
  total_cost: number
  processing_time: number
}

export interface Step1ImportState extends PhaseStepState {
  novel_imported: boolean
  novel_file_name?: string
  novel_file_size: number
  novel_encoding?: string
  novel_chapter_count: number
  script_imported: boolean
  script_episodes: string[]
  script_total_entries: number
  script_total_duration: number
}

export interface Step2ScriptAnalysisState extends PhaseStepState {
  episodes_status: Record<string, {
    status: PhaseStatus
    phases: Record<string, {
      phase_id: string
      phase_name: string
      status: PhaseStatus
      started_at?: string
      completed_at?: string
      result_summary?: string
    }>
    quality_score?: number
    llm_calls: number
    cost: number
    processing_time: number
  }>
  total_episodes: number
  completed_episodes: number
  failed_episodes: number
}

export interface Step3NovelAnalysisState extends PhaseStepState {
  novel_steps: Record<string, {
    step_id: string
    step_name: string
    status: PhaseStatus
    started_at?: string
    completed_at?: string
    result_summary?: string
  }>
  total_chapters: number
  total_paragraphs: number
  total_events: number
  total_settings: number
  total_system_elements: number
}

export interface Step4AlignmentState extends PhaseStepState {
  alignment_pairs: Array<{
    episode_id: string
    chapter_ids: number[]
    status: PhaseStatus
  }>
  total_alignments: number
  average_match_confidence?: number
  event_coverage_rate?: number
  setting_coverage_rate?: number
}

export interface PhaseIAnalystState {
  phase_name: string
  overall_status: PhaseStatus
  overall_progress: number
  step_1_import: Step1ImportState
  step_2_script: Step2ScriptAnalysisState
  step_3_novel: Step3NovelAnalysisState
  step_4_alignment: Step4AlignmentState
  started_at?: string
  completed_at?: string
  total_llm_calls: number
  total_cost: number
  total_processing_time: number
}

// WebSocket 消息类型
export type WebSocketMessage =
  | { type: 'connected'; project_id: string; message: string; timestamp: string }
  | { type: 'step_started'; step_id: string; step_name: string; timestamp: string }
  | { type: 'step_completed'; step_id: string; step_name: string; quality_score?: number; timestamp: string }
  | { type: 'step_failed'; step_id: string; step_name: string; error_message: string; timestamp: string }
  | { type: 'progress_update'; step_id: string; progress: number; current_task?: string; timestamp: string }
  | { type: 'log'; step_id: string; level: 'info' | 'warning' | 'error'; message: string; timestamp: string }
  | { type: 'llm_thinking'; step_id: string; model: string; prompt_summary: string; response_summary: string; timestamp: string }

export interface WorkflowExecuteRequest {
  projectId: string
  workflowId: string
  params?: Record<string, any>
}

export interface WorkflowTask {
  taskId: string
  status: PhaseStatus
  result?: any
}
