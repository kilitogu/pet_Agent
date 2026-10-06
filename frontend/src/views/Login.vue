<template>
  <div class="auth-page">
    <aside class="auth-brand">
      <div class="auth-brand__logo">
        <span class="auth-brand__badge"><AppIcon name="paw" :size="19" /></span>
        <span class="auth-brand__name">领养登记处</span>
      </div>

      <div>
        <h1 class="auth-brand__headline">让每一只<br />都被接回家</h1>
        <p class="auth-brand__note">
          登记在库宠物、跟进领养状态，随时问 AI 助手要真实数据。
        </p>
      </div>

      <div class="auth-brand__foot">智能宠物领养平台</div>
    </aside>

    <section class="auth-form-col">
      <div class="auth-card">
        <div class="auth-card__title">登录</div>
        <p class="auth-card__desc">使用你的账号进入登记处</p>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="0"
          @keyup.enter="login"
        >
          <el-form-item prop="username">
            <el-input size="large" v-model="form.username" placeholder="账号">
              <template #prefix><AppIcon name="user" :size="16" /></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              size="large"
              type="password"
              v-model="form.password"
              placeholder="密码"
              show-password
            >
              <template #prefix><AppIcon name="lock" :size="16" /></template>
            </el-input>
          </el-form-item>

          <el-button
            class="auth-submit"
            size="large"
            type="primary"
            :loading="loadingValue"
            @click="login"
          >
            登录
          </el-button>

          <div class="auth-hint">
            还没有账号？<router-link to="/register">去注册</router-link>
          </div>
        </el-form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import AppIcon from '@/components/AppIcon.vue'
import { loginApi } from '@/api/auth'
import { useUser } from '@/utils/user'

const { saveLoginData } = useUser()

const form = reactive({
  username: '',
  password: ''
})
const formRef = ref()

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const loadingValue = ref(false)
const login = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loadingValue.value = true
  try {
    const res = await loginApi(form)
    if (res.code === 200) {
      // 先确保 token 落盘，再跳转，否则路由守卫会把人打回来
      await saveLoginData(res.data)
      ElMessage.success('登录成功')
      router.push('/manager/home').catch((err) => {
        console.warn('路由跳转被拦截或发生冗余导航:', err)
      })
    } else {
      ElMessage.error(res.message || '账号或密码错误')
    }
  } catch (error) {
    console.error('登录请求失败:', error)
    ElMessage.error('网络异常，请稍后再试')
  } finally {
    loadingValue.value = false
  }
}
</script>
