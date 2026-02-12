# 前端UI开发指南

**最后更新**: 2026-02-12  
**目的**: 前端开发规范、API集成、组件设计的完整参考

---

## 🎯 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **React** | 18.x | UI框架 |
| **Vite** | 5.x | 构建工具 |
| **TypeScript** | 5.x | 类型系统 |
| **shadcn/ui** | latest | UI组件库 |
| **Tailwind CSS** | 3.x | 样式框架 |
| **React Query** | 5.x | 数据请求与缓存 |
| **React Router** | 6.x | 路由管理 |
| **Zustand** | 4.x | 状态管理（可选） |

---

## 📁 目录结构

```
frontend-new/
├── src/
│   ├── components/              # UI组件
│   │   ├── ui/                  # shadcn基础组件
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── app-sidebar.tsx      # 应用侧边栏
│   │   ├── site-header.tsx      # 站点头部
│   │   └── layout/              # 布局组件
│   │
│   ├── pages/                   # 页面组件
│   │   ├── Dashboard.tsx               # 项目列表
│   │   ├── ProjectDetailPage.tsx      # 项目详情 ⭐
│   │   ├── NovelViewerPage.tsx        # 小说查看器
│   │   ├── ScriptViewerPage.tsx       # 脚本查看器
│   │   ├── WorkflowPage.tsx           # 工作流页面
│   │   └── SettingsPage.tsx           # 设置页面
│   │
│   ├── api/                     # API客户端
│   │   ├── projectsV2.ts        # V2项目API ⭐
│   │   └── workflows.ts         # 工作流API
│   │
│   ├── types/                   # TypeScript类型定义
│   │   └── project.ts
│   │
│   ├── lib/                     # 工具库
│   │   ├── queryClient.ts       # React Query配置
│   │   └── utils.ts
│   │
│   ├── hooks/                   # 自定义Hooks
│   ├── store/                   # 状态管理（Zustand）
│   ├── App.tsx                  # 应用入口
│   ├── main.tsx                 # 主入口
│   └── index.css                # 全局样式
│
├── public/                      # 静态资源
├── components.json              # shadcn配置
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 🎨 UI设计规范

### 设计原则

1. **优先使用shadcn/ui组件** ✅  
   - 所有UI组件必须使用shadcn/ui
   - 不自己写样式

2. **参考shadcn blocks** ✅  
   - 布局和设计参考 https://ui.shadcn.com/blocks
   - 保持设计一致性

3. **全英文UI** ✅  
   - 所有界面文本使用英文
   - 不使用中文

4. **统一字体大小** ✅  
   - 参考shadcn的typography标准
   - 使用Tailwind的字体类名

### 颜色规范

使用shadcn的主题系统：

```css
/* 主色调 */
--primary: ...
--primary-foreground: ...

/* 次要色 */
--secondary: ...
--secondary-foreground: ...

/* 背景色 */
--background: ...
--foreground: ...

/* 边框和分割线 */
--border: ...
--ring: ...
```

### 字体规范

| 元素 | Tailwind类 | 大小 |
|------|-----------|------|
| 页面标题 | `text-3xl font-bold` | 30px |
| 章节标题 | `text-2xl font-semibold` | 24px |
| 卡片标题 | `text-lg font-medium` | 18px |
| 正文 | `text-base` | 16px |
| 辅助文字 | `text-sm text-muted-foreground` | 14px |
| 小号文字 | `text-xs` | 12px |

---

## 📱 核心页面

### 1. Dashboard - 项目列表页

**路由**: `/`

**功能**:
- 显示所有项目卡片
- 创建新项目
- 搜索和过滤项目

**API调用**:
```typescript
import { getProjects, createProject } from '@/api/projectsV2';

// 获取项目列表
const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: getProjects
});

// 创建项目
const createMutation = useMutation({
  mutationFn: createProject,
  onSuccess: () => queryClient.invalidateQueries(['projects'])
});
```

**组件结构**:
```tsx
<Dashboard>
  <Header>
    <h1>Projects</h1>
    <CreateProjectDialog />
  </Header>
  
  <ProjectGrid>
    {projects.map(project => (
      <ProjectCard 
        key={project.id}
        project={project}
        onClick={() => navigate(`/projects/${project.id}`)}
      />
    ))}
  </ProjectGrid>
