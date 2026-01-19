import axios from 'axios'

// 使用环境变量配置 API 基础路径
// 开发环境: /dev-api, 生产环境: /prod-api
const apiBaseURL = import.meta.env.VITE_API_BASE || '/dev-api'

const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 300000
})

export default api
