/**
 * Workflow State API Client
 */
import type { PhaseIAnalystState } from '@/types/workflow'

const API_BASE = '/api/v2/projects'

export const workflowStateApi = {
  /**
   * 获取工作流状态
   */
  async getWorkflowState(projectId: string): Promise<PhaseIAnalystState> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow-state`)
    if (!response.ok) {
      throw new Error('Failed to fetch workflow state')
    }
    return response.json()
  },

  /**
   * 启动指定步骤
   */
  async startStep(projectId: string, stepId: string): Promise<{ message: string; step_id: string }> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow/${stepId}/start`, {
      method: 'POST',
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to start step')
    }
    return response.json()
  },

  /**
   * 标记步骤为完成
   */
  async completeStep(
    projectId: string,
    stepId: string,
    qualityScore?: number,
    resultPath?: string
  ): Promise<{ message: string; step_id: string }> {
    const params = new URLSearchParams()
    if (qualityScore !== undefined) {
      params.append('quality_score', qualityScore.toString())
    }
    if (resultPath) {
      params.append('result_path', resultPath)
    }

    const response = await fetch(
      `${API_BASE}/${projectId}/workflow/${stepId}/complete?${params.toString()}`,
      { method: 'POST' }
    )
    if (!response.ok) {
      throw new Error('Failed to complete step')
    }
    return response.json()
  },

  /**
   * 标记步骤为失败
   */
  async failStep(
    projectId: string,
    stepId: string,
    errorMessage: string
  ): Promise<{ message: string; step_id: string }> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow/${stepId}/fail`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ error_message: errorMessage }).toString(),
    })
    if (!response.ok) {
      throw new Error('Failed to mark step as failed')
    }
    return response.json()
  },

  /**
   * 更新步骤进度
   */
  async updateProgress(
    projectId: string,
    stepId: string,
    progress: number,
    currentTask?: string
  ): Promise<{ message: string; progress: number }> {
    const params = new URLSearchParams({ progress: progress.toString() })
    if (currentTask) {
      params.append('current_task', currentTask)
    }

    const response = await fetch(
      `${API_BASE}/${projectId}/workflow/${stepId}/progress?${params.toString()}`,
      { method: 'POST' }
    )
    if (!response.ok) {
      throw new Error('Failed to update progress')
    }
    return response.json()
  },

  /**
   * 停止步骤
   */
  async stopStep(projectId: string, stepId: string): Promise<{ message: string; step_id: string }> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow/${stepId}/stop`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error('Failed to stop step')
    }
    return response.json()
  },

  /**
   * 启动单个episode处理
   */
  async startEpisode(projectId: string, episodeId: string): Promise<{ message: string; episode_id: string }> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow/step_2_script/episode/${episodeId}/start`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error('Failed to start episode')
    }
    return response.json()
  },

  /**
   * 停止单个episode处理
   */
  async stopEpisode(projectId: string, episodeId: string): Promise<{ message: string; episode_id: string }> {
    const response = await fetch(`${API_BASE}/${projectId}/workflow/step_2_script/episode/${episodeId}/stop`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error('Failed to stop episode')
    }
    return response.json()
  },

  /**
   * 创建 WebSocket 连接
   */
  createWebSocket(projectId: string): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/api/v2/projects/${projectId}/ws`)
    return ws
  },
}
