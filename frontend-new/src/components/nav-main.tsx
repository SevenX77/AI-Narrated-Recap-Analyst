import { ChevronRight, type LucideIcon } from "lucide-react"
import { Link } from "react-router-dom"

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

export function NavMain({
  items,
}: {
  items: {
    title: string
    url: string
    icon?: LucideIcon
    isActive?: boolean
    items?: {
      title: string
      url: string
      isActive?: boolean
      isLocked?: boolean
      lockReason?: string
    }[]
  }[]
}) {
  return (
    <SidebarGroup>
      <SidebarGroupLabel>Workflows</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <Collapsible
            key={item.title}
            asChild
            defaultOpen={item.isActive}
            className="group/collapsible"
          >
            <SidebarMenuItem>
              <CollapsibleTrigger asChild>
                <SidebarMenuButton tooltip={item.title}>
                  {item.icon && <item.icon />}
                  <span>{item.title}</span>
                  <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                </SidebarMenuButton>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarMenuSub>
                  {item.items?.map((subItem) => (
                    <SidebarMenuSubItem key={subItem.title}>
                      {subItem.isLocked && subItem.lockReason ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <SidebarMenuSubButton
                              isActive={subItem.isActive}
                              className="cursor-not-allowed opacity-50"
                            >
                              <span>{subItem.title}</span>
                            </SidebarMenuSubButton>
                          </TooltipTrigger>
                          <TooltipContent side="right">
                            <p>{subItem.lockReason}</p>
                          </TooltipContent>
                        </Tooltip>
                      ) : subItem.isLocked ? (
                        <SidebarMenuSubButton
                          isActive={subItem.isActive}
                          className="cursor-not-allowed opacity-50"
                        >
                          <span>{subItem.title}</span>
                        </SidebarMenuSubButton>
                      ) : (
                        <SidebarMenuSubButton asChild isActive={subItem.isActive}>
                          <Link to={subItem.url}>
                            <span>{subItem.title}</span>
                          </Link>
                        </SidebarMenuSubButton>
                      )}
                    </SidebarMenuSubItem>
                  ))}
                </SidebarMenuSub>
              </CollapsibleContent>
            </SidebarMenuItem>
          </Collapsible>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}
