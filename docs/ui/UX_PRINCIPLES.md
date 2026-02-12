# 前端用户体验设计原则

**最后更新**: 2026-02-13  
**目的**: 定义前端开发的核心UX原则，确保一致的用户体验

---

## 🎯 三大核心原则

### 原则1: 让用户始终知道"发生了什么" ⭐⭐⭐

**理念**: 用户不应该感到困惑或迷失

**具体要求**:
- ✅ 任何操作都要有即时反馈
- ✅ 错误要说清楚原因和解决方法
- ✅ 长任务要显示进度和预估时间
- ✅ 状态变化要明确可见

---

### 原则2: 降低认知负担 ⭐⭐⭐

**理念**: 不要让用户同时处理太多信息

**具体要求**:
- ✅ 不要一次展示过多信息
- ✅ 使用渐进式展示（卡片→详情）
- ✅ 关键操作要突出显示
- ✅ 信息分组和层级清晰

---

### 原则3: 提供"后悔药" ⭐⭐⭐

**理念**: 让用户有安全感，敢于尝试

**具体要求**:
- ✅ 操作前确认（删除等危险操作）
- ✅ 支持暂停/取消
- ✅ 失败后提供重试选项
- ✅ 关键数据有备份/历史版本

---

## 📋 实施检查清单

### ✅ 操作反馈（原则1）

#### 按钮加载状态
```tsx
// ❌ 错误示范：没有加载状态
<Button onClick={handleSubmit}>
  Submit
</Button>

// ✅ 正确示范：有加载状态
<Button onClick={handleSubmit} disabled={isLoading}>
  {isLoading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      Processing...
    </>
  ) : (
    'Submit'
  )}
</Button>
```

**检查点**:
- [ ] 所有异步操作都有加载状态
- [ ] 按钮在加载时disabled
- [ ] 加载文案明确（"Uploading..."而非"Loading..."）

---

#### Toast通知
```tsx
import { toast } from '@/components/ui/use-toast';

// ✅ 成功操作
toast({
  title: "File uploaded successfully",
  description: "Processing will start automatically.",
});

// ❌ 失败操作（要说明原因）
toast({
  title: "Upload failed",
  description: "File size exceeds 50MB limit. Please compress and try again.",
  variant: "destructive",
  action: (
    <ToastAction altText="Retry" onClick={handleRetry}>
      Retry
    </ToastAction>
  ),
});
```

**检查点**:
- [ ] 成功操作有Toast反馈
- [ ] 失败操作有Toast + 错误原因
- [ ] 重要操作提供action按钮（Retry/Undo）

---

#### 乐观更新（Optimistic UI）
```tsx
const deleteMutation = useMutation({
  mutationFn: deleteProject,
  // 立即从UI移除（乐观更新）
  onMutate: async (projectId) => {
    await queryClient.cancelQueries(['projects']);
    const previousProjects = queryClient.getQueryData(['projects']);
    
    queryClient.setQueryData(['projects'], (old) =>
      old.filter(p => p.id !== projectId)
    );
    
    return { previousProjects };
  },
  // 失败则回滚
  onError: (err, projectId, context) => {
    queryClient.setQueryData(['projects'], context.previousProjects);
    toast({
      title: "Delete failed",
      description: "Please try again later.",
      variant: "destructive",
    });
  },
});
```

**检查点**:
- [ ] 删除/更新操作有乐观更新
- [ ] 失败时能正确回滚
- [ ] 用户感知延迟 < 200ms

---

### ✅ 错误处理（原则1）

#### 错误码映射表
```typescript
// src/lib/error-messages.ts
export const ERROR_CODES = {
  // 文件相关
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  FILE_INVALID_FORMAT: 'FILE_INVALID_FORMAT',
  FILE_UPLOAD_FAILED: 'FILE_UPLOAD_FAILED',
  
  // 处理相关
  PROCESSING_FAILED: 'PROCESSING_FAILED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  CHAPTER_TOO_LONG: 'CHAPTER_TOO_LONG',
  
  // 资源相关
  PROJECT_NOT_FOUND: 'PROJECT_NOT_FOUND',
  CHAPTER_NOT_FOUND: 'CHAPTER_NOT_FOUND',
} as const;

export const ERROR_MESSAGES: Record<string, {
  title: string;
  message: string;
  actions: string[];
}> = {
  FILE_TOO_LARGE: {
    title: 'File Too Large',
    message: 'Maximum file size is 50MB. Please compress the file and try again.',
    actions: ['Compress File', 'Upload Another']
  },
  
  RATE_LIMIT_EXCEEDED: {
    title: 'API Rate Limit Exceeded',
    message: 'Too many requests. The system will auto-retry in 60 seconds.',
    actions: ['Wait', 'Change API Key']
  },
  
  CHAPTER_TOO_LONG: {
    title: 'Chapter Exceeds Token Limit',
    message: 'This chapter has 12,000 tokens (limit: 10,000). Consider splitting it into parts.',
    actions: ['Auto Split', 'Skip Chapter', 'Edit Manually']
  },
  
  PROJECT_NOT_FOUND: {
    title: 'Project Not Found',
    message: 'The project may have been deleted or you don\'t have access.',
    actions: ['Go to Dashboard', 'Contact Support']
  },
};

// 获取友好的错误信息
export function getErrorInfo(errorCode: string) {
  return ERROR_MESSAGES[errorCode] || {
    title: 'Unknown Error',
    message: 'An unexpected error occurred. Please try again.',
    actions: ['Retry', 'Report Issue']
  };
}
```

