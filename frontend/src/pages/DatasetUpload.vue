<template>
  <div class="dataset-upload">
    <div class="card">
      <h2>上传数据集</h2>
      <div class="form-group">
        <label>选择 ZIP 文件</label>
        <input type="file" accept=".zip" @change="handleFileSelect" :disabled="uploading" />
      </div>
      <button @click="uploadFile" :disabled="!selectedFile || uploading">
        <span v-if="uploading" class="loading-spinner"></span>
        {{ uploading ? '上传中...' : '上传' }}
      </button>
      <div v-if="uploadResult" class="result">
        <p>✓ 上传成功: {{ uploadResult.dataset_id }}</p>
        <button @click="prepareDataset" :disabled="preparingNew">
          <span v-if="preparingNew" class="loading-spinner"></span>
          {{ preparingNew ? '准备中...' : '准备数据集' }}
        </button>
      </div>
    </div>

    <div class="card">
      <h2>数据集列表</h2>
      <button @click="loadDatasets" :disabled="loading" class="secondary">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? '加载中...' : '刷新' }}
      </button>
      <div v-if="loading" class="loading-state">
        <span class="loading-spinner large"></span>
        <span>加载数据集列表...</span>
      </div>
      <div v-else class="dataset-list">
        <div v-for="dataset in datasets" :key="dataset.dataset_id" class="dataset-item">
          <div class="dataset-header">
            <h3>{{ dataset.dataset_id }}</h3>
            <div class="dataset-actions">
              <button 
                v-if="dataset.status === 'uploaded'" 
                @click="prepareDatasetFromList(dataset.dataset_id)" 
                :disabled="preparingDataset === dataset.dataset_id"
              >
                <span v-if="preparingDataset === dataset.dataset_id" class="loading-spinner"></span>
                {{ preparingDataset === dataset.dataset_id ? '准备中...' : '准备' }}
              </button>
              <button 
                @click="editDataset(dataset)" 
                class="secondary"
                :disabled="editingDataset === dataset.dataset_id"
              >
                <span v-if="editingDataset === dataset.dataset_id" class="loading-spinner"></span>
                {{ editingDataset === dataset.dataset_id ? '保存中...' : '编辑' }}
              </button>
              <button 
                @click="deleteDatasetItem(dataset.dataset_id)" 
                class="danger"
                :disabled="deletingDataset === dataset.dataset_id"
              >
                <span v-if="deletingDataset === dataset.dataset_id" class="loading-spinner"></span>
                {{ deletingDataset === dataset.dataset_id ? '删除中...' : '删除' }}
              </button>
            </div>
          </div>
          <p>文件名: {{ dataset.filename }}</p>
          <p>大小: {{ (dataset.size / 1024 / 1024).toFixed(2) }} MB</p>
          <p>状态: <span :class="'status-badge status-' + dataset.status">{{ dataset.status }}</span></p>
          <p v-if="dataset.image_count">图片数: {{ dataset.image_count }}</p>
          <p v-if="dataset.label_count">标签数: {{ dataset.label_count }}</p>
          <p v-if="dataset.classes">类别: {{ dataset.classes.join(', ') }}</p>
          <p v-if="dataset.description">描述: {{ dataset.description }}</p>
          <p v-if="dataset.tags && dataset.tags.length">标签: {{ dataset.tags.join(', ') }}</p>
        </div>
        <div v-if="datasets.length === 0" class="empty-state">
          暂无数据集，请上传数据集
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { uploadDataset, prepareDataset as prepareDst, listDatasets, updateDataset, deleteDataset } from '@/api/datasets'

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadResult = ref<any>(null)
const datasets = ref<any[]>([])
const loading = ref(false)
const preparingDataset = ref<string | null>(null)  // 正在准备的数据集ID（列表中）
const preparingNew = ref(false)  // 正在准备新上传的数据集
const editingDataset = ref<string | null>(null)  // 正在编辑的数据集ID
const deletingDataset = ref<string | null>(null)  // 正在删除的数据集ID

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0]
    uploadResult.value = null
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  
  uploading.value = true
  try {
    const result = await uploadDataset(selectedFile.value)
    uploadResult.value = result
    alert('上传成功!')
    loadDatasets()
  } catch (error: any) {
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploading.value = false
  }
}

const prepareDataset = async () => {
  if (!uploadResult.value) return
  
  preparingNew.value = true
  try {
    await prepareDst(uploadResult.value.dataset_id)
    alert('准备成功!')
    uploadResult.value = null
    loadDatasets()
  } catch (error: any) {
    alert('准备失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    preparingNew.value = false
  }
}

const prepareDatasetFromList = async (datasetId: string) => {
  preparingDataset.value = datasetId
  try {
    await prepareDst(datasetId)
    alert('准备成功!')
    loadDatasets()
  } catch (error: any) {
    alert('准备失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    preparingDataset.value = null
  }
}

const loadDatasets = async () => {
  loading.value = true
  try {
    const result = await listDatasets()
    datasets.value = result.datasets
  } catch (error: any) {
    alert('加载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const editDataset = async (dataset: any) => {
  const description = prompt('请输入数据集描述（可选）:', dataset.description || '')
  if (description === null) return
  
  const tagsInput = prompt('请输入标签（逗号分隔，可选）:', dataset.tags ? dataset.tags.join(',') : '')
  const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(t => t) : undefined
  
  editingDataset.value = dataset.dataset_id
  try {
    await updateDataset(dataset.dataset_id, {
      description: description || undefined,
      tags: tags
    })
    alert('更新成功!')
    loadDatasets()
  } catch (error: any) {
    alert('更新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    editingDataset.value = null
  }
}

const deleteDatasetItem = async (datasetId: string) => {
  if (!confirm(`确定要删除数据集 ${datasetId} 吗？此操作不可恢复！`)) return
  
  deletingDataset.value = datasetId
  try {
    await deleteDataset(datasetId)
    alert('删除成功!')
    loadDatasets()
  } catch (error: any) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deletingDataset.value = null
  }
}

onMounted(() => {
  loadDatasets()
})
</script>

<style scoped>
.result {
  margin-top: 1rem;
  padding: 1rem;
  background: #d5f4e6;
  border-radius: 4px;
}

.dataset-list {
  margin-top: 1rem;
  display: grid;
  gap: 1rem;
}

.dataset-item {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.dataset-header h3 {
  margin: 0;
  color: #2c3e50;
}

.dataset-actions {
  display: flex;
  gap: 0.5rem;
}

.dataset-actions button {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.dataset-item p {
  margin: 0.25rem 0;
  color: #7f8c8d;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #7f8c8d;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 4px;
}

button {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}
</style>
