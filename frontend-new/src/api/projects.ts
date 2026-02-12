import { apiClient } from './client'
import type { Project, ProjectStatsResponse, CreateProjectRequest } from '@/types/project'

/**
 * 项目管理 API
 */
export const projectsApi = {
  /**
   * 获取所有项目列表
   */
  list: async (): Promise<{ projects: Project[]; total: number }> => {
    const response = await apiClient.get('/api/projects')
    return response.data
  },

  /**
   * 获取项目统计
   */
  getStats: async (): Promise<ProjectStatsResponse> => {
    const response = await apiClient.get('/api/projects/stats')
    return response.data
  },

  /**
   * 获取项目详情
   */
  get: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get(`/api/projects/${projectId}`)
    return response.data
  },

  /**
   * 创建新项目
   */
  create: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await apiClient.post('/api/projects', data)
    return response.data
  },

  /**
   * 上传文件
   */
  uploadFiles: async (projectId: string, files: File[]): Promise<{ message: string; files: string[] }> => {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await apiClient.post(`/api/projects/${projectId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * 初始化项目
   */
  initialize: async (projectId: string): Promise<Project> => {
    const response = await apiClient.post(`/api/projects/${projectId}/initialize`)
    return response.data
  },

  /**
   * 删除项目
   */
  delete: async (projectId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/projects/${projectId}`)
    return response.data
  },
}
