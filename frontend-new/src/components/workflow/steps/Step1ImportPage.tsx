/**
 * Step1ImportPage - File Import & Standardization
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/ui/file-upload'
import { Separator } from '@/components/ui/separator'
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
import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { toast } from 'sonner'
import { Upload, File, Eye, Trash2, CheckCircle, Clock, Loader2, Play, FileText } from 'lucide-react'
import { format } from 'date-fns'
import type { Step1ImportState } from '@/types/workflow'
import { cn } from '@/lib/utils'

interface Step1ImportPageProps {
  projectId: string
  stepState: Step1ImportState
  onComplete?: () => void
}

export function Step1ImportPage({ projectId, onComplete }: Step1ImportPageProps) {
  const queryClient = useQueryClient()
  const [uploadFiles, setUploadFiles] = useState<File[]>([])
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [viewingFile, setViewingFile] = useState<{ name: string; category?: 'novel' | 'srt' } | null>(null)
  const [fileContent, setFileContent] = useState<string>('')
  const [loadingContent, setLoadingContent] = useState(false)

  const { data: filesData } = useQuery({
    queryKey: ['project-files', projectId],
    queryFn: () => projectsApiV2.getFiles(projectId),
  })

  // Fetch project meta to get preprocess status
  const { data: projectMeta } = useQuery({
    queryKey: ['project-meta', projectId],
    queryFn: () => projectsApiV2.get(projectId),
  })

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (uploadFiles.length === 0) return
      return projectsApiV2.uploadFiles(projectId, uploadFiles, true)
    },
    onSuccess: () => {
      setUploadFiles([])
      setUploadDialogOpen(false)
      toast.success('Files uploaded successfully')
      queryClient.invalidateQueries({ queryKey: ['project-files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['workflow-state', projectId] })
      if (onComplete) setTimeout(onComplete, 1000)
    },
    onError: () => toast.error('Upload failed'),
  })

  const deleteFileMutation = useMutation({
    mutationFn: ({ filename, category }: { filename: string; category?: 'novel' | 'srt' }) =>
      projectsApiV2.deleteFile(projectId, filename, category),
    onSuccess: () => {
      toast.success('File deleted')
      queryClient.invalidateQueries({ queryKey: ['project-files', projectId] })
      queryClient.invalidateQueries({ queryKey: ['workflow-state', projectId] })
    },
  })

  // Manual trigger for preprocessing
  const startProcessMutation = useMutation({
    mutationFn: async ({ filename, category }: { filename?: string; category?: 'novel' | 'script' }) => {
      return projectsApiV2.triggerPreprocess(projectId, filename, category)
    },
    onSuccess: () => {
      toast.success('Processing started')
      queryClient.invalidateQueries({ queryKey: ['workflow-state', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-meta', projectId] })
    },
    onError: () => toast.error('Failed to start processing'),
  })

  // Load file content when viewing file changes
  useEffect(() => {
    if (viewingFile) {
      setLoadingContent(true)
      setFileContent('')
      projectsApiV2.getFileContent(projectId, viewingFile.name, viewingFile.category)
        .then((text) => {
          setFileContent(text)
          setLoadingContent(false)
        })
        .catch((err) => {
          console.error('Failed to load file:', err)
          setFileContent('Failed to load file content')
          setLoadingContent(false)
        })
    }
  }, [viewingFile, projectId])

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-auto">
      <div className="px-2">
        <h2 className="text-3xl font-bold tracking-tight">Step 1: Import</h2>
        <p className="text-muted-foreground">Upload Novel and Script files to begin processing</p>
      </div>

      {/* Processing Workflow Description */}
      <div className="mx-2 mb-2 p-4 border rounded-lg bg-muted/20">
        <h3 className="font-semibold mb-4 text-sm uppercase tracking-wider text-muted-foreground">Processing Pipeline</h3>
        <div className="flex gap-4">
          {/* Left: Flow Diagram */}
          <div className="flex flex-col items-center pt-1">
            <div className="w-3 h-3 rounded-full bg-primary shadow-sm ring-2 ring-background" />
            <div className="w-0.5 h-16 bg-border my-1" />
            <div className="w-3 h-3 rounded-full bg-primary shadow-sm ring-2 ring-background" />
            <div className="w-0.5 h-16 bg-border my-1" />
            <div className="w-3 h-3 rounded-full bg-primary shadow-sm ring-2 ring-background" />
          </div>

          {/* Right: Content */}
          <div className="space-y-6 pt-0 flex-1">
            <div className="relative">
              <h4 className="font-medium text-sm">1. Input Analysis</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Automatically detects file encoding (UTF-8, GBK, etc.) and format types.
                Validates file integrity before processing.
              </p>
            </div>
            <div className="relative">
              <h4 className="font-medium text-sm">2. Structure Extraction</h4>
              <div className="grid grid-cols-2 gap-4 mt-1">
                <div className="bg-background/50 p-2 rounded border text-xs">
                  <span className="font-semibold block mb-1">Novel</span>
                  Identifies chapter boundaries, extracts titles, and cleans text content.
                </div>
                <div className="bg-background/50 p-2 rounded border text-xs">
                  <span className="font-semibold block mb-1">Script</span>
                  Parses dialogue lines, timestamps, and speaker information.
                </div>
              </div>
            </div>
            <div className="relative">
              <h4 className="font-medium text-sm">3. Standardization</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Converts all inputs into a unified JSON format optimized for AI analysis.
                Generates metadata and structural indices.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card
          className={cn(
            "transition-all duration-200", 
            projectMeta?.sources?.has_novel && projectMeta.sources.novel_chapters > 0 && "cursor-pointer hover:border-primary/50 hover:shadow-md"
          )}
          onClick={() => {
            if (projectMeta?.sources?.has_novel && projectMeta.sources.novel_chapters > 0) {
              window.location.href = `/project/${projectId}/novel`
            }
          }}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                {projectMeta?.sources?.has_novel ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <Clock className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <div>
                <CardTitle className="text-base">Novel Status</CardTitle>
                <CardDescription className="text-xs">
                  {projectMeta?.sources?.has_novel 
                    ? `${projectMeta.sources.novel_chapters || 0} chapters detected` 
                    : 'Not imported'}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          {projectMeta?.sources?.has_novel ? (
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Chapters:</span>
                <span className="font-mono text-xs">{projectMeta.sources.novel_chapters}</span>
              </div>
              <Button 
                size="sm" 
                className="w-full" 
                onClick={(e) => {
                  e.stopPropagation()
                  startProcessMutation.mutate({ category: 'novel' })
                }}
                disabled={
                  startProcessMutation.isPending || 
                  (projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                   projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'novel' && t.status === 'running'))
                }
              >
                {projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                 projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'novel' && t.status === 'running') ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {projectMeta.sources.novel_chapters > 0 ? 'Reprocess Novel Files' : 'Process Novel Files'}
              </Button>
            </CardContent>
          ) : (
            <CardContent className="space-y-2">
              {filesData?.files.some(f => f.category === 'novel' || f.name.endsWith('.txt')) ? (
                <Button 
                  size="sm" 
                  className="w-full" 
                  onClick={(e) => {
                    e.stopPropagation()
                    startProcessMutation.mutate({ category: 'novel' })
                  }}
                  disabled={
                    startProcessMutation.isPending || 
                    (projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                     projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'novel' && t.status === 'running'))
                  }
                >
                  {projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                   projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'novel' && t.status === 'running') ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Process Novel Files
                </Button>
              ) : (
                <div className="text-xs text-muted-foreground text-center py-2">
                  Upload a .txt file to begin
                </div>
              )}
            </CardContent>
          )}
        </Card>

        <Card
          className={cn(
            "transition-all duration-200", 
            projectMeta?.sources?.has_script && projectMeta.sources.script_episodes > 0 && "cursor-pointer hover:border-primary/50 hover:shadow-md"
          )}
          onClick={() => {
            if (projectMeta?.sources?.has_script && projectMeta.sources.script_episodes > 0) {
              window.location.href = `/project/${projectId}/script`
            }
          }}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-accent/10">
                {projectMeta?.sources?.has_script ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <Clock className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <div>
                <CardTitle className="text-base">Script Status</CardTitle>
                <CardDescription className="text-xs">
                  {projectMeta?.sources?.has_script 
                    ? `${projectMeta.sources.script_episodes || 0} episodes processed` 
                    : 'Not imported'}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          {projectMeta?.sources?.has_script ? (
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Episodes:</span>
                <span className="font-mono text-xs">{projectMeta.sources.script_episodes}</span>
              </div>
              <Button 
                size="sm" 
                className="w-full" 
                onClick={(e) => {
                  e.stopPropagation()
                  startProcessMutation.mutate({ category: 'script' })
                }}
                disabled={
                  startProcessMutation.isPending || 
                  (projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                   projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'script' && t.status === 'running'))
                }
              >
                {projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                 projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'script' && t.status === 'running') ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {projectMeta.sources.script_episodes > 0 ? 'Reprocess Script Files' : 'Process Script Files'}
              </Button>
            </CardContent>
          ) : (
            <CardContent className="space-y-2">
              {filesData?.files.some(f => f.category === 'srt' || f.name.endsWith('.srt')) ? (
                <Button 
                  size="sm" 
                  className="w-full" 
                  onClick={(e) => {
                    e.stopPropagation()
                    startProcessMutation.mutate({ category: 'script' })
                  }}
                  disabled={
                    startProcessMutation.isPending || 
                    (projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                     projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'script' && t.status === 'running'))
                  }
                >
                  {projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                   projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_type === 'script' && t.status === 'running') ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Process Script Files
                </Button>
              ) : (
                <div className="text-xs text-muted-foreground text-center py-2">
                  Upload a .srt file to begin
                </div>
              )}
            </CardContent>
          )}
        </Card>
      </div>

      <Separator />

      {/* Raw Files List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Raw Files ({filesData?.files.length ?? 0})</CardTitle>
              <CardDescription>Uploaded source files</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => setUploadDialogOpen(true)}>
              <Upload className="h-4 w-4 mr-2" />
              Upload Files
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
                  <AccordionItem key={cat} value={cat} className="border rounded-lg px-2 last:border-b">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <div className="flex items-center gap-2">
                        <span className="text-foreground">{categoryLabel}</span>
                        <span className="text-xs text-muted-foreground">({categoryFiles.length})</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-2">
                      <div className="space-y-1">
                        {categoryFiles.map((file) => {
                          // 查找该文件的处理状态
                          const fileTask = projectMeta?.workflow_stages?.preprocess?.tasks?.find(
                            t => t.task_name.includes(file.name)
                          )
                          
                          return (
                            <div
                              key={`${file.category ?? 'root'}-${file.name}`}
                              className="flex items-center justify-between rounded-md p-2 hover:bg-accent/50 transition-colors"
                            >
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <File className="h-4 w-4 shrink-0 text-muted-foreground" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono text-sm truncate">{file.name}</span>
                                    {/* 处理状态标签 */}
                                    {fileTask && (
                                      <span className={cn(
                                        "inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium",
                                        fileTask.status === 'completed' && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
                                        fileTask.status === 'running' && "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
                                        fileTask.status === 'failed' && "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
                                        fileTask.status === 'pending' && "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400"
                                      )}>
                                        {fileTask.status === 'completed' ? '✓ Done' : 
                                         fileTask.status === 'running' ? '⟳ Processing' : 
                                         fileTask.status === 'failed' ? '✗ Failed' : 
                                         'Pending'}
                                      </span>
                                    )}
                                  </div>
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
                                onClick={() => startProcessMutation.mutate({ filename: file.name })}
                                disabled={
                                  startProcessMutation.isPending || 
                                  (projectMeta?.workflow_stages?.preprocess?.status === 'running' && 
                                   projectMeta?.workflow_stages?.preprocess?.tasks?.some(t => t.task_name.includes(file.name) && t.status === 'running'))
                                }
                                title="Process file"
                              >
                                {projectMeta?.workflow_stages?.preprocess?.tasks?.find(t => t.task_name.includes(file.name))?.status === 'running' ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
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
                          )
                        })}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                )
              })}
            </Accordion>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">No files yet</p>
              <p className="text-xs mt-1">Click "Upload Files" to add Novel (.txt) or Script (.srt) files</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preprocess Status Banner */}
      {projectMeta?.workflow_stages?.preprocess && (
        <Card className="border-2 border-blue-500/20 bg-blue-500/5">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {projectMeta.workflow_stages.preprocess.status === 'completed' ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : projectMeta.workflow_stages.preprocess.status === 'running' ? (
                  <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
                ) : (
                  <Clock className="h-6 w-6 text-muted-foreground" />
                )}
                <div>
                  <h3 className="font-semibold">
                    Auto Preprocessing {projectMeta.workflow_stages.preprocess.status === 'completed' ? 'Completed' : 
                     projectMeta.workflow_stages.preprocess.status === 'running' ? 'In Progress' : 'Pending'}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {projectMeta.workflow_stages.preprocess.status === 'completed' 
                      ? `${projectMeta.workflow_stages.preprocess.tasks?.length || 0} files processed`
                      : 'Encoding detection, chapter detection, text extraction'}
                  </p>
                </div>
              </div>
              {projectMeta.workflow_stages.preprocess.status === 'completed' && (
                <Button variant="ghost" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  View Logs
                </Button>
              )}
            </div>
            
            {/* Processing Tasks Details */}
            {projectMeta.workflow_stages.preprocess.tasks && projectMeta.workflow_stages.preprocess.tasks.length > 0 && (
              <div className="mt-4 space-y-2">
                {projectMeta.workflow_stages.preprocess.tasks.map((task: any) => (
                  <div key={task.task_id} className="flex items-center justify-between text-sm p-2 rounded bg-background/50">
                    <div className="flex items-center gap-2">
                      {task.status === 'completed' ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : task.status === 'running' ? (
                        <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
                      ) : (
                        <Clock className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span>{task.task_name}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">{task.progress}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-2xl min-h-[400px]">
          <DialogHeader>
            <DialogTitle>Upload Files</DialogTitle>
            <DialogDescription>Upload Novel (.txt) or Script (.srt) files for automatic processing</DialogDescription>
          </DialogHeader>
          <FileUpload accept=".txt,.srt,.md,.pdf" multiple value={uploadFiles} onFilesChange={setUploadFiles} />
          {uploadFiles.length > 0 && (
            <DialogFooter>
              <Button onClick={() => uploadMutation.mutate()} disabled={uploadMutation.isPending}>
                {uploadMutation.isPending && <Clock className="h-4 w-4 mr-2 animate-spin" />}
                Upload {uploadFiles.length} file{uploadFiles.length > 1 ? 's' : ''}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>

      {/* View File Dialog */}
      <Dialog open={!!viewingFile} onOpenChange={(open: boolean) => !open && setViewingFile(null)}>
        <DialogContent className="sm:max-w-4xl max-h-[85vh] flex flex-col p-0">
          <DialogHeader className="px-6 pt-6 pb-2">
            <DialogTitle className="font-mono truncate pr-8">{viewingFile?.name ?? ''}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 min-h-0 px-6 pb-6 overflow-hidden">
            {loadingContent ? (
              <div className="flex items-center justify-center h-[70vh] text-muted-foreground">
                <Clock className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <pre className="w-full h-[70vh] overflow-auto rounded-md border bg-muted/30 p-4 text-sm font-mono text-foreground whitespace-pre-wrap break-words">
                {fileContent}
              </pre>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
