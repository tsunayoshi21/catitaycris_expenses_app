import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  collapsed: boolean
  mobileOpen: boolean
  toggleCollapsed: () => void
  setMobileOpen: (open: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set, get) => ({
      collapsed: false,
      mobileOpen: false,
      toggleCollapsed: () => set({ collapsed: !get().collapsed }),
      setMobileOpen: (open) => set({ mobileOpen: open }),
    }),
    { name: 'sidebar-storage', partialize: (s) => ({ collapsed: s.collapsed }) }
  )
)
