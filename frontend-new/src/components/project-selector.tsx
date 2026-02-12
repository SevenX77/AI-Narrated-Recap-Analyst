"use client"

import { ChevronsUpDown, FolderOpen, Home } from "lucide-react"
import { useNavigate, useMatch } from "react-router-dom"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import type { Project } from '@/types/project'

interface ProjectSelectorProps {
  onManageClick?: () => void
}

export function ProjectSelector({ onManageClick }: ProjectSelectorProps) {
  const { isMobile } = useSidebar()
  const navigate = useNavigate()
  
  // Extract current projectId from route
  const projectMatch = useMatch('/project/:projectId/*')
  const currentProjectId = projectMatch?.params.projectId

  // Fetch projects
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApiV2.list(),
  })

  const projects = projectsData?.projects || []
  const activeProject = projects.find((p: Project) => p.id === currentProjectId) || projects[0]

  if (!activeProject && projects.length === 0) {
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton size="lg" onClick={onManageClick}>
            <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
              <FolderOpen className="size-4" />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium">No Projects</span>
              <span className="truncate text-xs">Click to create</span>
            </div>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    )
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                <FolderOpen className="size-4" />
              </div>
              <div className="grid flex-1 text-left leading-tight">
                <span className="truncate text-xs font-semibold">
                  {activeProject?.name || 'Select Project'}
                </span>
                <span className="truncate text-[10px] text-muted-foreground mt-1">
                  {activeProject ? `ID: ${activeProject.id}` : 'No project selected'}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-muted-foreground text-xs">
              Projects
            </DropdownMenuLabel>
            {projects.map((project: Project) => (
              <DropdownMenuItem
                key={project.id}
                onClick={() => navigate(`/project/${project.id}`)}
                className="gap-2 p-2"
              >
                <div className="flex size-6 items-center justify-center rounded-md border">
                  <FolderOpen className="size-3.5 shrink-0" />
                </div>
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="truncate text-sm">{project.name}</span>
                  <span className="truncate text-xs text-muted-foreground">{project.status}</span>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 p-2" onClick={onManageClick}>
              <div className="flex size-6 items-center justify-center rounded-md border bg-transparent">
                <Home className="size-4" />
              </div>
              <div className="text-muted-foreground font-medium">All Projects</div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
