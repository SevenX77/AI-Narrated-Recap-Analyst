"use client"

import * as React from 'react'
import { useNavigate, useLocation, useMatch } from 'react-router-dom'
import { Bot, Settings } from 'lucide-react'

import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar'
import { NavMain } from '@/components/nav-main'
import { ProjectSelector } from '@/components/project-selector'
import { useQuery } from '@tanstack/react-query'
import { workflowStateApi } from '@/api/workflowState'

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const navigate = useNavigate()
  const location = useLocation()

  // Extract projectId from current route
  const projectMatch = useMatch('/project/:projectId/*')
  const projectId = projectMatch?.params.projectId

  // Fetch workflow state if in project context
  const { data: workflowState } = useQuery({
    queryKey: ['workflow-state', projectId],
    queryFn: () => workflowStateApi.getWorkflowState(projectId!),
    enabled: !!projectId,
    refetchInterval: 5000,
  })

  // Build navMain data structure
  const navMainItems = workflowState
    ? [
        {
          title: 'Analyst Agent',
          url: '#',
          icon: Bot,
          isActive: !!projectId, // Always active when in project context
          items: [
            {
              title: 'Import',
              url: `/project/${projectId}/workflow/step_1_import`,
              isActive: location.pathname.includes('step_1_import'),
              isLocked: workflowState.step_1_import?.status === 'locked',
              lockReason: undefined,
            },
            {
              title: 'Script Analysis',
              url: `/project/${projectId}/workflow/step_2_script`,
              isActive: location.pathname.includes('step_2_script'),
              isLocked: workflowState.step_2_script?.status === 'locked',
              lockReason: workflowState.step_2_script?.status === 'locked' 
                ? 'Requires Import step to be completed' 
                : undefined,
            },
            {
              title: 'Novel Analysis',
              url: `/project/${projectId}/workflow/step_3_novel`,
              isActive: location.pathname.includes('step_3_novel'),
              isLocked: workflowState.step_3_novel?.status === 'locked',
              lockReason: workflowState.step_3_novel?.status === 'locked'
                ? 'Requires Import step to be completed'
                : undefined,
            },
            {
              title: 'Alignment',
              url: `/project/${projectId}/workflow/step_4_alignment`,
              isActive: location.pathname.includes('step_4_alignment'),
              isLocked: workflowState.step_4_alignment?.status === 'locked',
              lockReason: workflowState.step_4_alignment?.status === 'locked'
                ? 'Requires Script Analysis and Novel Analysis to be completed'
                : undefined,
            },
          ],
        },
      ]
    : []

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <ProjectSelector onManageClick={() => navigate('/')} />
      </SidebarHeader>
      <SidebarContent>
        {projectId ? (
          <NavMain items={navMainItems} />
        ) : (
          <div className="px-4 py-6 text-sm text-muted-foreground">Select a project to view workflows</div>
        )}
        {/* Settings - Bottom button */}
        <SidebarGroup className="mt-auto">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton onClick={() => navigate('/settings')}>
                  <Settings className="h-4 w-4" />
                  <span>Settings</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