#### 错误展示组件
```tsx
// components/ErrorAlert.tsx
interface ErrorAlertProps {
  errorCode?: string;
  error?: Error;
  onRetry?: () => void;
  onSkip?: () => void;
}

export function ErrorAlert({ errorCode, error, onRetry, onSkip }: ErrorAlertProps) {
  const errorInfo = errorCode 
    ? getErrorInfo(errorCode)
    : { title: 'Error', message: error?.message || 'Unknown error', actions: [] };
  
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{errorInfo.title}</AlertTitle>
      <AlertDescription>
        <p className="mb-2">{errorInfo.message}</p>
        
        {errorInfo.actions.length > 0 && (
          <div className="flex gap-2 mt-3">
            {errorInfo.actions.map(action => (
              <Button
                key={action}
                size="sm"
                variant={action === 'Retry' ? 'default' : 'outline'}
                onClick={action === 'Retry' ? onRetry : onSkip}
              >
                {action}
              </Button>
            ))}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

**检查点**:
- [ ] 所有错误都有友好的错误码
- [ ] 错误信息说明了"为什么"和"怎么办"
- [ ] 提供可操作的解决方案（Retry/Skip/Contact）
- [ ] 避免技术术语（"API Error 500" → "Server temporarily unavailable"）

---

### ✅ 进度显示（原则1）

#### 详细进度卡片
```tsx
interface ProcessingStatusProps {
  status: 'idle' | 'running' | 'completed' | 'failed';
  currentStep: string;
  progress: number;
  completedItems: number;
  totalItems: number;
  estimatedTimeRemaining?: number; // 秒
  currentTask?: string;
}

