<template>
  <div class="log-panel">
    <LogToolbar 
      :is-streaming="isStreaming"
      :auto-scroll="autoScroll"
      :has-job-id="hasJobId"
      :log-info="logInfo"
      :loading-history="loadingHistory"
      @toggle-scroll="toggleScroll"
      @clear="clearLogs"
      @update-filter="updateFilter"
      @load-history="onLoadHistory"
      @lines-change="onLinesChange"
    />
    <div ref="logContainer" class="log-container">
      <div 
        v-for="(log, idx) in filteredLogs" 
        :key="idx" 
        class="log-line"
        v-html="parseAnsi(log)"
      ></div>
      <div v-if="filteredLogs.length === 0" class="log-empty">
        暂无日志
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useLogStore } from '@/store/logs'
import LogToolbar from './LogToolbar.vue'

defineProps<{
  hasJobId?: boolean
  logInfo?: string
  loadingHistory?: boolean
}>()

const emit = defineEmits<{
  'load-history': [lines: number]
  'lines-change': [lines: number]
}>()

const logStore = useLogStore()
const logContainer = ref<HTMLElement | null>(null)
const filter = ref('')

const isStreaming = computed(() => logStore.isStreaming)
const autoScroll = computed(() => logStore.autoScroll)

const filteredLogs = computed(() => {
  if (!filter.value) return logStore.logs
  return logStore.logs.filter(log => log.toLowerCase().includes(filter.value.toLowerCase()))
})

// ANSI 颜色映射
const ansiColors: Record<number, string> = {
  30: '#000000', // 黑色
  31: '#cd3131', // 红色
  32: '#0dbc79', // 绿色
  33: '#e5e510', // 黄色
  34: '#2472c8', // 蓝色
  35: '#bc3fbc', // 紫色
  36: '#11a8cd', // 青色
  37: '#e5e5e5', // 白色（浅灰，适配深色背景）
  90: '#666666', // 亮黑色
  91: '#f14c4c', // 亮红色
  92: '#23d18b', // 亮绿色
  93: '#f5f543', // 亮黄色
  94: '#3b8eea', // 亮蓝色
  95: '#d670d6', // 亮紫色
  96: '#29b8db', // 亮青色
  97: '#ffffff', // 亮白色
}

// 解析 ANSI 转义码并转换为 HTML
const parseAnsi = (text: string): string => {
  if (!text) return ''
  
  // 转义 HTML 特殊字符
  const escapeHtml = (str: string) => {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }
    return str.replace(/[&<>"']/g, (m) => map[m])
  }
  
  // ANSI 转义序列正则（匹配 \x1b[ 或 \033[ 开头的序列）
  const ansiRegex = /\x1B\[([0-9]{1,3}(;[0-9]{1,3})*)?[mK]/g
  
  const parts: Array<{ text: string; style: string }> = []
  let lastIndex = 0
  let currentStyle = ''
  
  // 获取当前样式字符串
  const getStyleString = (styles: string[]): string => {
    return styles.length > 0 ? styles.join('; ') : ''
  }
  
  let match
  while ((match = ansiRegex.exec(text)) !== null) {
    // 添加转义序列前的文本
    if (match.index > lastIndex) {
      const textBefore = text.substring(lastIndex, match.index)
      if (textBefore) {
        parts.push({ text: escapeHtml(textBefore), style: currentStyle })
      }
    }
    
    const fullCode = match[0]
    const codeStr = match[1] || ''
    
    // 处理重置码 [0m
    if (fullCode === '\x1B[0m' || fullCode === String.fromCharCode(27) + '[0m') {
      currentStyle = ''
    }
    // 处理清除到行尾 [K（忽略）
    else if (fullCode.endsWith('K')) {
      // 清除到行尾，不需要处理文本
    }
    // 处理样式码 [数字m
    else if (fullCode.endsWith('m')) {
      const codes = codeStr ? codeStr.split(';').map(Number) : [0]
      const styles: string[] = []
      
      for (const c of codes) {
        if (c === 0) {
          // 重置所有样式
          styles.length = 0
          currentStyle = ''
        } else if (c === 1) {
          // 粗体
          styles.push('font-weight: bold')
        } else if (c === 2) {
          // 弱化
          styles.push('opacity: 0.5')
        } else if (c === 3) {
          // 斜体
          styles.push('font-style: italic')
        } else if (c === 4) {
          // 下划线
          styles.push('text-decoration: underline')
        } else if (c === 22) {
          // 取消粗体和弱化
          styles.push('font-weight: normal')
          styles.push('opacity: 1')
        } else if (c === 23) {
          // 取消斜体
          styles.push('font-style: normal')
        } else if (c === 24) {
          // 取消下划线
          styles.push('text-decoration: none')
        } else if (c >= 30 && c <= 37) {
          // 前景色
          const color = ansiColors[c]
          if (color) styles.push(`color: ${color}`)
        } else if (c >= 90 && c <= 97) {
          // 亮前景色
          const color = ansiColors[c]
          if (color) styles.push(`color: ${color}`)
        } else if (c >= 40 && c <= 47) {
          // 背景色
          const bgColors: Record<number, string> = {
            40: '#000000',
            41: '#cd3131',
            42: '#0dbc79',
            43: '#e5e510',
            44: '#2472c8',
            45: '#bc3fbc',
            46: '#11a8cd',
            47: '#e5e5e5',
          }
          const bgColor = bgColors[c]
          if (bgColor) styles.push(`background-color: ${bgColor}`)
        } else if (c >= 100 && c <= 107) {
          // 亮背景色
          const bgColors: Record<number, string> = {
            100: '#666666',
            101: '#f14c4c',
            102: '#23d18b',
            103: '#f5f543',
            104: '#3b8eea',
            105: '#d670d6',
            106: '#29b8db',
            107: '#ffffff',
          }
          const bgColor = bgColors[c]
          if (bgColor) styles.push(`background-color: ${bgColor}`)
        }
      }
      
      // 更新当前样式（如果不是重置）
      if (codes[0] !== 0 && styles.length > 0) {
        currentStyle = getStyleString(styles)
      }
    }
    
    lastIndex = match.index + match[0].length
  }
  
  // 添加剩余的文本
  if (lastIndex < text.length) {
    const textAfter = text.substring(lastIndex)
    if (textAfter) {
      parts.push({ text: escapeHtml(textAfter), style: currentStyle })
    }
  }
  
  // 如果没有匹配到任何转义序列，直接返回转义后的文本
  if (parts.length === 0) {
    return escapeHtml(text)
  }
  
  // 组装 HTML
  return parts.map(part => {
    if (part.style) {
      return `<span style="${part.style}">${part.text}</span>`
    }
    return part.text
  }).join('')
}

const toggleScroll = () => {
  logStore.toggleAutoScroll()
}

const clearLogs = () => {
  logStore.clearLogs()
}

const updateFilter = (newFilter: string) => {
  filter.value = newFilter
}

const onLoadHistory = (lines: number) => {
  emit('load-history', lines)
}

const onLinesChange = (lines: number) => {
  emit('lines-change', lines)
}

watch(() => logStore.logs.length, async () => {
  if (autoScroll.value) {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
})
</script>

<style scoped>
.log-panel {
  background: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 500px;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #d4d4d4;
}

.log-line {
  margin-bottom: 0.25rem;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.4;
}

.log-empty {
  color: #888;
  text-align: center;
  padding: 2rem;
}

/* 确保 ANSI 样式正确应用 */
.log-line :deep(span) {
  white-space: pre-wrap;
}
</style>
