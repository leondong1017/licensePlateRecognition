<template>
  <div class="page-card">
    <div class="state-tabs">
      <button
        class="state-tab"
        :class="{ active: activeTab === 'upload' }"
        @click="activeTab = 'upload'"
      >上传图片</button>
      <button
        class="state-tab"
        :class="{ active: activeTab === 'result', disabled: !hasResult }"
        @click="hasResult && (activeTab = 'result')"
      >识别结果</button>
    </div>

    <!-- Upload state -->
    <div v-if="activeTab === 'upload'" class="tab-content">
      <UploadZone ref="uploadZoneRef" @file-selected="onFileSelected" @file-removed="onFileRemoved" />

      <RoiSelector
        v-if="showRoi && previewUrl"
        :image-src="previewUrl"
        @roi-change="roi = $event"
        @skip="showRoi = false; roi = null"
      />

      <div class="action-row">
        <button class="btn btn-outline" @click="reset">重置</button>
        <button
          class="btn btn-primary"
          :disabled="!selectedFile || loading"
          @click="submit"
        >{{ loading ? '识别中…' : '开始识别' }}</button>
      </div>
    </div>

    <!-- Result state -->
    <div v-if="activeTab === 'result' && result" class="tab-content result-layout">
      <div class="result-image-wrap">
        <img :src="previewUrl" class="result-image" ref="resultImg" @load="drawBboxes" />
        <canvas ref="bboxCanvas" class="bbox-canvas" />
        <span class="plate-count-tag">
          {{ result.plates.length > 0 ? `✓ ${result.plates.length} 张车牌` : '未检测到车牌' }}
        </span>
      </div>

      <div class="result-panel">
        <p class="section-label">识别结果</p>
        <PlateCard
          v-for="(plate, i) in result.plates"
          :key="i"
          :plate="plate"
          :primary="i === 0"
          :duration-ms="result.duration_ms"
          :timestamp="savedAt"
        />
        <div v-if="result.plates.length === 0" class="no-plate-notice">
          未检测到车牌，请尝试更换图片或框选目标区域
        </div>
        <div class="action-row">
          <button class="btn btn-outline" @click="reset">重新识别</button>
          <button class="btn btn-primary" @click="onSave">保存记录</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import UploadZone from '../components/UploadZone.vue'
import RoiSelector from '../components/RoiSelector.vue'
import PlateCard from '../components/PlateCard.vue'
import { recognizePlate } from '../api'
import type { RecognizeResponse } from '../types'

const uploadZoneRef = ref<InstanceType<typeof UploadZone> | null>(null)
const activeTab = ref<'upload' | 'result'>('upload')
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const showRoi = ref(false)
const roi = ref<{ x: number; y: number; w: number; h: number } | null>(null)
const loading = ref(false)
const result = ref<RecognizeResponse | null>(null)
const hasResult = ref(false)
const savedAt = ref('')
const resultImg = ref<HTMLImageElement | null>(null)
const bboxCanvas = ref<HTMLCanvasElement | null>(null)

function onFileSelected(file: File) {
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  showRoi.value = false
  roi.value = null
}

function onFileRemoved() {
  selectedFile.value = null
  previewUrl.value = ''
  showRoi.value = false
  roi.value = null
}

async function submit() {
  if (!selectedFile.value) return
  loading.value = true
  try {
    const res = await recognizePlate(selectedFile.value, roi.value ?? undefined)
    result.value = res
    hasResult.value = true
    savedAt.value = new Date().toLocaleString('zh-CN')
    if (res.multi_vehicle && !roi.value) {
      showRoi.value = true
      alert('检测到多辆车，请框选目标车辆后重新识别')
      return
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

function reset() {
  uploadZoneRef.value?.removeFile()
  selectedFile.value = null
  previewUrl.value = ''
  showRoi.value = false
  roi.value = null
  result.value = null
  hasResult.value = false
  activeTab.value = 'upload'
}

function onSave() {
  alert('记录已保存')
}

function drawBboxes() {
  if (!bboxCanvas.value || !resultImg.value || !result.value) return
  const img = resultImg.value
  const canvas = bboxCanvas.value
  canvas.width = img.clientWidth
  canvas.height = img.clientHeight
  const scaleX = img.clientWidth / img.naturalWidth
  const scaleY = img.clientHeight / img.naturalHeight
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.strokeStyle = '#00e5a0'
  ctx.lineWidth = 2
  for (const plate of result.value.plates) {
    const [x, y, w, h] = plate.bbox
    ctx.strokeRect(x * scaleX, y * scaleY, w * scaleX, h * scaleY)
  }
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
.result-layout { display: grid; grid-template-columns: 1fr 360px; gap: 20px; }
.result-image-wrap { position: relative; border-radius: 6px; overflow: hidden; background: #111; }
.result-image { display: block; width: 100%; max-height: 400px; object-fit: contain; }
.bbox-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.plate-count-tag { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,.6); color: #fff; font-size: 12px; padding: 3px 8px; border-radius: 4px; }
.result-panel { display: flex; flex-direction: column; gap: 14px; }
.section-label { font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; letter-spacing: .08em; }
.no-plate-notice { font-size: 13px; color: #e65c00; padding: 12px; background: #fff3e0; border-radius: 4px; }
</style>
