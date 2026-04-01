<template>
  <!-- Compact variant for history modal: gray bg, plate left, conf+time right, no progress bar -->
  <div v-if="compact" class="plate-card plate-card--compact">
    <PlateVisual
      :province="plate.province"
      :city-code="plate.city_code"
      :number="plate.number"
      :type="plate.type"
      size="md"
    />
    <div class="compact-right">
      <span class="compact-conf">置信度 {{ (plate.confidence * 100).toFixed(0) }}%</span>
      <span class="compact-time" v-if="timestamp">{{ timestamp }}</span>
    </div>
  </div>

  <!-- Full variant for recognition result -->
  <div v-else class="plate-card">
    <div class="plate-display-row">
      <div class="plate-main">
        <PlateVisual
          :province="plate.province"
          :city-code="plate.city_code"
          :number="plate.number"
          :type="plate.type"
          size="lg"
        />
      </div>
      <div class="confidence-flow" :class="{ 'confidence-flow--warn': plate.confidence < 0.9 }">
        <span class="confidence-value confidence-value--after">{{ toPercent(plate.confidence) }}</span>
      </div>
    </div>
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
  compact?: boolean
  primary?: boolean
  durationMs?: number
  timestamp?: string
}>()

function toPercent(value: number | null | undefined): string {
  if (value == null) return ''
  return `${(value * 100).toFixed(0)}%`
}
</script>

<style scoped>
/* Full card */
.plate-card {
  background: #fff;
  border: 1px solid var(--td-component-stroke, #e8e8e8);
  border-radius: var(--td-radius-medium, 6px);
  padding: 18px;
}
.plate-display-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}
.plate-main {
  min-width: 0;
  flex: 1;
}
.confidence-flow {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.confidence-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.15;
  white-space: nowrap;
}
.confidence-value--after {
  color: var(--td-brand-color, #0052d9);
}
.confidence-flow--warn .confidence-value--after {
  color: var(--td-warning-color, #e37318);
}
.sr-notice {
  font-size: 12px;
  color: var(--td-warning-color, #e65c00);
  margin-top: 4px;
  padding: 6px 10px;
  background: var(--td-warning-color-1, #fff3e0);
  border-radius: var(--td-radius-small, 4px);
}
.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--td-text-color-placeholder, #bbb);
  margin-top: 12px;
  padding-top: 0;
}

/* Compact card */
.plate-card--compact {
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.compact-right {
  margin-left: auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
}
.compact-conf {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a1a;
}
.compact-time {
  font-size: 11px;
  color: #999;
}
</style>
