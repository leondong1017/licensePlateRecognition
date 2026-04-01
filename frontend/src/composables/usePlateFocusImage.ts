import { ref, computed, type Ref, watch, onUnmounted } from 'vue'
import type { PlateResult } from '../types'

export function getImageScaleParams(img: HTMLImageElement) {
  const scale = Math.min(img.clientWidth / img.naturalWidth, img.clientHeight / img.naturalHeight)
  const renderedW = img.naturalWidth * scale
  const renderedH = img.naturalHeight * scale
  const offsetX = (img.clientWidth - renderedW) / 2
  const offsetY = (img.clientHeight - renderedH) / 2
  return { scale, offsetX, offsetY }
}

/** 车牌区域清晰、其余模糊的裁切层样式（与识别页一致） */
export function usePlateFocusImage(
  imgRef: Ref<HTMLImageElement | null>,
  getPlates: () => PlateResult[],
  onLayout?: () => void
) {
  const layoutVersion = ref(0)
  let resizeObserver: ResizeObserver | null = null

  const sharpClipStyles = computed(() => {
    layoutVersion.value
    const img = imgRef.value
    const plates = getPlates()
    if (!img?.naturalWidth || plates.length === 0) return []
    const { scale, offsetX, offsetY } = getImageScaleParams(img)
    const nw = img.naturalWidth
    const nh = img.naturalHeight
    return plates.map((plate) => {
      const [x, y, w, h] = plate.bbox
      return {
        clip: {
          left: `${offsetX + x * scale}px`,
          top: `${offsetY + y * scale}px`,
          width: `${w * scale}px`,
          height: `${h * scale}px`,
        },
        inner: {
          width: `${nw * scale}px`,
          height: `${nh * scale}px`,
          left: `${-x * scale}px`,
          top: `${-y * scale}px`,
        },
      }
    })
  })

  function bumpLayout() {
    layoutVersion.value++
  }

  function attachResizeObserver() {
    resizeObserver?.disconnect()
    const el = imgRef.value
    if (!el || typeof ResizeObserver === 'undefined') return
    resizeObserver = new ResizeObserver(() => {
      bumpLayout()
      onLayout?.()
    })
    resizeObserver.observe(el)
  }

  function onImageLoad() {
    bumpLayout()
    attachResizeObserver()
    onLayout?.()
  }

  watch(
    () => getPlates(),
    () => {
      bumpLayout()
      onLayout?.()
    },
    { deep: true }
  )

  onUnmounted(() => {
    resizeObserver?.disconnect()
    resizeObserver = null
  })

  return {
    sharpClipStyles,
    bumpLayout,
    onImageLoad,
  }
}