</Dashboard>
```

---

### 2. ProjectDetailPage - 项目详情页 ⭐

**路由**: `/projects/:id`

**功能**:
- 显示项目信息
- 文件上传（支持拖拽）
- 原始文件列表
- 预处理状态追踪（实时更新）
- 章节/集数列表展示
- 导航到查看器页面

**API调用**:
```typescript
import { 
  getProject, 
  uploadFile, 
  getPreprocessStatus 
} from '@/api/projectsV2';

// 获取项目详情
const { data: project } = useQuery({
  queryKey: ['project', projectId],
  queryFn: () => getProject(projectId)
});

// 上传文件
const uploadMutation = useMutation({
  mutationFn: (file: File) => uploadFile(projectId, file),
  onSuccess: () => {
    // 开始轮询预处理状态
    startStatusPolling();
  }
});

// 轮询预处理状态
const { data: status } = useQuery({
  queryKey: ['preprocess-status', projectId],
  queryFn: () => getPreprocessStatus(projectId),
  refetchInterval: 2000,  // 每2秒轮询
  enabled: isProcessing    // 只在处理中时轮询
});
```

**组件结构**:
```tsx
<ProjectDetailPage>
  <Header>
    <h1>{project.name}</h1>
    <Badge>{project.status}</Badge>
  </Header>
  
  <FileUploadSection>
    <DropZone onUpload={handleUpload} />
    <FileList files={project.sources} />
  </FileUploadSection>
  
  <PreprocessStatusSection>
    {status.novel && (
      <StatusCard title="Novel Processing">
        <ProgressBar value={status.novel.progress} />
        <TaskList tasks={status.novel.tasks} />
      </StatusCard>
    )}
    
    {status.script && (
      <StatusCard title="Script Processing">
        <ProgressBar value={status.script.progress} />
        <TaskList tasks={status.script.tasks} />
      </StatusCard>
    )}
  </PreprocessStatusSection>
  
  <ProcessedDataSection>
    <ChapterList chapters={project.chapters} />
    <EpisodeList episodes={project.episodes} />
  </ProcessedDataSection>
</ProjectDetailPage>
```

---

### 3. NovelViewerPage - 小说查看器

**路由**: `/projects/:id/novel/:chapterId`

**功能**:
- 显示章节原文
- 显示分段结果
- 显示标注结果
- 章节导航

**API调用**:
```typescript
import { getChapter, getSegmentation, getAnnotation } from '@/api/projectsV2';

// 获取章节数据
const { data: chapter } = useQuery({
  queryKey: ['chapter', projectId, chapterId],
  queryFn: () => getChapter(projectId, chapterId)
});

// 获取分段结果
const { data: segmentation } = useQuery({
  queryKey: ['segmentation', projectId, chapterId],
  queryFn: () => getSegmentation(projectId, chapterId)
});

// 获取标注结果
const { data: annotation } = useQuery({
  queryKey: ['annotation', projectId, chapterId],
  queryFn: () => getAnnotation(projectId, chapterId)
});
```

**组件结构**:
```tsx
<NovelViewerPage>
  <Sidebar>
    <ChapterNav chapters={allChapters} currentChapter={chapterId} />
  </Sidebar>
  
  <MainContent>
    <ChapterHeader>
      <h2>{chapter.title}</h2>
      <ViewModeToggle mode={viewMode} onChange={setViewMode} />
    </ChapterHeader>
    
    {viewMode === 'original' && (
      <OriginalText content={chapter.content} />
    )}
    
    {viewMode === 'segmented' && (
      <SegmentedView 
        paragraphs={segmentation.paragraphs} 
        onParagraphClick={handleParagraphClick}
      />
    )}
    
    {viewMode === 'annotated' && (
      <AnnotatedView 
        events={annotation.event_timeline.events}
        settings={annotation.setting_correlation.settings}
      />
    )}
  </MainContent>
</NovelViewerPage>
```

---

### 4. ScriptViewerPage - 脚本查看器

**路由**: `/projects/:id/script/:episodeId`

**功能**:
- 显示集数原文
- 显示分段结果
- 显示Hook信息（ep01）
- 集数导航

**API调用**:
```typescript
import { getEpisode, getScriptSegmentation, getHook } from '@/api/projectsV2';

