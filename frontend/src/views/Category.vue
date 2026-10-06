<template>
  <div class="page">
    <el-card class="category-card">
      <template #header>
        <div class="card-header">宠物分类管理</div>
      </template>

      <div class="toolbar">
        <el-input
          placeholder="请输入分类名称或描述查询"
          v-model="params.keywords"
          style="width: 240px"
          clearable
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        ></el-input>
        <el-button @click="handleSearch">
          <AppIcon name="search" :size="15" />
          <span>查询</span>
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <AppIcon name="plus" :size="15" />
          <span>新增</span>
        </el-button>
      </div>

      <el-table
        :data="tableData"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="分类名称" width="140" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sort" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 1 ? 'success' : 'danger'"
              effect="light"
              round
            >
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" text bg @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" text bg @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="params.page"
          v-model:page-size="params.pageSize"
          :total="total"
          :pager-count="5"
          background
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑分类' : '新增分类'"
      width="480"
      class="category-dialog"
    >
      <el-form
        ref="formRef"
        :rules="rules"
        :model="form"
        label-width="80px"
        style="width: 100%; padding-right: 30px; padding-top: 8px"
      >
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="如：猫 / 狗 / 兔" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述"
          />
        </el-form-item>
        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="form.sort" :min="0" :max="999" />
          <span class="form-tip">数字越小越靠前</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="formLoading" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import AppIcon from '@/components/AppIcon.vue'
import {
  getCategoryPageList,
  createCategoryApi,
  updateCategoryApi,
  deleteCategoryApi
} from '@/api/petCategory'
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
  description: '',
  sort: 0,
  status: 1
})

const rules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  sort: [{ required: true, message: '请输入排序值', trigger: 'blur' }]
}

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: '',
    description: '',
    sort: 0,
    status: 1
  })
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
    description: row.description,
    sort: row.sort,
    status: row.status
  })
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确认删除分类 [${row.name}] ？`, '确认删除', {
    type: 'warning'
  }).then(async () => {
    const res = await deleteCategoryApi(row.id)
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
    const res = form.id
      ? await updateCategoryApi(form.id, form)
      : await createCategoryApi(form)
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
    const res = await getCategoryPageList({
      page: params.page,
      page_size: params.pageSize,
      keywords: params.keywords
    })
    if (res.code === 200) {
      tableData.value = res.data?.list || []
      total.value = res.data?.total || 0
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  params.page = 1
  load()
}

onMounted(load)
</script>

<style scoped>
.page {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.category-card {
  flex: 0 0 auto;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.6px;
  color: var(--ink);
}

.pagination-wrap {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: var(--muted);
}
</style>
