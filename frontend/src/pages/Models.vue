<template>
  <div class="models">
    <!-- 模型管理 -->
    <div class="card">
      <h2>模型管理</h2>
      
      <!-- 模型上传 -->
      <div class="upload-section">
        <h3>上传模型</h3>
        <div class="form-group">
          <label>选择 .zip 文件（格式与导出格式相同）</label>
          <input type="file" accept=".zip" @change="handleModelFileSelect" :disabled="uploadingModel" />
          <p class="form-hint">ZIP文件应包含 model.json 和 weights 目录</p>
        </div>
        <button @click="uploadModelFile" :disabled="!selectedModelFile || uploadingModel">
          <span v-if="uploadingModel" class="loading-spinner"></span>
          {{ uploadingModel ? '上传中...' : '上传模型' }}
        </button>
      </div>

      <div v-if="loadingModels" class="loading-state">
        <span class="loading-spinner large"></span>
        <span>加载模型列表...</span>
      </div>
      <div v-else-if="models.length > 0" class="models-list">
        <div v-for="model in models" :key="model.model_id" class="model-item">
          <div class="model-header">
            <h3>{{ model.model_id }}</h3>
            <div class="model-actions">
              <button @click="viewModelDetails(model)" class="secondary">详情</button>
              <button 
                @click="editModel(model)" 
                class="secondary"
                :disabled="editingModel === model.model_id"
              >
                <span v-if="editingModel === model.model_id" class="loading-spinner"></span>
                {{ editingModel === model.model_id ? '保存中...' : '编辑' }}
              </button>
              <button 
                @click="exportModelFile(model.model_id)" 
                class="secondary"
                :disabled="exportingModel === model.model_id"
              >
                <span v-if="exportingModel === model.model_id" class="loading-spinner"></span>
                {{ exportingModel === model.model_id ? '导出中...' : '导出' }}
              </button>
              <button 
                @click="deleteModelItem(model.model_id)" 
                class="danger"
                :disabled="deletingModel === model.model_id"
              >
                <span v-if="deletingModel === model.model_id" class="loading-spinner"></span>
                {{ deletingModel === model.model_id ? '删除中...' : '删除' }}
              </button>
            </div>
          </div>
          <p v-if="model.classes">类别数: {{ model.classes.length }}</p>
          <p v-if="model.base_model">基础模型: {{ model.base_model }}</p>
          <p v-if="model.created_at">创建时间: {{ model.created_at }}</p>
          <p v-if="model.description">描述: {{ model.description }}</p>
        </div>
      </div>
      <div v-else class="empty-state">
        暂无模型，请先训练模型
      </div>
      <button @click="loadModels" class="secondary" :disabled="loadingModels">
        <span v-if="loadingModels" class="loading-spinner"></span>
        {{ loadingModels ? '加载中...' : '刷新模型列表' }}
      </button>
    </div>

    <!-- 模型详情对话框 -->
    <div v-if="showModelDetails" class="modal-overlay" @click.self="closeModelDetails">
      <div class="modal-content modal-large">
        <div class="modal-header">
          <h3>模型详情: {{ detailModel?.model_id }}</h3>
          <button @click="closeModelDetails" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingDetails" class="loading-state">
            <span class="loading-spinner large"></span>
            <span>加载模型详情...</span>
          </div>
          <template v-else>
            <!-- 基本信息 -->
            <div class="detail-section">
              <h4>基本信息</h4>
              <table class="detail-table">
                <tr><td>模型ID</td><td>{{ detailModel?.model_id }}</td></tr>
                <tr><td>基础模型</td><td>{{ detailModel?.base_model || '-' }}</td></tr>
                <tr><td>创建时间</td><td>{{ detailModel?.created_at || '-' }}</td></tr>
                <tr><td>类别数量</td><td>{{ detailModel?.classes?.length || 0 }}</td></tr>
                <tr><td>图片尺寸</td><td>{{ detailModel?.imgsz || '-' }}</td></tr>
                <tr><td>训练轮数</td><td>{{ detailModel?.epochs || '-' }}</td></tr>
                <tr v-if="detailModel?.file_size_mb"><td>模型大小</td><td>{{ detailModel.file_size_mb }} MB</td></tr>
              </table>
            </div>
            
            <!-- 模型参数信息 -->
            <div v-if="detailModel?.model_info" class="detail-section">
              <h4>模型参数</h4>
              <table class="detail-table">
                <tr v-if="detailModel.model_info.total_params_m">
                  <td>参数数量</td>
                  <td>{{ detailModel.model_info.total_params_m }}M ({{ detailModel.model_info.total_params?.toLocaleString() }})</td>
                </tr>
                <tr v-if="detailModel.model_info.task">
                  <td>任务类型</td>
                  <td>{{ detailModel.model_info.task }}</td>
                </tr>
              </table>
            </div>
            
            <!-- 训练配置 -->
            <div v-if="detailModel?.training_metrics?.job_config" class="detail-section">
              <h4>训练配置</h4>
              <table class="detail-table">
                <tr><td>数据集</td><td>{{ detailModel.training_metrics.job_config.dataset_id || '-' }}</td></tr>
                <tr><td>训练轮数</td><td>{{ detailModel.training_metrics.job_config.epochs || '-' }}</td></tr>
                <tr><td>批次大小</td><td>{{ detailModel.training_metrics.job_config.batch || '-' }}</td></tr>
                <tr><td>训练状态</td><td>{{ detailModel.training_metrics.job_config.status || '-' }}</td></tr>
                <tr v-if="detailModel.training_metrics.job_config.completed_at">
                  <td>完成时间</td>
                  <td>{{ detailModel.training_metrics.job_config.completed_at }}</td>
                </tr>
              </table>
            </div>
            
            <!-- 下载训练图表 -->
            <div v-if="detailModel?.job_id" class="detail-section">
              <h4>下载训练图表</h4>
              <div class="chart-download-buttons">
                <button 
                  @click="downloadTrainingChart(detailModel.model_id, 'loss')" 
                  class="secondary"
                  :disabled="downloadingChart !== null"
                >
                  <span v-if="downloadingChart === 'loss'" class="loading-spinner"></span>
                  {{ downloadingChart === 'loss' ? '下载中...' : '下载损失曲线' }}
                </button>
                <button 
                  @click="downloadTrainingChart(detailModel.model_id, 'metrics')" 
                  class="secondary"
                  :disabled="downloadingChart !== null"
                >
                  <span v-if="downloadingChart === 'metrics'" class="loading-spinner"></span>
                  {{ downloadingChart === 'metrics' ? '下载中...' : '下载指标曲线' }}
                </button>
              </div>
            </div>
            
            <!-- 最终指标图表 -->
            <div v-if="finalMetricsOption" class="detail-section">
              <h4>最终训练指标</h4>
              <div class="chart-container">
                <v-chart :option="finalMetricsOption" autoresize />
              </div>
            </div>
            
            <!-- 训练损失曲线 -->
            <div v-if="lossChartOption" class="detail-section">
              <h4>训练损失曲线</h4>
              <div class="chart-container">
                <v-chart :option="lossChartOption" autoresize />
              </div>
            </div>
            
            <!-- mAP 曲线 -->
            <div v-if="mapChartOption" class="detail-section">
              <h4>训练指标曲线</h4>
              <div class="chart-container">
                <v-chart :option="mapChartOption" autoresize />
              </div>
            </div>
            
            <!-- 雷达图 - 多维指标对比 -->
            <div v-if="radarChartOption" class="detail-section">
              <h4>指标雷达图</h4>
              <div class="chart-container">
                <v-chart :option="radarChartOption" autoresize />
              </div>
            </div>
            
            <!-- 仪表盘图 - mAP分数 -->
            <div v-if="gaugeChartOption" class="detail-section">
              <h4>mAP50 评分仪表</h4>
              <div class="chart-container chart-gauge">
                <v-chart :option="gaugeChartOption" autoresize />
              </div>
            </div>
            
            <!-- 损失面积图 -->
            <div v-if="lossAreaOption" class="detail-section">
              <h4>训练损失面积图</h4>
              <div class="chart-container">
                <v-chart :option="lossAreaOption" autoresize />
              </div>
            </div>
            
            <!-- 损失散点图 -->
            <div v-if="lossScatterOption" class="detail-section">
              <h4>损失分布散点图</h4>
              <div class="chart-container">
                <v-chart :option="lossScatterOption" autoresize />
              </div>
            </div>
            
            <!-- 热力图 -->
            <div v-if="heatmapChartOption" class="detail-section">
              <h4>训练指标热力图</h4>
              <div class="chart-container chart-large">
                <v-chart :option="heatmapChartOption" autoresize />
              </div>
            </div>
            
            <!-- 类别列表 -->
            <div v-if="detailModel?.classes" class="detail-section">
              <h4>类别列表 ({{ detailModel.classes.length }})</h4>
              <div class="class-tags">
                <span v-for="(cls, idx) in detailModel.classes" :key="idx" class="class-tag">
                  {{ idx }}: {{ cls }}
                </span>
              </div>
            </div>
            
            <!-- 描述 -->
            <div v-if="detailModel?.description" class="detail-section">
              <h4>描述</h4>
              <p>{{ detailModel.description }}</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listModels, updateModel, deleteModel, getModel, uploadModel, exportModel, generateTrainingCharts, type ModelDetails } from '@/api/models'
