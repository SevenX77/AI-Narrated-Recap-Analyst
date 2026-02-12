import { ReactNode, useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Menu } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet"

interface ViewerLayoutProps {
  navTitle: string
  navContent: ReactNode
  mainContent: ReactNode
  currentIndex?: number
  totalCount?: number
  currentLabel?: string
}

/**
 * 通用的 Viewer 布局组件
 * 用于 Novel Viewer 和 Script Viewer，统一左侧导航和主内容区的布局样式
 */
export function ViewerLayout({
  navTitle,
  navContent,
  mainContent,
  currentIndex = -1,
  totalCount = 0,
  currentLabel,
}: ViewerLayoutProps) {
  const [open, setOpen] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  return (
    <div className="@container/main flex h-full overflow-hidden relative">
      <div className="flex w-full h-full">
        {/* Desktop 悬浮导航：纯色背景，上下渐变叠在列表上弱化截断感 */}
        <aside className="hidden md:block md:absolute -left-1 top-4 z-10 w-56 h-[calc(100vh-var(--header-height)-2rem)] overflow-hidden bg-background relative">
          <div className="absolute inset-0">
            <div ref={scrollAreaRef} className="h-full">
              <ScrollArea className="h-full">
                {navContent}
              </ScrollArea>
            </div>
          </div>
          <div className="absolute inset-x-0 top-0 h-5 z-20 pointer-events-none bg-gradient-to-b from-background to-transparent" aria-hidden />
          <div className="absolute inset-x-0 bottom-0 h-5 z-20 pointer-events-none bg-gradient-to-t from-background to-transparent" aria-hidden />
        </aside>

        {/* Mobile Sheet */}
        <Sheet open={open} onOpenChange={setOpen}>
          <div className="md:hidden fixed top-16 left-4 z-50 flex gap-2">
            <SheetTrigger asChild>
              <Button variant="outline" size="sm">
                <Menu className="h-4 w-4 mr-2" />
                {currentLabel || (currentIndex >= 0 ? `${currentIndex + 1}/${totalCount}` : navTitle)}
              </Button>
            </SheetTrigger>
          </div>
          <SheetContent side="left" className="w-64 p-0">
            <div className="py-2">
              <div className="px-4 mb-2 flex items-center justify-between">
                <h2 className="text-sm font-semibold">{navTitle}</h2>
                {totalCount > 0 && (
                  <span className="text-xs text-muted-foreground">
                    Total: {totalCount}
                  </span>
                )}
              </div>
              <div className="h-full [&_[data-slot=scroll-area-scrollbar]]:hidden">
                <ScrollArea className="h-full">
                  {navContent}
                </ScrollArea>
              </div>
            </div>
          </SheetContent>
        </Sheet>

        {/* Main Content - 左边距避开导航（-left-1 + w-56 = 14.25rem） */}
        <main className="flex-1 overflow-hidden relative">
          <ScrollArea className="h-[calc(100vh-var(--header-height))]">
            <div className="h-full">
              <div className="max-w-5xl py-6 pl-0 pr-1 md:pl-[14.25rem] md:pr-1 lg:py-10 lg:pl-[14.25rem] lg:pr-3">
                {mainContent}
              </div>
            </div>
          </ScrollArea>
        </main>
      </div>
    </div>
  )
}
