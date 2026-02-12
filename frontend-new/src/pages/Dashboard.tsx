import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { projectsApiV2 } from '@/api/projectsV2'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Plus, FolderKanban, BookOpen, Film, Calendar, TrendingUp, MoreVertical, Pencil, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import type { CreateProjectRequest, Project } from '@/types/project'

export default function DashboardPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')

  // Edit State
  const [projectToEdit, setProjectToEdit] = useState<Project | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')

  // Delete State
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null)

  // 获取项目统计
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['project-stats'],
    queryFn: projectsApiV2.getStats,
  })

  // 获取项目列表
  const { data: projectsData, isLoading: projectsLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApiV2.list,
  })

  const projects = projectsData?.projects ?? []

  // 创建项目
  const createMutation = useMutation({
    mutationFn: (data: CreateProjectRequest) => projectsApiV2.create(data),
    onSuccess: (newProject) => {
      toast.success('Project created successfully')
      setNewProjectName('')
      setNewProjectDesc('')
      setShowCreateDialog(false)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project-stats'] })
      // 自动导航到新项目
      navigate(`/project/${newProject.id}`)
    },
    onError: () => {
      toast.error('Failed to create project')
    },
  })

  // 更新项目
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateProjectRequest> }) =>
      projectsApiV2.update(id, data),
    onSuccess: () => {
      toast.success('Project updated successfully')
      setProjectToEdit(null)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      toast.error('Failed to update project')
    },
  })

  // 删除项目
  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApiV2.delete(id),
    onSuccess: () => {
      toast.success('Project deleted successfully')
      setProjectToDelete(null)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project-stats'] })
    },
    onError: () => {
      toast.error('Failed to delete project')
    },
  })

  const handleCreateProject = () => {
    if (!newProjectName.trim()) {
      toast.error('Please enter project name')
      return
    }
    createMutation.mutate({
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || undefined,
    })
  }

  const handleUpdateProject = () => {
    if (!projectToEdit) return
    if (!editName.trim()) {
      toast.error('Please enter project name')
      return
    }
    updateMutation.mutate({
      id: projectToEdit.id,
      data: {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      },
    })
  }

  const openEditDialog = (project: Project, e: React.MouseEvent) => {
    e.stopPropagation()
    setProjectToEdit(project)
    setEditName(project.name)
    setEditDesc(project.description || '')
  }

  const openDeleteDialog = (project: Project, e: React.MouseEvent) => {
    e.stopPropagation()
    setProjectToDelete(project)
  }

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        {/* Header */}
        <div className="px-4 lg:px-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
            <p className="text-muted-foreground mt-1">
              Manage and organize your analysis projects
            </p>
          </div>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="px-4 lg:px-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {statsLoading ? (
            <>
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </>
          ) : (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Projects</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-baseline gap-2">
                    <div className="text-3xl font-bold">{stats?.total_projects ?? 0}</div>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Initialized</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{stats?.initialized ?? 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Discovered</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{stats?.discovered ?? 0}</div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Projects List */}
        <div className="px-4 lg:px-6">
          <h3 className="text-lg font-semibold mb-4">All Projects</h3>
          {projectsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-48" />
              ))}
            </div>
          ) : projects.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <FolderKanban className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Create your first project to get started
                </p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Project
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <Card
                  key={project.id}
                  className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
                  onClick={() => navigate(`/project/${project.id}`)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="truncate">{project.name}</CardTitle>
                        {project.description && (
                          <CardDescription className="line-clamp-2 mt-1.5">
                            {project.description}
                          </CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={project.status === 'completed' ? 'default' : 'secondary'}>
                          {project.status}
                        </Badge>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 -mr-2"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={(e) => openEditDialog(project, e)}>
                              <Pencil className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={(e) => openDeleteDialog(project, e)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Sources */}
                    <div className="flex items-center gap-4 text-sm">
                      {project.sources.has_novel && (
                        <div className="flex items-center gap-1.5">
                          <BookOpen className="h-4 w-4 text-primary" />
                          <span className="font-medium">{project.sources.novel_chapters}</span>
                          <span className="text-muted-foreground">chapters</span>
                        </div>
                      )}
                      {project.sources.has_script && (
                        <div className="flex items-center gap-1.5">
                          <Film className="h-4 w-4 text-accent" />
                          <span className="font-medium">{project.sources.script_episodes}</span>
                          <span className="text-muted-foreground">episodes</span>
                        </div>
                      )}
                    </div>

                    {/* Created Date */}
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Calendar className="h-3.5 w-3.5" />
                      {format(new Date(project.created_at), 'MMM d, yyyy')}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Project Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Project</DialogTitle>
            <DialogDescription>
              Create a new analysis project to get started.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Project Name *</Label>
              <Input
                id="name"
                placeholder="Enter project name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleCreateProject()
                  }
                }}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                placeholder="Enter project description"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false)
                setNewProjectName('')
                setNewProjectDesc('')
              }}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              disabled={createMutation.isPending || !newProjectName.trim()}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Project Dialog */}
      <Dialog open={!!projectToEdit} onOpenChange={(open: boolean) => !open && setProjectToEdit(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
            <DialogDescription>
              Update project details.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Project Name *</Label>
              <Input
                id="edit-name"
                placeholder="Enter project name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description (Optional)</Label>
              <Input
                id="edit-description"
                placeholder="Enter project description"
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setProjectToEdit(null)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateProject}
              disabled={updateMutation.isPending || !editName.trim()}
            >
              {updateMutation.isPending ? 'Updating...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Project Alert */}
      <AlertDialog open={!!projectToDelete} onOpenChange={(open) => !open && setProjectToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the project
              <span className="font-medium text-foreground"> {projectToDelete?.name} </span>
              and all associated files.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={(e: React.MouseEvent) => {
                e.preventDefault()
                if (projectToDelete) deleteMutation.mutate(projectToDelete.id)
              }}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete Project'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
