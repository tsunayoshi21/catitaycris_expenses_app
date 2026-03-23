import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  toggle: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'dark',
      toggle: () => set({ theme: get().theme === 'dark' ? 'light' : 'dark' }),
    }),
    { name: 'theme-storage' }
  )
)
