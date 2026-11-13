<script setup>
import { ref, onMounted } from 'vue'
import { request } from '@/api/client'
import AppIcon from '@/components/AppIcon.vue'
const state = ref('checking')
async function check() {
  state.value = 'checking'
  try {
    const data = await request('/health/')
    state.value = data.status === 'ok' ? 'ok' : 'offline'
  } catch {
    state.value = 'offline'
  }
}
onMounted(check)
const modules = [
  {
    to: '/inventory',
    icon: 'inventory',
    title: '器材与材料',
    text: '查找物品、核对位置，建立实验室的第一本台账。',
    state: '已开放',
    ready: true,
  },
  {
    to: '/procurement',
    icon: 'procurement',
    title: '采购管理',
    text: '从采购申请到订单，集中记录每一次采购需求。',
    state: '规划中',
  },
  {
    to: '/receipts',
    icon: 'receipts',
    title: '收货入库',
    text: '关联采购、登记批次，让物品去向清晰可查。',
    state: '规划中',
  },
  {
    to: '/assistant',
    icon: 'assistant',
    title: '智能问答',
    text: '用自然语言查询信息，预留实验室助手入口。',
    state: '规划中',
  },
]
</script>
<template>
  <section class="welcome">
    <div>
      <div class="eyebrow">YOUR LAB, ORGANIZED</div>
      <h1>
        实验室的日常，
        <br />
        从这里开始。
      </h1>
      <p>器材、材料与团队协作，在同一处有序开展。</p>
      <RouterLink to="/inventory" class="button">
        打开物品台账
        <AppIcon name="arrow" />
      </RouterLink>
    </div>
    <div class="welcome-graphic" aria-hidden="true">
      <div class="graphic-grid"></div>
      <div class="cabinet">
        <div class="cabinet-header">LAB / 01</div>
        <div class="cabinet-row">
          <i></i>
          <i></i>
          <i></i>
        </div>
        <div class="cabinet-row">
          <i></i>
          <i></i>
          <i></i>
        </div>
        <div class="cabinet-line"></div>
        <span>每一件，都有位置。</span>
      </div>
      <div class="graphic-caption">RECORD · LOCATE · COLLABORATE</div>
    </div>
  </section>
  <section class="section-block">
    <div class="section-heading">
      <div>
        <span class="eyebrow">WORKSPACE</span>
        <h2>常用功能</h2>
      </div>
      <span class="muted">从一个入口，找到需要的工作</span>
    </div>
    <div class="module-grid">
      <RouterLink v-for="item in modules" :key="item.to" :to="item.to" class="module-card">
        <div class="module-top">
          <AppIcon :name="item.icon" />
          <span class="badge" :class="{ success: item.ready }">{{ item.state }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p>{{ item.text }}</p>
        <span class="module-link">
          {{ item.ready ? '进入台账' : '查看规划' }}
          <AppIcon name="arrow" />
        </span>
      </RouterLink>
    </div>
  </section>
  <div class="home-bottom">
    <section class="notice-panel">
      <div class="section-heading">
        <h2>实验室通知</h2>
        <span class="muted">信息公告</span>
      </div>
      <p class="empty-line">暂未接入通知。后续可在这里查看实验安排与管理公告。</p>
    </section>
    <section class="connection-panel">
      <span class="eyebrow">服务连接</span>
      <div class="connection-state">
        <span class="status-dot" :class="state"></span>
        <strong>
          {{ { checking: '正在检查连接', ok: '服务连接正常', offline: '服务暂时不可用' }[state] }}
        </strong>
      </div>
      <p>{{ state === 'ok' ? '后台与数据库可以正常通信。' : '检查后台和数据库是否已启动。' }}</p>
      <button class="text-button" @click="check" :disabled="state === 'checking'">
        重新检查 →
      </button>
    </section>
  </div>
</template>
