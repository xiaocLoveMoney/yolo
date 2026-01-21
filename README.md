# 🚀 YOLO 训练平台 | YOLO Training Platform

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>

## 中文文档

### 简介

基于 YOLOv8 + FastAPI + Vue3 的目标检测模型训练平台。提供完整的数据集管理、可视化标注、模型训练和推理功能，支持 GPU 加速训练，开箱即用。

### 功能特性

- ✅ **数据集上传与准备** - 支持 ZIP 格式数据集上传，自动解压和组织
- ✅ **可视化 BBox 标注** - Canvas 画布交互式标注工具
- ✅ **YOLOv8 模型训练** - 后台异步训练任务，支持 GPU 加速
- ✅ **实时日志流** - SSE 实时日志推送，断线自动降级到轮询
- ✅ **模型推理** - 支持图片和视频推理，可视化检测结果
- ✅ **高性能训练** - 自动 Batch Size、混合精度训练、磁盘缓存优化
- ✅ **模型上传与导出** - 支持上传已有模型，导出训练后的模型为ZIP
- ✅ **数据集导出** - 支持导出标注前后的数据集（YOLO格式）
- ✅ **推理结果导出** - 推理结果自动生成UUID，支持CSV和图片导出
- ✅ **训练图表生成** - 使用matplotlib生成训练指标可视化图表

### 项目结构

```
yolo-platform/
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── api/routes/  # 路由层
│   │   ├── services/    # 业务逻辑层
│   │   ├── yolo/        # YOLO 封装
│   │   ├── core/        # 配置
│   │   └── main.py      # 入口
│   ├── data/            # 数据存储
│   ├── models/          # 模型注册表
│   └── requirements.txt
├── frontend/            # Vue3 前端
│   ├── src/
│   │   ├── pages/       # 页面
│   │   ├── components/  # 组件
│   │   ├── api/         # 接口封装
│   │   └── store/       # Pinia 状态
│   └── package.json
└── docker/              # Docker 配置
    ├── backend/
    ├── frontend/
    └── docker-compose.yml
```

---

## 🚀 快速开始

### 方式一：本地开发（推荐用于开发调试）

#### 1. 后端启动

```bash
# 1. 创建虚拟环境
conda create -n yoloapi python=3.10 -y
conda activate yoloapi

# 2. 安装 PyTorch (RTX 5070 需要 CUDA 12.1)
# 方式一：使用 pip（推荐）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 方式二：使用 conda
# conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia

# 3. 安装其他依赖
cd backend
pip install -r requirements.txt

# 4. 验证 CUDA（可选）
python -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# 5. 启动服务
cd ..
python -m uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

**注意**: RTX 5070 需要安装支持 CUDA 12.x 的 PyTorch。如果使用 CPU 训练，可以跳过 PyTorch 的 CUDA 安装，直接安装 `pip install torch torchvision`。

后端将运行在 http://localhost:8000

#### 2. 前端启动

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:3000

---

### 方式二：Docker 部署（推荐用于生产环境）

本项目提供了统一的 Docker 镜像，将前端页面（Nginx）与深度学习后端（Python/FastAPI）集成在同一个容器中。

#### 镜像拉取

**国内用户（推荐使用 CNB 镜像）：**

```bash
# 从 CNB 镜像仓库拉取（需要替换为实际的 CNB 镜像地址）
docker pull docker.cnb.cool/xiaoclab/vegetable/yolo:latest
```

**海外用户（使用 Docker Hub）：**

```bash
# 从 Docker Hub 拉取（需要替换为实际的 Docker Hub 用户名）
docker pull xiaoclovemoney/yolo-training-platform:latest
```

#### 启动方式

##### 方案 A：GPU 模式（训练推荐）🚀

如果您进行模型训练，强烈建议使用此命令以启用 GPU 加速。
*前提：宿主机需安装 NVIDIA 驱动及 NVIDIA Container Toolkit。*

```bash
docker run -d \
  --name yolo-platform \
  -p 3000:80 \
  -p 8000:8000 \
  --gpus all \
  --shm-size=24gb \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  docker.cnb.cool/xiaoclab/vegetable/yolo:latest
