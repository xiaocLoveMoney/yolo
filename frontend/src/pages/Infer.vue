<template>
  <div class="infer">
    <!-- 模型推理 -->
    <div class="card">
      <h2>模型推理</h2>
      
      <!-- 模型选择（多选） -->
      <div class="form-group">
        <label>选择模型（可多选）</label>
        <div class="model-checkboxes">
          <label v-for="model in models" :key="model.model_id" class="checkbox-item">
            <input 
              type="checkbox" 
              :value="model.model_id" 
              v-model="selectedModels"
              :disabled="inferring"
            />
            <span>{{ model.model_id }} ({{ model.classes?.length || 0 }} 类)</span>
          </label>
        </div>
        <div class="selection-actions">
          <button type="button" @click="selectAllModels" class="secondary small" :disabled="inferring">全选</button>
          <button type="button" @click="clearModelSelection" class="secondary small" :disabled="inferring">清空</button>
          <span class="selection-count">已选 {{ selectedModels.length }} 个模型</span>
        </div>
      </div>
      
      <!-- 图片上传（多选） -->
      <div class="form-group">
        <label>上传图片（可多选）</label>
        <input 
          type="file" 
          accept="image/*" 
          multiple 
          @change="handleImageSelect" 
          ref="fileInputRef"
          :disabled="inferring"
        />
        <div v-if="selectedImages.length > 0" class="selected-images">
          <div v-for="(img, idx) in selectedImages" :key="idx" class="selected-image-item">
            <img :src="imagePreviews[idx]" class="thumbnail" />
            <span>{{ img.name }}</span>
            <button type="button" @click="removeImage(idx)" class="danger small" :disabled="inferring">×</button>
          </div>
        </div>
      </div>
      
      <!-- 推理模式选择 -->
      <div class="form-group">
        <label class="checkbox-item">
          <input type="checkbox" v-model="saveInferenceResults" :disabled="inferring || selectedModels.length > 1" />
          <span>保存推理结果（仅单模型支持）</span>
        </label>
      </div>
      
      <button 
        @click="saveInferenceResults ? runInferenceAndSave() : runBatchInference()" 
        :disabled="selectedModels.length === 0 || selectedImages.length === 0 || inferring"
      >
        <span v-if="inferring" class="loading-spinner"></span>
        {{ inferring ? '推理中...' : `开始推理 (${selectedModels.length}模型 × ${selectedImages.length}图片)` }}
      </button>
    </div>

    <!-- 批量推理结果 -->
    <div v-if="batchResults" class="card">
      <h2>推理结果</h2>
      <p class="result-summary">
        共 {{ batchResults.total_models }} 个模型，{{ batchResults.total_images }} 张图片
      </p>
      
      <!-- 导出推理结果 -->
      <div v-if="inferenceSessionId" class="export-section">
        <p>会话ID: <strong>{{ inferenceSessionId }}</strong></p>
        <button @click="exportInferResults" class="secondary">
          导出推理结果（ZIP）
        </button>
      </div>
      
      <!-- 折叠面板展示每个模型的结果 -->
      <div class="accordion">
        <div 
          v-for="(modelResult, mIdx) in batchResults.results" 
          :key="modelResult.model_id"
          class="accordion-item"
        >
          <div 
            class="accordion-header" 
            @click="toggleAccordion(mIdx)"
            :class="{ active: expandedModels.includes(mIdx) }"
          >
            <span class="accordion-title">
              {{ modelResult.model_id }}
              <span v-if="modelResult.error" class="error-badge">错误</span>
              <span v-else class="detection-badge">
                {{ getTotalDetections(modelResult) }} 个检测
              </span>
            </span>
            <span class="accordion-icon">{{ expandedModels.includes(mIdx) ? '▼' : '▶' }}</span>
          </div>
          
          <div v-if="expandedModels.includes(mIdx)" class="accordion-content">
            <div v-if="modelResult.error" class="error-message">
              {{ modelResult.error }}
            </div>
            <div v-else class="images-grid">
              <div 
                v-for="(imgResult, iIdx) in modelResult.images" 
                :key="iIdx"
                class="image-result-card"
              >
                <h4>{{ imgResult.filename }}</h4>
                <div class="image-result-container">
                  <img 
                    :src="getImagePreview(imgResult.filename)" 
                    :ref="el => setImageRef(mIdx, iIdx, el)"
                    @load="drawDetectionsOnImage(mIdx, iIdx, imgResult)"
                  />
                  <canvas :ref="el => setCanvasRef(mIdx, iIdx, el)"></canvas>
                </div>
                <div class="detection-summary">
                  <span v-if="imgResult.error" class="error">{{ imgResult.error }}</span>
                  <span v-else>检测到 {{ imgResult.detections.length }} 个目标</span>
                </div>
                <div v-if="imgResult.detections.length > 0" class="detection-list">
                  <div 
                    v-for="(det, dIdx) in imgResult.detections" 
                    :key="dIdx"
                    class="detection-tag"
                  >
                    {{ det.class_name }} ({{ (det.conf * 100).toFixed(0) }}%)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { listModels } from '@/api/models'
