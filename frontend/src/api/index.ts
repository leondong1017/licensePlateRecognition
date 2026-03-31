import axios from 'axios'
import type { RecognizeResponse, RecordsResponse, RecordItem } from '../types'

export async function recognizePlate(file: File): Promise<RecognizeResponse> {
  const form = new FormData()
  form.append('image', file)
  const { data } = await axios.post<RecognizeResponse>('/api/recognize', form)
  return data
}

export async function confirmPlate(recordId: number, plateIndex: number): Promise<RecognizeResponse> {
  const { data } = await axios.post<RecognizeResponse>('/api/recognize/confirm', {
    record_id: recordId,
    plate_index: plateIndex,
  })
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

export async function getRecord(id: number): Promise<RecordItem> {
  const { data } = await axios.get<RecordItem>(`/api/records/${id}`)
  return data
}

export async function deleteRecord(id: number): Promise<void> {
  await axios.delete(`/api/records/${id}`)
}
