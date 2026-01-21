import api from './axios'

export const inference = async (modelId: string, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post(`/infer/${modelId}`, formData)
  return data
}

export interface BatchInferenceResult {
  results: {
    model_id: string
    model_name?: string
    classes?: string[]
    error?: string
    images: {
      filename: string
      image_width: number
      image_height: number
      detections: {
        class_id: number
        class_name: string
        conf: number
        x1: number
        y1: number
        x2: number
        y2: number
      }[]
      detection_count?: number
      error?: string
    }[]
  }[]
  total_models: number
  total_images: number
}

export const batchInference = async (modelIds: string[], files: File[]): Promise<BatchInferenceResult> => {
  const formData = new FormData()
  
  // 添加模型ID列表（逗号分隔）
  formData.append('model_ids', modelIds.join(','))
  
  // 添加所有文件
  files.forEach(file => {
    formData.append('files', file)
  })
  
  const { data } = await api.post('/infer/batch/run', formData)
  return data
}

// 视频推理相关接口
export interface VideoInferenceResult {
  model_id: string
  video_data: string  // base64编码的视频数据
  video_info: {
    fps: number
    width: number
    height: number
    total_frames: number
    processed_frames: number
  }
  summary: {
    total_detections: number
    frames_with_detections: number
  }
  error?: string
}

export interface VideoFrameData {
  type: 'info' | 'frame' | 'complete' | 'error'
  // info类型
  fps?: number
  width?: number
  height?: number
  total_frames?: number
  // frame类型
  frame_number?: number
  frame_data?: string  // base64编码的JPEG图片
  detections?: {
    class_id: number
    class_name: string
    conf: number
    bbox: [number, number, number, number]
  }[]
  // complete类型
  processed_frames?: number
  // error类型
  error?: string
}

/**
 * 视频推理：处理整个视频并返回结果
 */
export const videoInference = async (
  modelId: string, 
  file: File, 
  conf: number = 0.25
): Promise<VideoInferenceResult> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conf', conf.toString())
  
  const { data } = await api.post(`/infer/video/${modelId}`, formData, {
    timeout: 600000  // 10分钟超时，视频处理可能较慢
  })
  return data
}

/**
 * 视频推理流式接口：逐帧返回结果
 */
export const videoInferenceStream = (
  modelId: string,
  file: File,
  conf: number = 0.25,
  onFrame: (data: VideoFrameData) => void,
  onError?: (error: any) => void,
  onComplete?: () => void
): Promise<void> => {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('conf', conf.toString())
    
    // 使用fetch API进行流式请求
    fetch(`${import.meta.env.VITE_API_BASE || '/dev-api'}/infer/video/${modelId}/stream`, {
      method: 'POST',
      body: formData
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }
      
      const decoder = new TextDecoder()
      let buffer = ''
      
      const processStream = async () => {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            if (onComplete) onComplete()
            resolve()
            break
          }
          
          buffer += decoder.decode(value, { stream: true })
          
          // 处理SSE数据
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as VideoFrameData
                if (data.error) {
                  if (onError) onError(new Error(data.error))
                } else {
                  onFrame(data)
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e)
              }
            }
          }
        }
      }
      
      processStream().catch(error => {
        if (onError) onError(error)
        reject(error)
      })
    }).catch(error => {
      if (onError) onError(error)
      reject(error)
    })
  })
}

export interface InferenceAndSaveResult {
  session_id: string
  results: {
    image_uuid: string
    image_filename: string
    model_id: string
    image_width: number
    image_height: number
    detection_count: number
    detections: {
      class_id: number
      class_name: string
      conf: number
      x1: number
      y1: number
      x2: number
      y2: number
    }[]
  }[]
  session_dir: string | null
}

export const inferenceAndSave = async (modelId: string, files: File[]): Promise<InferenceAndSaveResult> => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  const { data } = await api.post(`/infer/${modelId}/export`, formData)
  return data
}

export const exportInferenceResults = async (sessionId: string): Promise<Blob> => {
  const response = await api.get(`/infer/results/${sessionId}/export`, {
    responseType: 'blob'
  })
  return response.data
}