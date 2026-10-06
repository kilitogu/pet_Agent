import { createApp } from 'vue'
import 'element-plus/dist/index.css'
import App from './App.vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import '@/assets/css/global.css'
import router from './router'

const app = createApp(App)

app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})

// 说明：不再全局注册整套图标库。
// 全量注册 @element-plus/icons-vue（约 290 个组件）会把它们全部打进产物，
// 而各页面用的图标都已在自身文件里按需 import。新增页面时同样按需引入即可。

app.mount('#app')
