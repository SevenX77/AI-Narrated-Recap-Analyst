import * as React from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { useProject } from '@/contexts/project-context'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Plus,
  Trash2,
  Eye,
  Calendar,
  BookOpen,
  Film,
  FolderOpen,
  MoreVertical,
  Folder,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { format } from 'date-fns'
import { toast } from 'sonner'
import type { CreateProjectRequest } from '@/types/project'
import { cn } from '@/lib/utils'

interface ProjectManagerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ProjectManagerDialog({ open, onOpenChange }: ProjectManagerDialogProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { projects, isLoading, refetch, setCurrentProject } = useProject()
  const [showCreateForm, setShowCreateForm] = React.useState(false)
  const [newProjectName, setNewProjectName] = React.useState('')
  const [newProjectDesc, setNewProjectDesc] = React.useState('')

  // 创建项目
  const createMutation = useMutation({
    mutationFn: (data: CreateProjectRequest) => projectsApiV2.create(data),
    onSuccess: (newProject) => {
      toast.success('项目创建成功')
      setNewProjectName('')
      setNewProjectDesc('')
      setShowCreateForm(false)
      refetch()
      queryClient.invalidateQueries({ queryKey: ['projects-list'] })
      // 自动选择新创建的项目
      setCurrentProject(newProject)
    },
    onError: () => {
      toast.error('项目创建失败')
    },
  })

  // 删除项目
  const deleteMutation = useMutation({
    mutationFn: (projectId: string) => projectsApiV2.delete(projectId),
    onSuccess: () => {
      toast.success('项目删除成功')
      refetch()
      queryClient.invalidateQueries({ queryKey: ['projects-list'] })
    },
    onError: () => {
      toast.error('项目删除失败')
    },
  })

  const handleCreateProject = () => {
    if (!newProjectName.trim()) {
      toast.error('请输入项目名称')
      return
    }
    createMutation.mutate({
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || undefined,
    })
  }

  const handleDeleteProject = (projectId: string, projectName: string) => {
    if (confirm(`确定要删除项目 "${projectName}" 吗？此操作不可撤销。`)) {
      deleteMutation.mutate(projectId)
    }
  }

  const handleViewProject = (projectId: string) => {
    onOpenChange(false)
    navigate(`/project/${projectId}`)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl max-h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-8 pt-8 pb-4 border-b">
          <DialogTitle className="flex items-center gap-3 text-3xl font-semibold">
            <FolderOpen className="size-8" />
            项目管理
          </DialogTitle>
          <DialogDescription className="text-base">
            管理所有项目，创建新项目或删除不需要的项目
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto px-8 py-6">
          {/* 创建新项目对话框 */}
          {showCreateForm && (
            <Card className="border-2 border-dashed mb-6 bg-muted/30">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">创建新项目</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="project-name">项目名称 *</Label>
                  <Input
                    id="project-name"
                    placeholder="输入项目名称"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCreateProject()
                      }
                    }}
                    autoFocus
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-desc">项目描述（可选）</Label>
                  <Input
                    id="project-desc"
                    placeholder="输入项目描述"
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <Button
                    onClick={handleCreateProject}
                    disabled={createMutation.isPending || !newProjectName.trim()}
                    className="gap-2 flex-1"
                  >
                    {createMutation.isPending && <Spinner size="sm" />}
                    创建项目
                  </Button>
                  <Button
                    onClick={() => {
                      setShowCreateForm(false)
                      setNewProjectName('')
                      setNewProjectDesc('')
                    }}
                    variant="outline"
                    disabled={createMutation.isPending}
                  >
                    取消
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 项目网格 */}
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner className="size-8" />
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {/* 创建新项目卡片 */}
              {!showCreateForm && (
                <Card
                  className={cn(
                    'group relative overflow-hidden cursor-pointer',
                    'border-2 border-dashed hover:border-primary',
                    'transition-all duration-200',
                    'hover:shadow-lg hover:scale-[1.02]'
                  )}
                  onClick={() => setShowCreateForm(true)}
                >
                  {/* 预览区域 */}
                  <div className="aspect-video bg-muted/30 flex items-center justify-center">
                    <Plus className="size-16 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  {/* 项目信息 */}
                  <CardContent className="p-4">
                    <div className="text-center">
                      <p className="font-medium text-muted-foreground group-hover:text-primary transition-colors">
                        创建新项目
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 项目卡片 */}
              {projects.map((project) => (
                <Card
                  key={project.id}
                  className={cn(
                    'group relative overflow-hidden cursor-pointer',
                    'border hover:border-primary/50',
                    'transition-all duration-200',
                    'hover:shadow-xl hover:scale-[1.02]'
                  )}
                  onClick={() => handleViewProject(project.id)}
                >
                  {/* 预览区域 */}
                  <div className="aspect-video bg-gradient-to-br from-primary/10 via-accent/10 to-muted relative overflow-hidden">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Folder className="size-20 text-muted-foreground/20" />
                    </div>
                    {/* 状态标识 */}
                    <Badge
                      className="absolute top-3 right-3"
                      variant={project.status === 'completed' ? 'default' : 'secondary'}
                    >
                      {project.status}
                    </Badge>
                    {/* 操作菜单 */}
                    <div className="absolute top-3 left-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button size="icon" variant="secondary" className="size-8">
                            <MoreVertical className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation()
                              handleViewProject(project.id)
                            }}
                          >
                            <Eye className="size-4 mr-2" />
                            查看项目
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteProject(project.id, project.name)
                            }}
                            className="text-destructive focus:text-destructive"
                          >
                            <Trash2 className="size-4 mr-2" />
                            删除项目
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {/* 项目信息 */}
                  <CardContent className="p-4 space-y-2">
                    {/* 项目名称 */}
                    <div>
                      <h3 className="font-semibold text-base truncate group-hover:text-primary transition-colors">
                        {project.name}
                      </h3>
                      {project.description && (
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-1">
                          {project.description}
                        </p>
                      )}
                    </div>

                    {/* 数据源指示器 */}
                    <div className="flex items-center gap-3 pt-2">
                      {project.sources.has_novel && (
                        <div className="flex items-center gap-1.5 text-xs">
                          <BookOpen className="size-3.5 text-primary" />
                          <span className="font-medium">{project.sources.novel_chapters}</span>
                          <span className="text-muted-foreground">章</span>
                        </div>
                      )}
                      {project.sources.has_script && (
                        <div className="flex items-center gap-1.5 text-xs">
                          <Film className="size-3.5 text-accent" />
                          <span className="font-medium">{project.sources.script_episodes}</span>
                          <span className="text-muted-foreground">集</span>
                        </div>
                      )}
                      {!project.sources.has_novel && !project.sources.has_script && (
                        <span className="text-xs text-muted-foreground">无数据</span>
                      )}
                    </div>

                    {/* 创建日期 */}
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground pt-1">
                      <Calendar className="size-3" />
                      <span>{format(new Date(project.created_at), 'yyyy-MM-dd')}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* 空状态 */}
          {!isLoading && projects.length === 0 && !showCreateForm && (
            <div className="text-center py-20">
              <FolderOpen className="size-20 mx-auto mb-6 text-muted-foreground/30" />
              <h3 className="text-xl font-semibold mb-2">暂无项目</h3>
              <p className="text-muted-foreground mb-6">创建您的第一个项目开始工作</p>
              <Button onClick={() => setShowCreateForm(true)} size="lg" className="gap-2">
                <Plus className="size-5" />
                创建新项目
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