```

##### 方案 B：CPU 模式（仅推理/测试）

如果您没有 GPU，或者仅需浏览界面和进行简单的代码调试。

```bash
docker run -d \
  --name yolo-platform \
  -p 3000:80 \
  -p 8000:8000 \
  docker.cnb.cool/xiaoclab/vegetable/yolo:latest
```

#### 访问服务

- **Web 界面**: 浏览器访问 `http://localhost:3000`
- **API 文档**: 浏览器访问 `http://localhost:8000/docs`

#### Docker 参数说明

| 参数 | 说明 |
| --- | --- |
| `-p 3000:80` | 将宿主机的 3000 端口映射到容器的 Web 服务端口。 |
| `-p 8000:8000` | 将宿主机的 8000 端口映射到容器的 API 服务端口。 |
| `--gpus all` | 允许容器使用宿主机上的所有 GPU。 |
| `--shm-size=24gb` | **重要**：增加共享内存大小。YOLO/PyTorch 在处理多进程数据加载时需要较大的共享内存，否则可能报错。 |
| `-e NVIDIA_VISIBLE_DEVICES=all` | 显式指定容器可见的 GPU 设备。 |
| `-e NVIDIA_DRIVER_CAPABILITIES...` | 赋予容器调用宿主机 GPU 驱动计算能力的权限。 |

---

## 📖 使用指南

### 完整操作流程

#### 1️⃣ 上传数据集（必须第一步）

访问 http://localhost:3000/datasets

1. 点击"选择 ZIP 文件"，选择包含图片的 zip 文件
2. 点击"上传"
3. **重要**：上传成功后，点击"准备数据集"按钮
4. 等待准备完成，状态变为 `prepared`

**数据集 ZIP 文件要求：**

**方式一：YOLO 格式（推荐）**
```
dataset.zip
├── images/
│   ├── train/
│   │   ├── img1.jpg
│   │   └── img2.jpg
│   └── val/
│       └── img3.jpg
└── labels/
    ├── train/
    │   ├── img1.txt
    │   └── img2.txt
    └── val/
        └── img3.txt
```

**方式二：仅图片（需要标注）**
```
dataset.zip
├── img1.jpg
├── img2.jpg
└── img3.jpg
```

#### 2️⃣ 创建标注任务

访问 http://localhost:3000/annotate

1. 复制数据集页面中已准备好的数据集 ID（如 `ds_20260115_212121`）
2. 粘贴到"数据集ID"输入框
3. 输入类别（如 `person,car,dog`）
4. 点击"创建任务"
5. 在画布上拖动鼠标绘制边界框
6. 右侧选择类别并查看当前标注
7. 点击"保存"保存当前图片标注
8. 使用"上一张/下一张"切换图片
9. 完成后点击"导出YOLO"生成 YOLO 格式标签

**⚠️ 常见错误**：
- 如果提示 "数据集中未找到图片目录"，说明没有执行 prepare 操作
- 必须先在数据集页面完成 prepare，再来标注页面创建任务

#### 3️⃣ 模型训练

访问 http://localhost:3000/train

1. 输入已准备好的数据集 ID
2. 选择模型（建议首次测试用 YOLOv8n）
3. 设置参数（建议首次测试：epochs=2, batch=8）
4. 点击"开始训练"
5. 实时查看训练日志
6. 训练完成后在任务列表查看模型 ID

#### 4️⃣ 模型推理

访问 http://localhost:3000/infer

1. 点击"刷新模型"加载已训练模型
2. 选择一个模型
3. 上传测试图片
4. 点击"开始推理"
5. 查看检测结果和可视化

---

## ⚡ 训练性能优化

系统使用**高性能模式**，最大化 GPU 利用率，同时避免内存溢出。

### 核心优化

| 参数 | 设置 | 说明 |
|------|------|------|
| Batch Size | 自动 | 根据显存大小自动计算最佳值 |
| Workers | 8 | 平衡数据加载速度和内存使用 |
| Cache | disk | 磁盘缓存，加速数据加载，不占内存 |
| AMP | 启用 | 混合精度训练，节省显存，提升速度 |

