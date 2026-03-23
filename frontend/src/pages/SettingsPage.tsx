import { useState, FormEvent, useEffect } from 'react'
import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import { Input, Button, Card, StatusMessage, Modal } from '../components/ui'
import PageLayout from '../components/PageLayout'

interface UserEntry {
  id: number
  username: string
  is_staff: boolean
}

export default function SettingsPage() {
  const { isAdmin } = useAuthStore()

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
    if (isAdmin) {
      axios.get('/api/users/').then((r) => setUsers(r.data.results ?? r.data)).catch(() => {})
    }
  }, [isAdmin])

  async function handleChangeOwnPassword(e: FormEvent) {
    e.preventDefault()
    setOwnMsg(null)
    if (newPw !== confirmPw) {
      setOwnMsg({ text: 'Las contraseñas nuevas no coinciden.', ok: false })
      return
    }
    setOwnLoading(true)
    try {
      await axios.post('/api/users/change-password/', { current_password: currentPw, new_password: newPw })
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
      await axios.post(`/api/users/${modalUser.id}/change-password/`, { new_password: adminNewPw })
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
