<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { signIn } from '@/stores/auth'
const username = ref(''),
  password = ref(''),
  error = ref(''),
  busy = ref(false)
const router = useRouter(),
  route = useRoute()
async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await signIn(username.value, password.value)
    const target = route.query.redirect
    router.push(
      typeof target === 'string' && target.startsWith('/') && !target.startsWith('//')
        ? target
        : '/inventory',
    )
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <section class="login-panel">
    <span class="eyebrow">WELCOME BACK</span>
    <h1>登录工作台</h1>
    <p class="muted">使用实验室分配的账号继续。</p>
    <form @submit.prevent="submit">
      <label>
        用户名
        <input v-model="username" autocomplete="username" required maxlength="150" />
      </label>
      <label>
        密码
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
          maxlength="1024"
        />
      </label>
      <p v-if="error" class="alert error" role="alert">{{ error }}</p>
      <button class="button" :disabled="busy">{{ busy ? '正在登录…' : '登录' }}</button>
    </form>
    <p class="page-note">暂不开放自行注册。如需账号，请联系项目管理员。</p>
  </section>
</template>
