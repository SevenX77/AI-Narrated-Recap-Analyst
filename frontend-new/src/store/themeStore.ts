import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeStore {
  theme: Theme
  setTheme: (theme: Theme) => void
  effectiveTheme: 'light' | 'dark'
}

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const applyTheme = (theme: 'light' | 'dark') => {
  const root = window.document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(theme)
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set) => ({
      theme: 'dark',
      effectiveTheme: 'dark',
      setTheme: (theme: Theme) => {
        set({ theme })
        const effectiveTheme = theme === 'system' ? getSystemTheme() : theme
        set({ effectiveTheme })
        applyTheme(effectiveTheme)
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => (state) => {
        if (state) {
          const effectiveTheme = state.theme === 'system' ? getSystemTheme() : state.theme
          state.effectiveTheme = effectiveTheme
          applyTheme(effectiveTheme)
        }
      },
    }
  )
)

// 监听系统主题变化
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme, setTheme } = useThemeStore.getState()
    if (theme === 'system') {
      setTheme('system')
    }
  })
}
