<script setup>
defineProps({ name: { type: String, default: 'home' } })
const paths = {
  home: 'M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z',
  inventory: 'M3 7 12 3l9 4v10l-9 4-9-4V7Zm0 0 9 4 9-4M12 11v10M7.5 5 17 9',
  procurement: 'M7 3h10v4H7V3ZM7 5H4v16h16V5h-3M8 12h8M8 16h5',
  receipts: 'M4 12v8h16v-8M12 3v12m-5-5 5 5 5-5M3 12h4m10 0h4',
  assistant: 'M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-6 3V6a2 2 0 0 1 2-2ZM7 9h10M7 13h6',
  profile: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-2a8 8 0 0 1 16 0v2',
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  search: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Zm-2 5 6 6',
  plus: 'M12 5v14M5 12h14',
}
</script>
<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] || paths.home" />
  </svg>
</template>
