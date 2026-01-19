import api from './axios'

// 获取 API 基础路径
const getApiBase = () => import.meta.env.VITE_API_BASE || '/dev-api'

export const subscribeLogsSSE = (
  jobId: string,
  onLine: (line: string) => void,
  onError?: (error: any) => void
) => {
  // SSE 需要使用完整的 URL 路径（包含 API 基础路径）
  const apiBase = getApiBase()
  const eventSource = new EventSource(`${apiBase}/logs/stream?job_id=${jobId}`)
  
  eventSource.onmessage = (event) => {
    onLine(event.data)
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE error:', error)
    eventSource.close()
    if (onError) {
      onError(error)
    }
  }
  
  return eventSource
}

export const pollLogsTail = async (jobId: string, offset: number) => {
  const { data } = await api.get('/logs/tail', {
    params: { job_id: jobId, offset }
  })
  return data
}

export interface LogLinesResult {
  lines: string[]
  total: number
  returned: number
  error?: string
}

/**
 * 获取日志文件的最后N行
 * @param jobId 任务ID
 * @param n 要获取的行数，默认100，设为0表示获取所有日志
 */
export const getLogLines = async (jobId: string, n: number = 100): Promise<LogLinesResult> => {
  const { data } = await api.get('/logs/lines', {
    params: { job_id: jobId, n }
  })
  return data
}
