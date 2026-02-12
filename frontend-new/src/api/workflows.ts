import { apiClient } from './client'
import type { WorkflowExecuteRequest, WorkflowTask } from '@/types/workflow'

/**
 * 工作流 API
 */
export const workflowsApi = {
  /**
   * 执行工作流
   */
  execute: async (data: WorkflowExecuteRequest): Promise<WorkflowTask> => {
    const response = await apiClient.post('/api/workflows/execute', data)
    return response.data
  },

  /**
   * 获取工作流状态
   */
  getStatus: async (taskId: string): Promise<WorkflowTask> => {
    const response = await apiClient.get(`/api/workflows/${taskId}`)
    return response.data
  },

  /**
   * 列出所有工作流任务
   */
  list: async (): Promise<WorkflowTask[]> => {
    const response = await apiClient.get('/api/workflows')
    return response.data
  },

  /**
   * 取消工作流
   */
  cancel: async (taskId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/api/workflows/${taskId}/cancel`)
    return response.data
  },
}
