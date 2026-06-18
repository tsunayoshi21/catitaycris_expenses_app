import { Link } from 'react-router-dom'
import { useSidebarStore } from '../store/sidebarStore'
import logo from '../assets/logo.svg'

export default function MobileTopBar() {
  const setMobileOpen = useSidebarStore((s) => s.setMobileOpen)

  return (
    <div className="md:hidden fixed top-0 left-0 right-0 z-40 glass-nav h-14 flex items-center px-4 gap-3">
      <button
        onClick={() => setMobileOpen(true)}
        className="p-1 text-surface-600 dark:text-surface-300"
        aria-label="Abrir menu"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <Link to="/dashboard" className="flex items-center gap-2 font-bold text-primary-600 dark:text-primary-400">
        <img src={logo} alt="Finanzas" className="h-7 w-7" />
        <span>Finanzas</span>
      </Link>
    </div>
  )
}
