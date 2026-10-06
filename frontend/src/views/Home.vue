<template>
  <div class="home">
    <div class="home__head">
      <div>
        <h1 class="page-title">总览</h1>
        <p class="page-sub">你好，{{ userInfo?.name || '管理员' }}。这里是登记处的实时在库情况。</p>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="home__stats">
      <div v-for="card in statCards" :key="card.key" class="stat-card">
        <span class="stat-card__icon" :class="card.tone">
          <AppIcon :name="card.icon" :size="20" />
        </span>
        <div class="stat-card__main">
          <div class="stat-card__value" :class="{ 'is-stamp': card.tone === 'is-stamp' }">
            {{ stats[card.key] }}
          </div>
          <div class="stat-card__label">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="home__panels">
      <section class="panel">
        <div class="panel__head">
          <span class="panel__title">物种分布</span>
          <span class="panel__note">共 {{ speciesTotal }} 只</span>
        </div>
        <div class="panel__body">
          <div v-if="stats.species_distribution.length" class="species">
            <div
              v-for="(item, idx) in stats.species_distribution"
              :key="idx"
              class="species__row"
            >
              <span class="species__name">{{ item.name }}</span>
              <span class="species__track">
                <span
                  class="species__fill"
                  :style="{ width: speciesPercent(item.value) + '%' }"
                ></span>
              </span>
              <span class="species__count">{{ item.value }}</span>
              <span class="species__share">{{ speciesShare(item.value) }}%</span>
            </div>
          </div>
          <el-empty v-else description="暂无物种数据" :image-size="64" />
        </div>
      </section>

      <section class="panel">
        <div class="panel__head">
          <span class="panel__title">近 7 天入库</span>
          <span class="panel__note">共 {{ trendTotal }} 只</span>
        </div>
        <div class="panel__body">
          <div class="trend">
            <div v-for="(item, idx) in stats.pet_trend" :key="idx" class="trend__col">
              <span class="trend__value">{{ item.count || '' }}</span>
              <div class="trend__area">
                <div
                  v-if="item.count > 0"
                  class="trend__bar"
                  :style="{ height: trendHeight(item.count) + '%' }"
                ></div>
                <div v-else class="trend__empty"></div>
              </div>
              <span class="trend__date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- 最近入库 -->
    <section class="panel home__recent">
      <div class="panel__head">
        <span class="panel__title">最近入库</span>
        <el-button text type="primary" @click="$router.push('/manager/pet')">
          查看全部
        </el-button>
      </div>

      <div class="home__records">
        <div v-for="pet in stats.recent_pets" :key="pet.id" class="record-row">
          <img
            v-if="pet.img"
            :src="resolveImg(pet.img)"
            class="record-row__thumb"
            alt=""
          />
          <span v-else class="record-row__thumb record-row__thumb--empty"></span>

          <div class="record-row__main">
            <div class="record-row__name">{{ pet.name }}</div>
            <div class="record-row__meta">
              {{ pet.species || '未知物种' }}
              <template v-if="pet.breed"> · {{ pet.breed }}</template>
            </div>
          </div>

          <span class="stamp" :class="pet.status === 1 ? 'is-waiting' : 'is-done'">
            {{ pet.status === 1 ? '待领养' : '已领养' }}
          </span>
        </div>

        <el-empty
          v-if="!stats.recent_pets.length"
          description="还没有入库记录"
          :image-size="64"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, onMounted } from 'vue'
import { useUser } from '@/utils/user'
import AppIcon from '@/components/AppIcon.vue'
import { getDashboardStatsApi } from '@/api/dashboard'

const { userInfo } = useUser()

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const stats = reactive({
  pet_total: 0,
  pet_waiting: 0,
  pet_adopted: 0,
  user_total: 0,
  pet_trend: [],
  species_distribution: [],
  recent_pets: []
})

const statCards = [
  { key: 'pet_total', label: '在库宠物', icon: 'box', tone: '' },
  { key: 'pet_waiting', label: '待领养', icon: 'clock', tone: 'is-stamp' },
  { key: 'pet_adopted', label: '已领养', icon: 'check', tone: 'is-done' },
  { key: 'user_total', label: '注册用户', icon: 'users', tone: '' }
]

