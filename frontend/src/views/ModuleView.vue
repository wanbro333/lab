<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
const route = useRoute()
const modules = {
  procurement: {
    label: 'PROCUREMENT',
    description: '把采购需求、订单与审核记录连起来。',
    steps: ['创建采购单', '提交审核', '确认采购', '关联收货'],
    fields: ['采购单号', '供应商', '下单日期', '预计到货日期', '物品与数量', '订单状态'],
    note: '采购审批角色、状态流转与科研项目归属仍需讨论确认。',
  },
  receipts: {
    label: 'RECEIVING',
    description: '逐项核对到货，留下完整的入库依据。',
    steps: ['选择采购单', '核对本次收货', '登记批次与库位', '确认入库'],
    fields: ['收货单号', '关联采购单', '收货日期', '本次实收数量', '批次与有效期', '存放位置'],
    note: '后续支持分批收货与累计数量校验；当前不会修改物品数量。',
  },
  assistant: {
    label: 'LAB ASSISTANT',
    description: '让查询实验室信息，像提问一样自然。',
    steps: ['输入问题', '查询授权信息', '展示回答与依据', '保留会话记录'],
    fields: ['对话区', '输入与发送', '历史会话', '信息来源'],
    note: '尚未连接 AI 服务。后续由后端接入 Dify，先提供查询能力。',
  },
}
const module = computed(() => modules[route.meta.module])
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">{{ module.label }}</span>
      <h1>{{ route.meta.title }}</h1>
      <p>{{ module.description }}</p>
    </div>
    <span class="badge">规划中</span>
  </div>
  <section class="roadmap-panel">
    <div class="roadmap-icon"><AppIcon :name="route.meta.module" /></div>
    <h2>这一站，正在规划。</h2>
    <p>{{ module.note }}</p>
    <ol class="step-list">
      <li v-for="(step, index) in module.steps" :key="step">
        <span>{{ String(index + 1).padStart(2, '0') }}</span>
        {{ step }}
      </li>
    </ol>
    <h3>草图中的核心信息</h3>
    <div class="field-tags">
      <span v-for="field in module.fields" :key="field">{{ field }}</span>
    </div>
    <p class="page-note">本页整理设计范围，暂未提供业务提交功能。</p>
    <RouterLink to="/inventory" class="button secondary">
      先查看物品台账
      <AppIcon name="arrow" />
    </RouterLink>
  </section>
</template>
