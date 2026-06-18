import { useEffect } from 'react'
import { useThemeStore } from '../store/themeStore'

export function useTheme() {
  const theme = useThemeStore((s) => s.theme)
  const toggle = useThemeStore((s) => s.toggle)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }, [theme])

  return { theme, isDark: theme === 'dark', toggle } as const
}
