<template>
  <div class="plate-card" :class="{ 'plate-card--primary': primary }">
    <div class="plate-display-row">
      <PlateVisual
        :province="plate.province"
        :city-code="plate.city_code"
        :number="plate.number"
        :type="plate.type"
        size="lg"
      />
      <span class="type-label">{{ plate.type_label }}</span>
    </div>
    <div class="confidence-bar">
      <div
        class="confidence-fill"
        :class="{ warn: plate.confidence < 0.9 }"
        :style="{ width: (plate.confidence * 100) + '%' }"
      />
    </div>
    <p class="confidence-label">
      置信度 {{ (plate.confidence * 100).toFixed(0) }}%
      <span v-if="plate.confidence_before_sr != null">
        （超分前 {{ (plate.confidence_before_sr * 100).toFixed(0) }}%）
      </span>
    </p>
    <div v-if="plate.confidence_before_sr != null" class="sr-notice">
      ⚠ 图片较模糊，已自动启用超分增强
    </div>
    <div class="info-row">
      <span v-if="durationMs">耗时 {{ durationMs }}ms</span>
      <span v-if="timestamp">{{ timestamp }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import PlateVisual from './PlateVisual.vue'
import type { PlateResult } from '../types'

defineProps<{
  plate: PlateResult
  primary?: boolean
  durationMs?: number
  timestamp?: string
}>()
</script>

<style scoped>
.plate-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 6px; padding: 18px; }
.plate-card--primary { border-color: #1a1a1a; box-shadow: 0 0 0 3px rgba(0,0,0,.04); }
.plate-display-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.type-label { font-size: 11px; color: #999; }
.confidence-bar { height: 3px; background: #f0f0f0; border-radius: 2px; overflow: hidden; margin-bottom: 4px; }
.confidence-fill { height: 100%; background: #1a1a1a; border-radius: 2px; transition: width .3s; }
.confidence-fill.warn { background: #e65c00; }
.confidence-label { font-size: 11px; color: #999; }
.sr-notice { font-size: 12px; color: #e65c00; margin-top: 8px; padding: 6px 10px; background: #fff3e0; border-radius: 4px; }
.info-row { display: flex; justify-content: space-between; font-size: 11px; color: #bbb; padding-top: 10px; border-top: 1px solid #f0f0f0; margin-top: 8px; }
</style>
