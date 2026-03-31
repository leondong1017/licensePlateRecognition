<template>
  <div class="page-card">
    <div class="state-tabs">
      <button class="state-tab" :class="{ active: activeTab === 'upload' }" @click="activeTab = 'upload'">上传图片</button>
      <button class="state-tab" :class="{ active: activeTab === 'result', disabled: !hasResult }" @click="hasResult && (activeTab = 'result')">识别结果</button>
    </div>

    <!-- Upload state -->
    <div v-if="activeTab === 'upload'" class="tab-content">
      <UploadZone ref="uploadZoneRef" @file-selected="onFileSelected" @file-removed="onFileRemoved" />
      <div class="action-row">
        <button class="btn btn-outline" @click="reset">重置</button>
        <button class="btn btn-primary" :disabled="!selectedFile || loading" @click="submit">
          {{ loading ? '检测中…' : '开始识别' }}
        </button>
      </div>
    </div>

    <!-- Result state -->
    <div v-if="activeTab === 'result'" class="tab-content result-layout">
      <!-- Left: image with bbox overlays -->
      <div class="result-image-wrap">
        <img
          :src="previewUrl"
          class="result-image"
          ref="resultImg"
          @load="drawBboxes"
          draggable="false"
        />
        <canvas
          ref="bboxCanvas"
          class="bbox-canvas"
          @click="onCanvasClick"
        />
        <span class="plate-count-tag" v-if="detectedPlates.length > 0">
          {{ confirmedPlate ? '✓ 已确认' : `检测到 ${detectedPlates.length} 张车牌，请点选目标` }}
        </span>
        <span class="plate-count-tag warn" v-else>未检测到车牌</span>
      </div>

      <!-- Right: plate list + confirm -->
      <div class="result-panel">
        <p class="section-label">{{ confirmedPlate ? '识别结果' : '请选择目标车牌' }}</p>

        <!-- Before confirm: show all detected plates for selection -->
        <template v-if="!confirmedPlate">
          <div
            v-for="(plate, i) in detectedPlates"
            :key="i"
            class="plate-select-card"
            :class="{ selected: selectedPlateIndex === i }"
            @click="selectPlate(i)"
          >
            <span class="plate-select-num">{{ i + 1 }}</span>
            <div class="plate-select-info">
              <PlateVisual
                :province="plate.province"
                :city-code="plate.city_code"
                :number="validatePlateNumber(plate.number, plate.type)"
                :type="plate.type"
                size="md"
              />
              <span
                v-if="hasUncertainChars(validatePlateNumber(plate.number, plate.type))"
                class="plate-uncertain-hint"
              >含不确定字符，建议超分识别</span>
            </div>
            <span class="plate-select-conf" :class="{ 'conf-low': plate.confidence < 0.8 }">
              {{ (plate.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div v-if="detectedPlates.length === 0" class="no-plate-notice">
            未检测到车牌，请尝试更换图片
          </div>
          <!-- 垂直按钮组，全宽与选牌卡一致 -->
          <div class="action-col" v-if="detectedPlates.length > 0">
            <button class="btn-full btn-full--outline" @click="reset">重新上传</button>
            <button
              class="btn-full btn-full--primary"
              :disabled="selectedPlateIndex === null || confirmLoading"
              @click="confirmRecognize"
            >{{ confirmLoading ? '超分识别中…' : '确认识别' }}</button>
          </div>
        </template>

        <!-- After confirm: show final result -->
        <template v-if="confirmedPlate">
          <PlateCard
            :plate="confirmedPlate"
            :primary="true"
            :duration-ms="confirmDurationMs"
            :timestamp="savedAt"
          />
          <div class="action-row">
            <button class="btn btn-outline" @click="reset">重新识别</button>
            <button class="btn btn-primary" @click="onSave">保存记录</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import UploadZone from '../components/UploadZone.vue'
import PlateCard from '../components/PlateCard.vue'
import PlateVisual from '../components/PlateVisual.vue'
import { recognizePlate, confirmPlate } from '../api'
import type { PlateResult } from '../types'

// ── 车牌格式校验 ────────────────────────────────────────────────
// 国标字符集（排除 I、O）
const VALID_CHARS = new Set('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789')

// 各牌型期望的 number 字段位数（即省/市码之后的字符数）
const EXPECTED_NUMBER_LEN: Record<string, number> = {
  blue: 5,        // 蓝牌  7 位 = 省(1)+市(1)+5
  yellow: 5,      // 黄牌
  white: 5,       // 警/军
  black: 5,       // 使馆
  green_small: 6, // 新能源小型 8 位，末位 D/F
  unknown: 5,
}

function validatePlateNumber(number: string, type: string): string {
  const expected = EXPECTED_NUMBER_LEN[type] ?? 5
  const padded = number.padEnd(expected, '?')
  const truncated = padded.slice(0, expected)
  return truncated.split('').map((ch, idx) => {
    if (ch === '?') return '?'
    // 新能源末位只允许 D 或 F
    if (type === 'green_small' && idx === expected - 1 && ch !== 'D' && ch !== 'F') return '?'
    if (!VALID_CHARS.has(ch.toUpperCase())) return '?'
    return ch
  }).join('')
}

function hasUncertainChars(validated: string): boolean {
  return validated.includes('?')
}
// ────────────────────────────────────────────────────────────────

const activeTab = ref<'upload' | 'result'>('upload')
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const loading = ref(false)
const confirmLoading = ref(false)
const hasResult = ref(false)
const savedAt = ref('')
const confirmDurationMs = ref(0)

// Detection phase
const detectedPlates = ref<PlateResult[]>([])
const selectedPlateIndex = ref<number | null>(null)
const currentRecordId = ref<number | null>(null)

// Confirm phase
const confirmedPlate = ref<PlateResult | null>(null)

const uploadZoneRef = ref<any>(null)
const resultImg = ref<HTMLImageElement | null>(null)
const bboxCanvas = ref<HTMLCanvasElement | null>(null)

function onFileSelected(file: File) {
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

function onFileRemoved() {
  selectedFile.value = null
  previewUrl.value = ''
}

// Compute letterbox-aware scaling params
function getScaleParams() {
  const img = resultImg.value
  if (!img) return null
  const scale = Math.min(img.clientWidth / img.naturalWidth, img.clientHeight / img.naturalHeight)
  const renderedW = img.naturalWidth * scale
  const renderedH = img.naturalHeight * scale
  const offsetX = (img.clientWidth - renderedW) / 2
  const offsetY = (img.clientHeight - renderedH) / 2
  return { scale, renderedW, renderedH, offsetX, offsetY }
}

function drawBboxes() {
  const canvas = bboxCanvas.value
  const img = resultImg.value
  if (!canvas || !img) return
  canvas.width = img.clientWidth
  canvas.height = img.clientHeight
  const sp = getScaleParams()
  if (!sp) return
  const { scale, offsetX, offsetY } = sp
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  detectedPlates.value.forEach((plate, i) => {
    const [x, y, w, h] = plate.bbox
    const cx = offsetX + x * scale
    const cy = offsetY + y * scale
    const cw = w * scale
    const ch = h * scale
    const isSelected = selectedPlateIndex.value === i

    ctx.strokeStyle = isSelected ? '#00e5a0' : 'rgba(255,255,255,0.6)'
    ctx.lineWidth = isSelected ? 3 : 1.5
    ctx.strokeRect(cx, cy, cw, ch)

    if (isSelected) {
      ctx.fillStyle = 'rgba(0,229,160,0.15)'
      ctx.fillRect(cx, cy, cw, ch)
    }

    // Index label
    ctx.fillStyle = isSelected ? '#00e5a0' : 'rgba(255,255,255,0.8)'
    ctx.font = 'bold 13px sans-serif'
    ctx.fillText(`${i + 1}`, cx + 4, cy + 15)
  })
}

function selectPlate(index: number) {
  selectedPlateIndex.value = index
  drawBboxes()
}

function onCanvasClick(e: MouseEvent) {
  const canvas = bboxCanvas.value
  const sp = getScaleParams()
  if (!canvas || !sp) return
  const rect = canvas.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  const clickY = e.clientY - rect.top
  const { scale, offsetX, offsetY } = sp

  // Convert click to image coords
  const imgX = (clickX - offsetX) / scale
  const imgY = (clickY - offsetY) / scale

  // Find which bbox was clicked
  for (let i = 0; i < detectedPlates.value.length; i++) {
    const [x, y, w, h] = detectedPlates.value[i].bbox
    if (imgX >= x && imgX <= x + w && imgY >= y && imgY <= y + h) {
      selectPlate(i)
      return
    }
  }
}

async function submit() {
  if (!selectedFile.value) return
  loading.value = true
  detectedPlates.value = []
  selectedPlateIndex.value = null
  confirmedPlate.value = null
  currentRecordId.value = null
  try {
    const res = await recognizePlate(selectedFile.value)
    detectedPlates.value = res.plates
    currentRecordId.value = res.record_id
    hasResult.value = true
    // Auto-select if only one plate
    if (res.plates.length === 1) {
      selectedPlateIndex.value = 0
    }
    activeTab.value = 'result'
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    const status = e?.response?.status
    let msg = '识别失败，请重试'
    if (status === 503) {
      msg = `识别引擎未就绪\n\n${detail ?? '后端服务异常'}\n\n解决方法：重启后端服务（uvicorn main:app --reload）`
    } else if (status === 400) {
      msg = detail ?? '图片格式不支持或文件过大'
    } else if (status === 500) {
      msg = detail ?? '服务器内部错误，请检查后端日志'
    } else if (!status) {
      msg = '无法连接后端服务，请确认后端已启动（端口 8000）'
    }
    alert(msg)
  } finally {
    loading.value = false
  }
}

async function confirmRecognize() {
  if (selectedPlateIndex.value === null || currentRecordId.value === null) return
  confirmLoading.value = true
  const t0 = Date.now()
  try {
    const res = await confirmPlate(currentRecordId.value, selectedPlateIndex.value)
    confirmedPlate.value = res.plates[0]
    confirmDurationMs.value = Date.now() - t0
    savedAt.value = new Date().toLocaleString('zh-CN')
    drawBboxes()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    alert(detail ?? '超分识别失败，请重试')
  } finally {
    confirmLoading.value = false
  }
}

function reset() {
  uploadZoneRef.value?.removeFile()
  selectedFile.value = null
  previewUrl.value = ''
  detectedPlates.value = []
  selectedPlateIndex.value = null
  confirmedPlate.value = null
  currentRecordId.value = null
  hasResult.value = false
  activeTab.value = 'upload'
}

function onSave() {
  alert('记录已保存')
}
</script>

<style scoped>
.page-card { background: #fff; border-radius: 8px; border: 1px solid #e8e8e8; padding: 24px; }
.state-tabs { display: flex; border-bottom: 1px solid #e8e8e8; margin-bottom: 24px; }
.state-tab { padding: 10px 20px; font-size: 13px; cursor: pointer; color: #999; border: none; background: none; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all .15s; }
.state-tab.active { color: #1a1a1a; border-bottom-color: #1a1a1a; font-weight: 500; }
.state-tab.disabled { cursor: not-allowed; opacity: 0.5; }
.tab-content { padding-top: 4px; }
.action-row { margin-top: 20px; display: flex; justify-content: flex-end; gap: 10px; }
.btn { display: inline-flex; align-items: center; justify-content: center; width: 140px; padding: 9px 0; border-radius: 4px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; transition: all .15s; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #1a1a1a; color: #fff; }
.btn-primary:not(:disabled):hover { background: #333; }
.btn-outline { background: #fff; color: #1a1a1a; border: 1px solid #d4d4d4; }
.btn-outline:hover { border-color: #1a1a1a; }
.result-layout { display: grid; grid-template-columns: 1fr 360px; gap: 20px; align-items: start; }
.result-image-wrap { position: relative; border-radius: 6px; overflow: hidden; background: #111; }
.result-image { display: block; width: 100%; max-height: 400px; object-fit: contain; }
.bbox-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; cursor: crosshair; }
.plate-count-tag { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,.65); color: #fff; font-size: 12px; padding: 3px 10px; border-radius: 4px; }
.plate-count-tag.warn { color: #ffb84d; }
.result-panel { display: flex; flex-direction: column; gap: 10px; }
.section-label { font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; letter-spacing: .08em; }
.plate-select-card { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border: 1px solid #e8e8e8; border-radius: 6px; cursor: pointer; transition: all .15s; }
.plate-select-card:hover { border-color: #1a1a1a; background: #fafafa; }
.plate-select-card.selected { border-color: #1a1a1a; border-width: 2px; background: #f5f5f5; }
.plate-select-num { font-size: 13px; font-weight: 700; color: #999; width: 18px; text-align: center; flex-shrink: 0; }
.plate-select-card.selected .plate-select-num { color: #1a1a1a; }
.plate-select-info { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.plate-select-conf { font-size: 12px; color: #999; flex-shrink: 0; }
.plate-select-conf.conf-low { color: #e65c00; font-weight: 500; }
.plate-uncertain-hint { font-size: 11px; color: #e65c00; }
.no-plate-notice { font-size: 13px; color: #e65c00; padding: 12px; background: #fff3e0; border-radius: 4px; }

/* Vertical full-width button group */
.action-col { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.btn-full { width: 100%; padding: 10px 0; border-radius: 4px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; transition: all .15s; text-align: center; }
.btn-full:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-full--outline { background: #fff; color: #1a1a1a; border: 1px solid #d4d4d4; }
.btn-full--outline:hover { border-color: #1a1a1a; }
.btn-full--primary { background: #1a1a1a; color: #fff; }
.btn-full--primary:not(:disabled):hover { background: #333; }
</style>
