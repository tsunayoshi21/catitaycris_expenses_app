import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import MobileTopBar from './MobileTopBar'
import Footer from './Footer'
import { useSidebarStore } from '../store/sidebarStore'

interface PageLayoutProps {
  children: ReactNode
  maxWidth?: 'narrow' | 'default' | 'wide'
}

const maxWidthClasses = {
  narrow:  'max-w-page-narrow',
  default: 'max-w-6xl',
  wide:    'max-w-page',
}

export default function PageLayout({ children, maxWidth = 'wide' }: PageLayoutProps) {
  const collapsed = useSidebarStore((s) => s.collapsed)

  return (
    <div className="min-h-screen bg-app">
      <Sidebar />
      <MobileTopBar />
      <div className={`transition-all duration-200 ease-in-out pt-14 md:pt-0 ${collapsed ? 'md:ml-16' : 'md:ml-60'}`}>
        <main className={`${maxWidthClasses[maxWidth]} mx-auto w-full px-4 py-6 md:py-8 min-h-[calc(100vh-3.5rem)] md:min-h-screen flex flex-col animate-fade-in`}>
          <div className="flex-1">
            {children}
          </div>
          <Footer />
        </main>
      </div>
    </div>
  )
}
