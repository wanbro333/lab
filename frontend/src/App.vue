<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { auth, signOut } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'
const router = useRouter()
const route = useRoute()
const error = ref('')
const links = [
  ['/', '工作台', 'home'],
  ['/inventory', '器材与材料', 'inventory'],
  ['/procurement', '采购管理', 'procurement'],
  ['/receipts', '收货入库', 'receipts'],
  ['/assistant', '智能问答', 'assistant'],
  ['/profile', '个人中心', 'profile'],
]
async function logout() {
  error.value = ''
  try {
    await signOut()
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}
</script>
<template>
  <a href="#main" class="skip-link">跳转到内容</a>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">
          L
          <span>·</span>
        </span>
        <span>
          实验室工作台
          <small>LAB WORKSPACE</small>
        </span>
      </RouterLink>
      <div class="nav-label">实验室管理</div>
      <nav aria-label="主导航">
        <RouterLink
          v-for="[path, label, icon] in links"
          :key="path"
          :to="path"
          :class="{ active: route.path === path }"
        >
          <AppIcon :name="icon" />
          <span>{{ label }}</span>
          <span
            v-if="['procurement', 'receipts', 'assistant'].includes(icon)"
            class="nav-dot"
            title="规划中"
          ></span>
        </RouterLink>
      </nav>
      <div class="sidebar-note">
        <span class="tiny-label">一起，把日常理清楚</span>
        <p>物品有记录，协作有依据。</p>
        <span class="version">基础版本 · 0.1</span>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <div>
          <span class="breadcrumb">实验室管理</span>
          <span class="slash">/</span>
          <strong>{{ route.meta.title }}</strong>
        </div>
        <div class="account">
          <template v-if="auth.user">
            <RouterLink to="/profile" class="account-name">
              <span class="avatar">{{ auth.user.display_name.slice(0, 1) }}</span>
              {{ auth.user.display_name }}
            </RouterLink>
            <button class="text-button" @click="logout">退出</button>
          </template>
          <RouterLink v-else to="/login" class="button small">登录工作台</RouterLink>
        </div>
      </header>
      <p v-if="error" class="alert error" role="alert">{{ error }}</p>
      <main id="main" tabindex="-1"><RouterView /></main>
      <footer>
        实验室管理系统
        <span>让每一次协作都有迹可循</span>
      </footer>
    </div>
  </div>
</template>