### 自动 Batch Size

系统会根据 GPU 显存自动计算最佳 batch size：

| 显存 | 图片尺寸 416 | 图片尺寸 640 | 图片尺寸 1024 |
|------|-------------|-------------|---------------|
| 20GB+ (4090) | 64 | 32 | 16 |
| 10-20GB (5070/4080) | 48 | 24 | 12 |
| <10GB | 32 | 16 | 8 |

### GPU 利用率提升

- **优化前**：~70%
- **优化后**：~90-95%

详细优化说明请参考 [TRAINING_OPTIMIZATION.md](TRAINING_OPTIMIZATION.md)

---

## 🔧 API 测试

### 1. 上传数据集

```bash
curl -X POST http://localhost:8000/datasets/upload \
  -F "file=@your_dataset.zip"
```

返回:
```json
{
  "dataset_id": "ds_20240115_123456",
  "filename": "your_dataset.zip",
  "size": 12345678
}
```

### 2. 准备数据集

```bash
curl -X POST http://localhost:8000/datasets/ds_20240115_123456/prepare \
  -H "Content-Type: application/json" \
  -d '{"split_ratio": {"train": 0.8, "val": 0.2}, "classes": ["person", "car"]}'
```

### 3. 创建训练任务

```bash
curl -X POST http://localhost:8000/train/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ds_20240115_123456",
    "version": "v1",
    "model_name": "yolov8n.pt",
    "epochs": 10,
    "imgsz": 640,
    "batch": 16
  }'
```

返回:
```json
{
  "job_id": "job_20240115_123456",
  "status": "running"
}
```

### 4. 查看日志 (SSE)

```bash
curl -N http://localhost:8000/logs/stream?job_id=job_20240115_123456
```

### 5. 推理

```bash
curl -X POST http://localhost:8000/infer/model_20240115_123456 \
  -F "file=@test_image.jpg"
```

---

## 🛠️ 技术栈

**后端:**
- FastAPI - Web 框架
- Ultralytics YOLOv8 - 目标检测
- Uvicorn - ASGI 服务器
- Pydantic - 数据验证
- PyTorch - 深度学习框架

**前端:**
- Vue 3 - 前端框架
- Vite - 构建工具
- Vue Router - 路由
- Pinia - 状态管理
- Axios - HTTP 客户端
- TypeScript - 类型安全

**部署:**
- Docker - 容器化
- Nginx - Web 服务器
- Supervisor - 进程管理

---

## ⚠️ 注意事项

1. **数据集格式**: 支持两种输入
   - YOLO 格式: `images/` 和 `labels/` 目录
   - 纯图片: 仅 `images/` 目录（需要后续标注）

2. **训练日志**: 优先使用 SSE 流，断线自动切换到轮询模式

3. **模型存储**: 训练完成的模型保存在 `backend/models/registry/`

4. **端口配置**: 
   - 后端: 8000
   - 前端: 3000

5. **GPU 训练**: 需要 NVIDIA GPU 和 CUDA 支持，建议使用 GPU 模式进行训练

---

## 🔍 故障排查

### 训练任务不启动
- 检查数据集是否已准备 (status: "prepared")
- 确认 `data.yaml` 存在于数据集版本目录
- 检查 GPU 是否可用（如果使用 GPU 模式）

### 日志不显示
- 检查浏览器控制台 SSE 连接状态
- 确认训练进程已启动并写入日志文件
- 系统会自动降级到轮询模式

### 推理失败
- 确认模型权重文件 `best.pt` 存在
- 检查上传图片格式是否支持
- 确认模型已训练完成

### 创建标注任务失败
**错误信息**：`数据集 xxx 中未找到图片目录`

**解决方案**：
1. 回到数据集页面
2. 找到对应的数据集
3. 确认状态是 `prepared` 而不是 `uploaded`
4. 如果是 `uploaded`，点击该数据集的"准备数据集"按钮
5. 等待准备完成后再创建标注任务

