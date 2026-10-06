<template>
  <div class="profile">
    <div class="profile__head">
      <h1 class="page-title">个人信息</h1>
      <p class="page-sub">修改昵称、邮箱与手机号，头像支持上传替换。</p>
    </div>

    <el-card class="profile-card" :body-style="{ padding: '22px 26px 26px' }">
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="70px"
        style="width: 100%"
        v-loading="loading"
      >
        <!-- 头像区 -->
        <el-form-item label="头像" prop="avatar" class="avatar-form-item">
          <el-upload
            class="avatar-uploader"
            :http-request="handleFileUpload"
            :show-file-list="false"
            accept="image/jpeg,image/png,image/gif,image/webp"
            :before-upload="beforeAvatarUpload"
          >
            <div class="avatar-wrapper">
              <img v-if="form.avatar" :src="form.avatar" class="avatar" />
              <AppIcon v-else name="plus" :size="26" class="avatar-uploader-icon" />
              <div class="avatar-hover-tip">更换头像</div>
            </div>
          </el-upload>
        </el-form-item>

        <!-- 单列表单项 -->
        <el-form-item label="账号">
          <el-input disabled v-model="form.username" placeholder="请输入账号">
          </el-input>
        </el-form-item>

        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称">
          </el-input>
        </el-form-item>

        <el-form-item label="角色">
          <el-input disabled v-model="roleLabel">
          </el-input>
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱">
          </el-input>
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号">
          </el-input>
        </el-form-item>

        <el-form-item style="margin-top: 24px; margin-bottom: 0">
          <el-button type="primary" :loading="submitting" @click="handleSubmit" style="width: 100%">
            <AppIcon name="check" :size="16" />
            保存修改
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { getUserInfoApi as getUserInfo, updateUserInfoApi as updateUserInfo } from '@/api/user'
import { uploadFileApi } from '@/api/file'
import { ref, reactive, onMounted, computed } from 'vue'
import { useUser } from '@/utils/user'
import { ElMessage } from 'element-plus'
// 图标统一管理
import AppIcon from '@/components/AppIcon.vue'

const { updateUser } = useUser()

const loading = ref(false)
const submitting = ref(false)
const formRef = ref()

const form = reactive({
  username: '',
  name: '',
  role: '',
  email: '',
  phone: '',
  avatar: ''
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式错误', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误', trigger: 'blur' }]
}

const roleLabel = computed(() => {
  return form.role === 'admin' ? '管理员' : form.role === 'student' ? '学生' : '未知角色'
})

const beforeAvatarUpload = (file) => {
  const imageTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!imageTypes.includes(file.type)) {
    ElMessage.error('只能上传图片')
    return false
  }
  if (file.size / 1024 / 1024 > 2) {
    ElMessage.error('上传图片大小不能超过2M')
    return false
  }
  return true
}

const handleFileUpload = async ({ file }) => {
  try {
    const res = await uploadFileApi(file)
    if (res.code === 200) {
      // 如果后端返回相对路径 /uploads/xxx.png，请务必拼接后端地址：
      // form.avatar = 'http://127.0.0.1:8000' + res.data.url
      form.avatar = res.data?.url 
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    console.error(error)
    ElMessage.error('网络异常，上传失败')
  }
}

const loadUserInfo = async () => {
  loading.value = true
  try {
    const res = await getUserInfo()
    if (res.code === 200) {
      Object.assign(form, res.data)
    }
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await updateUserInfo(form)
    if (res.code === 200) {
      updateUser(res.data)
      ElMessage.success('更新成功')
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
}

.profile__head {
  flex-shrink: 0;
}

.profile-card {
  flex-shrink: 0;
}

.avatar-wrapper {
  position: relative;
  width: 104px;
  height: 104px;
  border-radius: var(--r);
  overflow: hidden;
  border: 1px solid var(--line);
}

.avatar-wrapper .avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-hover-tip {
  position: absolute;
  inset: auto 0 0 0;
  background: rgba(15, 43, 36, 0.82);
  color: #fff;
  text-align: center;
  font-size: 12px;
  padding: 3px 0;
  opacity: 0;
  transition: opacity 0.18s;
}

.avatar-wrapper:hover .avatar-hover-tip {
  opacity: 1;
}

.avatar-form-item {
  margin-bottom: 22px;
}
</style>

<style>
/* 上传区域（非 scoped，需要作用到 Element Plus 内部节点） */
.avatar-uploader .el-upload {
  border: 1px dashed var(--line);
  border-radius: var(--r);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  background-color: var(--surface-2);
  transition: border-color 0.15s;
}

.avatar-uploader .el-upload:hover {
  border-color: var(--brand);
}

.avatar-uploader-icon {
  font-size: 26px;
  color: var(--muted);
  width: 104px;
  height: 104px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