// 获取集数数据
const { data: episode } = useQuery({
  queryKey: ['episode', projectId, episodeId],
  queryFn: () => getEpisode(projectId, episodeId)
});

// 获取分段结果
const { data: segmentation } = useQuery({
  queryKey: ['script-segmentation', projectId, episodeId],
  queryFn: () => getScriptSegmentation(projectId, episodeId)
});

// 获取Hook信息（仅ep01）
const { data: hook } = useQuery({
  queryKey: ['hook', projectId, episodeId],
  queryFn: () => getHook(projectId, episodeId),
  enabled: episodeId === 'ep01'
});
```

---

### 5. WorkflowPage - 工作流页面

**路由**: `/projects/:id/workflow`

**功能**:
- 显示工作流各阶段状态
- 手动触发工作流步骤
- 查看工作流日志

**API调用**:
```typescript
import { getWorkflowState, startWorkflowStep } from '@/api/workflows';

// 获取工作流状态
const { data: workflowState } = useQuery({
  queryKey: ['workflow', projectId],
  queryFn: () => getWorkflowState(projectId),
  refetchInterval: 5000  // 每5秒刷新
});

// 启动工作流步骤
const startStepMutation = useMutation({
  mutationFn: (stepId: string) => startWorkflowStep(projectId, stepId),
  onSuccess: () => {
    queryClient.invalidateQueries(['workflow', projectId]);
  }
});
```

---

## 🔌 API集成

### API客户端配置

**文件**: `src/api/projectsV2.ts`

**基础配置**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = {
  get: async <T>(url: string): Promise<T> => {
    const res = await fetch(`${API_BASE_URL}${url}`, {
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },
  
  post: async <T>(url: string, data: any): Promise<T> => {
    const res = await fetch(`${API_BASE_URL}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },
  
  upload: async <T>(url: string, file: File): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE_URL}${url}`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  }
};
```

### 项目管理API（V2）⭐

**获取项目列表**:
```typescript
export const getProjects = async (): Promise<Project[]> => {
  const response = await api.get<{ items: Project[] }>('/api/v2/projects');
  return response.items;
};
```

**创建项目**:
```typescript
export const createProject = async (data: {
  name: string;
  description?: string;
}): Promise<Project> => {
  return api.post('/api/v2/projects', data);
};
```

**获取项目详情**:
```typescript
export const getProject = async (projectId: string): Promise<Project> => {
  return api.get(`/api/v2/projects/${projectId}`);
};
```

**上传文件**:
```typescript
export const uploadFile = async (
  projectId: string, 
  file: File
): Promise<{ success: boolean }> => {
  return api.upload(`/api/v2/projects/${projectId}/files`, file);
};
```

**获取预处理状态**:
```typescript
export const getPreprocessStatus = async (
  projectId: string
): Promise<PreprocessStatus> => {
  return api.get(`/api/v2/projects/${projectId}/preprocess-status`);
};
```

**获取章节列表**:
```typescript
export const getChapters = async (projectId: string): Promise<Chapter[]> => {
  return api.get(`/api/v2/projects/${projectId}/chapters`);
};
```

**获取章节详情**:
```typescript
export const getChapter = async (
  projectId: string,
  chapterId: string
): Promise<ChapterDetail> => {
  return api.get(`/api/v2/projects/${projectId}/chapters/${chapterId}`);
};
```

---

## 🎣 React Query配置

**文件**: `src/lib/queryClient.ts`

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5分钟
      cacheTime: 10 * 60 * 1000,     // 10分钟
      refetchOnWindowFocus: false,
      retry: 1
    },
    mutations: {
      retry: 0
    }
  }
});
```

---

## 🧩 通用组件

### FileUploadZone - 文件上传区

**功能**:
- 支持拖拽上传
- 支持点击选择文件
- 文件类型验证
- 上传进度显示

**使用**:
```tsx
import { FileUploadZone } from '@/components/FileUploadZone';

<FileUploadZone
  accept=".txt,.srt"
  multiple={true}
  onUpload={handleUpload}
  loading={uploading}
/>
```

---

### StatusBadge - 状态徽章

**使用**:
```tsx
import { Badge } from '@/components/ui/badge';

