<template>
  <div class="annotate">
    <div class="card">
      <h2>创建标注任务</h2>
      <div class="info-box">
        ⚠️ 请确保数据集已完成准备（prepare）操作，否则无法创建标注任务
      </div>
      <div class="form-group">
        <label>选择数据集</label>
        <div class="select-with-refresh">
          <select v-model="newTask.datasetId" :disabled="loadingDatasets || creatingTask">
            <option value="">-- 请选择数据集 --</option>
            <option 
              v-for="ds in datasets" 
              :key="ds.dataset_id" 
              :value="ds.dataset_id"
              :disabled="!isDatasetPrepared(ds)"
            >
              {{ ds.dataset_id }} ({{ getDatasetStatus(ds) }}) 
              {{ ds.image_count ? `- ${ds.image_count}张图片` : '' }}
            </option>
          </select>
          <button type="button" @click="loadDatasets" class="refresh-btn" :disabled="loadingDatasets">
            <span v-if="loadingDatasets" class="loading-spinner"></span>
            {{ loadingDatasets ? '加载中...' : '刷新' }}
          </button>
        </div>
        <small>提示：请选择数据集。如果数据集状态为"已上传"，需要先在数据集页面执行"准备"操作</small>
      </div>
      <div class="form-group">
        <label>类别（逗号分隔，可选）</label>
        <input v-model="classesInput" type="text" placeholder="留空则从 data.yaml 自动读取" :disabled="creatingTask" />
        <small>提示：如果数据集已有 data.yaml 配置，可留空自动读取类别</small>
      </div>
      <button @click="createTask" :disabled="creatingTask || !newTask.datasetId">
        <span v-if="creatingTask" class="loading-spinner"></span>
        {{ creatingTask ? '创建中...' : '创建任务' }}
      </button>
    </div>

    <div v-if="currentTask" class="annotate-workspace">
      <div class="sidebar">
        <h3>图片列表 ({{ items.length }})</h3>
        <div v-if="importedCount > 0" class="import-info">
          已导入 {{ importedCount }} 个标注
        </div>
        <div v-if="loadingItems" class="loading-state">
          <span class="loading-spinner"></span>
          <span>加载图片列表...</span>
        </div>
        <div v-else class="image-list">
          <div
            v-for="(item, idx) in items"
            :key="item.image_id"
            :class="['image-item', { active: currentIndex === idx, annotated: item.annotated }]"
            @click="selectImage(idx)"
          >
            {{ item.image_id }} {{ item.annotated ? '✓' : '' }}
          </div>
        </div>
        <div class="nav-buttons">
          <button @click="prevImage" :disabled="currentIndex === 0 || loadingAnnotation">上一张</button>
          <button @click="nextImage" :disabled="currentIndex === items.length - 1 || loadingAnnotation">下一张</button>
        </div>
      </div>

      <div class="canvas-area">
        <h3>
          {{ currentImage?.image_id }}
          <span v-if="loadingAnnotation" class="loading-indicator">
            <span class="loading-spinner"></span> 加载标注中...
          </span>
        </h3>
        <div class="canvas-container" @mousedown="startDrawing" @mousemove="drawing" @mouseup="endDrawing">
          <canvas ref="canvasRef"></canvas>
        </div>
        <div class="controls">
          <label>当前类别:</label>
          <select v-model="currentClass">
            <option v-for="(cls, idx) in classes" :key="idx" :value="idx">{{ cls }}</option>
          </select>
        </div>
      </div>

      <div class="annotations-panel">
        <h3>当前标注</h3>
        <div class="box-list">
          <div v-for="(box, idx) in currentBoxes" :key="idx" class="box-item">
            <span>{{ classes[box.class_id] }}</span>
            <button class="danger small" @click="removeBox(idx)">删除</button>
          </div>
        </div>
        <button @click="saveAnnotation" :disabled="savingAnnotation">
          <span v-if="savingAnnotation" class="loading-spinner"></span>
          {{ savingAnnotation ? '保存中...' : '保存' }}
        </button>
        <button class="secondary" @click="exportTask" :disabled="exporting">
          <span v-if="exporting" class="loading-spinner"></span>
          {{ exporting ? '导出中...' : '导出YOLO' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import type { BBox } from '@/api/annotations'
import { createAnnotationTask, getTaskItems, getImageAnnotation, saveAnnotation as saveAnn, exportAnnotations } from '@/api/annotations'
import { listDatasets } from '@/api/datasets'

const newTask = ref({ datasetId: '', version: 'v1' })
const datasets = ref<any[]>([])
const loadingDatasets = ref(false)
const creatingTask = ref(false)
const loadingItems = ref(false)
const savingAnnotation = ref(false)
const exporting = ref(false)

const loadDatasets = async () => {
  loadingDatasets.value = true
  try {
    const result = await listDatasets()
    datasets.value = result.datasets || []
  } catch (error: any) {
    console.error('加载数据集失败:', error)
    alert('加载数据集失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingDatasets.value = false
  }
}

// 获取数据集准备状态
const getDatasetStatus = (dataset: any) => {
  if (dataset.status === 'prepared') return '已准备'
  if (dataset.status === 'uploaded') return '已上传'
  return dataset.status || '未知'
}

// 检查数据集是否已准备（允许 prepared 和 uploaded 状态）
const isDatasetPrepared = (dataset: any) => {
  return dataset.status === 'prepared' || dataset.status === 'uploaded'
}
const classesInput = ref('')  // 默认为空，从数据集自动读取
const classes = ref<string[]>([])
const currentTask = ref<string | null>(null)
const items = ref<any[]>([])
const currentIndex = ref(0)
const currentImage = ref<any>(null)
const currentClass = ref(0)
const currentBoxes = ref<BBox[]>([])
const importedCount = ref(0)  // 导入的标注数量
const loadingAnnotation = ref(false)  // 加载标注状态

const canvasRef = ref<HTMLCanvasElement | null>(null)
const ctx = ref<CanvasRenderingContext2D | null>(null)
const img = ref<HTMLImageElement | null>(null)
const isDrawing = ref(false)
const startPos = ref({ x: 0, y: 0 })
const currentPos = ref({ x: 0, y: 0 })

const createTask = async () => {
  if (!newTask.value.datasetId) {
    alert('请选择数据集')
    return
  }
  
  // 检查数据集是否已准备
  const selectedDataset = datasets.value.find(ds => ds.dataset_id === newTask.value.datasetId)
  if (selectedDataset && selectedDataset.status === 'uploaded') {
    alert('数据集尚未准备（prepare）。请先在数据集上传页面执行"准备"操作后再创建标注任务。')
    return
  }
  
  // 如果用户输入了类别，使用用户输入的；否则传 undefined 让后端从 data.yaml 读取
  const inputClasses = classesInput.value.trim() 
    ? classesInput.value.split(',').map(c => c.trim()).filter(c => c)
    : undefined
  
  creatingTask.value = true
  try {
    const result = await createAnnotationTask(newTask.value.datasetId, newTask.value.version, inputClasses)
    currentTask.value = result.task_id
    
    // 使用返回的类别（可能是从 data.yaml 读取的）
    if (result.classes && result.classes.length > 0) {
      classes.value = result.classes
      classesInput.value = result.classes.join(', ')
    } else if (inputClasses) {
      classes.value = inputClasses
    }
    
    // 显示导入信息
    if (result.imported_annotations > 0) {
      importedCount.value = result.imported_annotations
      alert(`任务创建成功！\n共 ${result.total_images} 张图片\n已导入 ${result.imported_annotations} 个已有标注`)
    }
    
    await loadTaskItems()
  } catch (error: any) {
    alert('创建任务失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creatingTask.value = false
  }
}

const loadTaskItems = async () => {
  if (!currentTask.value) return
  
  loadingItems.value = true
  try {
    const result = await getTaskItems(currentTask.value)
    items.value = result.items
    
    // 更新类别（如果后端返回了）
    if (result.classes && result.classes.length > 0) {
      classes.value = result.classes
      if (!classesInput.value) {
        classesInput.value = result.classes.join(', ')
      }
    }
    
    // 记录导入的标注数量
    if (result.imported_annotations) {
      importedCount.value = result.imported_annotations
    }
    
    if (items.value.length > 0) {
      selectImage(0)
    }
  } catch (error: any) {
    alert('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingItems.value = false
  }
}

const selectImage = async (index: number) => {
  currentIndex.value = index
  currentImage.value = items.value[index]
  currentBoxes.value = []
  
  await nextTick()
  
  // 如果图片已有标注，先加载标注
  if (currentImage.value.annotated && currentTask.value) {
    await loadExistingAnnotation()
  }
  
  loadImageToCanvas()
}

// 加载已有标注
const loadExistingAnnotation = async () => {
  if (!currentTask.value || !currentImage.value) return
  
  loadingAnnotation.value = true
  try {
    const result = await getImageAnnotation(currentTask.value, currentImage.value.image_id)
    if (result && result.boxes && result.boxes.length > 0) {
      currentBoxes.value = result.boxes.map((box: any) => ({
        class_id: box.class_id,
        x1: box.x1,
        y1: box.y1,
        x2: box.x2,
        y2: box.y2
      }))
      console.log('Loaded existing annotations:', currentBoxes.value.length)
    }
  } catch (error: any) {
    console.error('加载标注失败:', error)
  } finally {
    loadingAnnotation.value = false
  }
}

const loadImageToCanvas = () => {
  if (!currentImage.value || !canvasRef.value) return
  
  const canvas = canvasRef.value
  ctx.value = canvas.getContext('2d')
  
  // 处理图片路径
  // 后端返回的路径应该是相对于 DATA_DIR 的（例如：datasets/ds_xxx/v1/images/xxx.jpg）
  // 静态文件服务挂载在 /static，目录是 backend/data
  // 所以需要：/static/datasets/...
  let imagePath = currentImage.value.image_path
  // 统一转换为正斜杠
  imagePath = imagePath.replace(/\\/g, '/')
  // 去掉可能的 backend/data/ 或 data/ 前缀（兼容旧格式）
  imagePath = imagePath.replace(/^(backend\/)?data\//, '')
  // 确保路径不以 / 开头（因为会加上 /static/ 前缀）
  imagePath = imagePath.replace(/^\//, '')
  // 静态文件路径不使用 API 基础路径，直接使用 /static/
  const imageUrl = '/static/' + imagePath
  
  console.log('Loading image:', {
    original: currentImage.value.image_path,
    processed: imageUrl
  })
  
  img.value = new Image()
  img.value.crossOrigin = 'anonymous'
  
  img.value.onload = () => {
    if (!img.value || !ctx.value) return
    canvas.width = img.value.width
    canvas.height = img.value.height
    ctx.value.drawImage(img.value, 0, 0)
    console.log('Image loaded:', img.value.width, 'x', img.value.height)
    
    // 绘制已有标注
    if (currentBoxes.value.length > 0) {
      redrawCanvas()
    }
  }
  
  img.value.onerror = (error) => {
    console.error('Image load error:', {
      url: imageUrl,
      originalPath: currentImage.value.image_path,
      error
    })
    // 显示更友好的错误提示
    const errorMsg = `图片加载失败\n路径: ${imageUrl}\n\n请检查：\n1. 后端服务是否运行\n2. 静态文件服务是否正常\n3. 图片文件是否存在`
    alert(errorMsg)
  }
  
  img.value.src = imageUrl
}

const startDrawing = (e: MouseEvent) => {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  startPos.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  isDrawing.value = true
}

const drawing = (e: MouseEvent) => {
  if (!isDrawing.value || !canvasRef.value || !ctx.value || !img.value) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  currentPos.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  
  // 重绘
  ctx.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  ctx.value.drawImage(img.value, 0, 0)
  
  // 绘制已有框
  currentBoxes.value.forEach(box => {
    drawBox(box.x1, box.y1, box.x2, box.y2, classes.value[box.class_id])
  })
  
  // 绘制当前框
  ctx.value.strokeStyle = 'red'
  ctx.value.lineWidth = 2
  ctx.value.strokeRect(
    startPos.value.x,
    startPos.value.y,
    currentPos.value.x - startPos.value.x,
    currentPos.value.y - startPos.value.y
  )
}

const endDrawing = () => {
  if (!isDrawing.value) return
  isDrawing.value = false
  
  const x1 = Math.min(startPos.value.x, currentPos.value.x)
  const y1 = Math.min(startPos.value.y, currentPos.value.y)
  const x2 = Math.max(startPos.value.x, currentPos.value.x)
  const y2 = Math.max(startPos.value.y, currentPos.value.y)
  
  if (x2 - x1 > 5 && y2 - y1 > 5) {
    currentBoxes.value.push({
      class_id: currentClass.value,
      x1, y1, x2, y2
    })
  }
  
  redrawCanvas()
}

const drawBox = (x1: number, y1: number, x2: number, y2: number, label: string) => {
  if (!ctx.value) return
  ctx.value.strokeStyle = 'lime'
  ctx.value.lineWidth = 2
  ctx.value.strokeRect(x1, y1, x2 - x1, y2 - y1)
  ctx.value.fillStyle = 'lime'
  ctx.value.font = '14px Arial'
  ctx.value.fillText(label, x1, y1 - 5)
}

const redrawCanvas = () => {
  if (!ctx.value || !canvasRef.value || !img.value) return
  ctx.value.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  ctx.value.drawImage(img.value, 0, 0)
  currentBoxes.value.forEach(box => {
    drawBox(box.x1, box.y1, box.x2, box.y2, classes.value[box.class_id])
  })
}

const removeBox = (index: number) => {
  currentBoxes.value.splice(index, 1)
  redrawCanvas()
}

const saveAnnotation = async () => {
  if (!currentTask.value || !currentImage.value) return
  
  savingAnnotation.value = true
  try {
    await saveAnn(currentTask.value, currentImage.value.image_id, currentBoxes.value)
    items.value[currentIndex.value].annotated = true
    alert('保存成功!')
  } catch (error: any) {
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    savingAnnotation.value = false
  }
}

const exportTask = async () => {
  if (!currentTask.value) return
  
  exporting.value = true
  try {
    const result = await exportAnnotations(currentTask.value)
    alert(`导出成功! 共导出 ${result.exported_count} 个标注`)
  } catch (error: any) {
    alert('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    exporting.value = false
  }
}

const prevImage = () => {
  if (currentIndex.value > 0) {
    selectImage(currentIndex.value - 1)
  }
}

const nextImage = () => {
  if (currentIndex.value < items.value.length - 1) {
    selectImage(currentIndex.value + 1)
  }
}

onMounted(() => {
  loadDatasets()
})
</script>

<style scoped>
.info-box {
  background: #fff3cd;
  border: 1px solid #ffc107;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  color: #856404;
}

.form-group small {
  display: block;
  margin-top: 0.25rem;
  color: #7f8c8d;
  font-size: 0.875rem;
}

.annotate-workspace {
  display: grid;
  grid-template-columns: 200px 1fr 250px;
  gap: 1rem;
  margin-top: 1rem;
}

.sidebar, .canvas-area, .annotations-panel {
  background: white;
  border-radius: 8px;
  padding: 1rem;
}

.image-list {
  max-height: 400px;
  overflow-y: auto;
  margin: 1rem 0;
}

.image-item {
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.image-item:hover {
  background: #ecf0f1;
}

.image-item.active {
  background: #3498db;
  color: white;
}

.image-item.annotated {
  border-left: 3px solid #2ecc71;
}

.nav-buttons {
  display: flex;
  gap: 0.5rem;
}

.nav-buttons button {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.canvas-container {
  border: 2px solid #ddd;
  overflow: auto;
  max-height: 600px;
  cursor: crosshair;
}

canvas {
  display: block;
}

.controls {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.controls select {
  flex: 1;
}

.box-list {
  margin: 1rem 0;
  max-height: 400px;
  overflow-y: auto;
}

.box-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.annotations-panel button {
  width: 100%;
  margin-bottom: 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

.select-with-refresh {
  display: flex;
  gap: 0.5rem;
}

.select-with-refresh select {
  flex: 1;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.import-info {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #7f8c8d;
}

.loading-indicator {
  font-size: 0.875rem;
  color: #7f8c8d;
  font-weight: normal;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

button.small {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}
</style>