import { downloadFile } from '@/utils/download'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, ScatterChart, RadarChart, HeatmapChart, GaugeChart } from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent, 
  TitleComponent,
  RadarComponent,
  VisualMapComponent,
  PolarComponent
} from 'echarts/components'

// 注册 ECharts 组件
use([
  CanvasRenderer, 
  LineChart, 
  BarChart, 
  ScatterChart, 
  RadarChart, 
  HeatmapChart,
  GaugeChart,
  GridComponent, 
  TooltipComponent, 
  LegendComponent, 
  TitleComponent,
  RadarComponent,
  VisualMapComponent,
  PolarComponent
])

const models = ref<any[]>([])

// 模型详情
const showModelDetails = ref(false)
const detailModel = ref<ModelDetails | null>(null)
const loadingDetails = ref(false)

// Loading 状态
const loadingModels = ref(false)
const editingModel = ref<string | null>(null)
const deletingModel = ref<string | null>(null)
const exportingModel = ref<string | null>(null)
const downloadingChart = ref<string | null>(null)

// 模型上传
const selectedModelFile = ref<File | null>(null)
const uploadingModel = ref(false)

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

const viewModelDetails = async (model: any) => {
  showModelDetails.value = true
  loadingDetails.value = true
  
  try {
    // 获取完整的模型详情（包含训练指标）
    const details = await getModel(model.model_id)
    detailModel.value = details
  } catch (error: any) {
    console.error('获取模型详情失败:', error)
    detailModel.value = model  // 降级使用基本信息
  } finally {
    loadingDetails.value = false
  }
}