### GPU 相关问题
- **CUDA out of memory**: 减小 batch size 或图片尺寸
- **GPU 利用率低**: 检查数据集大小，确保使用 disk 缓存
- **GPU 不可用**: 确认安装了 NVIDIA 驱动和 NVIDIA Container Toolkit

---

## 📚 相关文档

- [快速开始指南](QUICK_START.md) - 详细的快速开始教程
- [训练优化说明](TRAINING_OPTIMIZATION.md) - 训练性能优化详解

---

## 📄 License

MIT

---

<a name="english"></a>

## English Documentation

### Introduction

A YOLO training platform based on YOLOv8 + FastAPI + Vue3. Provides complete dataset management, visual annotation, model training, and inference capabilities, with GPU acceleration support, ready to use out of the box.

### Features

- ✅ **Dataset Upload & Preparation** - Support ZIP format dataset upload with automatic extraction and organization
- ✅ **Visual BBox Annotation** - Interactive Canvas annotation tool
- ✅ **YOLOv8 Model Training** - Background asynchronous training tasks with GPU acceleration
- ✅ **Real-time Log Streaming** - SSE real-time log push with automatic fallback to polling
- ✅ **Model Inference** - Support image and video inference with visualization
- ✅ **High-performance Training** - Auto Batch Size, mixed precision training, disk cache optimization
- ✅ **Model Upload & Export** - Upload existing models, export trained models as ZIP
- ✅ **Dataset Export** - Export datasets before/after annotation (YOLO format)
- ✅ **Inference Results Export** - Auto-generate UUID for inference results, support CSV and image export
- ✅ **Training Charts Generation** - Generate training metrics visualization charts using matplotlib

### Project Structure

```
yolo-platform/
├── backend/              # FastAPI Backend
│   ├── src/
│   │   ├── api/routes/  # Route layer
│   │   ├── services/    # Business logic layer
│   │   ├── yolo/        # YOLO wrapper
│   │   ├── core/        # Configuration
│   │   └── main.py      # Entry point
│   ├── data/            # Data storage
│   ├── models/          # Model registry
│   └── requirements.txt
├── frontend/            # Vue3 Frontend
│   ├── src/
│   │   ├── pages/       # Pages
│   │   ├── components/  # Components
│   │   ├── api/         # API wrapper
│   │   └── store/       # Pinia state
│   └── package.json
└── docker/              # Docker configuration
    ├── backend/
    ├── frontend/
    └── docker-compose.yml
```

---

## 🚀 Quick Start

### Option 1: Local Development (Recommended for Development)

#### 1. Backend Setup

```bash
# 1. Create virtual environment
conda create -n yoloapi python=3.10 -y
conda activate yoloapi

# 2. Install PyTorch (RTX 5070 requires CUDA 12.1)
# Option 1: Using pip (Recommended)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Option 2: Using conda
# conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia

# 3. Install other dependencies
cd backend
pip install -r requirements.txt

# 4. Verify CUDA (Optional)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# 5. Start service
cd ..
python -m uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: RTX 5070 requires PyTorch with CUDA 12.x support. For CPU training, skip CUDA installation and install `pip install torch torchvision` directly.

Backend will run at http://localhost:8000

#### 2. Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Start development server
npm run dev
```

Frontend will run at http://localhost:3000

---

### Option 2: Docker Deployment (Recommended for Production)

This project provides a unified Docker image that integrates the frontend (Nginx) and backend (Python/FastAPI) into a single container.

#### Pull Image

**For Chinese Users (Recommended: CNB Registry):**

```bash
# Pull from CNB registry (replace with actual CNB image address)
docker pull <cnb-registry>/<repo-name>/yolo:latest
```

**For Overseas Users (Docker Hub):**

```bash
# Pull from Docker Hub (replace with actual Docker Hub username)
docker pull xiaoclovemoney/yolo-training-platform:latest
```

#### Startup Methods

##### Option A: GPU Mode (Recommended for Training) 🚀

If you are training models, it is strongly recommended to use this command to enable GPU acceleration.
*Prerequisite: Host machine must have NVIDIA drivers and NVIDIA Container Toolkit installed.*

