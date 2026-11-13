<script setup>
import { ref, onMounted } from 'vue'
import { listItems } from '@/api/inventory'
import { auth } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'
import ItemForm from '@/components/ItemForm.vue'
const kind = ref('')
const query = ref('')
const page = ref(1)
const data = ref({ count: 0, results: [], page_size: 20 })
const busy = ref(false)
const error = ref('')
const success = ref('')
const adding = ref(false)
let sequence = 0
async function load(reset = false) {
  if (reset) page.value = 1
  const current = ++sequence
  busy.value = true
  error.value = ''
  try {
    const result = await listItems({ kind: kind.value, q: query.value, page: page.value })
    if (current === sequence) data.value = result
  } catch (e) {
    if (current === sequence) {
      error.value = e.message
      data.value = { count: 0, results: [], page_size: 20 }
    }
  } finally {
    if (current === sequence) busy.value = false
  }
}
function selectKind(value) {
  kind.value = value
  load(true)
}
function movePage(delta) {
  page.value += delta
  load()
}
function toggleForm() {
  adding.value = !adding.value
  success.value = ''
}
async function saved(item) {
  adding.value = false
  success.value = `已保存 ${item.code} · ${item.name}`
  query.value = item.code
  kind.value = ''
  await load(true)
}
onMounted(() => load())
</script>
<template>
  <div class="page-heading">
    <div>
      <span class="eyebrow">INVENTORY</span>
      <h1>器材与材料</h1>
      <p>统一登记物品，快速找到实验所需。</p>
    </div>
    <button v-if="auth.user?.is_staff" class="button" @click="toggleForm">
      <AppIcon name="plus" />
      {{ adding ? '收起表单' : '新增物品' }}
    </button>
  </div>
  <p v-if="success" class="alert success" role="status">{{ success }}</p>
  <ItemForm v-if="adding" @saved="saved" @cancel="adding = false" />
  <section class="table-panel">
    <div class="table-toolbar">
      <div class="tabs" aria-label="物品类型">
        <button
          v-for="[value, label] in [
            ['', '全部物品'],
            ['equipment', '器材'],
            ['material', '材料'],
          ]"
          :key="value"
          :class="{ selected: kind === value }"
          :aria-pressed="kind === value"
          @click="selectKind(value)"
        >
          {{ label }}
        </button>
      </div>
      <form class="search-form" role="search" @submit.prevent="load(true)">
        <AppIcon name="search" />
        <input
          v-model="query"
          aria-label="搜索物品"
          placeholder="搜索名称、编号或位置"
          maxlength="100"
        />
        <button class="button secondary small" :disabled="busy">搜索</button>
      </form>
    </div>
    <p v-if="error" class="alert error" role="alert">
      {{ error }}
      <button class="text-button" @click="load()">重试</button>
      <RouterLink v-if="error.includes('登录')" to="/login">重新登录</RouterLink>
    </p>
    <div class="table-scroll" :aria-busy="busy">
      <table>
        <thead>
          <tr>
            <th>物品 / 编号</th>
            <th>类型</th>
            <th>规格</th>
            <th class="numeric">初始数量</th>
            <th>位置</th>
            <th>有效期至</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="busy">
            <td colspan="6" class="table-empty">正在读取物品…</td>
          </tr>
          <template v-else>
            <tr v-for="item in data.results" :key="item.id">
              <td>
                <strong>{{ item.name }}</strong>
                <small>{{ item.code }}</small>
              </td>
              <td>
                <span class="badge" :class="item.kind">
                  {{ item.kind === 'equipment' ? '器材' : '材料' }}
                </span>
              </td>
              <td>{{ item.specification || '—' }}</td>
              <td class="numeric">
                <strong>
                  {{ Number(item.quantity).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) }}
                </strong>
                <span class="muted">{{ item.unit }}</span>
              </td>
              <td>{{ item.location || '未登记' }}</td>
              <td>{{ item.expires_on || '—' }}</td>
            </tr>
            <tr v-if="!data.results.length && !error">
              <td colspan="6" class="table-empty">
                {{
                  query || kind
                    ? '没有符合条件的物品，请调整筛选。'
                    : '还没有物品。管理员可点击“新增物品”开始登记。'
                }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div class="table-footer">
      <span>共 {{ data.count }} 条记录 · 每页 {{ data.page_size }} 条</span>
      <div class="pagination">
        <button :disabled="busy || page <= 1" @click="movePage(-1)">上一页</button>
        <span>{{ page }} / {{ Math.max(1, Math.ceil(data.count / data.page_size)) }}</span>
        <button :disabled="busy || page * data.page_size >= data.count" @click="movePage(1)">
          下一页
        </button>
      </div>
    </div>
  </section>
  <p class="page-note">
    当前提供基础台账。名称含“示例”的记录仅用于演示；数量尚未关联采购、领用与归还流水。
  </p>
</template>
