import { useEffect } from 'react'

interface KeyPressOptions {
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  alt?: boolean
}

export function useKeyPress(
  targetKey: string,
  callback: () => void,
  options: KeyPressOptions = {}
) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const { ctrl = false, meta = false, shift = false, alt = false } = options

      const isModifierMatch =
        event.ctrlKey === ctrl &&
        event.metaKey === meta &&
        event.shiftKey === shift &&
        event.altKey === alt

      if (event.key.toLowerCase() === targetKey.toLowerCase() && isModifierMatch) {
        event.preventDefault()
        callback()
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [targetKey, callback, options])
}

// 检测是否是 Mac 平台
export const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0

// 获取修饰键符号
export const getModifierKey = () => (isMac ? '⌘' : 'Ctrl')
