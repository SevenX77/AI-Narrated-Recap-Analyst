import { BrowserRouter as Router, Routes, Route, Outlet } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { SiteHeader } from '@/components/site-header'
import { ProjectProvider } from '@/contexts/project-context'
import DashboardPage from '@/pages/Dashboard'
import ProjectWorkflowPage from '@/pages/ProjectWorkflowPage'
import NovelViewerPage from '@/pages/NovelViewerPage'
import ScriptViewerPage from '@/pages/ScriptViewerPage'
import ScriptAnalysisResultPage from '@/pages/ScriptAnalysisResultPage'
import NovelAnalysisResultPage from '@/pages/NovelAnalysisResultPage'
import SettingsPage from '@/pages/SettingsPage'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ThemeToggle } from '@/components/theme-toggle'

// 首页布局（无 sidebar）
function HomeLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex h-16 items-center justify-between border-b px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="bg-primary text-primary-foreground flex items-center justify-center rounded-lg size-8">
              <span className="text-sm font-bold">AI</span>
            </div>
            <div>
              <h1 className="text-base font-semibold">AI Recap Analyst</h1>
              <p className="text-xs text-muted-foreground">Narrated Analysis Platform</p>
            </div>
          </div>
        </div>
        <ThemeToggle />
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <Toaster />
    </div>
  )
}

// Sidebar 布局（项目页面）
function SidebarLayout() {
  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <div className="group/sidebar-wrapper flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-1 flex-col">
          <SiteHeader />
          <main className="flex-1">
            <div className="flex flex-1 flex-col gap-4 p-4">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
      <Toaster />
    </SidebarProvider>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider delayDuration={0}>
        <ProjectProvider>
          <Router>
            <Routes>
              {/* 首页路由 */}
              <Route element={<HomeLayout />}>
                <Route path="/" element={<DashboardPage />} />
              </Route>

              {/* Sidebar 布局路由 */}
              <Route element={<SidebarLayout />}>
                <Route path="/project/:projectId" element={<ProjectWorkflowPage />} />
                <Route path="/project/:projectId/workflow" element={<ProjectWorkflowPage />} />
                <Route path="/project/:projectId/workflow/:stepId" element={<ProjectWorkflowPage />} />
                <Route path="/project/:projectId/novel" element={<NovelViewerPage />} />
                <Route path="/project/:projectId/script" element={<ScriptViewerPage />} />
                
                {/* Analyst Result Pages */}
                <Route path="/project/:projectId/script-analysis/:episodeId" element={<ScriptAnalysisResultPage />} />
                <Route path="/project/:projectId/novel-analysis" element={<NovelAnalysisResultPage />} />
                
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </Router>
        </ProjectProvider>
      </TooltipProvider>
    </QueryClientProvider>
  )
}

export default App
