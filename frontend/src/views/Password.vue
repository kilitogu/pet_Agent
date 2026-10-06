<template>
  <div class="password">
    <div class="password__head">
      <h1 class="page-title">修改密码</h1>
      <p class="page-sub">为了账号安全，建议定期更换密码。修改后需要重新登录。</p>
    </div>

    <el-card class="password-card" :body-style="{ padding: '22px 26px 24px' }">
      <el-form :model="form" label-width="0">
        <el-form-item>
          <el-input
            type="password"
            size="large"
            v-model="form.oldPassword"
            placeholder="原密码"
            show-password
          >
            <template #prefix><AppIcon name="lock" :size="16" /></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-input
            type="password"
            size="large"
            v-model="form.newPassword"
            placeholder="新密码（至少 6 位）"
            show-password
          >
            <template #prefix><AppIcon name="key" :size="16" /></template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-input
            type="password"
            size="large"
            v-model="form.confirmPassword"
            placeholder="确认新密码"
            show-password
          >
            <template #prefix><AppIcon name="key" :size="16" /></template>
          </el-input>
        </el-form-item>

        <el-button
          class="password__submit"
          size="large"
          type="primary"
          :loading="loadingValue"
          @click="submit"
        >
          确认修改
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppIcon from '@/components/AppIcon.vue'
import { updatePasswordApi } from '@/api/user'
import { logout } from '@/utils/auth'

const router = useRouter()
const formRef = ref(null)
const loadingValue = ref(false)

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const submit = async () => {
  // 前端基础校验
  if (!form.oldPassword) return ElMessage.warning('请输入原密码')
  if (!form.newPassword) return ElMessage.warning('请输入新密码')
  if (form.newPassword.length < 6) return ElMessage.warning('新密码长度不能少于6位')
  if (form.newPassword === form.oldPassword) return ElMessage.warning('新密码不能与原密码相同')
  if (form.newPassword !== form.confirmPassword) return ElMessage.warning('两次输入的密码不一致')

  loadingValue.value = true
  try {
    // 字段名与后端 Pydantic 模型对齐（下划线）
    const res = await updatePasswordApi({
      old_password: form.oldPassword,
      new_password: form.newPassword
    })

    const ok = res?.code === 200 || res?.success === true || res === true
    if (ok) {
      ElMessage.success('密码修改成功，请重新登录')
      logout()
      setTimeout(() => router.replace('/login'), 800)
    } else {
      ElMessage.error(res?.msg || res?.message || '密码修改失败')
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.msg || e?.message || '网络异常，请稍后重试')
  } finally {
    loadingValue.value = false
  }
}
</script>

<style scoped>
.password {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
}

.password__head {
  flex-shrink: 0;
}

.password-card {
  flex-shrink: 0;
}

.password__submit {
  width: 100%;
  height: 42px;
  margin-top: 4px;
}
</style>
