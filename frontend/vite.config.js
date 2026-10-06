import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const API_TARGET = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    // DevTools 只在开发期启用，避免把调试代码带进生产产物
    mode === 'development' && vueDevTools()
  ].filter(Boolean),

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  server: {
    port: 5173,
    // 允许通过局域网 IP 在手机/同事机器上打开，方便验证响应式
    host: true,
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/uploads': { target: API_TARGET, changeOrigin: true }
    }
  },

  preview: {
    port: 4173,
    host: true,
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/uploads': { target: API_TARGET, changeOrigin: true }
    }
  },

  build: {
    // 提醒阈值：拆包后单个 chunk 明显变小，这里放宽到 900KB 避免噪音告警
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        // 把第三方库拆开：首屏可并行下载，且业务代码更新时第三方 chunk 缓存不失效
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('element-plus')) return 'vendor-element'
          if (id.includes('vue-router') || id.includes('@vue')) return 'vendor-vue'
          if (id.includes('axios')) return 'vendor-axios'
          return 'vendor'
        }
      }
    }
  }
}))
