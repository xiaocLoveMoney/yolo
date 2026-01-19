import api from './axios'

export interface BBox {
  class_id: number
  x1: number
  y1: number
  x2: number
  y2: number
}

export const createAnnotationTask = async (datasetId: string, version: string, classes?: string[]) => {
  const { data } = await api.post('/annotations/tasks', {
    dataset_id: datasetId,
    version,
    classes: classes || null  // 如果不提供则从 data.yaml 读取
  })
  return data
}

export const getTaskItems = async (taskId: string) => {
  const { data } = await api.get(`/annotations/tasks/${taskId}/items`)
  return data
}

export const getImageAnnotation = async (taskId: string, imageId: string) => {
  const { data } = await api.get(`/annotations/tasks/${taskId}/items/${imageId}`)
  return data
}

export const saveAnnotation = async (taskId: string, imageId: string, boxes: BBox[]) => {
  const { data } = await api.post(`/annotations/tasks/${taskId}/items/${imageId}`, {
    boxes
  })
  return data
}

export const exportAnnotations = async (taskId: string) => {
  const { data } = await api.get(`/annotations/tasks/${taskId}/export?format=yolo`)
  return data
}
