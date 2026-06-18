import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useSidebarStore } from '../store/sidebarStore'
import { useTheme } from '../hooks/useTheme'
import logo from '../assets/logo.svg'

const NAV_LINKS = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25a2.25 2.25 0 01-2.25-2.25v-2.25z" />
      </svg>
    ),
  },
  {
    to: '/transactions',
    label: 'Transacciones',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
      </svg>
    ),
  },
  {
    to: '/settings',
    label: 'Ajustes',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export default function Sidebar() {
  const { username, logout } = useAuthStore()
  const { isDark, toggle } = useTheme()
  const { collapsed, mobileOpen, toggleCollapsed, setMobileOpen } = useSidebarStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [hovered, setHovered] = useState(false)

  const expanded = !collapsed || hovered

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function isActive(path: string) {
    return location.pathname === path
  }

  const sidebarContent = (isMobile: boolean) => (
    <div className="flex flex-col h-full">
      {/* Top: Logo + collapse toggle */}
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-2">
          <img src={logo} alt="Finanzas" className="h-8 w-8 flex-shrink-0" />
          <span
            className={`font-bold text-primary-600 dark:text-primary-400 text-lg overflow-hidden whitespace-nowrap transition-all duration-200 ${
              !isMobile && !expanded ? 'w-0 opacity-0' : 'w-auto opacity-100'
            }`}
          >
            Finanzas
          </span>
        </div>
        {!isMobile && (
          <button
            onClick={toggleCollapsed}
            className="p-1 rounded-md text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-white/[0.08] flex-shrink-0"
            aria-label={collapsed ? 'Expandir menú' : 'Colapsar menú'}
          >
            {expanded ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            )}
          </button>
        )}
        {isMobile && (
          <button
            onClick={() => setMobileOpen(false)}
            className="p-1 rounded-md text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-white/[0.08]"
            aria-label="Cerrar menú"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Middle: Nav links */}
      <nav className="flex-1 flex flex-col gap-1 mt-2">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            onClick={() => setMobileOpen(false)}
            className={`flex items-center gap-3 px-4 py-2.5 text-sm font-medium border-l-[3px] transition-colors ${
              isActive(link.to)
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-white/[0.06]'
            }`}
            title={link.label}
          >
            <span className="flex-shrink-0">{link.icon}</span>
            <span
              className={`overflow-hidden whitespace-nowrap transition-all duration-200 ${
                !isMobile && !expanded ? 'w-0 opacity-0' : 'w-auto opacity-100'
              }`}
            >
              {link.label}
            </span>
          </Link>
        ))}
      </nav>

      {/* Bottom: Divider + theme toggle + user info + logout */}
      <div className="border-t border-surface-200 dark:border-white/[0.06] flex flex-col gap-1 py-2">
        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-surface-600 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-white/[0.06] w-full"
          title={isDark ? 'Modo claro' : 'Modo oscuro'}
        >
          <span className="flex-shrink-0">
            {isDark ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m8.66-13.66l-.71.71M4.05 19.95l-.71.71M21 12h-1M4 12H3m16.66 7.66l-.71-.71M4.05 4.05l-.71-.71M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </span>
          <span
            className={`overflow-hidden whitespace-nowrap transition-all duration-200 ${
              !expanded ? 'w-0 opacity-0' : 'w-auto opacity-100'
            }`}
          >
            {isDark ? 'Modo claro' : 'Modo oscuro'}
          </span>
        </button>

        {/* Username */}
        <div
          className={`flex items-center gap-3 px-4 py-2 text-sm text-surface-500 dark:text-surface-400 overflow-hidden whitespace-nowrap transition-all duration-200 ${
            !isMobile && !expanded ? 'justify-center' : ''
          }`}
          title={username ?? undefined}
        >
          <span className="flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </span>
          <span
            className={`overflow-hidden whitespace-nowrap transition-all duration-200 ${
              !isMobile && !expanded ? 'w-0 opacity-0' : 'w-auto opacity-100'
            }`}
          >
            {username}
          </span>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-2.5 text-sm font-medium text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 w-full"
          title="Salir"
        >
          <span className="flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </span>
          <span
            className={`overflow-hidden whitespace-nowrap transition-all duration-200 ${
              !isMobile && !expanded ? 'w-0 opacity-0' : 'w-auto opacity-100'
            }`}
          >
            Salir
          </span>
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden md:flex fixed left-0 top-0 h-screen z-30 glass-sidebar flex-col transition-all duration-200 ease-in-out ${
          expanded ? 'w-60' : 'w-16'
        }`}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {sidebarContent(false)}
      </aside>

      {/* Mobile overlay + sidebar */}
      {mobileOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-black/50 dark:bg-black/60 md:hidden"
            onClick={() => setMobileOpen(false)}
          />
          {/* Mobile sidebar */}
          <aside className="fixed left-0 top-0 h-screen z-50 w-60 glass-sidebar flex flex-col md:hidden animate-fade-in">
            {sidebarContent(true)}
          </aside>
        </>
      )}
    </>
  )
}
