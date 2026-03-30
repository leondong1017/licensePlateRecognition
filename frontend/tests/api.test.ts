import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { recognizePlate, listRecords } from '../src/api/index'

vi.mock('axios')
const mockedAxios = axios as any

describe('API client', () => {
  beforeEach(() => vi.clearAllMocks())

  it('recognizePlate posts to /api/recognize', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: { record_id: 1, plates: [], used_sr: false, duration_ms: 50, multi_vehicle: false }
    })
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    const result = await recognizePlate(file)
    expect(result.record_id).toBe(1)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/recognize', expect.any(FormData))
  })

  it('listRecords passes query params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { total: 0, items: [] } })
    await listRecords({ page: 2, plate: '粤B' })
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/records', {
      params: { page: 2, limit: 20, plate: '粤B', type: '', date_from: '', date_to: '' }
    })
  })
})
