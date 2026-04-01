<template>
  <div class="page-card">
    <div class="workbench-layout" :class="{ 'workbench-layout--result': hasResult }">
      <section class="pane left-pane">
        <div class="pane-card">
          <div class="section-heading">上传图片</div>

          <div v-if="hasResult" class="result-image-wrap">
          <div v-if="previewUrl" class="result-image-frame" :class="{ 'is-decoding': confirmLoading }">
            <img
              ref="resultImg"
              :src="previewUrl"
              class="result-image result-image--blur"
              alt=""
              @load="onResultImgLoad"
            />
            <div v-if="confirmLoading" class="decode-mask">
              <span class="decode-text">超分解码中…</span>
            </div>
            <div class="sharp-layer" aria-hidden="true">
              <div
                v-for="(clipStyle, i) in sharpClipStyles"
                :key="i"
                class="sharp-clip"
                :style="clipStyle.clip"
              >
                <img :src="previewUrl" class="sharp-img" alt="" :style="clipStyle.inner" />
              </div>
            </div>
            <canvas ref="bboxCanvas" class="bbox-canvas" @click="onCanvasClick" />
            <span v-if="platesForView.length > 0" class="plate-count-tag">
              {{ confirmedPlate ? '✓ 已确认' : `检测到 ${detectedPlates.length} 张车牌，请点选目标` }}
            </span>
            <span v-else class="plate-count-tag warn">未检测到车牌</span>
          </div>
          </div>
          <div v-else class="upload-wrap">
            <UploadZone ref="uploadZoneRef" @file-selected="onFileSelected" @file-removed="onFileRemoved" />
          </div>

        </div>
      </section>

      <section class="pane right-pane">
        <div class="pane-card">
          <div class="section-heading">
            {{ hasResult ? (confirmedPlate ? '识别结果' : '目标车牌') : '识别结果' }}
          </div>

          <div class="right-content">
          <template v-if="!hasResult">
            <div class="empty-result">上传图片并点击“开始识别”后，结果将显示在这里</div>
            <t-space direction="vertical" size="small" class="result-actions-td">
              <t-button block theme="default" variant="outline" @click="reset">重置</t-button>
              <t-button
                block
                theme="primary"
                :loading="loading"
                :disabled="!selectedFile"
                @click="submit"
              >
                {{ loading ? '检测中…' : '开始识别' }}
              </t-button>
            </t-space>
          </template>

          <template v-else-if="!confirmedPlate">
            <div class="plate-list">
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
                <span
                  class="plate-select-conf"
                  :class="{ 'plate-select-conf--warn': plate.confidence < CONFIDENCE_THRESHOLD }"
                >
                  {{ (plate.confidence * 100).toFixed(0) }}%
                </span>
              </div>
              <div v-if="detectedPlates.length === 0" class="no-plate-notice">
                未检测到车牌，请尝试更换图片
              </div>
            </div>

            <div v-if="!feedbackSubmitted && detectedPlates.length > 0" class="feedback-row">
              <span class="section-heading section-heading--inline">结果反馈</span>
              <t-space :size="8">
                <t-button
                  shape="square"
                  size="large"
                  :variant="accuracyFeedback === 'accurate' ? 'base' : 'outline'"
                  theme="primary"
                  :disabled="feedbackDisabled"
                  aria-label="识别准确"
                  @click="submitThumbFeedback('accurate')"
                >
                  <template #icon><ThumbUpIcon /></template>
                </t-button>
                <t-button
                  shape="square"
                  size="large"
                  :variant="accuracyFeedback === 'inaccurate' ? 'base' : 'outline'"
                  theme="danger"
                  :disabled="feedbackDisabled"
                  aria-label="识别有误"
                  @click="submitThumbFeedback('inaccurate')"
                >
                  <template #icon><ThumbDownIcon /></template>
                </t-button>
              </t-space>
            </div>
            <p v-if="feedbackDisabled" class="feedback-warn-hint">请先在左侧图中点选目标车牌</p>

            <t-space
              direction="vertical"
              size="small"
              class="result-actions-td"
            >
              <t-button block theme="default" variant="outline" @click="reset">重新上传</t-button>
              <t-button
                v-if="detectedPlates.length > 0"
                block
                theme="primary"
                :loading="confirmLoading"
                :disabled="selectedPlateIndex === null"
                @click="runSuperResolution"
              >
                {{ confirmLoading ? '超分识别中…' : '超分识别' }}
              </t-button>
            </t-space>
          </template>

          <template v-else>
            <PlateCard
              :plate="confirmedPlate"
              :primary="true"
              :duration-ms="confirmDurationMs"
              :timestamp="savedAt"
            />

            <div v-if="!feedbackSubmitted" class="feedback-row">
              <span class="section-heading section-heading--inline">结果反馈</span>
              <t-space :size="8">
                <t-button
                  shape="square"
                  size="large"
                  :variant="accuracyFeedback === 'accurate' ? 'base' : 'outline'"
                  theme="primary"
                  aria-label="识别准确"
                  @click="submitThumbFeedback('accurate')"
                >
                  <template #icon><ThumbUpIcon /></template>
                </t-button>
                <t-button
                  shape="square"
                  size="large"
                  :variant="accuracyFeedback === 'inaccurate' ? 'base' : 'outline'"
                  theme="danger"
                  aria-label="识别有误"
                  @click="submitThumbFeedback('inaccurate')"
                >
                  <template #icon><ThumbDownIcon /></template>
                </t-button>
              </t-space>
            </div>

            <t-button
              block
              theme="default"
              variant="outline"
              class="result-actions-td"
              @click="reset"
            >
              重新识别
            </t-button>
          </template>
          </div>
      </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import { ThumbUpIcon, ThumbDownIcon } from 'tdesign-icons-vue-next'
