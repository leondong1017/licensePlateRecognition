import axios from 'axios'
import type { RecognizeResponse, RecordsResponse } from '../types'

export async function recognizePlate(
  file: File,
  roi?: { x: number; y: number; w: number; h: number }
): Promise<RecognizeResponse> {
  const form = new FormData()
  form.append('image', file)
  const params = roi ? `?roi_x=${roi.x}&roi_y=${roi.y}&roi_w=${roi.w}&roi_h=${roi.h}` : ''
  const endpoint = roi ? `/api/recognize/roi${params}` : '/api/recognize'
  const { data } = await axios.post<RecognizeResponse>(endpoint, form)
  return data
}

export async function listRecords(params: {
  page?: number
  limit?: number
  plate?: string
  type?: string
  date_from?: string
  date_to?: string
} = {}): Promise<RecordsResponse> {
  const { data } = await axios.get<RecordsResponse>('/api/records', {
    params: {
      page: params.page ?? 1,
      limit: params.limit ?? 20,
      plate: params.plate ?? '',
      type: params.type ?? '',
      date_from: params.date_from ?? '',
      date_to: params.date_to ?? '',
    }
  })
  return data
}

export function exportRecordsUrl(): string {
  return '/api/records/export?format=csv'
}
