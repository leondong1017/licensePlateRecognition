<template>
  <div :class="['plate-root', typeClass, sizeClass]">
    <div class="plate-province">{{ province }}</div>
    <div class="plate-number">
      <span class="plate-city">
        <span class="char-cell">{{ cityCode }}</span>
      </span>
      <span class="plate-dot">·</span>
      <span class="plate-serial">
        <span v-for="(ch, idx) in serialChars" :key="idx" class="char-cell">{{ ch }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PlateType } from '../types'

const props = withDefaults(defineProps<{
  province: string
  cityCode: string
  number: string
  type: PlateType
  size?: 'sm' | 'md' | 'lg'
}>(), { size: 'md' })

const TYPE_CLASS: Record<PlateType, string> = {
  blue: 'plate-blue',
  green_small: 'plate-green',
  yellow: 'plate-yellow',
  white: 'plate-white',
  black: 'plate-black',
  unknown: 'plate-blue',
}

const typeClass = TYPE_CLASS[props.type]
const sizeClass = `plate-${props.size}`
const serialChars = computed(() => props.number.split(''))
</script>

<style scoped>
.plate-root {
  display: inline-flex;
  align-items: stretch;
  border-radius: 5px;
  overflow: hidden;
  border: 2px solid rgba(0,0,0,.25);
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  font-weight: 700;
  user-select: none;
}
.plate-province {
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid rgba(0,0,0,.2);
  padding: 0 4px;
  font-weight: 900;
}
.plate-number {
  display: flex;
  align-items: center;
  padding: 6px 15px;
  justify-content: center;
  white-space: nowrap;
  gap: 3px;
}
.plate-city,
.plate-serial {
  font-family:
    "DIN Alternate",
    "DIN Condensed",
    "Bahnschrift",
    "Roboto Mono",
    "SFMono-Regular",
    "Menlo",
    monospace;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  letter-spacing: 0.09em;
  line-height: 1;
}
.plate-city {
  display: inline-flex;
  text-align: center;
  flex: 0 0 auto;
}
.plate-serial {
  display: inline-flex;
  text-align: left;
  white-space: nowrap;
  flex: 0 0 auto;
}
.char-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.18ch;
  min-width: 1.18ch;
  text-align: center;
  line-height: 1;
}
.plate-dot {
  margin: 0 7px;
  opacity: 0.78;
  line-height: 1;
}

.plate-blue { background: #1a3a8f; color: #fff; }
.plate-blue .plate-province { background: #1a3a8f; }
.plate-green { background: linear-gradient(to right, #1d7a3a 0%, #1d7a3a 20%, #8db828 60%, #c8b020 100%); color: #000; }
.plate-green .plate-province { background: #1d7a3a; }
.plate-yellow { background: #e8b800; color: #1a1a1a; }
.plate-yellow .plate-province { background: #d4a800; }
.plate-white { background: #f5f5f5; color: #1a1a1a; border-color: #bbb; }
.plate-white .plate-province { background: #e8e8e8; }
.plate-black { background: #1a1a1a; color: #fff; }
.plate-black .plate-province { background: #111; }

.plate-sm .plate-province { width: 24px; font-size: 11px; }
.plate-sm .plate-number { font-size: 13px; padding: 4px 12px; }
.plate-md .plate-province { width: 32px; font-size: 14px; }
.plate-md .plate-number { font-size: 18px; padding: 6px 15px; }
.plate-lg .plate-province { width: 38px; font-size: 16px; }
.plate-lg .plate-number { font-size: 22px; padding: 8px 20px; }
</style>
