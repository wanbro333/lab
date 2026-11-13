<script setup>
import { ref, reactive } from 'vue'
import { createItem } from '@/api/inventory'
const emit = defineEmits(['saved', 'cancel'])
const busy = ref(false)
const error = ref('')
const errors = ref({})
const form = reactive({
  code: '',
  name: '',
  kind: 'equipment',
  specification: '',
  unit: '台',
  quantity: '0',
  location: '',
  expires_on: '',
})
async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  errors.value = {}
  try {
    const item = await createItem({
      ...form,
      expires_on: form.kind === 'material' ? form.expires_on || null : null,
    })
    emit('saved', item)
  } catch (e) {
    error.value = e.message
    errors.value = e.errors || {}
  } finally {
    busy.value = false
  }
}
const message = (field) => (errors.value[field] || []).map((e) => e.message).join(' ')
</script>
<template>
  <section class="form-panel" aria-labelledby="new-item-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">NEW RECORD</span>
        <h2 id="new-item-title">新增物品</h2>
      </div>
      <button class="text-button" @click="emit('cancel')" :disabled="busy">取消</button>
    </div>
    <p class="muted">登记基础资料与初始数量。领用、归还和库存流水将在后续版本开放。</p>
    <form @submit.prevent="submit">
      <div class="form-grid">
        <label>
          物品类型
          <select v-model="form.kind">
            <option value="equipment">器材</option>
            <option value="material">材料</option>
          </select>
        </label>
        <label>
          编号
          <span class="required">*</span>
          <input v-model="form.code" required maxlength="40" placeholder="如 EQ-001" />
          <span class="field-error">{{ message('code') }}</span>
        </label>
        <label>
          名称
          <span class="required">*</span>
          <input v-model="form.name" required maxlength="100" placeholder="填写物品名称" />
          <span class="field-error">{{ message('name') }}</span>
        </label>
        <label>
          规格
          <input v-model="form.specification" maxlength="120" placeholder="型号、尺寸等" />
          <span class="field-error">{{ message('specification') }}</span>
        </label>
        <label>
          单位
          <span class="required">*</span>
          <input v-model="form.unit" required maxlength="16" placeholder="台、个、根" />
          <span class="field-error">{{ message('unit') }}</span>
        </label>
        <label>
          初始数量
          <span class="required">*</span>
          <input
            v-model="form.quantity"
            type="number"
            min="0"
            max="99999999.99"
            step="0.01"
            required
          />
          <span class="field-error">{{ message('quantity') }}</span>
        </label>
        <label>
          存放位置
          <input v-model="form.location" maxlength="120" placeholder="房间 · 柜号" />
          <span class="field-error">{{ message('location') }}</span>
        </label>
        <label v-if="form.kind === 'material'">
          有效期至
          <input v-model="form.expires_on" type="date" />
          <span class="field-error">{{ message('expires_on') }}</span>
        </label>
      </div>
      <p v-if="error" class="alert error" role="alert">{{ error }}</p>
      <div class="form-actions">
        <button class="button" :disabled="busy">{{ busy ? '正在保存…' : '保存物品' }}</button>
        <span class="muted">带 * 的项目为必填</span>
      </div>
    </form>
  </section>
</template>
