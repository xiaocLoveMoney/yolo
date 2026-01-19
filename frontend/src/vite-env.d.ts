/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
  readonly VITE_API_TARGET?: string
  // 更多环境变量...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