import UploadZone from '../components/UploadZone.vue'
import PlateCard from '../components/PlateCard.vue'
import PlateVisual from '../components/PlateVisual.vue'
import { recognizePlate, confirmPlate, patchRecordFeedback } from '../api'
import type { PlateResult } from '../types'
import { usePlateFocusImage, getImageScaleParams } from '../composables/usePlateFocusImage'

const CONFIDENCE_THRESHOLD = 0.9
const VALID_CHARS = new Set('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789')
const EXPECTED_NUMBER_LEN: Record<string, number> = {
  blue: 5, yellow: 5, white: 5, black: 5, green_small: 6, unknown: 5,
}

function validatePlateNumber(number: string, type: string): string {
  const expected = EXPECTED_NUMBER_LEN[type] ?? 5
  const padded = number.padEnd(expected, '?')
  const truncated = padded.slice(0, expected)
  return truncated.split('').map((ch, idx) => {
    if (ch === '?') return '?'
    if (type === 'green_small' && idx === expected - 1 && ch !== 'D' && ch !== 'F') return '?'
    if (!VALID_CHARS.has(ch.toUpperCase())) return '?'
    return ch
  }).join('')
}

function hasUncertainChars(validated: string): boolean {
  return validated.includes('?')
}

const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const loading = ref(false)
const confirmLoading = ref(false)
const hasResult = ref(false)
const savedAt = ref('')
const confirmDurationMs = ref(0)

const detectedPlates = ref<PlateResult[]>([])
const selectedPlateIndex = ref<number | null>(null)
const currentRecordId = ref<number | null>(null)
const confirmedPlate = ref<PlateResult | null>(null)

const accuracyFeedback = ref<'accurate' | 'inaccurate' | undefined>(undefined)
const lastSyncedFeedback = ref<'accurate' | 'inaccurate' | undefined>(undefined)
const feedbackSubmitted = ref(false)

const feedbackDisabled = computed(
  () => detectedPlates.value.length > 1 && selectedPlateIndex.value === null
)

const platesForView = computed(() => confirmedPlate.value ? [confirmedPlate.value] : detectedPlates.value)

const uploadZoneRef = ref<{ removeFile: () => void } | null>(null)
const resultImg = ref<HTMLImageElement | null>(null)
const bboxCanvas = ref<HTMLCanvasElement | null>(null)

function drawBboxes() {
  const canvas = bboxCanvas.value
  const img = resultImg.value
  if (!canvas || !img) return
  canvas.width = img.clientWidth
  canvas.height = img.clientHeight
  const { scale, offsetX, offsetY } = getImageScaleParams(img)
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  platesForView.value.forEach((plate, i) => {
    const [x, y, w, h] = plate.bbox
    const cx = offsetX + x * scale
    const cy = offsetY + y * scale
    const cw = w * scale
    const ch = h * scale
    const isSelected = confirmedPlate.value ? true : selectedPlateIndex.value === i

    ctx.strokeStyle = isSelected ? '#00e5a0' : 'rgba(255,255,255,0.6)'
    ctx.lineWidth = isSelected ? 3 : 1.5
    ctx.strokeRect(cx, cy, cw, ch)

    if (isSelected) {
      ctx.fillStyle = 'rgba(0,229,160,0.15)'
      ctx.fillRect(cx, cy, cw, ch)
    }

    ctx.fillStyle = isSelected ? '#00e5a0' : 'rgba(255,255,255,0.8)'
    ctx.font = 'bold 13px sans-serif'
    ctx.fillText(`${i + 1}`, cx + 4, cy + 15)
  })
}

const { sharpClipStyles, bumpLayout, onImageLoad: onFocusImageLoad } = usePlateFocusImage(
  resultImg,
  () => platesForView.value,
  drawBboxes
)