export function ProcessingStatusCard({
  status,
  currentStep,
  progress,
  completedItems,
  totalItems,
  estimatedTimeRemaining,
  currentTask
}: ProcessingStatusProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Novel Processing</CardTitle>
          <StatusBadge status={status} />
        </div>
      </CardHeader>
      
      <CardContent>
        {/* 当前步骤指示器 */}
        <StepIndicator>
          <Step completed>1. Importing</Step>
          <Step completed>2. Metadata Extraction</Step>
          <Step active>3. Segmentation</Step>
          <Step>4. Annotation</Step>
          <Step>5. System Detection</Step>
        </StepIndicator>
        
        {/* 当前任务详情 */}
        {currentTask && (
          <div className="my-4 text-sm text-muted-foreground">
            {currentTask}
          </div>
        )}
        
        {/* 进度条 */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{completedItems}/{totalItems} chapters</span>
            {estimatedTimeRemaining && (
              <span>~{formatDuration(estimatedTimeRemaining)} remaining</span>
            )}
          </div>
          <Progress value={progress} />
        </div>
        
        {/* 操作按钮 */}
        <div className="flex gap-2 mt-4">
          {status === 'running' && (
            <>
              <Button variant="outline" size="sm" onClick={handlePause}>
                <Pause className="mr-2 h-4 w-4" />
                Pause
              </Button>
              <Button variant="destructive" size="sm" onClick={handleCancel}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            </>
          )}
          {status === 'completed' && (
            <Button size="sm" onClick={handleViewResults}>
              <Eye className="mr-2 h-4 w-4" />
              View Results
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**检查点**:
- [ ] 显示当前步骤名称（而非"Step 3"）
- [ ] 显示进度百分比和完成数量
- [ ] 显示预估剩余时间
- [ ] 提供暂停/取消按钮

---

#### 长任务后台运行提示
```tsx
export function BackgroundTaskNotice() {
  return (
    <Alert>
      <Info className="h-4 w-4" />
      <AlertTitle>Processing in Background</AlertTitle>
      <AlertDescription>
        <p className="mb-2">
          The task will continue even if you close this page.
          You'll receive a notification when it's done.
        </p>
        <Button variant="outline" size="sm" onClick={enableNotifications}>
          Enable Desktop Notifications
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// 完成通知
useEffect(() => {
  if (status === 'completed') {
    // 桌面通知
    if (Notification.permission === 'granted') {
      new Notification('Processing Complete! 🎉', {
        body: `${projectName}: ${totalChapters} chapters processed successfully.`,
        icon: '/icon.png',
        tag: `project-${projectId}`,
      });
    }
    
    // Toast通知
    toast({
      title: "Processing complete! 🎉",
      description: `${totalChapters} chapters processed successfully.`,
      duration: 5000,
    });
    
    // 可选：播放提示音
    new Audio('/notification.mp3').play();
  }
}, [status]);
```

**检查点**:
- [ ] 长任务（>2分钟）提示可以后台运行
- [ ] 提供启用桌面通知选项
- [ ] 完成时发送桌面通知
- [ ] Toast通知保持5秒以上

---

### ✅ 信息密度控制（原则2）

#### 渐进式展示
```tsx
// ❌ 错误示范：一次展示所有信息
<ChapterCard>
  <h3>{chapter.title}</h3>
  <p>Character count: {chapter.charCount}</p>
  <p>Paragraph count: {chapter.paragraphCount}</p>
  <p>Event count: {chapter.eventCount}</p>
  <div>Functional tags: {chapter.tags.join(', ')}</div>
  <div>Created: {chapter.createdAt}</div>
  <div>Updated: {chapter.updatedAt}</div>
  {/* ... 更多字段 */}
</ChapterCard>

// ✅ 正确示范：卡片 + 折叠详情
<Collapsible>
  <CollapsibleTrigger className="w-full">
    <ChapterCard>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">{chapter.title}</h3>
          <p className="text-sm text-muted-foreground">
            {chapter.charCount} characters
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={chapter.status} />
          <ChevronDown className="h-4 w-4" />
        </div>
      </div>
    </ChapterCard>
  </CollapsibleTrigger>
  
  <CollapsibleContent>
    <div className="mt-2 space-y-2 text-sm">
      <Separator />
      <div className="grid grid-cols-2 gap-2">
        <div>
          <span className="text-muted-foreground">Paragraphs:</span>
          <span className="ml-2">{chapter.paragraphCount}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Events:</span>
          <span className="ml-2">{chapter.eventCount}</span>
        </div>
      </div>
      <div>
        <span className="text-muted-foreground">Tags:</span>
        <div className="flex flex-wrap gap-1 mt-1">
          {chapter.tags.map(tag => (
            <Badge key={tag} variant="secondary">{tag}</Badge>
          ))}
        </div>
      </div>
      <Button size="sm" onClick={() => navigate(`/chapters/${chapter.id}`)}>
        View Details
      </Button>
    </div>
  </CollapsibleContent>
</Collapsible>
```

**检查点**:
- [ ] 卡片只显示核心信息（标题、状态、1-2个关键指标）
- [ ] 详细信息折叠或放在详情页
- [ ] 每个卡片的信息量 ≤ 5个字段

---

#### 分页和虚拟滚动
```tsx
// 对于 > 50 项的列表，使用分页
<DataTable
  data={chapters}
  columns={columns}
  pagination={{
    pageSize: 20,
    pageIndex: currentPage,
    onPageChange: setCurrentPage,
  }}
/>

// 对于 > 100 项的列表，使用虚拟滚动
import { useVirtualizer } from '@tanstack/react-virtual';

function ChapterList({ chapters }: { chapters: Chapter[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const rowVirtualizer = useVirtualizer({
    count: chapters.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,
    overscan: 5,
  });
  
  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const chapter = chapters[virtualRow.index];
          return (
            <div
              key={chapter.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <ChapterCard chapter={chapter} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

**检查点**:
- [ ] 列表 > 50项时使用分页
- [ ] 列表 > 100项时使用虚拟滚动
- [ ] 加载时显示Skeleton

---

### ✅ 操作确认（原则3）

#### 危险操作确认对话框
```tsx
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

// ✅ 删除确认
<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">
      <Trash2 className="mr-2 h-4 w-4" />
      Delete Project
    </Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
      <AlertDialogDescription>
        This action cannot be undone. This will permanently delete the
        project "{projectName}" and all its data including:
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li>{chapterCount} chapters</li>
          <li>{episodeCount} episodes</li>
          <li>All analysis results</li>
          <li>All alignment data</li>
        </ul>
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        onClick={handleDelete}
        className="bg-destructive text-destructive-foreground"
      >
        Yes, delete permanently
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>

// ✅ 二次确认（超危险操作）
function DeleteWithConfirmation() {
  const [confirmText, setConfirmText] = useState('');
  const canDelete = confirmText === projectName;
  
  return (
    <AlertDialog>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Project: {projectName}</AlertDialogTitle>
          <AlertDialogDescription>
            To confirm deletion, please type the project name below:
            <Input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder={projectName}
              className="mt-2"
            />
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={!canDelete}
            className="bg-destructive"
          >
            Delete Permanently
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

**检查点**:
- [ ] 删除操作有确认对话框
- [ ] 说明删除的内容和数量
- [ ] 强调"不可恢复"
- [ ] 重要项目需要二次确认（输入名称）

---

### ✅ 暂停/取消机制（原则3）

#### 长任务控制
```tsx
function WorkflowControls({ workflowId, status }: WorkflowControlsProps) {
  const [isPausing, setIsPausing] = useState(false);
  
  const pauseMutation = useMutation({
    mutationFn: () => pauseWorkflow(workflowId),
    onSuccess: () => {
      toast({ title: "Workflow paused" });
    },
  });
  
  const cancelMutation = useMutation({
    mutationFn: () => cancelWorkflow(workflowId),
    onSuccess: () => {
      toast({ title: "Workflow cancelled" });
    },
  });
  
  const resumeMutation = useMutation({
    mutationFn: () => resumeWorkflow(workflowId),
    onSuccess: () => {
      toast({ title: "Workflow resumed" });
    },
  });
  
  if (status === 'running') {
    return (
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => pauseMutation.mutate()}
          disabled={pauseMutation.isLoading}
        >
          <Pause className="mr-2 h-4 w-4" />
          Pause
        </Button>
        
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cancel Processing?</AlertDialogTitle>
              <AlertDialogDescription>
                Progress will be lost. Already processed items will be kept.
                You can restart later from the beginning.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>No, continue</AlertDialogCancel>
              <AlertDialogAction onClick={() => cancelMutation.mutate()}>
                Yes, cancel
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    );
  }
  
  if (status === 'paused') {
    return (
      <Button
        size="sm"
        onClick={() => resumeMutation.mutate()}
        disabled={resumeMutation.isLoading}
      >
        <Play className="mr-2 h-4 w-4" />
        Resume
      </Button>
    );
  }
  
  return null;
}
```

**检查点**:
- [ ] 长任务（>1分钟）提供暂停按钮
- [ ] 暂停状态可以恢复
- [ ] 取消操作需要确认
- [ ] 说明取消后的影响（已完成的部分是否保留）

---

#### 重试机制
```tsx
function ProcessingError({ error, onRetry }: ProcessingErrorProps) {
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;
  
  const handleRetry = () => {
    if (retryCount < maxRetries) {
      setRetryCount(c => c + 1);
      onRetry();
    }
  };
  
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Processing Failed</AlertTitle>
      <AlertDescription>
        <p className="mb-2">{error.message}</p>
        
        <div className="flex gap-2 mt-3">
          <Button
            size="sm"
            onClick={handleRetry}
            disabled={retryCount >= maxRetries}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Retry ({retryCount}/{maxRetries})
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleSkip}
          >
            Skip and Continue
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleViewLogs}
          >
            View Logs
          </Button>
        </div>
        
        {retryCount >= maxRetries && (
          <p className="mt-2 text-sm text-muted-foreground">
            Maximum retries reached. Please check logs or contact support.
          </p>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

**检查点**:
- [ ] 失败操作提供重试按钮
- [ ] 显示重试次数限制
- [ ] 提供"跳过"选项
- [ ] 提供"查看日志"链接

---

## 🎨 组件设计模式

### 状态指示器
```tsx
// 统一的状态徽章
export function StatusBadge({ status }: { status: WorkflowStatus }) {
  const variants = {
    pending: { variant: 'secondary', icon: Clock, label: 'Pending' },
    running: { variant: 'default', icon: Loader2, label: 'Running', animate: true },
    completed: { variant: 'success', icon: CheckCircle, label: 'Completed' },
    failed: { variant: 'destructive', icon: XCircle, label: 'Failed' },
    paused: { variant: 'outline', icon: Pause, label: 'Paused' },
  };
  
  const config = variants[status];
  const Icon = config.icon;
  
  return (
    <Badge variant={config.variant}>
      <Icon className={cn("mr-1 h-3 w-3", config.animate && "animate-spin")} />
      {config.label}
    </Badge>
  );
}
```

### 空状态
```tsx
// 友好的空状态提示
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <Icon className="h-12 w-12 text-muted-foreground mb-4" />
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-4">
        {description}
      </p>
      {action}
    </div>
  );
}

// 使用示例
<EmptyState
  icon={FileText}
  title="No chapters found"
  description="Upload a novel file to get started. The system will automatically detect and segment chapters."
  action={
    <Button onClick={handleUpload}>
      <Upload className="mr-2 h-4 w-4" />
      Upload Novel
    </Button>
  }
/>
```

---

## 📊 性能原则

### 感知性能优化
```tsx
// 1. Skeleton加载（优于Loading Spinner）
import { Skeleton } from '@/components/ui/skeleton';

function ChapterListSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
        </div>
      ))}
    </div>
  );
}

