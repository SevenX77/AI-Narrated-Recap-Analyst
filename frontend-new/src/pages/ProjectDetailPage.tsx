import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Skeleton } from '@/components/ui/skeleton'
import { FileUpload } from '@/components/ui/file-upload'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Separator } from '@/components/ui/separator'
import {
  Upload,
  BookOpen,
  Film,
  File,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  RefreshCw,
  Trash2,
  Play,
  Eye,
} from 'lucide-react'
import { format } from 'date-fns'
import type { WorkflowStageStatus } from '@/types/project'
import { useState } from 'react'
import { toast } from 'sonner'

const stageStatusConfig: Record<WorkflowStageStatus, { icon: React.ReactNode; color: string }> = {
  pending: { icon: <Clock className="h-4 w-4" />, color: 'text-muted-foreground' },
  running: { icon: <Spinner size="sm" />, color: 'text-yellow-500' },
  completed: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-500' },
  failed: { icon: <XCircle className="h-4 w-4" />, color: 'text-red-500' },
  skipped: { icon: <AlertCircle className="h-4 w-4" />, color: 'text-muted-foreground' },
}

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [uploadFiles, setUploadFiles] = useState<File[]>([])
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [viewingFile, setViewingFile] = useState<{ name: string; category?: 'novel' | 'srt' } | null>(null)

  if (!projectId) {
    return <div className="p-6">Project ID not found</div>
  }

  // 上传文件
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (uploadFiles.length === 0) return
      return projectsApiV2.uploadFiles(projectId, uploadFiles, true)
    },
    onSuccess: () => {
      setUploadFiles([])
      setUploadDialogOpen(false)
      toast.success('Files uploaded successfully')
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['preprocess-status', projectId] })
    },
    onError: () => {
      toast.error('Failed to upload files')
    }
  })

  // 获取项目详情
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApiV2.get(projectId),
    refetchInterval: (query) => {
      return query.state.data?.status === 'processing' ? 5000 : false
    },
  })

  // 获取原始文件列表
  const { data: filesData } = useQuery({
    queryKey: ['project-files', projectId],
    queryFn: () => projectsApiV2.getFiles(projectId),
  })

  // 获取章节列表
  const { data: chaptersData } = useQuery({
    queryKey: ['project-chapters', projectId],
    queryFn: () => projectsApiV2.getChapters(projectId),
    enabled: project?.sources.has_novel ?? false,
  })

  // 获取集数列表
  const { data: episodesData } = useQuery({
    queryKey: ['project-episodes', projectId],
    queryFn: () => projectsApiV2.getEpisodes(projectId),
    enabled: project?.sources.has_script ?? false,
  })

  // 获取预处理状态
  const { data: preprocessStatus } = useQuery({
    queryKey: ['preprocess-status', projectId],
    queryFn: () => projectsApiV2.getPreprocessStatus(projectId),
    refetchInterval: (query) => {
      return query.state.data?.preprocess_stage?.status === 'running' ? 3000 : false
    },
  })

  // 取消预处理
  const cancelPreprocessMutation = useMutation({
    mutationFn: () => projectsApiV2.cancelPreprocess(projectId),
    onSuccess: () => {
      toast.success('Preprocessing cancelled')
      queryClient.invalidateQueries({ queryKey: ['preprocess-status', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  // 重新预处理
  const retryPreprocessMutation = useMutation({
    mutationFn: () => projectsApiV2.triggerPreprocess(projectId),
    onSuccess: () => {
      toast.success('Preprocessing started')
      queryClient.invalidateQueries({ queryKey: ['preprocess-status', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  // 删除文件（传入 category 以从正确子目录删除）
  const deleteFileMutation = useMutation({
    mutationFn: ({ filename, category }: { filename: string; category?: 'novel' | 'srt' }) =>
      projectsApiV2.deleteFile(projectId, filename, category),
    onSuccess: () => {
      toast.success('File deleted')
      queryClient.invalidateQueries({ queryKey: ['project-files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  if (projectLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (!project) {
    return <div className="p-6">Project not found</div>
  }

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <div className="px-4 lg:px-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
            <Badge variant={project.status === 'completed' ? 'default' : 'secondary'}>
              {project.status}
            </Badge>
          </div>
          {project.description && (
            <p className="text-muted-foreground mt-2">{project.description}</p>
          )}
        </div>
      </div>

      <Separator />

      {/* Metadata Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              Created At
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-base font-mono">
              {format(new Date(project.created_at), 'yyyy-MM-dd HH:mm')}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {project.sources.has_novel && (
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-primary" />
                  <span className="font-mono text-sm">{project.sources.novel_chapters} chapters</span>
                </div>
              )}
              {project.sources.has_script && (
                <div className="flex items-center gap-2">
                  <Film className="h-4 w-4 text-accent" />
                  <span className="font-mono text-sm">{project.sources.script_episodes} episodes</span>
                </div>
              )}
              {!project.sources.has_novel && !project.sources.has_script && (
                <span className="text-sm text-muted-foreground">No sources yet</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Raw files:</span>
                <span className="font-mono font-medium">{project.stats.raw_files_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Processed:</span>
                <span className="font-mono font-medium">{project.stats.processed_files_count}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content Viewers - Novel & Scripts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {project.sources.has_novel && (
          <Card
            className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
            onClick={() => navigate(`/project/${projectId}/novel`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                Novel
              </CardTitle>
              <CardDescription>
                {chaptersData?.total_chapters ?? 0} chapters available
              </CardDescription>
            </CardHeader>
            <CardContent>
              {chaptersData && chaptersData.chapters.length > 0 ? (
                <p className="text-sm text-muted-foreground">
                  Click to view novel content with chapter navigation
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No chapters found. Upload a novel file to see chapters.
                </p>
              )}
            </CardContent>
          </Card>
        )}
        {project.sources.has_script && (
          <Card
            className="cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
            onClick={() => navigate(`/project/${projectId}/script`)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Film className="h-5 w-5 text-accent" />
                Scripts
              </CardTitle>
              <CardDescription>
                {episodesData?.total_episodes ?? 0} episodes available
              </CardDescription>
            </CardHeader>
            <CardContent>
              {episodesData && episodesData.episodes.length > 0 ? (
                <p className="text-sm text-muted-foreground">
                  Click to view script content with episode navigation
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No episodes found. Upload script files to see episodes.
                </p>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Raw Files */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle className="flex items-center gap-2">
              <File className="h-5 w-5" />
              Raw Files ({filesData?.files.length ?? 0})
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => setUploadDialogOpen(true)}
            >
              <Upload className="h-4 w-4" />
              Upload
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {filesData && filesData.files.length > 0 ? (
            <Accordion type="multiple" defaultValue={['novel', 'srt']} className="w-full space-y-2">
              {(['novel', 'srt'] as const).map((cat) => {
                const categoryFiles = filesData.files.filter(
                  (f) => (f.category ?? (f.type === 'script' ? 'srt' : 'novel')) === cat
                )
                if (categoryFiles.length === 0) return null
                const categoryLabel = cat === 'novel' ? 'Novel' : 'SRT'
                return (
                  <AccordionItem key={cat} value={cat} className="border rounded-lg px-2">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <div className="flex items-center gap-2">
                        <span className="text-foreground">{categoryLabel}</span>
                        <span className="text-xs text-muted-foreground">({categoryFiles.length})</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-2">
                      <div className="space-y-1">
                        {categoryFiles.map((file) => (
                          <div
                            key={`${file.category ?? 'root'}-${file.name}`}
                            className="flex items-center justify-between rounded-md p-2 hover:bg-accent/50 transition-colors"
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <File className="h-4 w-4 shrink-0 text-muted-foreground" />
                              <div className="flex-1 min-w-0">
                                <div className="font-mono text-sm truncate">{file.name}</div>
                                <div className="text-xs text-muted-foreground">
                                  {(file.size / 1024).toFixed(2)} KB • {file.type} •{' '}
                                  {format(new Date(file.uploaded_at), 'yyyy-MM-dd HH:mm')}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => retryPreprocessMutation.mutate()}
                                disabled={retryPreprocessMutation.isPending || preprocessStatus?.preprocess_stage?.status === 'running'}
                                title="Process file"
                              >
                                {preprocessStatus?.preprocess_stage?.status === 'running' ? (
                                  <Spinner className="h-4 w-4" />
                                ) : (
                                  <Play className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => setViewingFile({ name: file.name, category: file.category })}
                                title="View file"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive hover:text-destructive"
                                onClick={() => {
                                  if (confirm(`Delete ${file.name}?`)) {
                                    deleteFileMutation.mutate({ filename: file.name, category: file.category })
                                  }
                                }}
                                disabled={deleteFileMutation.isPending}
                                title="Delete file"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                )
              })}
            </Accordion>
          ) : (
            <p className="text-sm text-muted-foreground py-4">
              No raw files yet. Click Upload to add novel (.txt) or script (.srt) files.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Upload Files</DialogTitle>
            <DialogDescription>
              Upload novel (.txt) or script (.srt) files to process. Preprocessing will run automatically.
            </DialogDescription>
          </DialogHeader>
          <FileUpload
            accept=".txt,.srt,.md,.pdf"
            multiple
            value={uploadFiles}
            onFilesChange={setUploadFiles}
          />
          {uploadFiles.length > 0 && (
            <DialogFooter className="gap-2 sm:gap-0">
              <Button
                onClick={() => uploadMutation.mutate()}
                disabled={uploadMutation.isPending}
                className="gap-2"
              >
                {uploadMutation.isPending && <Spinner size="sm" />}
                Upload {uploadFiles.length} file(s)
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>

      {/* View File Overlay */}
      <Dialog open={!!viewingFile} onOpenChange={(open: boolean) => !open && setViewingFile(null)}>
        <DialogContent className="sm:max-w-4xl max-h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle className="font-mono truncate pr-8">{viewingFile?.name ?? ''}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 min-h-0 px-6 pb-6">
            {viewingFile && (
              <iframe
                title={viewingFile.name}
                src={projectsApiV2.getFileViewUrl(projectId, viewingFile.name, viewingFile.category)}
                className="w-full h-[70vh] rounded-md border bg-muted/30"
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Preprocessing Status */}
      {preprocessStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Preprocessing Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Overall Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={stageStatusConfig[preprocessStatus.preprocess_stage.status].color}>
                  {stageStatusConfig[preprocessStatus.preprocess_stage.status].icon}
                </div>
                <div>
                  <div className="font-medium">
                    Status: <Badge variant="outline">{preprocessStatus.preprocess_stage.status}</Badge>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                {preprocessStatus.preprocess_stage.status === 'running' && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => cancelPreprocessMutation.mutate()}
                    disabled={cancelPreprocessMutation.isPending}
                    className="gap-2"
                  >
                    {cancelPreprocessMutation.isPending ? <Spinner size="sm" /> : <XCircle className="h-4 w-4" />}
                    Cancel
                  </Button>
                )}
                {(preprocessStatus.preprocess_stage.status === 'failed' || 
                  preprocessStatus.preprocess_stage.status === 'pending') && (
                  <Button
                    size="sm"
                    onClick={() => retryPreprocessMutation.mutate()}
                    disabled={retryPreprocessMutation.isPending}
                    className="gap-2"
                  >
                    {retryPreprocessMutation.isPending ? <Spinner size="sm" /> : <RefreshCw className="h-4 w-4" />}
                    Retry
                  </Button>
                )}
              </div>
            </div>

            {/* Task List */}
            {preprocessStatus.preprocess_stage.tasks && preprocessStatus.preprocess_stage.tasks.length > 0 && (
              <>
                <Separator />
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-muted-foreground">Processing Tasks</h4>
                  {preprocessStatus.preprocess_stage.tasks.map((task) => (
                    <div
                      key={task.task_id}
                      className="flex items-center gap-3 p-3 rounded-lg bg-accent/30"
                    >
                      <div className={stageStatusConfig[task.status].color}>
                        {stageStatusConfig[task.status].icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-sm truncate">{task.task_name}</div>
                        {task.current_step && task.status === 'running' && (
                          <div className="text-xs text-muted-foreground mt-1">{task.current_step}</div>
                        )}
                        {task.progress && (
                          <div className="text-xs text-muted-foreground mt-1">{task.progress}</div>
                        )}
                      </div>
                      <Badge variant={task.task_type === 'novel' ? 'default' : 'secondary'}>
                        {task.task_type}
                      </Badge>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

    </div>
      </div>
    </div>
  )
}
