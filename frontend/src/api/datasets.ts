import api from './axios'

export interface UpdateDatasetRequest {
  description?: string
  tags?: string[]
}

export const uploadDataset = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/datasets/upload', formData)
  return data
}

export const prepareDataset = async (datasetId: string, splitRatio?: any, classes?: string[]) => {
  const { data } = await api.post(`/datasets/${datasetId}/prepare`, {
    split_ratio: splitRatio,
    classes
  })
  return data
}

export const listDatasets = async () => {
  const { data } = await api.get('/datasets')
  return data
}

export const getDataset = async (datasetId: string) => {
  const { data } = await api.get(`/datasets/${datasetId}`)
  return data
}

export const updateDataset = async (datasetId: string, request: UpdateDatasetRequest) => {
  const { data } = await api.put(`/datasets/${datasetId}`, request)
  return data
}

export const deleteDataset = async (datasetId: string) => {
  const { data } = await api.delete(`/datasets/${datasetId}`)
  return data
}
