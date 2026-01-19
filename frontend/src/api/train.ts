import api from './axios'

export interface TrainJobRequest {
  dataset_id: string
  version?: string
  model_name?: string
  epochs: number
  imgsz?: number
  batch?: number
  base_model_id?: string  // 用于微调的已有模型ID
}

export const createTrainJob = async (params: TrainJobRequest) => {
  const { data } = await api.post('/train/jobs', params)
  return data
}

export const listTrainJobs = async () => {
  const { data } = await api.get('/train/jobs')
  return data
}

export const getTrainJob = async (jobId: string) => {
  const { data } = await api.get(`/train/jobs/${jobId}`)
  return data
}

export const stopTrainJob = async (jobId: string) => {
  const { data } = await api.post(`/train/jobs/${jobId}/stop`)
  return data
}

export const resumeTrainJob = async (jobId: string) => {
  const { data } = await api.post(`/train/jobs/${jobId}/resume`)
  return data
}

export const deleteTrainJob = async (jobId: string) => {
  const { data } = await api.delete(`/train/jobs/${jobId}`)
  return data
}
