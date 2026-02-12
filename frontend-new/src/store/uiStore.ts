import { create } from 'zustand'

/**
 * UI 状态管理
 * 控制侧边栏等全局 UI 状态
 */
interface UIState {
  // 侧边栏是否折叠
  sidebarCollapsed: boolean
  setSidebarCollapsed: (collapsed: boolean) => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}))