const closeModelDetails = () => {
  showModelDetails.value = false
  detailModel.value = null
}

// 训练损失图表配置
const lossChartOption = computed(() => {
  const history = detailModel.value?.training_metrics?.training_history
  if (!history || !history.epochs) return null
  
  const series: any[] = []
  
  if (history.train_box_loss) {
    series.push({
      name: 'Train Box Loss',
      type: 'line',
      data: history.train_box_loss,
      smooth: true
    })
  }
  if (history.train_cls_loss) {
    series.push({
      name: 'Train Cls Loss',
      type: 'line',
      data: history.train_cls_loss,
      smooth: true
    })
  }
  if (history.val_box_loss) {
    series.push({
      name: 'Val Box Loss',
      type: 'line',
      data: history.val_box_loss,
      smooth: true,
      lineStyle: { type: 'dashed' }
    })
  }
  if (history.val_cls_loss) {
    series.push({
      name: 'Val Cls Loss',
      type: 'line',
      data: history.val_cls_loss,
      smooth: true,
      lineStyle: { type: 'dashed' }
    })
  }
  
  if (series.length === 0) return null
  
  return {
    title: { text: '训练损失曲线', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    xAxis: {
      type: 'category',
      data: history.epochs,
      name: 'Epoch'
    },
    yAxis: { type: 'value', name: 'Loss' },
    series
  }
})

// mAP 图表配置
const mapChartOption = computed(() => {
  const history = detailModel.value?.training_metrics?.training_history
  if (!history || !history.epochs) return null
  
  const series: any[] = []
  
  if (history.metrics_mAP50) {
    series.push({
      name: 'mAP50',
      type: 'line',
      data: history.metrics_mAP50,
      smooth: true
    })
  }
  if (history.metrics_mAP50_95) {
    series.push({
      name: 'mAP50-95',
      type: 'line',
      data: history.metrics_mAP50_95,
      smooth: true
    })
  }
  if (history.metrics_precision) {
    series.push({
      name: 'Precision',
      type: 'line',
      data: history.metrics_precision,
      smooth: true
    })
  }
  if (history.metrics_recall) {
    series.push({
      name: 'Recall',
      type: 'line',
      data: history.metrics_recall,
      smooth: true
    })
  }
  
  if (series.length === 0) return null
  
  return {
    title: { text: '训练指标曲线', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    xAxis: {
      type: 'category',
      data: history.epochs,
      name: 'Epoch'
    },
    yAxis: { type: 'value', name: 'Value', max: 1 },
    series
  }
})

// 最终指标柱状图
const finalMetricsOption = computed(() => {
  const metrics = detailModel.value?.training_metrics?.training_history?.final_metrics
  if (!metrics) return null
  
  const data = []
  const labels = []
  
  if (metrics.mAP50 !== null && metrics.mAP50 !== undefined) {
    labels.push('mAP50')
    data.push((metrics.mAP50 * 100).toFixed(1))
  }
  if (metrics.mAP50_95 !== null && metrics.mAP50_95 !== undefined) {
    labels.push('mAP50-95')
    data.push((metrics.mAP50_95 * 100).toFixed(1))
  }
  if (metrics.precision !== null && metrics.precision !== undefined) {
    labels.push('Precision')
    data.push((metrics.precision * 100).toFixed(1))
  }
  if (metrics.recall !== null && metrics.recall !== undefined) {
    labels.push('Recall')
    data.push((metrics.recall * 100).toFixed(1))
  }
  
  if (data.length === 0) return null
  
  return {
    title: { text: '最终训练指标 (%)', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', max: 100 },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: {
        color: function(params: any) {
          const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666']
          return colors[params.dataIndex % colors.length]
        }
      },
      label: {
        show: true,
        position: 'top',
        formatter: '{c}%'
      }
    }]
  }
})

