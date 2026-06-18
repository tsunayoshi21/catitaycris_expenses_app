import { useMemo } from 'react'
import { useThemeStore } from '../store/themeStore'

export function useChartTheme() {
  const theme = useThemeStore((s) => s.theme)
  const isDark = theme === 'dark'

  return useMemo(() => ({
    gridColor:          isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    tickColor:          isDark ? 'rgba(255,255,255,0.5)'  : 'rgba(0,0,0,0.5)',
    tooltipBg:          isDark ? 'rgba(15,23,42,0.9)'     : 'rgba(255,255,255,0.95)',
    tooltipText:        isDark ? '#e2e8f0'                : '#1e293b',
    tooltipBorder:      isDark ? 'rgba(255,255,255,0.1)'  : 'rgba(0,0,0,0.1)',
    doughnutBorderColor: isDark ? 'rgba(2,6,23,0.5)'     : '#ffffff',
  }), [isDark])
}
