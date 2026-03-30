<template>
  <div class="roi-wrapper">
    <div class="roi-header">
      <span class="roi-title">
        ℹ 检测到多辆车，请框选目标车辆
        <span class="badge-warn">多车场景</span>
      </span>
      <button class="skip-btn" @click="emit('skip')">跳过</button>
    </div>
    <div
      class="roi-container"
      @mousedown="startDraw"
      @mousemove="drawing"
      @mouseup="endDraw"
    >
      <img ref="imgEl" :src="imageSrc" class="roi-image" @load="onImgLoad" draggable="false" />
      <canvas ref="canvas" class="roi-canvas" />
    </div>
    <p class="roi-hint">在图片上拖动绘制框选区域，框选后点击"开始识别"</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ imageSrc: string }>()
const emit = defineEmits<{
  (e: 'roi-change', roi: { x: number; y: number; w: number; h: number } | null): void
  (e: 'skip'): void
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
const imgEl = ref<HTMLImageElement | null>(null)
let startX = 0, startY = 0, isDrawing = false

function onImgLoad() {
  if (!canvas.value || !imgEl.value) return
  canvas.value.width = imgEl.value.clientWidth
  canvas.value.height = imgEl.value.clientHeight
}

function getPos(e: MouseEvent) {
  const rect = canvas.value!.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function startDraw(e: MouseEvent) {
  const pos = getPos(e)
  startX = pos.x; startY = pos.y
  isDrawing = true
}

function drawing(e: MouseEvent) {
  if (!isDrawing || !canvas.value) return
  const ctx = canvas.value.getContext('2d')!
  const pos = getPos(e)
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.strokeStyle = '#fff'
  ctx.lineWidth = 2
  ctx.fillStyle = 'rgba(255,255,255,0.1)'
  const w = pos.x - startX, h = pos.y - startY
  ctx.strokeRect(startX, startY, w, h)
  ctx.fillRect(startX, startY, w, h)
}

function endDraw(e: MouseEvent) {
  if (!isDrawing || !imgEl.value) return
  isDrawing = false
  const pos = getPos(e)
  const scaleX = imgEl.value.naturalWidth / imgEl.value.clientWidth
  const scaleY = imgEl.value.naturalHeight / imgEl.value.clientHeight
  const x = Math.round(Math.min(startX, pos.x) * scaleX)
  const y = Math.round(Math.min(startY, pos.y) * scaleY)
  const w = Math.round(Math.abs(pos.x - startX) * scaleX)
  const h = Math.round(Math.abs(pos.y - startY) * scaleY)
  emit('roi-change', w > 10 && h > 10 ? { x, y, w, h } : null)
}
</script>

<style scoped>
.roi-wrapper { padding: 16px; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 6px; margin-top: 20px; }
.roi-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.roi-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; }
.badge-warn { background: #fff3e0; color: #e65c00; font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.skip-btn { font-size: 12px; color: #999; background: none; border: none; cursor: pointer; }
.roi-container { position: relative; background: #1a1a1a; border-radius: 4px; overflow: hidden; }
.roi-image { display: block; width: 100%; max-height: 280px; object-fit: contain; }
.roi-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; cursor: crosshair; }
.roi-hint { font-size: 12px; color: #999; margin-top: 8px; }
</style>
