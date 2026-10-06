<template>
  <div class="shell">
    <header class="shell__top">
      <div class="brand">
        <span class="brand__mark">
          <AppIcon name="paw" :size="18" />
        </span>
        <span class="brand__name">领养登记处</span>
      </div>

      <el-dropdown @command="handleCommand" trigger="click">
        <button class="user" type="button">
          <img :src="avatarUrl" class="user__avatar" alt="" @error="onAvatarError" />
          <span class="user__name">{{ displayName }}</span>
          <AppIcon name="chevron-down" :size="14" class="user__caret" />
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="password">修改密码</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </header>

    <div class="shell__body">
      <nav class="rail">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="rail__item"
          :class="{ active: route.path === item.path }"
        >
          <AppIcon :name="item.icon" :size="17" class="rail__icon" />
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <main class="shell__main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import AppIcon from '@/components/AppIcon.vue'
import { useUser } from '@/utils/user'
import { getUserInfoApi } from '@/api/user'

const { userInfo, clearUser, updateUser } = useUser()
const route = useRoute()
const router = useRouter()

/* ==================== 导航 ==================== */
const navItems = computed(() =>
  [
    { path: '/manager/home', label: '总览', icon: 'overview', admin: false },
    { path: '/manager/pet', label: '宠物档案', icon: 'records', admin: true },
    { path: '/manager/category', label: '分类管理', icon: 'tag', admin: false },
    { path: '/manager/user', label: '用户管理', icon: 'users', admin: true },
    { path: '/manager/ai', label: 'AI 助手', icon: 'spark', admin: false }
  ].filter((item) => !item.admin || userInfo.value?.role === 'admin')
)

/* ==================== 头像 ==================== */
// 为空时使用相对路径，交给反向代理（开发用 vite proxy，线上用 nginx）
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const DEFAULT_AVATAR =
  'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

const rawAvatar = computed(
  () =>
    userInfo.value?.avatar ||
    userInfo.value?.headImg ||
    userInfo.value?.avatarUrl ||
    userInfo.value?.img ||
    ''
)

const displayName = computed(
  () =>
    userInfo.value?.name ||
    userInfo.value?.username ||
    userInfo.value?.nickName ||
    userInfo.value?.nickname ||
    '未登录'
)

const brokenAvatar = ref(false)

watch(rawAvatar, () => {
  brokenAvatar.value = false
})

const avatarUrl = computed(() => {
  if (brokenAvatar.value) return DEFAULT_AVATAR
  const a = rawAvatar.value
  if (!a) return DEFAULT_AVATAR
  if (/^https?:\/\//.test(a) || a.startsWith('data:') || a.startsWith('blob:')) return a
  return `${API_BASE}${a.startsWith('/') ? '' : '/'}${a}`
})

function onAvatarError() {
  brokenAvatar.value = true
}

/* ==================== 用户菜单 ==================== */
async function handleCommand(command) {
  if (command === 'logout') await handleLogout()
  else if (command === 'profile') router.push('/manager/profile')
  else if (command === 'password') router.push('/manager/password')
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  if (typeof clearUser === 'function') clearUser()
  else userInfo.value = null

  localStorage.removeItem('userInfo')
  localStorage.removeItem('token')
  sessionStorage.clear()

  ElMessage.success('已退出登录')
  router.replace('/login')
}

/* ==================== 生命周期 ==================== */
onMounted(async () => {
  try {
    const res = await getUserInfoApi()
    if (res.code === 200 && res.data) {
      if (typeof updateUser === 'function') updateUser(res.data)
      else Object.assign(userInfo.value, res.data)
    }
  } catch (e) {
    console.error('[Layout] 拉取用户信息失败', e)
  }
})
</script>

<style scoped>
.shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--page);
}

/* ============ 顶栏 ============ */
.shell__top {
  height: 58px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.brand__mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--brand);
  color: #fff;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(224, 124, 36, 0.28);
}

.brand__name {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--ink);
  white-space: nowrap;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 5px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  color: var(--ink-2);
  transition: border-color 0.14s, background-color 0.14s;
}

.user:hover {
  background: var(--surface-2);
  border-color: var(--line-strong);
}

.user__avatar {
  width: 25px;
  height: 25px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.user__name {
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user__caret {
  color: var(--faint);
}

/* ============ 主体 ============ */
.shell__body {
  flex: 1;
  min-height: 0;
  display: flex;
}

.rail {
  width: 210px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--line);
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow-y: auto;
}

.rail__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--r);
  font-size: 13.5px;
  color: var(--ink-2);
  transition: background-color 0.14s, color 0.14s;
}

.rail__item:hover {
  background: var(--surface-2);
  color: var(--ink);
}

.rail__item.active {
  background: var(--brand-soft);
  color: var(--brand-700);
  font-weight: 600;
}

.rail__icon {
  flex-shrink: 0;
}

/* 内容区 */
.shell__main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

/* ============ 小屏：导航收成横向条 ============ */
@media (max-width: 900px) {
  .shell__body {
    flex-direction: column;
  }

  .rail {
    width: 100%;
    flex-direction: row;
    gap: 6px;
    padding: 8px 10px;
    border-right: none;
    border-bottom: 1px solid var(--line);
    overflow-x: auto;
    overflow-y: hidden;
  }

  .rail__item {
    white-space: nowrap;
    padding: 8px 13px;
  }

  .brand__name {
    display: none;
  }

  .shell__main {
    padding: 14px;
  }
}
</style>