// 2. Suspense边界
<Suspense fallback={<ChapterListSkeleton />}>
  <ChapterList />
</Suspense>

// 3. 懒加载页面
const NovelViewerPage = lazy(() => import('./pages/NovelViewerPage'));
```

**检查点**:
- [ ] 首屏加载 < 2秒
- [ ] 页面切换 < 300ms
- [ ] 使用Skeleton替代Spinner
- [ ] 大型页面使用懒加载

---

## 🔍 可访问性（A11y）

### 键盘导航
```tsx
// 快捷键支持
import { useHotkeys } from 'react-hotkeys-hook';

function ProjectPage() {
  useHotkeys('ctrl+k', () => openCommandPalette());
  useHotkeys('ctrl+p', () => openProjectSearch());
  useHotkeys('escape', () => closeModal());
  useHotkeys('left', () => gotoPrevChapter());
  useHotkeys('right', () => gotoNextChapter());
  
  return (
    <>
      {/* 快捷键提示 */}
      <KeyboardShortcutHelp />
      {/* ... */}
    </>
  );
}
```

### ARIA标签
```tsx
// 为屏幕阅读器提供语义化标签
<Button
  onClick={handleDelete}
  aria-label="Delete project"
  aria-describedby="delete-description"
>
  <Trash2 className="h-4 w-4" />