```bash
docker run -d \
  --name yolo-platform \
  -p 3000:80 \
  -p 8000:8000 \
  --gpus all \
  --shm-size=24gb \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  docker.cnb.cool/xiaoclab/vegetable/yolo:latest
```

##### Option B: CPU Mode (Inference/Testing Only)

If you don't have a GPU, or only need to browse the interface and perform simple debugging.

```bash
docker run -d \
  --name yolo-platform \
  -p 3000:80 \
  -p 8000:8000 \
  docker.cnb.cool/xiaoclab/vegetable/yolo:latest
```

#### Access Services

- **Web UI**: Open browser and visit `http://localhost:3000`
- **API Docs**: Visit `http://localhost:8000/docs`

#### Docker Parameter Explanation

| Flag | Description |
| --- | --- |
| `-p 3000:80` | Maps host port 3000 to container port 80 (Frontend UI). |
| `-p 8000:8000` | Maps host port 8000 to container port 8000 (Backend API). |
| `--gpus all` | Enables access to all available NVIDIA GPUs. |
| `--shm-size=24gb` | **Important**: Increases shared memory to prevent PyTorch `DataLoader` crashes. |
| `-e NVIDIA_VISIBLE_DEVICES=all` | Explicitly exposes all GPU devices to the container. |
| `-e NVIDIA_DRIVER_CAPABILITIES...` | Ensures the container can use compute and utility drivers. |

---

## 📖 User Guide

### Complete Workflow

#### 1️⃣ Upload Dataset (Required First Step)

Visit http://localhost:3000/datasets

1. Click "Select ZIP File" and choose a zip file containing images
2. Click "Upload"
3. **Important**: After upload succeeds, click "Prepare Dataset" button
4. Wait for preparation to complete, status changes to `prepared`

**Dataset ZIP File Requirements:**

**Option 1: YOLO Format (Recommended)**
```
dataset.zip
├── images/
│   ├── train/
│   │   ├── img1.jpg
│   │   └── img2.jpg
│   └── val/
│       └── img3.jpg
└── labels/
    ├── train/
    │   ├── img1.txt
    │   └── img2.txt
    └── val/
        └── img3.txt
```

**Option 2: Images Only (Requires Annotation)**
```
dataset.zip
├── img1.jpg
├── img2.jpg
└── img3.jpg
```

#### 2️⃣ Create Annotation Task

Visit http://localhost:3000/annotate

1. Copy the prepared dataset ID from the dataset page (e.g., `ds_20260115_212121`)
2. Paste into "Dataset ID" input field
3. Enter classes (e.g., `person,car,dog`)
4. Click "Create Task"
5. Draw bounding boxes on canvas by dragging mouse
6. Select class on the right and view current annotations
7. Click "Save" to save current image annotation
8. Use "Previous/Next" to switch images
9. After completion, click "Export YOLO" to generate YOLO format labels

**⚠️ Common Error**:
- If prompted "Image directory not found in dataset", it means prepare operation was not executed
- Must complete prepare on dataset page first, then create annotation task

#### 3️⃣ Model Training

Visit http://localhost:3000/train

1. Enter prepared dataset ID
2. Select model (recommend YOLOv8n for first test)
3. Set parameters (recommend for first test: epochs=2, batch=8)
4. Click "Start Training"
5. View real-time training logs
6. After training completes, check model ID in task list

#### 4️⃣ Model Inference

Visit http://localhost:3000/infer

1. Click "Refresh Models" to load trained models
2. Select a model
3. Upload test image
4. Click "Start Inference"
5. View detection results and visualization

---

## ⚡ Training Performance Optimization

The system uses **high-performance mode** to maximize GPU utilization while avoiding memory overflow.

### Core Optimizations

| Parameter | Setting | Description |
|------|------|------|
| Batch Size | Auto | Automatically calculates optimal value based on VRAM |
| Workers | 8 | Balances data loading speed and memory usage |
| Cache | disk | Disk cache, accelerates data loading without using memory |
| AMP | Enabled | Mixed precision training, saves VRAM, improves speed |

### Auto Batch Size

The system automatically calculates optimal batch size based on GPU VRAM:

