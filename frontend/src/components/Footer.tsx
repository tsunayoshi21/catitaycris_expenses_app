export default function Footer() {
  return (
    <footer className="border-t border-surface-200 dark:border-white/[0.06] bg-white/80 dark:bg-surface-900/50 text-center text-sm text-surface-500 dark:text-surface-400 py-4 mt-auto backdrop-blur-sm">
      Finanzas {new Date().getFullYear()}. Todos los derechos reservados.
    </footer>
  )
}
