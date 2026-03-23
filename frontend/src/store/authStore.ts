import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  username: string | null
  isAdmin: boolean | null
  setTokens: (access: string, refresh: string, username?: string, isAdmin?: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      username: null,
      isAdmin: null,
      setTokens: (access, refresh, username, isAdmin) =>
        set({ accessToken: access, refreshToken: refresh, username: username ?? null, isAdmin: isAdmin ?? null }),
      logout: () => set({ accessToken: null, refreshToken: null, username: null, isAdmin: null }),
    }),
    { name: 'auth-storage' }
  )
)
