import api from './axios'

export interface UpdateModelRequest {
  name?: string
  description?: string
  tags?: string[]
}

export interface ModelDetails {
  model_id: string
  job_id?: string
  base_model?: string
  task?: string
  classes?: string[]
  imgsz?: number
  epochs?: number
  created_at?: string
  weights_path?: string
  name?: string
  description?: string
  tags?: string[]
  file_size?: number
  file_size_mb?: number
  training_metrics?: {
    training_history?: {
      epochs?: number[]
      train_box_loss?: number[]
      train_cls_loss?: number[]
      train_dfl_loss?: number[]
      val_box_loss?: number[]
      val_cls_loss?: number[]
      val_dfl_loss?: number[]
      metrics_precision?: number[]
      metrics_recall?: number[]
      metrics_mAP50?: number[]
      metrics_mAP50_95?: number[]
      final_metrics?: {
        mAP50?: number
        mAP50_95?: number
        precision?: number
        recall?: number
      }
    }
    job_config?: {
      dataset_id?: string
      epochs?: number
      imgsz?: number
      batch?: number
      model_name?: string
      status?: string
      created_at?: string
      completed_at?: string
    }
  }
  model_info?: {
    task?: string
    model_type?: string
    total_params?: number
    trainable_params?: number
    total_params_m?: number
  }
}

export const listModels = async () => {
  const { data } = await api.get('/models')
  return data
}

export const getModel = async (modelId: string): Promise<ModelDetails> => {
  const { data } = await api.get(`/models/${modelId}`)
  return data
}

export const updateModel = async (modelId: string, request: UpdateModelRequest) => {
  const { data } = await api.put(`/models/${modelId}`, request)
  return data
}

export const deleteModel = async (modelId: string) => {
  const { data } = await api.delete(`/models/${modelId}`)
  return data
}