// 损失散点图 - 显示训练和验证损失的分布
const lossScatterOption = computed(() => {
  const history = detailModel.value?.training_metrics?.training_history
  if (!history || !history.epochs) return null
  
  const trainData: number[][] = []
  const valData: number[][] = []
  
  if (history.train_box_loss && history.train_cls_loss) {
    history.epochs.forEach((epoch: number, idx: number) => {
      const boxLoss = history.train_box_loss![idx]
      const clsLoss = history.train_cls_loss![idx]
      if (boxLoss !== undefined && clsLoss !== undefined) {
        trainData.push([boxLoss, clsLoss, epoch])
      }
    })
  }
  
  if (history.val_box_loss && history.val_cls_loss) {
    history.epochs.forEach((epoch: number, idx: number) => {
      const boxLoss = history.val_box_loss![idx]
      const clsLoss = history.val_cls_loss![idx]
      if (boxLoss !== undefined && clsLoss !== undefined) {
        valData.push([boxLoss, clsLoss, epoch])
      }
    })
  }
  
  if (trainData.length === 0 && valData.length === 0) return null
  
  return {
    title: { text: '损失分布散点图', left: 'center' },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        return `${params.seriesName}<br/>Box Loss: ${params.data[0].toFixed(4)}<br/>Cls Loss: ${params.data[1].toFixed(4)}<br/>Epoch: ${params.data[2]}`
      }
    },
    legend: { bottom: 0 },
    xAxis: { type: 'value', name: 'Box Loss', scale: true },
    yAxis: { type: 'value', name: 'Cls Loss', scale: true },
    series: [
      {
        name: 'Train Loss',
        type: 'scatter',
        data: trainData,
        symbolSize: 10,
        itemStyle: { color: '#5470c6' }
      },
      {
        name: 'Val Loss',
        type: 'scatter',
        data: valData,
        symbolSize: 10,
        itemStyle: { color: '#ee6666' }
      }
    ]
  }
})

// 雷达图 - 多维指标对比
const radarChartOption = computed(() => {
  const metrics = detailModel.value?.training_metrics?.training_history?.final_metrics
  if (!metrics) return null
  
  const indicator = []
  const values = []
  
  if (metrics.mAP50 !== null && metrics.mAP50 !== undefined) {
    indicator.push({ name: 'mAP50', max: 1 })
    values.push(metrics.mAP50)
  }
  if (metrics.mAP50_95 !== null && metrics.mAP50_95 !== undefined) {
    indicator.push({ name: 'mAP50-95', max: 1 })
    values.push(metrics.mAP50_95)
  }
  if (metrics.precision !== null && metrics.precision !== undefined) {
    indicator.push({ name: 'Precision', max: 1 })
    values.push(metrics.precision)
  }
  if (metrics.recall !== null && metrics.recall !== undefined) {
    indicator.push({ name: 'Recall', max: 1 })
    values.push(metrics.recall)
  }
  
  if (indicator.length < 3) return null  // 雷达图至少需要3个维度
  
  return {
    title: { text: '指标雷达图', left: 'center' },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicator,
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#666'
      },
      splitLine: {
        lineStyle: { color: '#ddd' }
      },
      splitArea: {
        areaStyle: { color: ['rgba(114, 172, 209, 0.1)', 'rgba(114, 172, 209, 0.2)'] }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '模型性能',
        areaStyle: {
          color: 'rgba(84, 112, 198, 0.4)'
        },
        lineStyle: {
          color: '#5470c6',
          width: 2
        },
        itemStyle: {
          color: '#5470c6'
        }
      }]
    }]
  }
})

