<template>
  <div class="log-toolbar">
    <div class="toolbar-left">
      <span :class="['status-indicator', { active: isStreaming }]"></span>
      <span>{{ isStreaming ? '实时日志' : '日志已停止' }}</span>
    </div>
    <div class="toolbar-center">
      <select 
        v-model="selectedLines" 
        @change="onLinesChange"
        class="lines-select"
        :disabled="loadingHistory"
      >
        <option :value="100">最后 100 条</option>
        <option :value="200">最后 200 条</option>
        <option :value="500">最后 500 条</option>
        <option :value="800">最后 800 条</option>
        <option :value="1000">最后 1000 条</option>
        <option :value="0">所有日志</option>
      </select>
      <button 
        @click="loadHistory" 
        class="secondary"
        :disabled="loadingHistory || !hasJobId"
      >
        <span v-if="loadingHistory" class="loading-spinner small"></span>
        {{ loadingHistory ? '加载中...' : '加载历史日志' }}
      </button>
      <span v-if="logInfo" class="log-info">{{ logInfo }}</span>
    </div>
    <div class="toolbar-right">
      <input 
        type="text" 
        placeholder="过滤..." 
        @input="e => $emit('update-filter', (e.target as HTMLInputElement).value)"
        class="filter-input"
      />
      <button @click="$emit('toggle-scroll')" class="secondary">
        {{ autoScroll ? '暂停滚动' : '自动滚动' }}
      </button>
      <button @click="$emit('clear')" class="danger">清空</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  isStreaming: boolean
  autoScroll: boolean
  hasJobId?: boolean
  logInfo?: string
  loadingHistory?: boolean
}>()

const emit = defineEmits<{
  'toggle-scroll': []
  'clear': []
  'update-filter': [filter: string]
  'load-history': [lines: number]
  'lines-change': [lines: number]
}>()

const selectedLines = ref(100)

const onLinesChange = () => {
  emit('lines-change', selectedLines.value)
}

const loadHistory = () => {
  emit('load-history', selectedLines.value)
}
</script>

<style scoped>
.log-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #2d2d2d;
  border-bottom: 1px solid #444;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #d4d4d4;
}

.toolbar-center {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.lines-select {
  padding: 0.4rem 0.6rem;
  background: #1e1e1e;
  color: #d4d4d4;
  border: 1px solid #444;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
}

.lines-select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.log-info {
  color: #888;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
}

.status-indicator.active {
  background: #2ecc71;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.toolbar-right {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.filter-input {
  width: 150px;
  background: #1e1e1e;
  color: #d4d4d4;
  border: 1px solid #444;
}

.toolbar-right button,
.toolbar-center button {
  padding: 0.4rem 0.8rem;
  font-size: 0.875rem;
}

.loading-spinner.small {
  width: 12px;
  height: 12px;
  border-width: 2px;
  margin-right: 4px;
}
</style>
