import { useState, FormEvent, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { Input, Button, Card, StatusMessage, Modal, Badge } from '../components/ui'
import PageLayout from '../components/PageLayout'
import apiClient from '../api/client'
import { fetchMe, generateTelegramToken, unlinkTelegram } from '../api/users'
import type { UserMe } from '../types'

interface UserEntry {
  id: number
  username: string
  is_staff: boolean
}

export default function SettingsPage() {
  const { isAdmin } = useAuthStore()

  // User profile (for telegram status)
  const [me, setMe] = useState<UserMe | null>(null)
  const [telegramMsg, setTelegramMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [telegramLoading, setTelegramLoading] = useState(false)

  // Change own password
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [ownMsg, setOwnMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [ownLoading, setOwnLoading] = useState(false)

  // Admin: user list + modal
  const [users, setUsers] = useState<UserEntry[]>([])
  const [modalUser, setModalUser] = useState<UserEntry | null>(null)
  const [adminNewPw, setAdminNewPw] = useState('')
  const [adminMsg, setAdminMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [adminLoading, setAdminLoading] = useState(false)

  useEffect(() => {
    fetchMe().then(setMe).catch(() => {})
    if (isAdmin) {
      apiClient.get('/users/').then((r) => setUsers(r.data.results ?? r.data)).catch(() => {})
    }
  }, [isAdmin])

  async function handleGenerateToken() {
    setTelegramMsg(null)
    setTelegramLoading(true)
    try {
      const data = await generateTelegramToken()
      setMe((prev) => prev ? { ...prev, telegram_link_token: data.telegram_link_token } : prev)
      setTelegramMsg({ text: 'Token generado. Envialo al bot en Telegram.', ok: true })
    } catch {
      setTelegramMsg({ text: 'Error al generar token.', ok: false })
    } finally {
      setTelegramLoading(false)
    }
  }

  async function handleUnlink() {
    setTelegramMsg(null)
    setTelegramLoading(true)
    try {
      await unlinkTelegram()
      setMe((prev) => prev ? { ...prev, telegram_linked: false, telegram_chat_id: null, telegram_link_token: null } : prev)
      setTelegramMsg({ text: 'Telegram desvinculado.', ok: true })
    } catch {
      setTelegramMsg({ text: 'Error al desvincular.', ok: false })
    } finally {
      setTelegramLoading(false)
    }
  }

  async function handleVerify() {
    setTelegramMsg(null)
    try {
      const data = await fetchMe()
      setMe(data)
      if (data.telegram_linked) {
        setTelegramMsg({ text: 'Vinculacion confirmada!', ok: true })
      } else {
        setTelegramMsg({ text: 'Aun no vinculado. Envia /vincular <token> al bot.', ok: false })
      }
    } catch {
      setTelegramMsg({ text: 'Error al verificar.', ok: false })
    }
  }

  function handleCopy() {
    if (me?.telegram_link_token) {
      navigator.clipboard.writeText(`/vincular ${me.telegram_link_token}`)
      setTelegramMsg({ text: 'Comando copiado al portapapeles.', ok: true })
    }
  }

  async function handleChangeOwnPassword(e: FormEvent) {
    e.preventDefault()
    setOwnMsg(null)
    if (newPw !== confirmPw) {
      setOwnMsg({ text: 'Las contraseñas nuevas no coinciden.', ok: false })
      return
    }
    setOwnLoading(true)
    try {
      await apiClient.post('/users/change-password/', { current_password: currentPw, new_password: newPw })
      setOwnMsg({ text: 'Contraseña actualizada correctamente.', ok: true })
      setCurrentPw('')
      setNewPw('')
      setConfirmPw('')
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Error al cambiar contraseña.'
      setOwnMsg({ text: detail, ok: false })
    } finally {
      setOwnLoading(false)
    }
  }

  async function handleAdminChangePassword(e: FormEvent) {
    e.preventDefault()
    if (!modalUser) return
    setAdminMsg(null)
    setAdminLoading(true)
    try {
      await apiClient.post(`/users/${modalUser.id}/change-password/`, { new_password: adminNewPw })
      setAdminMsg({ text: `Contraseña de ${modalUser.username} actualizada.`, ok: true })
      setAdminNewPw('')
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Error al cambiar contraseña.'
      setAdminMsg({ text: detail, ok: false })
    } finally {
      setAdminLoading(false)
    }
  }

  function openModal(user: UserEntry) {
    setModalUser(user)
    setAdminNewPw('')
    setAdminMsg(null)
  }

  function closeModal() {
    setModalUser(null)
    setAdminMsg(null)
  }

  return (
    <PageLayout maxWidth="narrow">
      <div className="space-y-8">

        {/* Telegram linking */}
        <Card>
          <h2 className="text-lg font-semibold text-surface-800 dark:text-surface-100 mb-4">Telegram</h2>

          {me?.telegram_linked ? (
            <div className="space-y-3">
              <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" dot="#22c55e">
                Vinculado
              </Badge>
              <p className="text-sm text-surface-600 dark:text-surface-400">
                Tu cuenta de Telegram esta vinculada. Recibiras notificaciones de transacciones.
              </p>
              <Button variant="danger" size="sm" onClick={handleUnlink} loading={telegramLoading} loadingText="Desvinculando...">
                Desvincular Telegram
              </Button>
            </div>
          ) : me?.telegram_link_token ? (
            <div className="space-y-3">
              <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" dot="#eab308">
                Pendiente
              </Badge>
              <p className="text-sm text-surface-600 dark:text-surface-400">
                Envia este comando al bot en Telegram:
              </p>
              <div className="flex gap-2 items-end">
                <Input
                  label="Comando"
                  value={`/vincular ${me.telegram_link_token}`}
                  readOnly
                  className="font-mono"
                />
                <Button variant="secondary" size="sm" onClick={handleCopy}>
                  Copiar
                </Button>
              </div>
              {me.telegram_bot_username && (
                <a
                  href={`https://t.me/${me.telegram_bot_username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block text-sm text-primary-600 dark:text-primary-400 hover:underline"
                >
                  Abrir bot en Telegram
                </a>
              )}
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={handleVerify}>
                  Verificar vinculacion
                </Button>
                <Button variant="ghost" size="sm" onClick={handleGenerateToken} loading={telegramLoading} loadingText="Generando...">
                  Regenerar token
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <Badge className="bg-surface-100 text-surface-500 dark:bg-white/[0.08] dark:text-surface-400">
                No vinculado
              </Badge>
              <p className="text-sm text-surface-600 dark:text-surface-400">
                Vincula tu cuenta de Telegram para recibir notificaciones de transacciones.
              </p>
              <Button onClick={handleGenerateToken} loading={telegramLoading} loadingText="Generando...">
                Generar token de vinculacion
              </Button>
            </div>
          )}

          {telegramMsg && <StatusMessage text={telegramMsg.text} variant={telegramMsg.ok ? 'success' : 'error'} />}
        </Card>

        {/* Change own password */}
        <Card>
          <h2 className="text-lg font-semibold text-surface-800 dark:text-surface-100 mb-4">Cambiar contraseña</h2>
          <form onSubmit={handleChangeOwnPassword} className="space-y-3">
            <Input
              label="Contraseña actual"
              type="password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              required
            />
            <Input
              label="Nueva contraseña"
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              required
            />
            <Input
              label="Confirmar nueva contraseña"
              type="password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              required
            />
            {ownMsg && <StatusMessage text={ownMsg.text} variant={ownMsg.ok ? 'success' : 'error'} />}
            <Button type="submit" loading={ownLoading} loadingText="Guardando...">
              Cambiar contraseña
            </Button>
          </form>
        </Card>

        {/* Admin: user list */}
        {isAdmin && (
          <Card>
            <h2 className="text-lg font-semibold text-surface-800 dark:text-surface-100 mb-4">Usuarios</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-surface-500 dark:text-surface-400 border-b border-surface-200 dark:border-white/[0.08]">
                  <th className="pb-2">Usuario</th>
                  <th className="pb-2">Rol</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-surface-200 dark:border-white/[0.06] last:border-0">
                    <td className="py-2">{u.username}</td>
                    <td className="py-2">{u.is_staff ? 'Admin' : 'Usuario'}</td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => openModal(u)}
                        className="text-primary-600 dark:text-primary-400 hover:underline text-xs"
                      >
                        Cambiar contraseña
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </div>

      {/* Modal */}
      <Modal open={!!modalUser} onClose={closeModal} title={`Cambiar contraseña de ${modalUser?.username}`}>
        <form onSubmit={handleAdminChangePassword} className="space-y-3">
          <Input
            label="Nueva contraseña"
            type="password"
            value={adminNewPw}
            onChange={(e) => setAdminNewPw(e.target.value)}
            required
          />
          {adminMsg && <StatusMessage text={adminMsg.text} variant={adminMsg.ok ? 'success' : 'error'} />}
          <div className="flex gap-2 justify-end">
            <Button variant="ghost" type="button" onClick={closeModal}>Cancelar</Button>
            <Button type="submit" loading={adminLoading} loadingText="Guardando...">Guardar</Button>
          </div>
        </form>
      </Modal>
    </PageLayout>
  )
}
