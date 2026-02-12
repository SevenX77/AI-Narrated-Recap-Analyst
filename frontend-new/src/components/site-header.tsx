import { useLocation, useNavigate, useMatch } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'

export function SiteHeader() {
  const location = useLocation()
  const navigate = useNavigate()
  
  // Use useMatch to extract params since SiteHeader is outside Routes
  const projectMatch = useMatch('/project/:projectId/*')
  const stepMatch = useMatch('/project/:projectId/workflow/:stepId')
  const novelMatch = useMatch('/project/:projectId/novel')
  const scriptMatch = useMatch('/project/:projectId/script')
  
  const projectId = projectMatch?.params.projectId
  const stepId = stepMatch?.params.stepId

  // Fetch project details
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApiV2.list(),
    enabled: !!projectId,
  })

  const project = projects?.projects.find((p: { id: string }) => p.id === projectId)
  const projectName = project?.name || projectId || 'Project'

  // Map stepId to readable name
  const stepNames: Record<string, string> = {
    step_1_import: 'Import',
    step_2_script: 'Script Analysis',
    step_3_novel: 'Novel Analysis',
    step_4_alignment: 'Alignment',
  }

  // Determine breadcrumb based on route
  const renderBreadcrumb = () => {
    // Novel Viewer and Script Viewer: no breadcrumb (use back button instead)
    if (novelMatch || scriptMatch) {
      return null
    }

    // Projects list page
    if (location.pathname === '/' || location.pathname === '/projects') {
      return (
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage>Projects</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      )
    }

    // Settings page
    if (location.pathname === '/settings') {
      return (
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage>Settings</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      )
    }

    // Project pages
    if (projectId) {
      return (
        <Breadcrumb>
          <BreadcrumbList>
            {/* Project dashboard: show project name only */}
            {!stepId && !novelMatch && !scriptMatch && location.pathname === `/project/${projectId}` && (
              <BreadcrumbItem>
                <BreadcrumbPage>{projectName}</BreadcrumbPage>
              </BreadcrumbItem>
            )}
            
            {/* Step pages: show project name (clickable) > step name */}
            {stepId && (
              <>
                <BreadcrumbItem>
                  <BreadcrumbLink onClick={() => navigate(`/project/${projectId}`)} className="cursor-pointer">
                    {projectName}
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>
                    {stepNames[stepId]}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </>
            )}
          </BreadcrumbList>
        </Breadcrumb>
      )
    }

    return null
  }

  return (
    <header className="sticky top-0 z-50 flex h-16 shrink-0 items-center gap-2 border-b bg-background">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        
        {/* Novel/Script Viewer: show Back button */}
        {(novelMatch || scriptMatch) && projectId ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/project/${projectId}/workflow/step_1_import`)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Workflow
          </Button>
        ) : (
          renderBreadcrumb()
        )}
      </div>
      <div className="ml-auto flex items-center gap-2 px-4">
        <ThemeToggle />
      </div>
    </header>
  )
}
