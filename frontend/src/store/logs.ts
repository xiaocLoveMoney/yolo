import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLogStore = defineStore('logs', () => {
  const logs = ref<string[]>([])
  const isStreaming = ref(false)
  const autoScroll = ref(true)
  
  const addLog = (line: string) => {
    logs.value.push(line)
  }
  
  const clearLogs = () => {
    logs.value = []
  }
  
  const setStreaming = (streaming: boolean) => {
    isStreaming.value = streaming
  }
  
  const toggleAutoScroll = () => {
    autoScroll.value = !autoScroll.value
  }
  
  return {
    logs,
    isStreaming,
    autoScroll,
    addLog,
    clearLogs,
    setStreaming,
    toggleAutoScroll
  }
})
