<template>
  <div class="pet">
    <div class="pet__head">
      <div>
        <h1 class="page-title">宠物档案</h1>
        <p class="page-sub">在库 {{ total }} 条记录</p>
      </div>
    </div>

    <section class="panel pet__panel">
      <div class="panel__head">
        <span class="panel__title">在库记录</span>
        <div class="pet__actions">
          <el-input
            placeholder="按名字或物种查询"
            v-model="params.keywords"
            style="width: 210px"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
          <el-button @click="handleSearch">
          <AppIcon name="search" :size="15" />
          <span>查询</span>
        </el-button>
          <el-button type="primary" @click="handleCreate">
          <AppIcon name="plus" :size="15" />
          <span>新增</span>
        </el-button>
        </div>
      </div>

      <div class="pet__table">
        <el-table :data="tableData" style="width: 100%" v-loading="loading">
          <el-table-column prop="name" label="名字" min-width="110" />
          <el-table-column label="封面" width="86">
            <template #default="{ row }">
              <img v-if="row.img" class="cover" :src="row.img" alt="" />
              <span v-else class="cover cover--empty"></span>
            </template>
          </el-table-column>
          <el-table-column prop="species" label="物种" min-width="80" />
          <el-table-column prop="breed" label="品种" min-width="110" />
          <el-table-column prop="age" label="月龄" width="80" />
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column label="状态" width="104">
            <template #default="{ row }">
              <span class="stamp" :class="row.status === 1 ? 'is-waiting' : 'is-done'">
                {{ row.status === 1 ? '待领养' : '已领养' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
              <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pet__foot">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑档案' : '新增档案'" width="520">
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="86px"
        style="padding-right: 20px"
      >
        <el-form-item label="封面">
          <el-upload
            :http-request="handleFileUpload"
            :show-file-list="false"
            accept="image/jpeg,image/png,image/gif,image/webp"
          >
            <img v-if="form.img" :src="form.img" class="upload-preview" alt="" />
            <el-button v-else plain>上传封面</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="名字" prop="name">
          <el-input v-model="form.name" placeholder="请输入宠物名字" />
        </el-form-item>
        <el-form-item label="物种">
          <el-input v-model="form.species" placeholder="如：猫 / 狗 / 兔" />
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="form.breed" placeholder="如：中华田园猫" />
        </el-form-item>
        <el-form-item label="月龄" prop="age">
          <el-input-number v-model="form.age" :min="0" :max="300" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio value="公">公</el-radio>
            <el-radio value="母">母</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="毛色">
          <el-input v-model="form.color" placeholder="如：白色 / 橘色" />
        </el-form-item>
        <el-form-item label="健康状况">
          <el-input v-model="form.health" placeholder="如：健康" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入简介"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">待领养</el-radio>
            <el-radio :value="0">已领养</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import AppIcon from '@/components/AppIcon.vue'
import { createPetApi, deletePetApi, getPetPageList, updatePetApi } from '@/api/pet'
import { uploadFileApi } from '@/api/file'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: ''
})
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref()
const formLoading = ref(false)
const form = reactive({
  id: null,
  name: '',
  species: '',
  breed: '',
  age: 0,
  gender: '公',
  color: '',
  health: '',
  description: '',
  img: '',
  status: 1
})

const rules = {
  name: [{ required: true, message: '请输入宠物名字', trigger: 'blur' }],
  age: [{ required: true, message: '请输入月龄', trigger: 'blur' }]
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: '',
    species: '',
    breed: '',
    age: 0,
    gender: '公',
    color: '',
    health: '',
    description: '',
    img: '',
    status: 1
  })
}

const handleFileUpload = async ({ file }) => {
  const res = await uploadFileApi(file)
  if (res.code === 200) {
    form.img = res.data?.url
  }
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  resetForm()
  Object.assign(form, {
    id: row.id,
    name: row.name,
    species: row.species,
    breed: row.breed,
    age: row.age,
    gender: row.gender,
    color: row.color,
    health: row.health,
    description: row.description,
    img: row.img,
    status: row.status
  })
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除宠物「${row.name}」？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    const res = await deletePetApi(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      load()
    }
  })
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  formLoading.value = true
  try {
    const res = form.id ? await updatePetApi(form.id, form) : await createPetApi(form)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success('操作成功')
      load()
    }
  } finally {
    formLoading.value = false
  }
}

const load = async () => {
  loading.value = true
  try {
    const res = await getPetPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code === 200) {
      tableData.value = res.data?.list
      total.value = res.data?.total
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  params.page = 1
  load()
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.pet {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.pet__head {
  flex-shrink: 0;
}

.pet__panel {
  flex: 1;
  min-height: 0;
}

.pet__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pet__table {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.pet__foot {
  display: flex;
  justify-content: flex-end;
  padding: 10px 14px;
  border-top: 1px solid var(--line);
  background: var(--surface);
  flex-shrink: 0;
}

.cover {
  display: block;
  width: 44px;
  height: 44px;
  border-radius: var(--r);
  object-fit: cover;
  border: 1px solid var(--line);
}

.cover--empty {
  background: var(--surface-2);
}

.upload-preview {
  width: 84px;
  height: 84px;
  border-radius: var(--r);
  display: block;
  object-fit: cover;
  border: 1px solid var(--line);
}

@media (max-width: 900px) {
  .panel__head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