watch(selectedPlateIndex, () => {
  accuracyFeedback.value = undefined
  lastSyncedFeedback.value = undefined
})

onBeforeRouteLeave((to) => {
  if (to.path !== '/history') return true
  const dirty = hasResult.value || !!selectedFile.value || !!previewUrl.value
  if (!dirty) return true

  return new Promise<boolean>((resolve) => {
    let settled = false
    const done = (v: boolean) => {
      if (settled) return
      settled = true
      resolve(v)
    }
    let dlgClosed = false
    const closeDlg = () => {
      if (dlgClosed) return
      dlgClosed = true
      dlg.destroy()
    }
    let dlg: ReturnType<typeof DialogPlugin.confirm>
    dlg = DialogPlugin.confirm({
      header: '确认离开当前页？',
      body: '离开将中断当前识别流程，未保存的界面状态可能丢失。是否仍要离开？',
      theme: 'warning',
      confirmBtn: '仍要离开',
      cancelBtn: '取消',
      closeOnOverlayClick: true,
      closeOnEscKeydown: true,
      closeBtn: true,
      onConfirm: () => { done(true); closeDlg() },
      onCancel: () => { done(false); closeDlg() },
      onClose: () => { done(false); closeDlg() },
    })
  })
})

function onFileSelected(file: File) {
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
}

function onFileRemoved() {
  selectedFile.value = null
  previewUrl.value = ''
}

function onResultImgLoad() {
  onFocusImageLoad()
  drawBboxes()
}

function selectPlate(index: number) {
  if (confirmedPlate.value) return
  selectedPlateIndex.value = index
  drawBboxes()
}

function onCanvasClick(e: MouseEvent) {
  if (confirmedPlate.value) return
  const canvas = bboxCanvas.value
  const img = resultImg.value
  if (!canvas || !img) return
  const { scale, offsetX, offsetY } = getImageScaleParams(img)
  const rect = canvas.getBoundingClientRect()
  const imgX = (e.clientX - rect.left - offsetX) / scale
  const imgY = (e.clientY - rect.top - offsetY) / scale

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
  accuracyFeedback.value = undefined
  lastSyncedFeedback.value = undefined
  feedbackSubmitted.value = false
  try {
    const res = await recognizePlate(selectedFile.value)
    detectedPlates.value = res.plates
    currentRecordId.value = res.record_id
    hasResult.value = true
    if (res.plates.length === 1) selectedPlateIndex.value = 0
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    const status = e?.response?.status
    let msg = '识别失败，请重试'
    if (status === 503) msg = `识别引擎未就绪\n\n${detail ?? '后端服务异常'}\n\n解决方法：重启后端服务（uvicorn main:app --reload）`
    else if (status === 400) msg = detail ?? '图片格式不支持或文件过大'
    else if (status === 500) msg = detail ?? '服务器内部错误，请检查后端日志'
    else if (!status) msg = '无法连接后端服务，请确认后端已启动（端口 8000）'
    MessagePlugin.error(typeof detail === 'string' ? detail : msg)
  } finally {
    loading.value = false
  }
}

function canSubmitFeedback(): boolean {
  if (confirmedPlate.value) return true
  if (detectedPlates.value.length === 0) return false
  if (detectedPlates.value.length > 1 && selectedPlateIndex.value === null) return false
  return true
}

async function submitThumbFeedback(value: 'accurate' | 'inaccurate') {
  if (!currentRecordId.value) return
  if (!canSubmitFeedback()) {
    MessagePlugin.warning('请先在图中点选目标车牌')
    return
  }
  const rollback = accuracyFeedback.value
  const rollbackSynced = lastSyncedFeedback.value
  accuracyFeedback.value = value
  try {
    await patchRecordFeedback(currentRecordId.value, value)
    lastSyncedFeedback.value = value
    feedbackSubmitted.value = true
    MessagePlugin.success('感谢反馈')
  } catch {
    accuracyFeedback.value = rollback
    lastSyncedFeedback.value = rollbackSynced
    MessagePlugin.error('反馈提交失败，请稍后重试')
  }
}

