import { apiClient } from './client'
import type {
  Project,
  ProjectStatsResponse,
  CreateProjectRequest,
  RawFile,
  Chapter,
  Episode,
  PreprocessStatus
} from '@/types/project'

/**
 * 项目管理 API V2
 * 使用新的数据存储架构和自动预处理功能
 */
export const projectsApiV2 = {
  /**
   * 获取所有项目列表
   */
  list: async (): Promise<{ projects: Project[]; total: number }> => {
    const response = await apiClient.get('/api/v2/projects')
    return response.data
  },

  /**
   * 获取所有项目列表 (Alias for list)
   */
  getProjects: async (): Promise<{ projects: Project[]; total: number }> => {
    const response = await apiClient.get('/api/v2/projects')
    return response.data
  },

  /**
   * 获取项目统计
   */
  getStats: async (): Promise<ProjectStatsResponse> => {
    const response = await apiClient.get('/api/v2/projects/stats')
    return response.data
  },

  /**
   * 获取项目详情
   */
  get: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}`)
    return response.data
  },

  /**
   * 获取项目完整元数据
   */
  getMeta: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/meta`)
    return response.data
  },

  /**
   * 创建新项目
   */
  create: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await apiClient.post('/api/v2/projects', data)
    return response.data
  },

  /**
   * 更新项目
   */
  update: async (projectId: string, data: Partial<CreateProjectRequest>): Promise<Project> => {
    const response = await apiClient.put(`/api/v2/projects/${projectId}`, data)
    return response.data
  },

  /**
   * 上传文件（自动触发预处理）
   */
  uploadFiles: async (
    projectId: string,
    files: File[],
    autoPreprocess: boolean = true
  ): Promise<{
    message: string
    files: { filename: string; size: number; type: string }[]
    auto_preprocess: boolean
  }> => {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })

    const response = await apiClient.post(
      `/api/v2/projects/${projectId}/upload?auto_preprocess=${autoPreprocess}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  /**
   * 手动触发预处理
   */
  triggerPreprocess: async (projectId: string, filename?: string, category?: 'novel' | 'script'): Promise<{ message: string; project_id: string; file?: string; category?: string }> => {
    const response = await apiClient.post(`/api/v2/projects/${projectId}/preprocess`, { filename, category })
    return response.data
  },

  /**
   * 获取预处理状态
   */
  getPreprocessStatus: async (projectId: string): Promise<PreprocessStatus> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/preprocess/status`)
    return response.data
  },

  /**
   * 取消预处理任务
   */
  cancelPreprocess: async (projectId: string): Promise<{ message: string; project_id: string; note: string }> => {
    const response = await apiClient.post(`/api/v2/projects/${projectId}/preprocess/cancel`)
    return response.data
  },

  /**
   * 获取原始文件列表
   */
  getFiles: async (projectId: string): Promise<{ files: RawFile[] }> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/files`)
    return response.data
  },

  /**
   * 获取小说章节列表
   */
  getChapters: async (projectId: string): Promise<{ total_chapters: number; chapters: Chapter[] }> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/chapters`)
    return response.data
  },

  /**
   * 获取脚本集数列表
   */
  getEpisodes: async (projectId: string): Promise<{ total_episodes: number; episodes: Episode[] }> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/episodes`)
    return response.data
  },

  /**
   * 获取导入后的Script Markdown（句子级时间标注）
   */
  getImportedScript: async (projectId: string, episodeId: string): Promise<string> => {
    // 直接使用fetch因为axios会解析HTML
    const response = await fetch(`http://localhost:8000/data/projects/${projectId}/analyst/import/script/${episodeId}-imported.md`)
    return await response.text()
  },

  /**
   * 获取单个集数的详细信息
   */
  getEpisodeDetail: async (projectId: string, episodeName: string): Promise<any> => {
    const response = await apiClient.get(`/api/v2/projects/${projectId}/episodes/${episodeName}`)
    return response.data
  },

  /**
   * 删除项目
   */
  delete: async (projectId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/v2/projects/${projectId}`)
    return response.data
  },

  // ============ Analyst Results APIs ============
  
  /**
   * Step 2: Script Analysis - 获取分段结果
   */
  getScriptSegmentation: async (projectId: string, episodeId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/script_analysis/${episodeId}/segmentation`
    )
    return response.data
  },

  /**
   * Step 2: Script Analysis - 获取Hook检测结果
   */
  getScriptHook: async (projectId: string, episodeId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/script_analysis/${episodeId}/hook`
    )
    return response.data
  },

  /**
   * Step 2: Script Analysis - 获取质量报告
   */
  getScriptValidation: async (projectId: string, episodeId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/script_analysis/${episodeId}/validation`
    )
    return response.data
  },

  /**
   * Step 2: Script Analysis - 获取汇总统计
   */
  getScriptAnalysisSummary: async (projectId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/script_analysis/summary`
    )
    return response.data
  },

  /**
   * Step 3: Novel Analysis - 获取章节列表及状态
   */
  getNovelAnalysisChapters: async (projectId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/novel_analysis/chapters`
    )
    return response.data
  },

  /**
   * Step 3: Novel Analysis - 获取单章分段结果
   */
  getNovelSegmentation: async (projectId: string, chapterId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/novel_analysis/${chapterId}/segmentation`
    )
    return response.data
  },

  /**
   * Step 3: Novel Analysis - 获取单章标注结果
   */
  getNovelAnnotation: async (projectId: string, chapterId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/novel_analysis/${chapterId}/annotation`
    )
    return response.data
  },

  /**
   * Step 3: Novel Analysis - 获取系统元素目录
   */
  getSystemCatalog: async (projectId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/novel_analysis/system_catalog`
    )
    return response.data
  },

  /**
   * Step 3: Novel Analysis - 获取质量报告
   */
  getNovelValidation: async (projectId: string, chapterId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/novel_analysis/${chapterId}/validation`
    )
    return response.data
  },

  /**
   * Step 4: Alignment - 获取对齐对列表
   */
  getAlignmentPairs: async (projectId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/alignment/pairs`
    )
    return response.data
  },

  /**
   * Step 4: Alignment - 获取对齐详情
   */
  getAlignmentResult: async (projectId: string, chapterId: string, episodeId: string) => {
    const response = await apiClient.get(
      `/api/v2/projects/${projectId}/analyst/alignment/${chapterId}/${episodeId}`
    )
    return response.data
  },

  /**
   * 删除原始文件。category 为 novel/srt 时从对应子目录删除。
   */
  deleteFile: async (
    projectId: string,
    filename: string,
    category?: 'novel' | 'srt'
  ): Promise<{ message: string }> => {
    let url = `/api/v2/projects/${projectId}/files/${encodeURIComponent(filename)}`
    if (category) url += `?category=${encodeURIComponent(category)}`
    const response = await apiClient.delete(url)
    return response.data
  },

  /**
   * 获取原始文件预览 URL。category 为 novel/srt 时加查询参数。
   */
  getFileViewUrl: (projectId: string, filename: string, category?: 'novel' | 'srt'): string => {
    const base = apiClient.defaults.baseURL ?? ''
    let path = `/api/v2/projects/${projectId}/files/${encodeURIComponent(filename)}/view`
    if (category) path += `?category=${encodeURIComponent(category)}`
    return base.endsWith('/') ? `${base.slice(0, -1)}${path}` : `${base}${path}`
  },

  /**
   * 获取原始文件内容
   */
  getFileContent: async (projectId: string, filename: string, category?: 'novel' | 'srt'): Promise<string> => {
    let url = `/api/v2/projects/${projectId}/files/${encodeURIComponent(filename)}/view`
    if (category) url += `?category=${encodeURIComponent(category)}`
    const response = await apiClient.get(url, { responseType: 'text' })
    return response.data
  },
}
