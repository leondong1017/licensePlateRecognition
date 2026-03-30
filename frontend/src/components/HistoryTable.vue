<template>
  <div>
    <div class="toolbar">
      <input v-model="filters.plate" placeholder="搜索车牌号…" class="search-input" @input="onFilter" />
      <select v-model="filters.type" class="select-input" @change="onFilter">
        <option value="">全部类型</option>
        <option value="blue">蓝牌</option>
        <option value="green_small">新能源</option>
        <option value="yellow">黄牌</option>
      </select>
      <div style="flex:1" />
      <button class="btn btn-outline btn-sm" @click="exportCsv">↓ 导出 CSV</button>
    </div>

    <div v-if="loading" class="loading-hint">加载中…</div>
    <table v-else class="records-table">
      <thead>
        <tr>
          <th>缩略图</th>
          <th>车牌</th>
          <th>置信度</th>
          <th>超分</th>
          <th>识别时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="record in records" :key="record.id">
          <td>
            <img :src="record.image_url" class="thumb" />
          </td>
          <td>
            <PlateVisual
              v-if="record.plates.length"
              :province="record.plates[0].province"
              :city-code="record.plates[0].city_code"
              :number="record.plates[0].number"
              :type="record.plates[0].type"
              size="sm"
            />
            <span v-else style="color:#999;font-size:12px">无</span>
          </td>
          <td>{{ record.plates.length ? (record.plates[0].confidence * 100).toFixed(0) + '%' : '-' }}</td>
          <td>
            <span :class="record.used_sr ? 'badge-warn' : 'badge-light'">
              {{ record.used_sr ? '是' : '否' }}
            </span>
          </td>
          <td>{{ record.created_at }}</td>
          <td><button class="link-btn">查看</button></td>
        </tr>
        <tr v-if="records.length === 0">
          <td colspan="6" style="text-align:center;color:#999;padding:24px">暂无记录</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <span class="pg-info">共 {{ total }} 条</span>
      <button class="pg-btn" :disabled="page <= 1" @click="page--; load()">‹</button>
      <span class="pg-current">{{ page }}</span>
      <button class="pg-btn" :disabled="page * 20 >= total" @click="page++; load()">›</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listRecords, exportRecordsUrl } from '../api'
import PlateVisual from './PlateVisual.vue'
import type { RecordItem } from '../types'

const records = ref<RecordItem[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filters = ref({ plate: '', type: '' })

async function load() {
  loading.value = true
  try {
    const res = await listRecords({ page: page.value, plate: filters.value.plate, type: filters.value.type })
    records.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onFilter() { page.value = 1; load() }

function exportCsv() {
  const a = document.createElement('a')
  a.href = exportRecordsUrl()
  a.download = 'records.csv'
  a.click()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
.search-input { padding: 7px 12px; border: 1px solid #d4d4d4; border-radius: 4px; font-size: 13px; width: 200px; outline: none; }
.search-input:focus { border-color: #1a1a1a; }
.select-input { padding: 7px 12px; border: 1px solid #d4d4d4; border-radius: 4px; font-size: 13px; background: #fff; }
.btn { display: inline-flex; align-items: center; justify-content: center; padding: 7px 16px; border-radius: 4px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.btn-outline { background: #fff; color: #1a1a1a; border: 1px solid #d4d4d4; }
.btn-outline:hover { border-color: #1a1a1a; }
.btn-sm { width: 120px; }
.loading-hint { text-align: center; color: #999; padding: 24px; }
.records-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.records-table thead th { text-align: left; padding: 9px 12px; font-size: 11px; font-weight: 600; color: #999; letter-spacing: .04em; border-bottom: 1px solid #e8e8e8; background: #fafafa; text-transform: uppercase; }
.records-table tbody tr { border-bottom: 1px solid #f5f5f5; transition: background .1s; }
.records-table tbody tr:hover { background: #fafafa; }
.records-table tbody td { padding: 12px; vertical-align: middle; }
.thumb { width: 54px; height: 34px; object-fit: cover; border-radius: 3px; background: #2b2b2b; display: block; }
.badge-warn { background: #fff3e0; color: #e65c00; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.badge-light { background: #f0f0f0; color: #4a4a4a; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.link-btn { color: #1a1a1a; background: none; border: 1px solid #d4d4d4; cursor: pointer; font-size: 12px; padding: 4px 10px; border-radius: 3px; }
.pagination { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; align-items: center; }
.pg-info { font-size: 12px; color: #999; }
.pg-btn { width: 30px; height: 30px; border: 1px solid #e8e8e8; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.pg-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.pg-current { font-size: 13px; font-weight: 500; padding: 0 4px; }
</style>