async function runSuperResolution() {
  if (selectedPlateIndex.value === null || currentRecordId.value === null) return
  confirmLoading.value = true
  const t0 = Date.now()
  try {
    const res = await confirmPlate(currentRecordId.value, selectedPlateIndex.value)
    confirmedPlate.value = res.plates[0]
    confirmDurationMs.value = Date.now() - t0
    savedAt.value = new Date().toLocaleString('zh-CN')
    accuracyFeedback.value = undefined
    lastSyncedFeedback.value = undefined
    feedbackSubmitted.value = false
    bumpLayout()
    drawBboxes()
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    MessagePlugin.error(detail ?? '超分识别失败，请重试')
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
  accuracyFeedback.value = undefined
  lastSyncedFeedback.value = undefined
  feedbackSubmitted.value = false
}
</script>

<style scoped>
.page-card {
  padding: 0;
}

.workbench-layout {
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 16px;
  --space-lg: 20px;
  --panel-media-height: clamp(340px, 46vh, 460px);
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: var(--space-lg);
  align-items: stretch;
}

.pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pane-card {
  background: #fff;
  border: 1px solid var(--td-component-border, #e8e8e8);
  border-radius: var(--td-radius-medium, 6px);
  padding: var(--space-md);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.section-heading {
  font-size: 12px;
  font-weight: 600;
  color: var(--td-text-color-secondary, rgba(0, 0, 0, 0.6));
  letter-spacing: 0.02em;
  line-height: 1.4;
  margin: 0 0 var(--space-xs);
}

.section-heading--inline {
  margin: 0;
}

.upload-wrap {
  min-height: var(--panel-media-height);
  height: var(--panel-media-height);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-wrap :deep(.upload-zone),
.upload-wrap :deep(.preview-zone) {
  height: 100%;
  min-height: 0;
  width: 100%;
}

.result-image-wrap {
  height: var(--panel-media-height);
  border-radius: var(--td-radius-medium, 6px);
  overflow: hidden;
  background: #111;
}

.result-image-frame {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
}

.result-image--blur {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  margin: 0 auto;
  filter: blur(14px);
  transform: scale(1.06);
  vertical-align: top;
}

.result-image-frame.is-decoding .result-image--blur {
  animation: decodingBlurPulse 1.4s ease-in-out infinite;
}

.sharp-layer { position: absolute; left: 0; top: 0; width: 100%; height: 100%; pointer-events: none; }
.sharp-clip { position: absolute; overflow: hidden; border-radius: 4px; box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.4); }
.sharp-img { position: absolute; max-width: none; pointer-events: none; }
.bbox-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; cursor: crosshair; }

.decode-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(1px);
  z-index: 3;
  pointer-events: none;
}

.decode-text {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.62);
  letter-spacing: 0.04em;
}

@keyframes decodingBlurPulse {
  0% { filter: blur(12px) brightness(0.92); }
  50% { filter: blur(18px) brightness(1.06); }
  100% { filter: blur(12px) brightness(0.92); }
}

.plate-count-tag {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: var(--td-radius-small, 4px);
  z-index: 2;
  pointer-events: none;
}
.plate-count-tag.warn { color: #ffb84d; }

.right-pane .right-content {
  display: flex;
  flex-direction: column;
  height: var(--panel-media-height);
  min-height: var(--panel-media-height);
  max-height: var(--panel-media-height);
  gap: var(--space-sm);
  overflow: auto;
}

.empty-result {
  border: 1px dashed var(--td-component-stroke, #e8e8e8);
  border-radius: var(--td-radius-medium);
  color: var(--td-text-color-placeholder);
  font-size: 13px;
  padding: var(--space-sm);
}

.plate-list { display: flex; flex-direction: column; gap: var(--space-xs); }
.plate-select-card {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) 14px;
  border: 1px solid var(--td-component-border);
  border-radius: var(--td-radius-medium);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.plate-select-card:hover { border-color: var(--td-brand-color); background: var(--td-bg-color-container-hover, #fafafa); }
.plate-select-card.selected { border-color: var(--td-brand-color); border-width: 2px; background: var(--td-bg-color-secondarycontainer, #f5f5f5); }
.plate-select-num { font-size: 13px; font-weight: 700; color: var(--td-text-color-placeholder); width: 18px; text-align: center; flex-shrink: 0; }
.plate-select-card.selected .plate-select-num { color: var(--td-text-color-primary); }
.plate-select-info { display: flex; flex-direction: column; gap: var(--space-xxs); flex: 1; align-items: flex-start; }
.plate-select-conf { font-size: 18px; font-weight: 700; color: var(--td-text-color-primary); flex-shrink: 0; line-height: 1.2; }
.plate-select-conf--warn { color: var(--td-warning-color, #e37318); }
.plate-uncertain-hint { font-size: 11px; color: var(--td-warning-color); }
.no-plate-notice {
  font-size: 13px;
  color: var(--td-warning-color);
  padding: 12px;
  background: var(--td-warning-color-1, #fff3e0);
  border-radius: var(--td-radius-medium);
}

.feedback-row { display: flex; align-items: center; justify-content: space-between; gap: var(--space-sm); flex-wrap: wrap; }
.feedback-warn-hint { margin: calc(-1 * var(--space-xxs)) 0 0; font-size: 12px; color: var(--td-warning-color); }

/* 关键：按钮区贴底，与左侧图片区下边缘对齐 */
.result-actions-td {
  width: 100%;
  margin-top: auto;
}
</style>