const load = async () => {
  try {
    const res = await getDashboardStatsApi()
    if (res.code === 200 && res.data) {
      Object.assign(stats, res.data)
    }
  } catch (e) {
    console.error('[Dashboard] 加载失败', e)
  }
}

const speciesTotal = computed(() =>
  stats.species_distribution.reduce((sum, i) => sum + (i.value || 0), 0)
)

const trendTotal = computed(() =>
  stats.pet_trend.reduce((sum, i) => sum + (i.count || 0), 0)
)

const speciesPercent = (value) => {
  const max = Math.max(...stats.species_distribution.map((i) => i.value), 1)
  return Math.round((value / max) * 100)
}

const speciesShare = (value) => {
  if (!speciesTotal.value) return 0
  return Math.round((value / speciesTotal.value) * 100)
}

// 0 值不画绿柱，只留一个浅色刻度，避免"几乎全是空柱"的难看
const trendHeight = (count) => {
  const max = Math.max(...stats.pet_trend.map((i) => i.count), 1)
  return Math.max(10, Math.round((count / max) * 100))
}

const resolveImg = (img) => {
  if (!img) return ''
  if (/^https?:\/\//.test(img) || img.startsWith('data:')) return img
  return `${API_BASE}${img.startsWith('/') ? '' : '/'}${img}`
}

onMounted(load)
</script>

<style scoped>
.home {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  overflow-y: auto;
}

.home__head {
  flex-shrink: 0;
}

/* ============ 统计卡 ============ */
.home__stats {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

/* ============ 图表行 ============ */
.home__panels {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.45fr);
  gap: 16px;
}

.home__panels > .panel {
  min-height: 236px;
}

.panel__note {
  font-size: 12.5px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

/* 物种分布 */
.species {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  height: 100%;
}

.species__row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) 30px 42px;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.species__name {
  color: var(--ink-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.species__track {
  height: 8px;
  background: var(--surface-3);
  border-radius: 999px;
  overflow: hidden;
}

.species__fill {
  display: block;
  height: 100%;
  background: var(--brand);
  border-radius: 999px;
  transition: width 0.5s ease;
}

.species__count {
  text-align: right;
  font-weight: 600;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

.species__share {
  text-align: right;
  color: var(--faint);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

/* 趋势图 */
.trend {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  height: 100%;
  min-height: 168px;
}

.trend__col {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
}

.trend__value {
  height: 18px;
  line-height: 18px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

.trend__area {
  flex: 1;
  width: 100%;
  max-width: 40px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  border-bottom: 1px solid var(--line-strong);
}

.trend__bar {
  width: 100%;
  background: var(--brand);
  border-radius: 6px 6px 0 0;
  transition: height 0.5s ease;
}

.trend__empty {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: var(--surface-3);
}

.trend__date {
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* ============ 最近入库 ============ */
.home__recent {
  flex: 1;
  min-height: 240px;
}

.home__records {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.record-row__thumb {
  width: 42px;
  height: 42px;
  border-radius: var(--r);
  object-fit: cover;
  border: 1px solid var(--line);
  flex-shrink: 0;
}

.record-row__thumb--empty {
  background: var(--surface-2);
}

.record-row__main {
  flex: 1;
  min-width: 0;
}

.record-row__name {
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.record-row__meta {
  margin-top: 1px;
  font-size: 12px;
  color: var(--muted);
}

/* ============ 响应式 ============ */
@media (max-width: 1100px) {
  .home__panels {
    grid-template-columns: minmax(0, 1fr);
  }

  .home__panels > .panel {
    min-height: 0;
  }
}

@media (max-width: 760px) {
  .home__stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .home {
    gap: 12px;
  }

  .stat-card {
    padding: 13px 14px;
    gap: 11px;
  }

  .stat-card__icon {
    width: 34px;
    height: 34px;
    font-size: 16px;
  }

  .stat-card__value {
    font-size: 22px;
  }

  .species__row {
    grid-template-columns: 46px minmax(0, 1fr) 26px 38px;
    gap: 8px;
    font-size: 12.5px;
  }

  .trend {
    gap: 5px;
    min-height: 140px;
  }

  .trend__date {
    font-size: 10.5px;
  }
}

@media (max-width: 420px) {
  .stat-card__label {
    font-size: 12px;
  }
}
</style>