| VRAM | Image Size 416 | Image Size 640 | Image Size 1024 |
|------|-------------|-------------|---------------|
| 20GB+ (4090) | 64 | 32 | 16 |
| 10-20GB (5070/4080) | 48 | 24 | 12 |
| <10GB | 32 | 16 | 8 |

### GPU Utilization Improvement

- **Before optimization**: ~70%
- **After optimization**: ~90-95%

For detailed optimization instructions, see [TRAINING_OPTIMIZATION.md](TRAINING_OPTIMIZATION.md)

---

## 🔧 API Testing

### 1. Upload Dataset

```bash
curl -X POST http://localhost:8000/datasets/upload \
  -F "file=@your_dataset.zip"
```

Response:
```json
{
  "dataset_id": "ds_20240115_123456",
  "filename": "your_dataset.zip",
  "size": 12345678
}
```

### 2. Prepare Dataset

```bash
curl -X POST http://localhost:8000/datasets/ds_20240115_123456/prepare \
  -H "Content-Type: application/json" \
  -d '{"split_ratio": {"train": 0.8, "val": 0.2}, "classes": ["person", "car"]}'
```

### 3. Create Training Job

```bash
curl -X POST http://localhost:8000/train/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ds_20240115_123456",
    "version": "v1",
    "model_name": "yolov8n.pt",
    "epochs": 10,
    "imgsz": 640,
    "batch": 16
  }'
```

Response:
```json
{
  "job_id": "job_20240115_123456",
  "status": "running"
}
```

### 4. View Logs (SSE)

```bash
curl -N http://localhost:8000/logs/stream?job_id=job_20240115_123456
```

### 5. Inference

```bash
curl -X POST http://localhost:8000/infer/model_20240115_123456 \
  -F "file=@test_image.jpg"
```

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Web framework
- Ultralytics YOLOv8 - Object detection
- Uvicorn - ASGI server
- Pydantic - Data validation
- PyTorch - Deep learning framework

**Frontend:**
- Vue 3 - Frontend framework
- Vite - Build tool
- Vue Router - Routing
- Pinia - State management
- Axios - HTTP client
- TypeScript - Type safety

**Deployment:**
- Docker - Containerization
- Nginx - Web server
- Supervisor - Process management

---

## ⚠️ Notes

1. **Dataset Format**: Supports two input types
   - YOLO format: `images/` and `labels/` directories
   - Images only: Only `images/` directory (requires subsequent annotation)

2. **Training Logs**: Prioritizes SSE streaming, automatically falls back to polling mode on disconnection

3. **Model Storage**: Trained models are saved in `backend/models/registry/`

4. **Port Configuration**: 
   - Backend: 8000
   - Frontend: 3000

5. **GPU Training**: Requires NVIDIA GPU and CUDA support, recommend using GPU mode for training

---

## 🔍 Troubleshooting

### Training Job Not Starting
- Check if dataset is prepared (status: "prepared")
- Confirm `data.yaml` exists in dataset version directory
- Check if GPU is available (if using GPU mode)

### Logs Not Displaying
- Check browser console SSE connection status
- Confirm training process has started and is writing log files
- System will automatically fallback to polling mode

### Inference Failed
- Confirm model weight file `best.pt` exists
- Check if uploaded image format is supported
- Confirm model training is complete

### Annotation Task Creation Failed
**Error**: `Image directory not found in dataset xxx`

**Solution**:
1. Return to dataset page
2. Find corresponding dataset
3. Confirm status is `prepared` not `uploaded`
4. If `uploaded`, click "Prepare Dataset" button for that dataset
5. Wait for preparation to complete before creating annotation task

### GPU Related Issues
- **CUDA out of memory**: Reduce batch size or image size
- **Low GPU utilization**: Check dataset size, ensure using disk cache
- **GPU not available**: Confirm NVIDIA drivers and NVIDIA Container Toolkit are installed

---

## 📚 Related Documentation

- [Quick Start Guide](QUICK_START.md) - Detailed quick start tutorial
- [Training Optimization Guide](TRAINING_OPTIMIZATION.md) - Training performance optimization details

---

## 📄 License

MIT