</Button>
<span id="delete-description" className="sr-only">
  This will permanently delete the project and all its data
</span>
```

**检查点**:
- [ ] 所有交互元素可用Tab导航
- [ ] 图标按钮有aria-label
- [ ] 表单有label关联
- [ ] 错误信息有role="alert"

---

## ✅ 开发前自查清单

在编写新功能时，问自己：

### 原则1: 用户知道"发生了什么"吗？
- [ ] 按钮有加载状态？
- [ ] 操作有Toast反馈？
- [ ] 错误说明了原因和解决方法？
- [ ] 长任务有进度显示和预估时间？

### 原则2: 信息密度合理吗？
- [ ] 首屏信息量 < 10个核心字段？
- [ ] 使用了折叠/分页/虚拟滚动？
- [ ] 关键操作突出显示？
- [ ] 避免了"信息墙"？

### 原则3: 提供"后悔药"了吗？
- [ ] 危险操作有确认对话框？
- [ ] 长任务可以暂停/取消？
- [ ] 失败后可以重试？
- [ ] 说明了操作的影响？

---

## 📝 代码Review清单

在Code Review时检查：

### UX层面
- [ ] 是否遵循三大核心原则？
- [ ] 错误提示是否友好？
- [ ] 空状态是否有引导？
- [ ] 加载状态是否明确？

### 性能层面
- [ ] 长列表使用了分页/虚拟滚动？
- [ ] 使用了Skeleton而非Spinner？
- [ ] 图片/页面使用了懒加载？

### 可访问性层面
- [ ] 图标按钮有aria-label？
- [ ] 表单有label关联？
- [ ] 支持键盘导航？

---

## 🎓 参考资源

### 设计系统
- [shadcn/ui](https://ui.shadcn.com/) - 我们的组件库
- [Radix UI](https://www.radix-ui.com/) - 无障碍组件基础

### UX指南
- [Laws of UX](https://lawsofux.com/) - UX设计原则
- [Nielsen Norman Group](https://www.nngroup.com/) - UX研究

### 代码示例
- [shadcn/ui blocks](https://ui.shadcn.com/blocks) - 现成的UI模式

---

**维护说明**:
- 新增组件时，请参考本文档的设计原则
- 发现违反原则的代码，请及时重构
- 有新的UX模式建议，请更新本文档

**最后更新**: 2026-02-13  
**维护者**: Frontend Team  
**相关文档**: 
- [UI_DEVELOPMENT_GUIDE.md](./UI_DEVELOPMENT_GUIDE.md) - 技术实现
- [DEV_STANDARDS.md](./DEV_STANDARDS.md) - 开发规范
