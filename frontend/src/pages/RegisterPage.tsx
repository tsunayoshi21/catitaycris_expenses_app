import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import axios from 'axios'
import { Input, Button, StatusMessage } from '../components/ui'
import logo from '../assets/logo.svg'

export default function RegisterPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [imapHost, setImapHost] = useState('imap.gmail.com')
  const [imapUser, setImapUser] = useState('')
  const [imapPassword, setImapPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await axios.post('/api/users/register/', {
        username,
        password,
        imap_host: imapHost,
        imap_user: imapUser,
        imap_password: imapPassword,
      })
      navigate('/login')
    } catch (err: any) {
      const detail = err?.response?.data
      if (typeof detail === 'object') {
        const first = Object.values(detail)[0]
        setError(Array.isArray(first) ? first[0] as string : String(first))
      } else {
        setError('Error al registrarse')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-auth flex">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900">
        {/* Abstract decorative shapes */}
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-40 h-40 rounded-full bg-white/10 blur-2xl" />
          <div className="absolute bottom-20 right-10 w-60 h-60 rounded-full bg-primary-300/10 blur-3xl" />
          <div className="absolute top-1/2 left-1/3 w-32 h-32 rounded-full bg-white/5 blur-xl" />
        </div>
        <div className="relative z-10 text-center px-12">
          <img src={logo} alt="Finanzas" className="h-16 w-16 mx-auto mb-6 brightness-0 invert" />
          <h2 className="text-3xl font-bold text-white mb-3">Finanzas</h2>
          <p className="text-primary-200 text-lg">Controla tus gastos de forma inteligente</p>
        </div>
      </div>
      {/* Right form panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center px-4 py-8 overflow-y-auto">
        <div className="glass-card p-8 w-full max-w-auth">
          <h1 className="text-2xl font-bold text-center mb-6 text-surface-800 dark:text-surface-100">Crear cuenta</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Input
              label="Contraseña"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <hr className="border-surface-200 dark:border-white/[0.08]" />
            <p className="text-xs text-surface-500 dark:text-surface-400 font-medium uppercase tracking-wide">Cuenta IMAP (email del banco)</p>
            <Input
              label="Servidor IMAP"
              value={imapHost}
              onChange={(e) => setImapHost(e.target.value)}
              required
            />
            <Input
              label="Email"
              type="email"
              value={imapUser}
              onChange={(e) => setImapUser(e.target.value)}
              required
            />
            <Input
              label="Contraseña de app (IMAP)"
              type="password"
              value={imapPassword}
              onChange={(e) => setImapPassword(e.target.value)}
              required
            />
            {error && <StatusMessage text={error} variant="error" />}
            <Button type="submit" fullWidth loading={loading} loadingText="Registrando...">
              Registrarse
            </Button>
          </form>
          <p className="text-center text-sm text-surface-500 dark:text-surface-400 mt-4">
            ¿Ya tienes cuenta?{' '}
            <Link to="/login" className="text-primary-600 dark:text-primary-400 hover:underline">
              Iniciá sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
