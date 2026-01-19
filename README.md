# YOLO 训练平台

基于 YOLOv8 + FastAPI + Vue3 的目标检测模型训练平台 MVP。

## 功能特性

- ✅ 数据集上传与准备
- ✅ 可视化 BBox 标注 (Canvas)
- ✅ YOLOv8 模型训练（后台任务）
- ✅ 实时日志流 (SSE + 轮询兜底)
- ✅ 模型推理

## 项目结构

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
└── README.md
```

## 快速开始

### 后端启动

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

# 5. 启动服务（两种方式任选其一）

# 方式一：从项目根目录启动（推荐）
cd ..
python -m uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：从 backend 目录启动（使用启动脚本）
# Windows:
# python run.py
# 或直接双击 start.bat

# Linux/Mac:
# python run.py
# 或 chmod +x start.sh && ./start.sh
```

**注意**: RTX 5070 需要安装支持 CUDA 12.x 的 PyTorch。如果使用 CPU 训练，可以跳过 PyTorch 的 CUDA 安装，直接安装 `pip install torch torchvision`。

后端将运行在 http://localhost:8000

### 前端启动

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:3000

## API 测试

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

## 页面操作流程

### 1. 数据集上传 (`/datasets`)

1. 点击"选择 ZIP 文件"，选择包含图片的 zip 文件
2. 点击"上传"
3. 上传成功后点击"准备数据集"
4. 在列表中查看数据集状态

### 2. 数据标注 (`/annotate`)

1. 输入数据集 ID（如 `ds_20240115_123456`）
2. 输入类别（逗号分隔，如 `person,car,dog`）
3. 点击"创建任务"
4. 在画布上拖动鼠标绘制边界框
5. 右侧选择类别并查看当前标注
6. 点击"保存"保存当前图片标注
7. 使用"上一张/下一张"切换图片
8. 完成后点击"导出YOLO"生成 YOLO 格式标签

### 3. 模型训练 (`/train`)

1. 输入已准备好的数据集 ID
2. 选择模型（YOLOv8n/s/m）
3. 配置训练参数（轮数、图片尺寸、批次）
4. 点击"开始训练"
5. 自动显示实时训练日志
6. 训练完成后在任务列表查看模型 ID

### 4. 模型推理 (`/infer`)

1. 点击"刷新模型"加载已训练模型
2. 选择一个模型
3. 上传测试图片
4. 点击"开始推理"
5. 查看检测结果和可视化

## 技术栈

**后端:**
- FastAPI - Web 框架
- Ultralytics YOLOv8 - 目标检测
- Uvicorn - ASGI 服务器
- Pydantic - 数据验证

**前端:**
- Vue 3 - 前端框架
- Vite - 构建工具
- Vue Router - 路由
- Pinia - 状态管理
- Axios - HTTP 客户端

## 注意事项

1. **数据集格式**: 支持两种输入
   - YOLO 格式: `images/` 和 `labels/` 目录
   - 纯图片: 仅 `images/` 目录（需要后续标注）

2. **训练日志**: 优先使用 SSE 流，断线自动切换到轮询模式

3. **模型存储**: 训练完成的模型保存在 `backend/models/registry/`

4. **端口配置**: 
   - 后端: 8000
   - 前端: 3000

## 故障排查

### 训练任务不启动
- 检查数据集是否已准备 (status: "prepared")
- 确认 `data.yaml` 存在于数据集版本目录

### 日志不显示
- 检查浏览器控制台 SSE 连接状态
- 确认训练进程已启动并写入日志文件

### 推理失败
- 确认模型权重文件 `best.pt` 存在
- 检查上传图片格式是否支持

## License

MIT
