<template>
  <div
    class="upload-zone"
    :class="{ 'upload-zone--dragover': isDragging }"
    @click="(fileInput as HTMLInputElement).click()"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="onDrop"
  >
    <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.bmp" style="display:none" @change="onFileChange" />
    <div class="upload-icon">↑</div>
    <p class="upload-text">点击或拖拽图片 / 视频帧至此处</p>
    <p class="upload-hint">支持 JPG、PNG、BMP，最大 <strong>20MB</strong></p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ (e: 'file-selected', file: File): void }>()
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

const ALLOWED = ['image/jpeg', 'image/png', 'image/bmp']

function validate(file: File): boolean {
  if (!ALLOWED.includes(file.type)) {
    alert('仅支持 JPG/PNG/BMP 格式')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    alert('文件不超过 20MB')
    return false
  }
  return true
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file && validate(file)) emit('file-selected', file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && validate(file)) emit('file-selected', file)
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed #d4d4d4;
  border-radius: 6px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: #fafafa;
}
.upload-zone:hover, .upload-zone--dragover {
  border-color: #1a1a1a;
  background: #f5f5f5;
}
.upload-icon { font-size: 36px; color: #999; margin-bottom: 12px; }
.upload-text { font-size: 14px; color: #4a4a4a; margin-bottom: 5px; }
.upload-hint { font-size: 12px; color: #999; }
.upload-hint strong { color: #1a1a1a; font-weight: 500; }
</style>
