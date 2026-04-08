import apiClient from './client'
import type { UserMe } from '../types'

export const fetchMe = () =>
  apiClient.get<UserMe>('/users/me/').then((r) => r.data)

export const generateTelegramToken = () =>
  apiClient
    .post<{ telegram_link_token: string }>('/users/me/telegram-token/')
    .then((r) => r.data)

export const unlinkTelegram = () =>
  apiClient
    .post<{ detail: string }>('/users/me/telegram-unlink/')
    .then((r) => r.data)
