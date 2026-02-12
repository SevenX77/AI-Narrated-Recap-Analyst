import { useEffect, useCallback } from "react"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Kbd } from "@/components/ui/kbd"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { useThemeStore } from "@/store/themeStore"

/**
 * 主题切换按钮：在亮/暗色间切换，带 Tooltip 与快捷键 D。
 * 快捷键在输入框/可编辑区域聚焦时不触发。
 */
export function ThemeToggle() {
  const { effectiveTheme, setTheme } = useThemeStore()

  const toggle = useCallback(() => {
    setTheme(effectiveTheme === "dark" ? "light" : "dark")
  }, [effectiveTheme, setTheme])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() !== "d") return
      const target = document.activeElement as HTMLElement | null
      const tag = target?.tagName?.toLowerCase()
      const isEditable =
        tag === "input" ||
        tag === "textarea" ||
        target?.getAttribute("contenteditable") === "true"
      if (isEditable) return
      e.preventDefault()
      toggle()
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [toggle])

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggle}
          className="size-8"
          aria-label="Toggle Mode"
        >
          {effectiveTheme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom" sideOffset={6}>
        <span className="flex items-center gap-2">
          Toggle Mode
          <Kbd>D</Kbd>
        </span>
      </TooltipContent>
    </Tooltip>
  )
}