// 面积图 - 训练损失趋势（填充区域）
const lossAreaOption = computed(() => {
  const history = detailModel.value?.training_metrics?.training_history
  if (!history || !history.epochs) return null
  
  const series: any[] = []
  
  if (history.train_box_loss) {
    series.push({
      name: 'Train Box Loss',
      type: 'line',
      data: history.train_box_loss,
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(84, 112, 198, 0.5)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#5470c6' }
    })
  }
  if (history.train_cls_loss) {
    series.push({
      name: 'Train Cls Loss',
      type: 'line',
      data: history.train_cls_loss,
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(145, 204, 117, 0.5)' },
            { offset: 1, color: 'rgba(145, 204, 117, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#91cc75' }
    })
  }
  if (history.train_dfl_loss) {
    series.push({
      name: 'Train DFL Loss',
      type: 'line',
      data: history.train_dfl_loss,
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(250, 200, 88, 0.5)' },
            { offset: 1, color: 'rgba(250, 200, 88, 0.1)' }
          ]
        }
      },
      lineStyle: { color: '#fac858' }
    })
  }
  
  if (series.length === 0) return null
  
  return {
    title: { text: '训练损失面积图', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0 },
    xAxis: {
      type: 'category',
      data: history.epochs,
      name: 'Epoch',
      boundaryGap: false
    },
    yAxis: { type: 'value', name: 'Loss' },
    series
  }
})

// 仪表盘图 - 显示最终 mAP 分数
const gaugeChartOption = computed(() => {
  const metrics = detailModel.value?.training_metrics?.training_history?.final_metrics
  if (!metrics || metrics.mAP50 === null || metrics.mAP50 === undefined) return null
  
  const mAP50Value = (metrics.mAP50 * 100)
  
  return {
    title: { text: 'mAP50 评分仪表', left: 'center' },
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 10,
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#ee6666' },
            { offset: 0.5, color: '#fac858' },
            { offset: 1, color: '#91cc75' }
          ]
        }
      },
      progress: {
        show: true,
        width: 20
      },
      pointer: {
        show: true,
        length: '60%',
        width: 8
      },
      axisLine: {
        lineStyle: {
          width: 20,
          color: [[1, '#e0e0e0']]
        }
      },
      axisTick: {
        distance: -30,
        splitNumber: 5,
        lineStyle: { width: 2, color: '#999' }
      },
      splitLine: {
        distance: -35,
        length: 10,
        lineStyle: { width: 3, color: '#999' }
      },
      axisLabel: {
        distance: -20,
        color: '#666',
        fontSize: 12
      },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: '#333',
        fontSize: 24,
        offsetCenter: [0, '70%']
      },
      data: [{ value: parseFloat(mAP50Value.toFixed(1)), name: 'mAP50' }]
    }]
  }
})

// 热力图 - 显示各epoch各指标的表现（归一化）
const heatmapChartOption = computed(() => {
  const history = detailModel.value?.training_metrics?.training_history
  if (!history || !history.epochs) return null
  
  const metrics: string[] = []
  const data: number[][] = []
  
  // 收集所有指标数据
  const metricData: { [key: string]: number[] } = {}
  
  if (history.metrics_mAP50) {
    metricData['mAP50'] = history.metrics_mAP50
    metrics.push('mAP50')
  }
  if (history.metrics_mAP50_95) {
    metricData['mAP50-95'] = history.metrics_mAP50_95
    metrics.push('mAP50-95')
  }
  if (history.metrics_precision) {
    metricData['Precision'] = history.metrics_precision
    metrics.push('Precision')
  }
  if (history.metrics_recall) {
    metricData['Recall'] = history.metrics_recall
    metrics.push('Recall')
  }
  
  if (metrics.length === 0) return null
  
  // 构建热力图数据 [epochIdx, metricIdx, value]
  metrics.forEach((metric, metricIdx) => {
    const values = metricData[metric]
    values.forEach((value, epochIdx) => {
      data.push([epochIdx, metricIdx, value])
    })
  })
  
  return {
    title: { text: '训练指标热力图', left: 'center' },
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        return `Epoch ${history.epochs![params.data[0]]}<br/>${metrics[params.data[1]]}: ${(params.data[2] * 100).toFixed(1)}%`
      }
    },
    grid: {
      top: 60,
      bottom: 60,
      left: 80
    },
    xAxis: {
      type: 'category',
      data: history.epochs,
      name: 'Epoch',
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: metrics,
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      }
    },
    series: [{
      name: '指标值',
      type: 'heatmap',
      data: data,
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})

