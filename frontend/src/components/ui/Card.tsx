import { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

export default function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div className={`glass-card ${className}`} {...props}>
      {children}
    </div>
  )
}