import { batchInference, inferenceAndSave, exportInferenceResults, type BatchInferenceResult, type InferenceAndSaveResult } from '@/api/infer'
import { downloadFile } from '@/utils/download'

const models = ref<any[]>([])
const selectedModels = ref<string[]>([])
const selectedImages = ref<File[]>([])
const imagePreviews = ref<string[]>([])
const inferring = ref(false)
const batchResults = ref<BatchInferenceResult | null>(null)
const expandedModels = ref<number[]>([0])  // 默认展开第一个

const fileInputRef = ref<HTMLInputElement | null>(null)

// Loading 状态
const loadingModels = ref(false)

// 推理结果导出
const inferenceSessionId = ref<string | null>(null)
const saveInferenceResults = ref(false)

// 图片和画布引用
const imageRefs = ref<Map<string, HTMLImageElement>>(new Map())
const canvasRefs = ref<Map<string, HTMLCanvasElement>>(new Map())

const loadModels = async () => {
  loadingModels.value = true
  try {
    const data = await listModels()
    models.value = data.models
  } catch (error: any) {
    alert('加载模型失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingModels.value = false
  }
}

const selectAllModels = () => {
  selectedModels.value = models.value.map(m => m.model_id)
}

const clearModelSelection = () => {
  selectedModels.value = []
}

const handleImageSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const newFiles = Array.from(target.files)
    selectedImages.value = [...selectedImages.value, ...newFiles]
    
    // 生成预览
    newFiles.forEach(file => {
      imagePreviews.value.push(URL.createObjectURL(file))
    })
    
    // 清除结果
    batchResults.value = null
  }
}

const removeImage = (index: number) => {
  URL.revokeObjectURL(imagePreviews.value[index])
  selectedImages.value.splice(index, 1)
  imagePreviews.value.splice(index, 1)
}

const getImagePreview = (filename: string) => {
  const idx = selectedImages.value.findIndex(f => f.name === filename)
  return idx >= 0 ? imagePreviews.value[idx] : ''
}

