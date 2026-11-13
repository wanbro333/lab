import { reactive } from 'vue'
import { request } from '@/api/client'

export const auth = reactive({ user: null, ready: false })
let pending
export async function ensureSession() {
  if (auth.ready) return
  if (!pending) {
    pending = request('/auth/me/')
      .then((data) => {
        auth.user = data.user
        auth.ready = true
      })
      .finally(() => {
        pending = null
      })
  }
  await pending
}
export async function signIn(username, password) {
  const data = await request('/auth/login/', { method: 'POST', body: { username, password } })
  auth.user = data.user
  auth.ready = true
}
export async function signOut() {
  await request('/auth/logout/', { method: 'POST', body: {} })
  auth.user = null
  auth.ready = true
}
