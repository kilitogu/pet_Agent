<template>
  <div class="auth-page">
    <aside class="auth-brand">
      <div class="auth-brand__logo">
        <span class="auth-brand__badge"><AppIcon name="paw" :size="19" /></span>
        <span class="auth-brand__name">领养登记处</span>
      </div>

      <div>
        <h1 class="auth-brand__headline">从一个账号<br />开始登记</h1>
        <p class="auth-brand__note">
          注册后即可查看在库宠物、提交领养申请，并让 AI 助手帮你查规则。
        </p>
      </div>

      <div class="auth-brand__foot">智能宠物领养平台</div>
    </aside>

    <section class="auth-form-col">
      <div class="auth-card">
        <div class="auth-card__title">注册</div>
        <p class="auth-card__desc">创建账号，开始使用登记处</p>

        <el-form ref="formRef" :rules="rules" :model="form" label-width="0">
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
              placeholder="密码（至少 6 位）"
              show-password
            >
              <template #prefix><AppIcon name="lock" :size="16" /></template>
            </el-input>
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              size="large"
              type="password"
              v-model="form.confirmPassword"
              placeholder="确认密码"
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
            @click="register"
          >
            注册
          </el-button>

          <div class="auth-hint">
            已有账号？<router-link to="/login">去登录</router-link>
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
import { registerApi } from '@/api/auth'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})
const loadingValue = ref(false)
const formRef = ref()

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== form.password) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass, trigger: 'blur' }]
}

const register = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loadingValue.value = true
  try {
    const res = await registerApi(form)
    if (res.code === 200) {
      ElMessage.success('注册成功')
      await router.push('/login')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>
