import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
// @ts-ignore - Node.js 类型在运行时可用
import path from 'path'
// @ts-ignore - Node.js 类型在运行时可用
import { fileURLToPath } from 'node:url'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, __dirname, '')
  
  // 获取 API 基础路径（默认 /dev-api）
  const apiBase = env.VITE_API_BASE || '/dev-api'
  
  // 后端 API 目标地址
  const apiTarget = env.VITE_API_TARGET || 'http://localhost:8000'
  
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    server: {
      port: 3000,
      proxy: {
        // 代理开发环境的 API 路径
        [apiBase]: {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(new RegExp(`^${apiBase}`), ''),
          // WebSocket 支持（用于日志流）
          ws: true,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err)
            })
          }
        },
        // 代理静态文件路径（图片等）
        '/static': {
          target: apiTarget,
          changeOrigin: true,
          // 不重写路径，直接转发 /static/... 到后端
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('static proxy error', err)
            })
          }
        }
      }
    }
  }
})