<Badge variant={
  status === 'completed' ? 'success' :
  status === 'running' ? 'default' :
  status === 'failed' ? 'destructive' : 'secondary'
}>
  {status}
</Badge>
```

---

### ProgressBar - 进度条

**使用**:
```tsx
import { Progress } from '@/components/ui/progress';

<Progress value={progress} />
```

---

## 🎯 TypeScript类型定义

**文件**: `src/types/project.ts`

```typescript
export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  sources: ProjectSources;
  workflow_stages: WorkflowStages;
}

export type ProjectStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ProjectSources {
  has_novel: boolean;
  has_script: boolean;
  novel_files: string[];
  script_files: string[];
  novel_chapters: number;
  script_episodes: number;
}

export interface WorkflowStages {
  import: WorkflowStage;
  metadata: WorkflowStage;
  segmentation: WorkflowStage;
  annotation: WorkflowStage;
  alignment: WorkflowStage;
}

export interface WorkflowStage {
  status: 'pending' | 'running' | 'completed' | 'failed';
  updated_at?: string;
  novel_progress?: number;
  novel_total?: number;
  script_progress?: number;
  script_total?: number;
}

export interface Chapter {
  id: string;
  index: number;
  title: string;
  char_count: number;
  has_segmentation: boolean;
  has_annotation: boolean;
}

export interface Episode {
  id: string;
  index: number;
  duration: number;
  has_segmentation: boolean;
}
```

---

## 🔧 开发环境

### 启动开发服务器

```bash
cd frontend-new
npm install
npm run dev
```

访问: `http://localhost:5173`

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

---

## 🎨 shadcn/ui组件使用

### 安装新组件

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
```

### 常用组件

| 组件 | 用途 |
|------|------|
| `Button` | 按钮 |
| `Card` | 卡片容器 |
| `Dialog` | 对话框/模态框 |
| `Badge` | 状态徽章 |
| `Progress` | 进度条 |
| `Table` | 表格 |
| `Tabs` | 标签页 |
| `Select` | 下拉选择 |
| `Input` | 输入框 |
| `Textarea` | 多行文本输入 |

### 使用示例

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog';

<Card>
  <CardHeader>
    <h3>Project Name</h3>
  </CardHeader>
  <CardContent>
    <p>Project description...</p>
    <Dialog>
      <DialogTrigger asChild>
        <Button>View Details</Button>
      </DialogTrigger>
      <DialogContent>
        <p>Details here...</p>
      </DialogContent>
    </Dialog>
  </CardContent>
</Card>
```

---

## 🚫 常见错误

### JSX中特殊字符转义

**问题**: JSX中`<`和`>`会被解析为标签

**解决**:
```tsx
// ❌ 错误
<div>A < B</div>

// ✅ 正确
<div>A {'<'} B</div>
<div>A &lt; B</div>
```

### React Query缓存失效

**问题**: 数据更新后UI未刷新

**解决**:
```typescript
// 更新后刷新缓存
const mutation = useMutation({
  mutationFn: updateProject,
  onSuccess: () => {
    queryClient.invalidateQueries(['projects']);
    queryClient.invalidateQueries(['project', projectId]);
  }
});
```

---

## 📝 代码规范

### 组件命名

- 组件文件: `PascalCase.tsx`
- 组件名: `PascalCase`
- 示例: `ProjectCard.tsx`, `FileUploadZone.tsx`

### API函数命名

- 使用动词开头: `getProjects`, `createProject`, `uploadFile`
- 遵循RESTful风格

### 类型定义

- 接口命名: `PascalCase`
- 类型别名: `PascalCase`
- 枚举: `PascalCase`

---

## 🎯 性能优化

### 虚拟化长列表

对于超过100项的列表，使用虚拟化：

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

const rowVirtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50
});
```

### 懒加载页面

```tsx
import { lazy, Suspense } from 'react';

const NovelViewerPage = lazy(() => import('./pages/NovelViewerPage'));

<Suspense fallback={<LoadingSpinner />}>
  <NovelViewerPage />
</Suspense>
```

---

**维护说明**: 
- 新增页面时，请同步更新本文档
- 修改API时，请更新API集成部分
- 新增组件时，请添加使用示例

**最后更新**: 2026-02-12  
**前端技术栈**: React 18 + Vite + shadcn/ui
