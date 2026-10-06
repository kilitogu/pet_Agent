<script setup>
import { computed } from 'vue'

/**
 * 自绘图标集：统一 24×24 网格、1.7px 描边、圆角端点。
 * 用 currentColor，跟随文字颜色。避免使用组件库那套通用线条图标。
 */
const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 18 },
  strokeWidth: { type: [Number, String], default: 1.7 }
})

const ICONS = {
  /* 品牌：爪印（实心） */
  paw: `
    <ellipse cx="7" cy="8.6" rx="2.1" ry="2.8" fill="currentColor" stroke="none"/>
    <ellipse cx="12" cy="6.9" rx="2.2" ry="2.9" fill="currentColor" stroke="none"/>
    <ellipse cx="17" cy="8.6" rx="2.1" ry="2.8" fill="currentColor" stroke="none"/>
    <path d="M12 11.8c-3.1 0-5.6 2.3-5.6 5.1 0 1.9 1.4 3 3.3 3 1 0 1.6-.4 2.3-.4s1.3.4 2.3.4c1.9 0 3.3-1.1 3.3-3 0-2.8-2.5-5.1-5.6-5.1z" fill="currentColor" stroke="none"/>
  `,

  /* 总览 */
  overview: `
    <rect x="3.5" y="3.5" width="7" height="7" rx="2"/>
    <rect x="13.5" y="3.5" width="7" height="7" rx="2"/>
    <rect x="3.5" y="13.5" width="7" height="7" rx="2"/>
    <rect x="13.5" y="13.5" width="7" height="7" rx="2"/>
  `,

  /* 宠物档案 */
  records: `
    <rect x="4.5" y="3.2" width="15" height="17.6" rx="3"/>
    <path d="M8.4 8.6h7.2M8.4 12.2h7.2M8.4 15.8h4.2"/>
  `,

  /* 分类 */
  tag: `
    <path d="M3.2 11.4V5.2A2 2 0 0 1 5.2 3.2h6.2a2 2 0 0 1 1.42.59l7.2 7.2a2 2 0 0 1 0 2.83l-6.2 6.2a2 2 0 0 1-2.83 0l-7.2-7.2a2 2 0 0 1-.59-1.42z"/>
    <circle cx="8" cy="8" r="1.5"/>
  `,

  /* 用户管理 */
  users: `
    <circle cx="9.4" cy="8" r="3.5"/>
    <path d="M3.4 20v-.8a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5V20"/>
    <path d="M16.6 4.7a3.5 3.5 0 0 1 0 6.6"/>
    <path d="M18.2 14.6a5 5 0 0 1 2.4 4.2V20"/>
  `,

  /* AI 助手 */
  spark: `
    <path d="M11.4 3.2l1.8 4.8 4.8 1.8-4.8 1.8-1.8 4.8-1.8-4.8L4.8 9.8l4.8-1.8z"/>
    <path d="M18.3 15.4l.7 1.9 1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7z"/>
  `,

  /* 在库 */
  box: `
    <path d="M3.8 8.4 12 4l8.2 4.4v7.2L12 20l-8.2-4.4z"/>
    <path d="M3.8 8.4 12 12.8l8.2-4.4M12 12.8V20"/>
  `,

  /* 待领养 */
  clock: `
    <circle cx="12" cy="12" r="8.3"/>
    <path d="M12 7.4V12l3.2 1.9"/>
  `,

  /* 已领养 */
  check: `
    <circle cx="12" cy="12" r="8.3"/>
    <path d="M8.4 12.2l2.5 2.5 4.7-5"/>
  `,

  /* 账号 */
  user: `
    <circle cx="12" cy="8.2" r="3.7"/>
    <path d="M4.8 20c.9-3.3 3.8-5.4 7.2-5.4s6.3 2.1 7.2 5.4"/>
  `,

  /* 密码 */
  lock: `
    <rect x="4.6" y="10.4" width="14.8" height="9.6" rx="2.8"/>
    <path d="M8.4 10.4V8.1a3.6 3.6 0 0 1 7.2 0v2.3"/>
    <path d="M12 14.4v2.2"/>
  `,

  /* 钥匙 */
  key: `
    <circle cx="8.6" cy="12" r="4.1"/>
    <path d="M12.7 12H20M17.5 12v2.9M14.8 12v2.2"/>
  `,

  /* 搜索 */
  search: `
    <circle cx="11" cy="11" r="6.4"/>
    <path d="M15.8 15.8l4.2 4.2"/>
  `,

  /* 新增 */
  plus: `
    <path d="M12 5.4v13.2M5.4 12h13.2"/>
  `,

  /* 编辑 */
  edit: `
    <path d="M4.2 19.8h4.1L19 9.1a2.9 2.9 0 0 0-4.1-4.1L4.2 15.7z"/>
    <path d="M13.9 6.1l4 4"/>
  `,

  /* 删除 */
  trash: `
    <path d="M4.6 6.9h14.8"/>
    <path d="M9.6 6.9V5.3c0-.72.58-1.3 1.3-1.3h2.2c.72 0 1.3.58 1.3 1.3v1.6"/>
    <path d="M6.6 6.9l.85 12.05A2.1 2.1 0 0 0 9.55 21h4.9a2.1 2.1 0 0 0 2.1-1.95L17.4 6.9"/>
  `,

  /* 发送 */
  send: `
    <path d="M20.6 3.4 3.9 10l6.2 2.3 2.3 6.2z"/>
    <path d="M20.6 3.4 10.1 12.3"/>
  `,

  /* 下拉 */
  'chevron-down': `
    <path d="M6.5 9.5l5.5 5.5 5.5-5.5"/>
  `,

  /* 空状态 */
  inbox: `
    <path d="M3.5 13.5 6 5.6A2 2 0 0 1 7.9 4.2h8.2A2 2 0 0 1 18 5.6l2.5 7.9"/>
    <path d="M3.5 13.5h4.2l1.2 2.6h6.2l1.2-2.6h4.2v4.4a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2z"/>
  `
}

const markup = computed(() => (ICONS[props.name] || '').trim())
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
    v-html="markup"
  />
</template>
