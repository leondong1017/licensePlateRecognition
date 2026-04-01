export type PlateType = 'blue' | 'green_small' | 'yellow' | 'white' | 'black' | 'unknown'

export interface PlateResult {
  text: string
  province: string
  city_code: string
  number: string
  type: PlateType
  type_label: string
  confidence: number
  confidence_before_sr: number | null
  bbox: [number, number, number, number]
}

export interface RecognizeResponse {
  record_id: number
  plates: PlateResult[]
  used_sr: boolean
  duration_ms: number
  multi_vehicle: boolean
}

export type UserFeedback = 'accurate' | 'inaccurate'

export interface RecordItem {
  id: number
  created_at: string
  plates: PlateResult[]
  used_sr: boolean
  image_url: string
  user_feedback?: UserFeedback | null
}

export interface RecordsResponse {
  total: number
  items: RecordItem[]
}