const runBatchInference = async () => {
  if (selectedModels.value.length === 0 || selectedImages.value.length === 0) return
  
  inferring.value = true
  batchResults.value = null
  
  try {
    const result = await batchInference(selectedModels.value, selectedImages.value)
    batchResults.value = result
    expandedModels.value = [0]  // 展开第一个模型
    
    // 等待 DOM 更新后绘制检测框
    await nextTick()
  } catch (error: any) {
    alert('推理失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    inferring.value = false
  }
}

const toggleAccordion = (index: number) => {
  const idx = expandedModels.value.indexOf(index)
  if (idx >= 0) {
    expandedModels.value.splice(idx, 1)
  } else {
    expandedModels.value.push(index)
  }
}

const getTotalDetections = (modelResult: any) => {
  return modelResult.images.reduce((sum: number, img: any) => sum + (img.detections?.length || 0), 0)
}

const setImageRef = (mIdx: number, iIdx: number, el: any) => {
  if (el) {
    imageRefs.value.set(`${mIdx}-${iIdx}`, el)
  }
}

const setCanvasRef = (mIdx: number, iIdx: number, el: any) => {
  if (el) {
    canvasRefs.value.set(`${mIdx}-${iIdx}`, el)
  }
}

const drawDetectionsOnImage = (mIdx: number, iIdx: number, imgResult: any) => {
  const key = `${mIdx}-${iIdx}`
  const img = imageRefs.value.get(key)
  const canvas = canvasRefs.value.get(key)
  
  if (!img || !canvas || !imgResult.detections) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  canvas.width = img.width
  canvas.height = img.height
  
  const scaleX = img.width / imgResult.image_width
  const scaleY = img.height / imgResult.image_height
  
  // 颜色列表
  const colors = ['#00ff00', '#ff0000', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ffa500', '#800080']
  
  imgResult.detections.forEach((det: any, _idx: number) => {
    const color = colors[det.class_id % colors.length]
    const x1 = det.x1 * scaleX
    const y1 = det.y1 * scaleY
    const x2 = det.x2 * scaleX
    const y2 = det.y2 * scaleY
    
    // 绘制框
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
    
    // 绘制标签背景
    const label = `${det.class_name} ${(det.conf * 100).toFixed(0)}%`
    ctx.font = '12px Arial'
    const textWidth = ctx.measureText(label).width
    ctx.fillStyle = color
    ctx.fillRect(x1, y1 - 16, textWidth + 4, 16)
    
    // 绘制标签文字
    ctx.fillStyle = '#000'
    ctx.fillText(label, x1 + 2, y1 - 4)
  })
}

// 推理并保存结果
const runInferenceAndSave = async () => {
  if (selectedModels.value.length === 0 || selectedImages.value.length === 0) return
  
  inferring.value = true
  inferenceSessionId.value = null
  try {
    // 只取第一个模型进行保存
    const result: InferenceAndSaveResult = await inferenceAndSave(selectedModels.value[0], selectedImages.value)
    inferenceSessionId.value = result.session_id
    // 转换为BatchInferenceResult格式以便显示
    batchResults.value = {
      results: [{
        model_id: selectedModels.value[0],
        images: result.results.map(r => ({
          filename: r.image_filename,
          image_width: r.image_width,
          image_height: r.image_height,
          detections: r.detections,
          detection_count: r.detection_count
        }))
      }],
      total_models: 1,
      total_images: result.results.length
    }
    alert(`推理完成！会话ID: ${result.session_id}`)
  } catch (error: any) {
    alert('推理失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    inferring.value = false
  }
}

// 导出推理结果
const exportInferResults = async () => {
  if (!inferenceSessionId.value) {
    alert('没有可导出的推理结果')
    return
  }
  
  try {
    const blob = await exportInferenceResults(inferenceSessionId.value)
    downloadFile(blob, `${inferenceSessionId.value}_results.zip`)
  } catch (error: any) {
    alert('导出失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 4px;
  margin: 1rem 0;
}

.model-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.5rem;
  margin: 0.5rem 0;
  max-height: 200px;
  overflow-y: auto;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem;
  cursor: pointer;
}

.checkbox-item:hover {
  background: #f0f0f0;
  border-radius: 4px;
}

.selection-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.selection-count {
  color: #7f8c8d;
  font-size: 0.875rem;
}

.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.selected-images {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.selected-image-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  background: #f0f0f0;
  border-radius: 4px;
}

.thumbnail {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
}

.result-summary {
  color: #7f8c8d;
  margin-bottom: 1rem;
}

.accordion {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.accordion-item {
  border-bottom: 1px solid #ddd;
}

.accordion-item:last-child {
  border-bottom: none;
}

.accordion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  cursor: pointer;
  user-select: none;
}

.accordion-header:hover {
  background: #e9ecef;
}

.accordion-header.active {
  background: #e3f2fd;
}

.accordion-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.error-badge {
  background: #dc3545;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.detection-badge {
  background: #28a745;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.accordion-icon {
  color: #7f8c8d;
}

.accordion-content {
  padding: 1rem;
  background: white;
}

.error-message {
  color: #dc3545;
  padding: 1rem;
  background: #f8d7da;
  border-radius: 4px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.image-result-card {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
}

.image-result-card h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: #2c3e50;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-result-container {
  position: relative;
  border: 1px solid #eee;
  overflow: hidden;
}

.image-result-container img {
  display: block;
  width: 100%;
  height: auto;
}

.image-result-container canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.detection-summary {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #7f8c8d;
}

.detection-summary .error {
  color: #dc3545;
}

.detection-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.5rem;
}

.detection-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #7f8c8d;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

/* 导出部分 */
.export-section {
  background: #e8f5e9;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  border-left: 4px solid #4caf50;
}

.export-section p {
  margin: 0 0 0.5rem 0;
}

.export-section strong {
  color: #2e7d32;
  font-family: monospace;
}
</style>
