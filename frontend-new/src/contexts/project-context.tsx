import * as React from 'react'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import type { Project } from '@/types/project'

interface ProjectContextValue {
  currentProject: Project | null
  setCurrentProject: (project: Project | null) => void
  projects: Project[]
  isLoading: boolean
  refetch: () => void
}

const ProjectContext = React.createContext<ProjectContextValue | null>(null)

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [currentProject, setCurrentProject] = React.useState<Project | null>(null)

  // 获取所有项目列表
  const { data: projectsData, isLoading, refetch } = useQuery({
    queryKey: ['projects-list'],
    queryFn: () => projectsApiV2.list(),
    refetchOnWindowFocus: false,
  })

  const projects = projectsData?.projects ?? []

  // 自动设置第一个项目为当前项目（如果没有选中的项目）
  React.useEffect(() => {
    if (!currentProject && projects.length > 0) {
      // 从 localStorage 恢复上次选中的项目
      const savedProjectId = localStorage.getItem('currentProjectId')
      if (savedProjectId) {
        const savedProject = projects.find((p) => p.id === savedProjectId)
        if (savedProject) {
          setCurrentProject(savedProject)
          return
        }
      }
      // 否则选择第一个项目
      setCurrentProject(projects[0])
    }
  }, [projects, currentProject])

  // 保存当前项目到 localStorage
  React.useEffect(() => {
    if (currentProject) {
      localStorage.setItem('currentProjectId', currentProject.id)
    }
  }, [currentProject])

  const value = React.useMemo<ProjectContextValue>(
    () => ({
      currentProject,
      setCurrentProject,
      projects,
      isLoading,
      refetch,
    }),
    [currentProject, projects, isLoading, refetch]
  )

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>
}

export function useProject() {
  const context = React.useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider')
  }
  return context
}