const editModel = async (model: any) => {
  const name = prompt('请输入模型名称（可选）:', model.name || model.model_id)
  if (name === null) return
  
  const description = prompt('请输入模型描述（可选）:', model.description || '')
  if (description === null) return
  
  const tagsInput = prompt('请输入标签（逗号分隔，可选）:', model.tags ? model.tags.join(',') : '')
  const tags = tagsInput ? tagsInput.split(',').map((t: string) => t.trim()).filter((t: string) => t) : undefined
  
  editingModel.value = model.model_id
  try {
    await updateModel(model.model_id, {
      name: name || undefined,
      description: description || undefined,
      tags: tags
    })
    alert('更新成功!')
    loadModels()
  } catch (error: any) {
    alert('更新失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    editingModel.value = null
  }
}

const deleteModelItem = async (modelId: string) => {
  if (!confirm(`确定要删除模型 ${modelId} 吗？此操作不可恢复！`)) return
  
  deletingModel.value = modelId
  try {
    await deleteModel(modelId)
    alert('删除成功!')
    loadModels()
  } catch (error: any) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deletingModel.value = null
  }
}

// 模型上传功能
const handleModelFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    selectedModelFile.value = target.files[0]
  }
}

const uploadModelFile = async () => {
  if (!selectedModelFile.value) return
  
  uploadingModel.value = true
  try {
    await uploadModel(selectedModelFile.value)
    alert('模型上传成功!')
    // 清空表单
    selectedModelFile.value = null
    // 重新加载模型列表
    loadModels()
  } catch (error: any) {
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    uploadingModel.value = false
  }
}

// 模型导出功能
const exportModelFile = async (modelId: string) => {
  exportingModel.value = modelId
  try {
    const blob = await exportModel(modelId)
    downloadFile(blob, `${modelId}.zip`)
  } catch (error: any) {
    alert('导出失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    exportingModel.value = null
  }
}

// 下载训练图表
const downloadTrainingChart = async (modelId: string, chartType: 'loss' | 'metrics') => {
  downloadingChart.value = chartType
  try {
    const blob = await generateTrainingCharts(modelId, chartType)
    downloadFile(blob, `${modelId}_${chartType}_chart.png`)
  } catch (error: any) {
    alert('下载图表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    downloadingChart.value = null
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

/* 模型列表样式 */
.models-list {
  margin: 1rem 0;
  display: grid;
  gap: 1rem;
}

.model-item {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.model-header h3 {
  margin: 0;
  color: #2c3e50;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
}

.model-actions button {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.model-item p {
  margin: 0.25rem 0;
  color: #7f8c8d;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #ddd;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #7f8c8d;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 1.5rem;
}

.detail-section h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.25rem;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table td {
  padding: 0.5rem;
  border-bottom: 1px solid #eee;
}

.detail-table td:first-child {
  color: #7f8c8d;
  width: 120px;
}

.class-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.class-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.modal-large {
  max-width: 900px;
  max-height: 90vh;
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

.chart-container {
  width: 100%;
  height: 300px;
  margin: 1rem 0;
}

.chart-container.chart-gauge {
  height: 250px;
}

.chart-container.chart-large {
  height: 400px;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
}

/* 模型上传部分 */
.upload-section {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border: 1px dashed #ddd;
}

.upload-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #2c3e50;
  font-size: 1rem;
}

.upload-section .form-group {
  margin-bottom: 0.75rem;
}

.upload-section .form-group:last-of-type {
  margin-bottom: 1rem;
}

.form-hint {
  font-size: 0.875rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

/* 图表下载按钮 */
.chart-download-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
</style>
