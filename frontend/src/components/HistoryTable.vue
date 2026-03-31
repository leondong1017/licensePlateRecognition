<template>
  <div>
    <div class="toolbar">
      <t-input
        v-model="filters.plate"
        placeholder="搜索车牌号…"
        style="width: 200px"
        clearable
        @input="onFilter"
      />
      <t-select
        v-model="filters.type"
        placeholder="全部类型"
        style="width: 200px"
        clearable
        @change="onTypeChange"
      >
        <t-option value="blue" label="蓝牌" />
        <t-option value="green_small" label="新能源" />
        <t-option value="yellow" label="黄牌" />
      </t-select>
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
          <td><img :src="record.image_url" class="thumb" /></td>
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
          <td class="action-cell">
            <button class="link-btn" @click="openDetail(record)">查看</button>
            <button class="link-btn danger" @click="onDeleteRow(record.id)">删除</button>
          </td>
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

    <!-- Detail Modal -->
    <Teleport to="body">
      <div v-if="detailVisible" class="modal-overlay" @click.self="detailVisible = false">
        <div class="modal-box">
          <div class="modal-header">
            <span>记录详情 #{{ detailRecord?.id }}</span>
            <button class="modal-close" @click="detailVisible = false">✕</button>
          </div>
          <div class="modal-body">
            <div class="modal-image-wrap" v-if="detailRecord">
              <img
                :src="detailRecord.image_url"
                class="modal-image"
                ref="modalImg"
                @load="drawModalBboxes"
                draggable="false"
              />
              <canvas ref="modalCanvas" class="modal-canvas" />
            </div>
            <div class="modal-plates" v-if="detailRecord">
              <PlateCard
                v-for="(plate, i) in detailRecord.plates"
                :key="i"
                :plate="plate"
                :primary="i === 0"
                :timestamp="detailRecord.created_at"
              />
              <div v-if="detailRecord.plates.length === 0" style="color:#999;font-size:13px;padding:12px">
                此记录无识别结果
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { listRecords, deleteRecord } from '../api'
import PlateVisual from './PlateVisual.vue'
import PlateCard from './PlateCard.vue'
import type { RecordItem } from '../types'

const records = ref<RecordItem[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filters = ref({ plate: '', type: '' as string | undefined })

// Detail modal
const detailVisible = ref(false)
const detailRecord = ref<RecordItem | null>(null)
const modalImg = ref<HTMLImageElement | null>(null)
const modalCanvas = ref<HTMLCanvasElement | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await listRecords({
      page: page.value,
      plate: filters.value.plate,
      type: filters.value.type ?? '',
    })
    records.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onFilter() { page.value = 1; load() }

function onTypeChange(val: string | undefined) {
  filters.value.type = val
  onFilter()
}

async function onDeleteRow(id: number) {
  if (!window.confirm('确认删除这条记录？')) return
  try {
    await deleteRecord(id)
    await load()
  } catch {
    alert('删除失败，请重试')
  }
}

function openDetail(record: RecordItem) {
  detailRecord.value = record
  detailVisible.value = true
  // Draw bboxes after modal renders
  nextTick(() => {
    if (modalImg.value?.complete) drawModalBboxes()
  })
}

function getScaleParams(img: HTMLImageElement) {
  const scale = Math.min(img.clientWidth / img.naturalWidth, img.clientHeight / img.naturalHeight)
  const renderedW = img.naturalWidth * scale
  const renderedH = img.naturalHeight * scale
  const offsetX = (img.clientWidth - renderedW) / 2
  const offsetY = (img.clientHeight - renderedH) / 2
  return { scale, offsetX, offsetY }
}

function drawModalBboxes() {
  const canvas = modalCanvas.value
  const img = modalImg.value
  if (!canvas || !img || !detailRecord.value) return
  canvas.width = img.clientWidth
  canvas.height = img.clientHeight
  const { scale, offsetX, offsetY } = getScaleParams(img)
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.strokeStyle = '#00e5a0'
  ctx.lineWidth = 2
  for (const plate of detailRecord.value.plates) {
    const [x, y, w, h] = plate.bbox
    ctx.strokeRect(offsetX + x * scale, offsetY + y * scale, w * scale, h * scale)
  }
}

// Watch detailVisible to re-draw when modal reopens
watch(detailVisible, (v) => {
  if (v) nextTick(() => { if (modalImg.value?.complete) drawModalBboxes() })
})

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; }
.loading-hint { text-align: center; color: #999; padding: 24px; }
.records-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.records-table thead th { text-align: left; padding: 9px 12px; font-size: 11px; font-weight: 600; color: #999; letter-spacing: .04em; border-bottom: 1px solid #e8e8e8; background: #fafafa; text-transform: uppercase; }
.records-table tbody tr { border-bottom: 1px solid #f5f5f5; transition: background .1s; }
.records-table tbody tr:hover { background: #fafafa; }
.records-table tbody td { padding: 12px; vertical-align: middle; }
.thumb { width: 54px; height: 34px; object-fit: cover; border-radius: 3px; background: #2b2b2b; display: block; }
.badge-warn { background: #fff3e0; color: #e65c00; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.badge-light { background: #f0f0f0; color: #4a4a4a; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.action-cell { display: flex; gap: 8px; align-items: center; }
.link-btn { color: #1a1a1a; background: none; border: 1px solid #d4d4d4; cursor: pointer; font-size: 12px; padding: 4px 10px; border-radius: 3px; }
.link-btn:hover { background: #f5f5f5; }
.link-btn.danger { color: #e65c00; border-color: #e65c00; }
.link-btn.danger:hover { background: #fff3e0; }
.pagination { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; align-items: center; }
.pg-info { font-size: 12px; color: #999; }
.pg-btn { width: 30px; height: 30px; border: 1px solid #e8e8e8; border-radius: 4px; background: #fff; cursor: pointer; font-size: 13px; }
.pg-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.pg-current { font-size: 13px; font-weight: 500; padding: 0 4px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.6); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-box { background: #fff; border-radius: 8px; width: 720px; max-width: 95vw; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e8e8e8; font-size: 15px; font-weight: 600; }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #999; padding: 0 4px; }
.modal-close:hover { color: #1a1a1a; }
.modal-body { display: flex; flex-direction: column; gap: 16px; padding: 20px; overflow-y: auto; }
.modal-image-wrap { position: relative; background: #111; border-radius: 6px; overflow: hidden; }
.modal-image { display: block; width: 100%; max-height: 340px; object-fit: contain; }
.modal-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.modal-plates { display: flex; flex-direction: column; gap: 10px; }
</style>
