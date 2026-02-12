/**
 * 项目相关类型定义
 */

// V1 类型（旧版）
export interface ProjectV1 {
  id: string
  name: string
  source_path: string
  status: 'discovered' | 'initialized'
  created_at: string
  initialized_at?: string
}

// V2 类型（新版）
export type ProjectStatus = 'draft' | 'ready' | 'processing' | 'completed' | 'error'
export type WorkflowStageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

export interface PreprocessTask {
  task_id: string
  task_type: 'novel' | 'script'
  task_name: string
  status: WorkflowStageStatus
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  current_step?: string | null
  progress?: string | null
}

export interface WorkflowStageInfo {
  status: WorkflowStageStatus
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  tasks?: PreprocessTask[]
}

export interface WorkflowStages {
  import_stage: WorkflowStageInfo
  preprocess: WorkflowStageInfo
  novel_segmentation: WorkflowStageInfo
  novel_annotation: WorkflowStageInfo
  script_segmentation: WorkflowStageInfo
  script_hooks: WorkflowStageInfo
  alignment: WorkflowStageInfo
}

export interface ProjectSources {
  has_novel: boolean
  has_script: boolean
  novel_chapters: number
  script_episodes: number
  other_files: number
}

export interface ProjectStats {
  total_size: number
  raw_files_count: number
  processed_files_count: number
  last_processed: string | null
}

export interface ProjectV2 {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  status: ProjectStatus
  sources: ProjectSources
  workflow_stages: WorkflowStages
  stats: ProjectStats
}

// 默认导出 V2 类型
export type Project = ProjectV2

// 统计信息
export interface ProjectStatsResponse {
  total_projects: number
  initialized: number
  discovered: number
}

export interface CreateProjectRequest {
  name: string
  description?: string
}

// 文件相关（category: raw 下分类目录 novel / srt）
export interface RawFile {
  name: string
  size: number
  type: string
  uploaded_at: string
  category?: 'novel' | 'srt'
}

// 章节信息
export interface Chapter {
  chapter_number: number
  title: string
  start_line: number
  end_line: number
  char_count: number
}

// 集数信息
export interface Episode {
  episode_name: string
  entry_count: number
  word_count: number
}

// 预处理状态
export interface PreprocessStatus {
  project_id: string
  preprocess_stage: WorkflowStageInfo
}
