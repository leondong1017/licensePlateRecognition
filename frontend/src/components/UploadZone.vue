<template>
  <!-- Empty state -->
  <div
    v-if="!previewUrl"
    class="upload-zone"
    :class="{ 'upload-zone--dragover': isDragging }"
    @click="fileInput!.click()"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="onDrop"
  >
    <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.bmp,.webp" style="display:none" @change="onFileChange" />
    <div class="upload-icon">↑</div>
    <p class="upload-text">点击或拖拽图片 / 视频帧至此处</p>
    <p class="upload-hint">支持 JPG、PNG、BMP、WebP（静态），最大 <strong>20MB</strong></p>
  </div>

  <!-- Preview state -->
  <div v-else class="preview-zone">
    <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.bmp,.webp" style="display:none" @change="onFileChange" />
    <div class="preview-wrap">
      <img :src="previewUrl" class="preview-img" @click="lightboxOpen = true" title="点击查看大图" />
      <div class="preview-overlay" @click="lightboxOpen = true">
        <span class="preview-zoom">🔍 查看大图</span>
      </div>
    </div>
    <div class="preview-info">
      <span class="preview-name">{{ fileName }}</span>
      <span class="preview-size">{{ fileSize }}</span>
      <button class="preview-delete" @click="removeFile" title="删除">✕ 删除</button>
    </div>
  </div>

  <!-- Lightbox -->
  <Teleport to="body">
    <div v-if="lightboxOpen" class="lightbox" @click.self="lightboxOpen = false">
      <div class="lightbox-inner">
        <button class="lightbox-close" @click="lightboxOpen = false">✕</button>
        <img :src="previewUrl" class="lightbox-img" />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  (e: 'file-selected', file: File): void
  (e: 'file-removed'): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const previewUrl = ref('')
const currentFile = ref<File | null>(null)
const lightboxOpen = ref(false)

const ALLOWED = ['image/jpeg', 'image/png', 'image/bmp', 'image/webp']

const fileName = computed(() => currentFile.value?.name ?? '')
const fileSize = computed(() => {
  const bytes = currentFile.value?.size ?? 0
  return bytes > 1024 * 1024
    ? `${(bytes / 1024 / 1024).toFixed(1)} MB`
    : `${(bytes / 1024).toFixed(0)} KB`
})

function validate(file: File): boolean {
  if (!ALLOWED.includes(file.type)) {
    alert('仅支持 JPG/PNG/BMP/WebP（静态）格式')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    alert('文件不超过 20MB')
    return false
  }
  return true
}

function setFile(file: File) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  currentFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  emit('file-selected', file)
}

function removeFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  currentFile.value = null
  if (fileInput.value) fileInput.value.value = ''
  emit('file-removed')
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file && validate(file)) setFile(file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && validate(file)) setFile(file)
}

defineExpose({ removeFile })
</script>

<style scoped>
/* Empty state */
.upload-zone {
  border: 2px dashed #d4d4d4;
  border-radius: 6px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: #fafafa;
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.upload-zone:hover, .upload-zone--dragover {
  border-color: #1a1a1a;
  background: #f5f5f5;
}
.upload-icon { font-size: 36px; color: #999; margin-bottom: 12px; }
.upload-text { font-size: 14px; color: #4a4a4a; margin-bottom: 5px; }
.upload-hint { font-size: 12px; color: #999; }
.upload-hint strong { color: #1a1a1a; font-weight: 500; }

/* Preview state */
.preview-zone {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.preview-wrap {
  position: relative;
  background: #f5f5f5;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 0;
}
.preview-img { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }
.preview-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,0);
  display: flex; align-items: center; justify-content: center;
  transition: background .2s;
}
.preview-wrap:hover .preview-overlay { background: rgba(0,0,0,.35); }
.preview-zoom { color: #fff; font-size: 13px; opacity: 0; transition: opacity .2s; }
.preview-wrap:hover .preview-zoom { opacity: 1; }
.preview-info {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-top: 1px solid #f0f0f0;
  min-height: 48px;
  height: 48px;
  flex-shrink: 0;
}
.preview-name { font-size: 13px; color: #1a1a1a; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.preview-size { font-size: 12px; color: #999; white-space: nowrap; }
.preview-delete {
  font-size: 12px; color: #e65c00; background: none; border: 1px solid #e65c00;
  border-radius: 3px; padding: 3px 10px; cursor: pointer; white-space: nowrap;
  transition: background .15s;
}
.preview-delete:hover { background: #fff3e0; }

/* Lightbox */
.lightbox {
  position: fixed; inset: 0; background: rgba(0,0,0,.85);
  z-index: 9999; display: flex; align-items: center; justify-content: center;
}
.lightbox-inner { position: relative; max-width: 90vw; max-height: 90vh; }
.lightbox-img { max-width: 90vw; max-height: 85vh; object-fit: contain; border-radius: 4px; }
.lightbox-close {
  position: absolute; top: -36px; right: 0; background: none; border: none;
  color: #fff; font-size: 20px; cursor: pointer; opacity: .7; padding: 4px 8px;
}
.lightbox-close:hover { opacity: 1; }
</style>

