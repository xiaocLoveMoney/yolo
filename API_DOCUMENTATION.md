# FastAPI 接口文档 | API Documentation

[English](#english) | [中文](#chinese)

---

<a name="chinese"></a>

## 中文文档

### 目录

- [基础信息](#基础信息)
- [数据集管理](#数据集管理)
- [标注管理](#标注管理)
- [训练管理](#训练管理)
- [日志管理](#日志管理)
- [推理服务](#推理服务)
- [模型管理](#模型管理)

---

## 基础信息

### 基础 URL

```
http://localhost:8000
```

### 响应格式

所有接口统一返回 JSON 格式数据。

### 错误码

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 数据集管理

### 1. 上传数据集

**接口描述**: 上传数据集 ZIP 文件到服务器

**请求方式**: `POST`

**接口地址**: `/datasets/upload`

**请求类型**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | ZIP 格式的数据集文件 |

**请求示例**:

```bash
curl -X POST http://localhost:8000/datasets/upload \
  -F "file=@your_dataset.zip"
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dataset_id | string | 数据集唯一标识符 |
| filename | string | 上传的文件名 |
| size | integer | 文件大小（字节） |
| created_at | string | 创建时间（ISO 8601 格式） |
| status | string | 数据集状态（uploaded/prepared） |

**响应示例**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "filename": "your_dataset.zip",
  "size": 12345678,
  "created_at": "2024-01-15T12:34:56",
  "status": "uploaded"
}
```

---

### 2. 准备数据集

**接口描述**: 解压数据集、校验格式、生成 YOLO 配置文件

**请求方式**: `POST`

**接口地址**: `/datasets/{dataset_id}/prepare`

**请求类型**: `application/json`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| split_ratio | object | 否 | {"train": 0.8, "val": 0.2} | 训练集和验证集划分比例 |
| classes | array[string] | 否 | null | 类别列表，如果不提供则从数据集中读取 |

**请求示例**:

```json
{
  "split_ratio": {
    "train": 0.8,
    "val": 0.2
  },
  "classes": ["person", "car", "dog"]
}
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dataset_id | string | 数据集 ID |
| version | string | 数据集版本（默认 v1） |
| status | string | 准备状态（prepared） |
| classes | array[string] | 类别列表 |
| train_count | integer | 训练集图片数量 |
| val_count | integer | 验证集图片数量 |
| data_yaml | string | data.yaml 文件路径 |

**响应示例**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "status": "prepared",
  "classes": ["person", "car", "dog"],
  "train_count": 800,
  "val_count": 200,
  "data_yaml": "/app/data/datasets/ds_20240115_123456/v1/data.yaml"
}
```

---

### 3. 列出所有数据集

**接口描述**: 获取所有数据集的列表

**请求方式**: `GET`

**接口地址**: `/datasets`

**请求类型**: 无

**请求参数**: 无

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| datasets | array[object] | 数据集列表 |

**数据集对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dataset_id | string | 数据集 ID |
| filename | string | 文件名 |
| size | integer | 文件大小 |
| status | string | 状态（uploaded/prepared） |
| created_at | string | 创建时间 |
| versions | array[string] | 版本列表 |

**响应示例**:

```json
{
  "datasets": [
    {
      "dataset_id": "ds_20240115_123456",
      "filename": "dataset.zip",
      "size": 12345678,
      "status": "prepared",
      "created_at": "2024-01-15T12:34:56",
      "versions": ["v1"]
    }
  ]
}
```

---

### 4. 获取数据集详情

**接口描述**: 获取指定数据集的详细信息

**请求方式**: `GET`

**接口地址**: `/datasets/{dataset_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**响应参数**: 同"列出所有数据集"的数据集对象结构，但包含更详细的信息

**响应示例**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "filename": "dataset.zip",
  "size": 12345678,
  "status": "prepared",
  "created_at": "2024-01-15T12:34:56",
  "versions": ["v1"],
  "description": "数据集描述",
  "tags": ["tag1", "tag2"]
}
```

---

### 5. 更新数据集信息

**接口描述**: 更新数据集的描述和标签信息

**请求方式**: `PUT`

**接口地址**: `/datasets/{dataset_id}`

**请求类型**: `application/json`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| description | string | 否 | 数据集描述 |
| tags | array[string] | 否 | 标签列表 |

**请求示例**:

```json
{
  "description": "这是一个目标检测数据集",
  "tags": ["person", "car", "detection"]
}
```

**响应参数**: 同"获取数据集详情"

---

### 6. 删除数据集

**接口描述**: 删除指定的数据集及其所有相关文件

**请求方式**: `DELETE`

**接口地址**: `/datasets/{dataset_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Dataset deleted successfully"
}
```

---

### 7. 导出标注后的数据集

**接口描述**: 导出包含标注的数据集（YOLO格式）

**请求方式**: `GET`

**接口地址**: `/datasets/{dataset_id}/export/annotated`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| version | string | 否 | "v1" | 数据集版本 |

**响应类型**: `application/zip`

**响应**: 返回ZIP文件流，包含：
- `images/` - 图片目录（train/val）
- `labels/` - 标签目录（YOLO格式）
- `data.yaml` - 数据集配置文件

**请求示例**:

```bash
curl -X GET http://localhost:8000/datasets/ds_20240115_123456/export/annotated \
  -o dataset_annotated.zip
```

---

### 8. 导出标注前的数据集

**接口描述**: 导出原始数据集（仅包含图片，不含标注）

**请求方式**: `GET`

**接口地址**: `/datasets/{dataset_id}/export/original`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dataset_id | string | 是 | 数据集 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| version | string | 否 | "v1" | 数据集版本 |

**响应类型**: `application/zip`

**响应**: 返回ZIP文件流，包含：
- `images/` - 图片目录
- `data.yaml` - 数据集配置文件（如果存在）

**请求示例**:

```bash
curl -X GET http://localhost:8000/datasets/ds_20240115_123456/export/original \
  -o dataset_original.zip
```

---

## 标注管理

### 1. 创建标注任务

**接口描述**: 为指定数据集创建标注任务

**请求方式**: `POST`

**接口地址**: `/annotations/tasks`

**请求类型**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dataset_id | string | 是 | - | 数据集 ID |
| version | string | 否 | "v1" | 数据集版本 |
| classes | array[string] | 否 | null | 类别列表，如果不提供则从 data.yaml 读取 |

**请求示例**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "classes": ["person", "car", "dog"]
}
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| task_id | string | 标注任务 ID |
| dataset_id | string | 数据集 ID |
| version | string | 数据集版本 |
| classes | array[string] | 类别列表 |
| total_items | integer | 图片总数 |
| annotated_count | integer | 已标注数量 |
| created_at | string | 创建时间 |

**响应示例**:

```json
{
  "task_id": "task_20240115_123456",
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "classes": ["person", "car", "dog"],
  "total_items": 1000,
  "annotated_count": 0,
  "created_at": "2024-01-15T12:34:56"
}
```

---

### 2. 获取标注任务图片列表

**接口描述**: 获取指定标注任务的所有图片列表

**请求方式**: `GET`

**接口地址**: `/annotations/tasks/{task_id}/items`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 标注任务 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| task_id | string | 标注任务 ID |
| items | array[object] | 图片列表 |

**图片对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| image_id | string | 图片 ID |
| image_path | string | 图片路径（相对路径，用于静态文件服务） |
| width | integer | 图片宽度 |
| height | integer | 图片高度 |
| has_annotation | boolean | 是否已有标注 |

**响应示例**:

```json
{
  "task_id": "task_20240115_123456",
  "items": [
    {
      "image_id": "img001",
      "image_path": "datasets/ds_20240115_123456/v1/images/train/img001.jpg",
      "width": 1920,
      "height": 1080,
      "has_annotation": false
    }
  ]
}
```

---

### 3. 保存图片标注

**接口描述**: 保存单张图片的标注信息

**请求方式**: `POST`

**接口地址**: `/annotations/tasks/{task_id}/items/{image_id}`

**请求类型**: `application/json`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 标注任务 ID |
| image_id | string | 是 | 图片 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| boxes | array[object] | 是 | 边界框列表 |

**边界框对象结构**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| class_id | integer | 是 | 类别 ID（从 0 开始） |
| x1 | float | 是 | 左上角 X 坐标（像素） |
| y1 | float | 是 | 左上角 Y 坐标（像素） |
| x2 | float | 是 | 右下角 X 坐标（像素） |
| y2 | float | 是 | 右下角 Y 坐标（像素） |

**请求示例**:

```json
{
  "boxes": [
    {
      "class_id": 0,
      "x1": 100.0,
      "y1": 200.0,
      "x2": 300.0,
      "y2": 400.0
    },
    {
      "class_id": 1,
      "x1": 500.0,
      "y1": 600.0,
      "x2": 700.0,
      "y2": 800.0
    }
  ]
}
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Annotation saved successfully"
}
```

---

### 4. 获取图片标注

**接口描述**: 获取指定图片的标注信息

**请求方式**: `GET`

**接口地址**: `/annotations/tasks/{task_id}/items/{image_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 标注任务 ID |
| image_id | string | 是 | 图片 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| image_id | string | 图片 ID |
| boxes | array[object] | 边界框列表（结构同保存标注） |
| updated_at | string | 更新时间 |

**响应示例**:

```json
{
  "image_id": "img001",
  "boxes": [
    {
      "class_id": 0,
      "x1": 100.0,
      "y1": 200.0,
      "x2": 300.0,
      "y2": 400.0
    }
  ],
  "updated_at": "2024-01-15T12:34:56"
}
```

---

### 5. 导出标注为 YOLO 格式

**接口描述**: 将标注任务的所有标注导出为 YOLO 格式标签文件

**请求方式**: `GET`

**接口地址**: `/annotations/tasks/{task_id}/export`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 标注任务 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| format | string | 否 | "yolo" | 导出格式（目前仅支持 yolo） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |
| labels_dir | string | 标签文件目录路径 |
| exported_count | integer | 导出的标签文件数量 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Annotations exported successfully",
  "labels_dir": "/app/data/datasets/ds_20240115_123456/v1/labels",
  "exported_count": 1000
}
```

---

## 训练管理

### 1. 创建训练任务

**接口描述**: 创建新的模型训练任务，支持基于已有模型进行微调

**请求方式**: `POST`

**接口地址**: `/train/jobs`

**请求类型**: `application/json`

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| dataset_id | string | 是 | - | 数据集 ID |
| version | string | 否 | "v1" | 数据集版本 |
| model_name | string | 否 | "yolov8n.pt" | 预训练模型名称（如 yolov8n.pt, yolov8s.pt）或已有模型 ID |
| epochs | integer | 否 | 10 | 训练轮数 |
| imgsz | integer | 否 | 640 | 图片尺寸 |
| batch | integer | 否 | -1 | 批次大小，-1 表示自动计算 |
| base_model_id | string | 否 | null | 用于微调的已有模型 ID |

**请求示例**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "model_name": "yolov8n.pt",
  "epochs": 50,
  "imgsz": 640,
  "batch": 16,
  "base_model_id": null
}
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| job_id | string | 训练任务 ID |
| status | string | 任务状态（running/completed/failed/stopped） |

**响应示例**:

```json
{
  "job_id": "job_20240115_123456",
  "status": "running"
}
```

---

### 2. 列出所有训练任务

**接口描述**: 获取所有训练任务的列表

**请求方式**: `GET`

**接口地址**: `/train/jobs`

**请求类型**: 无

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| jobs | array[object] | 训练任务列表 |

**训练任务对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| job_id | string | 任务 ID |
| dataset_id | string | 数据集 ID |
| version | string | 数据集版本 |
| model_name | string | 模型名称 |
| epochs | integer | 训练轮数 |
| imgsz | integer | 图片尺寸 |
| batch | integer | 批次大小 |
| status | string | 任务状态 |
| created_at | string | 创建时间 |
| model_id | string | 训练完成后生成的模型 ID（如果已完成） |

**响应示例**:

```json
{
  "jobs": [
    {
      "job_id": "job_20240115_123456",
      "dataset_id": "ds_20240115_123456",
      "version": "v1",
      "model_name": "yolov8n.pt",
      "epochs": 50,
      "imgsz": 640,
      "batch": 16,
      "status": "running",
      "created_at": "2024-01-15T12:34:56",
      "model_id": null
    }
  ]
}
```

---

### 3. 获取训练任务详情

**接口描述**: 获取指定训练任务的详细信息

**请求方式**: `GET`

**接口地址**: `/train/jobs/{job_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | string | 是 | 训练任务 ID |

**响应参数**: 同"列出所有训练任务"的训练任务对象结构，但包含更详细的信息

**响应示例**:

```json
{
  "job_id": "job_20240115_123456",
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "model_name": "yolov8n.pt",
  "base_model_id": null,
  "epochs": 50,
  "imgsz": 640,
  "batch": 16,
  "status": "completed",
  "created_at": "2024-01-15T12:34:56",
  "completed_at": "2024-01-15T14:30:00",
  "model_id": "model_20240115_143000",
  "log_file": "/app/data/jobs/job_20240115_123456.log"
}
```

---

### 4. 停止训练任务

**接口描述**: 停止正在运行的训练任务

**请求方式**: `POST`

**接口地址**: `/train/jobs/{job_id}/stop`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | string | 是 | 训练任务 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Training job stopped successfully"
}
```

---

### 5. 恢复训练任务

**接口描述**: 继续训练中断的任务（支持正常停止和崩溃恢复）

**请求方式**: `POST`

**接口地址**: `/train/jobs/{job_id}/resume`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | string | 是 | 训练任务 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |
| job_id | string | 任务 ID |
| status | string | 任务状态 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Training job resumed successfully",
  "job_id": "job_20240115_123456",
  "status": "running"
}
```

---

### 6. 删除训练任务

**接口描述**: 删除指定的训练任务及其相关文件

**请求方式**: `DELETE`

**接口地址**: `/train/jobs/{job_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | string | 是 | 训练任务 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Training job deleted successfully"
}
```

---

## 日志管理

### 1. SSE 流式日志

**接口描述**: 通过 Server-Sent Events (SSE) 实时推送训练日志

**请求方式**: `GET`

**接口地址**: `/logs/stream`

**请求类型**: 无

**查询参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| job_id | string | 是 | 训练任务 ID |

**响应类型**: `text/event-stream`

**响应格式**: SSE 格式，每行日志以 `data: ` 开头

**响应示例**:

```
data: [2024-01-15T12:34:56] Starting training...
data: [2024-01-15T12:34:57] Epoch 1/50
data: [2024-01-15T12:35:00] Loss: 0.5234
```

---

### 2. 轮询获取日志

**接口描述**: 通过轮询方式获取增量日志（用于 SSE 不可用时的降级方案）

**请求方式**: `GET`

**接口地址**: `/logs/tail`

**请求类型**: 无

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| job_id | string | 是 | - | 训练任务 ID |
| offset | integer | 否 | 0 | 日志文件读取偏移量（字节） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| offset | integer | 新的偏移量（用于下次请求） |
| lines | array[string] | 日志行列表（最多 50 行） |

**响应示例**:

```json
{
  "offset": 1024,
  "lines": [
    "[2024-01-15T12:34:56] Starting training...",
    "[2024-01-15T12:34:57] Epoch 1/50",
    "[2024-01-15T12:35:00] Loss: 0.5234"
  ]
}
```

---

### 3. 获取日志行

**接口描述**: 获取日志文件的最后 N 行

**请求方式**: `GET`

**接口地址**: `/logs/lines`

**请求类型**: 无

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| job_id | string | 是 | - | 训练任务 ID |
| n | integer | 否 | 100 | 要获取的行数，设为 0 表示获取所有日志 |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| lines | array[string] | 日志行列表 |
| total | integer | 日志文件总行数 |
| returned | integer | 本次返回的行数 |

**响应示例**:

```json
{
  "lines": [
    "[2024-01-15T12:34:56] Starting training...",
    "[2024-01-15T12:34:57] Epoch 1/50"
  ],
  "total": 1000,
  "returned": 2
}
```

---

## 推理服务

### 1. 图片推理

**接口描述**: 使用指定模型对图片进行目标检测推理

**请求方式**: `POST`

**接口地址**: `/infer/{model_id}`

**请求类型**: `multipart/form-data`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 图片文件（支持 jpg, png, jpeg） |

**请求示例**:

```bash
curl -X POST http://localhost:8000/infer/model_20240115_123456 \
  -F "file=@test_image.jpg"
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| model_id | string | 模型 ID |
| image_path | string | 图片路径（相对路径） |
| detections | array[object] | 检测结果列表 |

**检测结果对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| class_id | integer | 类别 ID |
| class_name | string | 类别名称 |
| confidence | float | 置信度（0-1） |
| bbox | object | 边界框坐标 |

**边界框对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| x1 | float | 左上角 X 坐标 |
| y1 | float | 左上角 Y 坐标 |
| x2 | float | 右下角 X 坐标 |
| y2 | float | 右下角 Y 坐标 |

**响应示例**:

```json
{
  "model_id": "model_20240115_123456",
  "image_path": "uploads/infer_20240115_123456.jpg",
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.95,
      "bbox": {
        "x1": 100.0,
        "y1": 200.0,
        "x2": 300.0,
        "y2": 400.0
      }
    }
  ]
}
```

---

### 2. 批量推理

**接口描述**: 使用多个模型对多张图片进行批量推理

**请求方式**: `POST`

**接口地址**: `/infer/batch/run`

**请求类型**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_ids | string | 是 | 逗号分隔的模型 ID 列表，如 "model_1,model_2" |
| files | array[File] | 是 | 多个图片文件 |

**请求示例**:

```bash
curl -X POST http://localhost:8000/infer/batch/run \
  -F "model_ids=model_1,model_2" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| results | array[object] | 推理结果列表 |

**推理结果对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| model_id | string | 模型 ID |
| image_path | string | 图片路径 |
| detections | array[object] | 检测结果列表（结构同图片推理） |

**响应示例**:

```json
{
  "results": [
    {
      "model_id": "model_1",
      "image_path": "uploads/infer_20240115_123456_1.jpg",
      "detections": [...]
    },
    {
      "model_id": "model_2",
      "image_path": "uploads/infer_20240115_123456_2.jpg",
      "detections": [...]
    }
  ]
}
```

---

### 3. 视频推理

**接口描述**: 对视频文件进行推理，返回带标注的视频

**请求方式**: `POST`

**接口地址**: `/infer/video/{model_id}`

**请求类型**: `multipart/form-data`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | File | 是 | - | 视频文件 |
| conf | float | 否 | 0.25 | 置信度阈值（0-1） |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| model_id | string | 模型 ID |
| video_data | string | 处理后的视频数据（base64 编码） |
| stats | object | 检测统计信息 |

**统计信息对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| total_frames | integer | 总帧数 |
| detections_per_frame | array[integer] | 每帧检测到的目标数量 |

**响应示例**:

```json
{
  "model_id": "model_20240115_123456",
  "video_data": "base64_encoded_video_data...",
  "stats": {
    "total_frames": 300,
    "detections_per_frame": [2, 3, 1, ...]
  }
}
```

---

### 4. 视频推理流式接口

**接口描述**: 视频推理的流式版本，逐帧返回检测结果

**请求方式**: `POST`

**接口地址**: `/infer/video/{model_id}/stream`

**请求类型**: `multipart/form-data`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| file | File | 是 | - | 视频文件 |
| conf | float | 否 | 0.25 | 置信度阈值（0-1） |

**响应类型**: `text/event-stream`

**响应格式**: SSE 格式，每帧返回 JSON 数据

**响应示例**:

```
data: {"frame": 0, "image_data": "base64_encoded_jpeg...", "detections": [...]}
data: {"frame": 1, "image_data": "base64_encoded_jpeg...", "detections": [...]}
```

---

### 5. 推理并保存结果

**接口描述**: 执行推理并保存结果图片，生成UUID和CSV文件

**请求方式**: `POST`

**接口地址**: `/infer/{model_id}/export`

**请求类型**: `multipart/form-data`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | array[File] | 是 | 多个图片文件 |

**请求示例**:

```bash
curl -X POST http://localhost:8000/infer/model_20240115_123456/export \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| session_id | string | 推理会话ID |
| results | array[object] | 推理结果列表 |
| session_dir | string | 结果保存目录 |

**结果对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| image_uuid | string | 图片唯一标识符（UUID） |
| image_filename | string | 原始文件名 |
| model_id | string | 模型ID |
| image_width | integer | 图片宽度 |
| image_height | integer | 图片高度 |
| detection_count | integer | 检测数量 |
| detections | array[object] | 检测结果列表 |

**响应示例**:

```json
{
  "session_id": "session_20240115_123456_a1b2c3d4",
  "results": [
    {
      "image_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "image_filename": "image1.jpg",
      "model_id": "model_20240115_123456",
      "image_width": 1920,
      "image_height": 1080,
      "detection_count": 2,
      "detections": [
        {
          "class_id": 0,
          "class_name": "person",
          "conf": 0.95,
          "x1": 100.0,
          "y1": 200.0,
          "x2": 300.0,
          "y2": 400.0
        }
      ]
    }
  ],
  "session_dir": "/app/data/inference_results/session_20240115_123456_a1b2c3d4"
}
```

---

### 6. 导出推理结果

**接口描述**: 导出推理结果为ZIP文件，包含标注图片和CSV

**请求方式**: `GET`

**接口地址**: `/infer/results/{session_id}/export`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| session_id | string | 是 | 推理会话ID |

**响应类型**: `application/zip`

**响应**: 返回ZIP文件流，包含：
- `images/{uuid}.jpg` - 带标注的结果图片
- `results.csv` - CSV格式的检测结果
- `metadata.json` - 会话元数据

**CSV文件格式**:

| 列名 | 说明 |
|------|------|
| image_uuid | 图片UUID |
| image_filename | 原始文件名 |
| model_id | 模型ID |
| image_width | 图片宽度 |
| image_height | 图片高度 |
| detection_count | 检测数量 |
| detection_index | 检测索引 |
| class_id | 类别ID |
| class_name | 类别名称 |
| confidence | 置信度 |
| x1, y1, x2, y2 | 边界框坐标 |

**请求示例**:

```bash
curl -X GET http://localhost:8000/infer/results/session_20240115_123456_a1b2c3d4/export \
  -o inference_results.zip
```

---

## 模型管理

### 1. 列出所有模型

**接口描述**: 获取所有已训练模型的列表

**请求方式**: `GET`

**接口地址**: `/models`

**请求类型**: 无

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| models | array[object] | 模型列表 |

**模型对象结构**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| model_id | string | 模型 ID |
| name | string | 模型名称 |
| description | string | 模型描述 |
| weights_path | string | 权重文件路径 |
| file_size | integer | 文件大小（字节） |
| file_size_mb | float | 文件大小（MB） |
| created_at | string | 创建时间 |
| job_id | string | 训练任务 ID |
| dataset_id | string | 数据集 ID |
| tags | array[string] | 标签列表 |

**响应示例**:

```json
{
  "models": [
    {
      "model_id": "model_20240115_123456",
      "name": "yolov8n_custom",
      "description": "Custom trained model",
      "weights_path": "/app/models/registry/model_20240115_123456/weights/best.pt",
      "file_size": 12345678,
      "file_size_mb": 11.78,
      "created_at": "2024-01-15T12:34:56",
      "job_id": "job_20240115_123456",
      "dataset_id": "ds_20240115_123456",
      "tags": ["person", "car"]
    }
  ]
}
```

---

### 2. 获取模型详情

**接口描述**: 获取指定模型的详细信息，包括训练指标

**请求方式**: `GET`

**接口地址**: `/models/{model_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**响应参数**: 同"列出所有模型"的模型对象结构，但包含更详细的信息，如训练指标

**响应示例**:

```json
{
  "model_id": "model_20240115_123456",
  "name": "yolov8n_custom",
  "description": "Custom trained model",
  "weights_path": "/app/models/registry/model_20240115_123456/weights/best.pt",
  "file_size": 12345678,
  "file_size_mb": 11.78,
  "created_at": "2024-01-15T12:34:56",
  "job_id": "job_20240115_123456",
  "dataset_id": "ds_20240115_123456",
  "tags": ["person", "car"],
  "training_metrics": {
    "mAP50": 0.85,
    "mAP50-95": 0.72,
    "precision": 0.88,
    "recall": 0.82
  }
}
```

---

### 3. 更新模型信息

**接口描述**: 更新模型的名称、描述和标签信息

**请求方式**: `PUT`

**接口地址**: `/models/{model_id}`

**请求类型**: `application/json`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 否 | 模型名称 |
| description | string | 否 | 模型描述 |
| tags | array[string] | 否 | 标签列表 |

**请求示例**:

```json
{
  "name": "Updated Model Name",
  "description": "Updated description",
  "tags": ["updated", "tags"]
}
```

**响应参数**: 同"获取模型详情"

---

### 4. 删除模型

**接口描述**: 删除指定的模型及其相关文件

**请求方式**: `DELETE`

**接口地址**: `/models/{model_id}`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| ok | boolean | 是否成功 |
| message | string | 提示信息 |

**响应示例**:

```json
{
  "ok": true,
  "message": "Model deleted successfully"
}
```

---

### 5. 上传模型

**接口描述**: 上传已有的模型文件（ZIP压缩包格式，与导出格式相同）

**请求方式**: `POST`

**接口地址**: `/models/upload`

**请求类型**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | ZIP格式的模型压缩包，包含model.json和weights目录 |

**ZIP文件结构要求**:

ZIP文件应包含以下结构之一：

**格式1（标准导出格式）**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**格式2（简化格式）**:
```
model.json
weights/
  └── best.pt
```

**说明**:
- ZIP文件必须包含`weights`目录，且至少包含一个`.pt`权重文件
- 如果ZIP中包含`model.json`，将使用其中的元数据（name、classes、description等）
- 如果ZIP中不包含`model.json`，将自动创建新的元数据
- 如果ZIP中的model_id已存在，将自动生成新的model_id

**请求示例**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**响应参数**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| model_id | string | 模型 ID |
| name | string | 模型名称 |
| weights_path | string | 权重文件路径 |
| file_size | integer | 文件大小（字节） |
| file_size_mb | float | 文件大小（MB） |
| created_at | string | 创建时间 |
| source | string | 来源（uploaded） |
| classes | array[string] | 类别列表 |
| description | string | 描述 |
| tags | array[string] | 标签 |

**响应示例**:

```json
{
  "model_id": "model_20240115_123456",
  "name": "Custom YOLOv8 Model",
  "weights_path": "/app/models/registry/model_20240115_123456/weights/best.pt",
  "file_size": 12345678,
  "file_size_mb": 11.78,
  "created_at": "2024-01-15T12:34:56",
  "source": "uploaded",
  "classes": ["person", "car", "dog"],
  "description": "Uploaded model from my_model.zip",
  "tags": ["uploaded"]
}
```

---

### 6. 导出模型

**接口描述**: 导出模型为ZIP文件，包含权重和元数据

**请求方式**: `GET`

**接口地址**: `/models/{model_id}/export`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**响应类型**: `application/zip`

**响应**: 返回ZIP文件流，包含：
- `{model_id}/weights/best.pt` - 模型权重文件
- `{model_id}/model.json` - 模型元数据

**请求示例**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. 生成训练图表

**接口描述**: 生成模型训练过程的可视化图表

**请求方式**: `GET`

**接口地址**: `/models/{model_id}/charts`

**请求类型**: 无

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model_id | string | 是 | 模型 ID |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| chart_type | string | 否 | "all" | 图表类型：loss（损失曲线）、metrics（指标曲线）、all（所有） |

**响应类型**: `image/png`

**响应**: 返回PNG格式的图表图片

**请求示例**:

```bash
# 获取损失曲线图
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# 获取指标曲线图
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```

---

<a name="english"></a>

## English Documentation

### Table of Contents

- [Basic Information](#basic-information)
- [Dataset Management](#dataset-management)
- [Annotation Management](#annotation-management)
- [Training Management](#training-management)
- [Log Management](#log-management)
- [Inference Service](#inference-service)
- [Model Management](#model-management)

---

## Basic Information

### Base URL

```
http://localhost:8000
```

### Response Format

All endpoints return JSON format data.

### Error Codes

| HTTP Status | Description |
|------------|-------------|
| 200 | Request successful |
| 400 | Request parameter error |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Dataset Management

### 1. Upload Dataset

**Description**: Upload dataset ZIP file to server

**Method**: `POST`

**Endpoint**: `/datasets/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Dataset file in ZIP format |

**Request Example**:

```bash
curl -X POST http://localhost:8000/datasets/upload \
  -F "file=@your_dataset.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| dataset_id | string | Unique dataset identifier |
| filename | string | Uploaded filename |
| size | integer | File size in bytes |
| created_at | string | Creation time (ISO 8601 format) |
| status | string | Dataset status (uploaded/prepared) |

**Response Example**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "filename": "your_dataset.zip",
  "size": 12345678,
  "created_at": "2024-01-15T12:34:56",
  "status": "uploaded"
}
```

---

### 2. Prepare Dataset

**Description**: Extract dataset, validate format, generate YOLO configuration file

**Method**: `POST`

**Endpoint**: `/datasets/{dataset_id}/prepare`

**Content-Type**: `application/json`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| split_ratio | object | No | {"train": 0.8, "val": 0.2} | Train/validation split ratio |
| classes | array[string] | No | null | Class list, if not provided will be read from dataset |

**Request Example**:

```json
{
  "split_ratio": {
    "train": 0.8,
    "val": 0.2
  },
  "classes": ["person", "car", "dog"]
}
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| dataset_id | string | Dataset ID |
| version | string | Dataset version (default v1) |
| status | string | Preparation status (prepared) |
| classes | array[string] | Class list |
| train_count | integer | Number of training images |
| val_count | integer | Number of validation images |
| data_yaml | string | Path to data.yaml file |

**Response Example**:

```json
{
  "dataset_id": "ds_20240115_123456",
  "version": "v1",
  "status": "prepared",
  "classes": ["person", "car", "dog"],
  "train_count": 800,
  "val_count": 200,
  "data_yaml": "/app/data/datasets/ds_20240115_123456/v1/data.yaml"
}
```

---

### 3. List All Datasets

**Description**: Get list of all datasets

**Method**: `GET`

**Endpoint**: `/datasets`

**Content-Type**: None

**Request Parameters**: None

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| datasets | array[object] | List of datasets |

**Dataset Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| dataset_id | string | Dataset ID |
| filename | string | Filename |
| size | integer | File size |
| status | string | Status (uploaded/prepared) |
| created_at | string | Creation time |
| versions | array[string] | Version list |

**Response Example**:

```json
{
  "datasets": [
    {
      "dataset_id": "ds_20240115_123456",
      "filename": "dataset.zip",
      "size": 12345678,
      "status": "prepared",
      "created_at": "2024-01-15T12:34:56",
      "versions": ["v1"]
    }
  ]
}
```

---

### 4. Get Dataset Details

**Description**: Get detailed information of specified dataset

**Method**: `GET`

**Endpoint**: `/datasets/{dataset_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Response Parameters**: Same as "List All Datasets" dataset object structure, but with more detailed information

---

### 5. Update Dataset Information

**Description**: Update dataset description and tags

**Method**: `PUT`

**Endpoint**: `/datasets/{dataset_id}`

**Content-Type**: `application/json`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| description | string | No | Dataset description |
| tags | array[string] | No | Tag list |

---

### 6. Delete Dataset

**Description**: Delete specified dataset and all related files

**Method**: `DELETE`

**Endpoint**: `/datasets/{dataset_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```

---

### 7. Export Annotated Dataset

**Description**: Export dataset with annotations (YOLO format)

**Method**: `GET`

**Endpoint**: `/datasets/{dataset_id}/export/annotated`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| version | string | No | "v1" | Dataset version |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `images/` - Image directory (train/val)
- `labels/` - Label directory (YOLO format)
- `data.yaml` - Dataset configuration file

**Request Example**:

```bash
curl -X GET http://localhost:8000/datasets/ds_20240115_123456/export/annotated \
  -o dataset_annotated.zip
```

---

### 8. Export Original Dataset

**Description**: Export original dataset (images only, no annotations)

**Method**: `GET`

**Endpoint**: `/datasets/{dataset_id}/export/original`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| dataset_id | string | Yes | Dataset ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| version | string | No | "v1" | Dataset version |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `images/` - Image directory
- `data.yaml` - Dataset configuration file (if exists)

**Request Example**:

```bash
curl -X GET http://localhost:8000/datasets/ds_20240115_123456/export/original \
  -o dataset_original.zip
```

---

## Annotation Management

### 1. Create Annotation Task

**Description**: Create annotation task for specified dataset

**Method**: `POST`

**Endpoint**: `/annotations/tasks`

**Content-Type**: `application/json`

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| dataset_id | string | Yes | - | Dataset ID |
| version | string | No | "v1" | Dataset version |
| classes | array[string] | No | null | Class list, if not provided will be read from data.yaml |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| task_id | string | Annotation task ID |
| dataset_id | string | Dataset ID |
| version | string | Dataset version |
| classes | array[string] | Class list |
| total_items | integer | Total number of images |
| annotated_count | integer | Number of annotated images |
| created_at | string | Creation time |

---

### 2. Get Task Items

**Description**: Get list of all images for specified annotation task

**Method**: `GET`

**Endpoint**: `/annotations/tasks/{task_id}/items`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | string | Yes | Annotation task ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| task_id | string | Annotation task ID |
| items | array[object] | Image list |

**Image Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| image_id | string | Image ID |
| image_path | string | Image path (relative path for static file service) |
| width | integer | Image width |
| height | integer | Image height |
| has_annotation | boolean | Whether annotation exists |

---

### 3. Save Annotation

**Description**: Save annotation for single image

**Method**: `POST`

**Endpoint**: `/annotations/tasks/{task_id}/items/{image_id}`

**Content-Type**: `application/json`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | string | Yes | Annotation task ID |
| image_id | string | Yes | Image ID |

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| boxes | array[object] | Yes | Bounding box list |

**Bounding Box Object Structure**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| class_id | integer | Yes | Class ID (starting from 0) |
| x1 | float | Yes | Top-left X coordinate (pixels) |
| y1 | float | Yes | Top-left Y coordinate (pixels) |
| x2 | float | Yes | Bottom-right X coordinate (pixels) |
| y2 | float | Yes | Bottom-right Y coordinate (pixels) |

---

### 4. Get Image Annotation

**Description**: Get annotation information for specified image

**Method**: `GET`

**Endpoint**: `/annotations/tasks/{task_id}/items/{image_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | string | Yes | Annotation task ID |
| image_id | string | Yes | Image ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| image_id | string | Image ID |
| boxes | array[object] | Bounding box list (same structure as save annotation) |
| updated_at | string | Update time |

---

### 5. Export Annotations

**Description**: Export all annotations for task as YOLO format label files

**Method**: `GET`

**Endpoint**: `/annotations/tasks/{task_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| task_id | string | Yes | Annotation task ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| format | string | No | "yolo" | Export format (currently only yolo supported) |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```
| labels_dir | string | Label file directory path |
| exported_count | integer | Number of exported label files |

---

## Training Management

### 1. Create Training Job

**Description**: Create new model training job, supports fine-tuning based on existing models

**Method**: `POST`

**Endpoint**: `/train/jobs`

**Content-Type**: `application/json`

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| dataset_id | string | Yes | - | Dataset ID |
| version | string | No | "v1" | Dataset version |
| model_name | string | No | "yolov8n.pt" | Pretrained model name (e.g., yolov8n.pt, yolov8s.pt) or existing model ID |
| epochs | integer | No | 10 | Number of training epochs |
| imgsz | integer | No | 640 | Image size |
| batch | integer | No | -1 | Batch size, -1 means auto-calculate |
| base_model_id | string | No | null | Existing model ID for fine-tuning |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | Training job ID |
| status | string | Job status (running/completed/failed/stopped) |

---

### 2. List All Training Jobs

**Description**: Get list of all training jobs

**Method**: `GET`

**Endpoint**: `/train/jobs`

**Content-Type**: None

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| jobs | array[object] | Training job list |

**Training Job Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | Job ID |
| dataset_id | string | Dataset ID |
| version | string | Dataset version |
| model_name | string | Model name |
| epochs | integer | Number of epochs |
| imgsz | integer | Image size |
| batch | integer | Batch size |
| status | string | Job status |
| created_at | string | Creation time |
| model_id | string | Generated model ID after training completes (if completed) |

---

### 3. Get Training Job Details

**Description**: Get detailed information of specified training job

**Method**: `GET`

**Endpoint**: `/train/jobs/{job_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Training job ID |

**Response Parameters**: Same as "List All Training Jobs" training job object structure, but with more detailed information

---

### 4. Stop Training Job

**Description**: Stop running training job

**Method**: `POST`

**Endpoint**: `/train/jobs/{job_id}/stop`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Training job ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```

---

### 5. Resume Training Job

**Description**: Resume interrupted training job (supports normal stop and crash recovery)

**Method**: `POST`

**Endpoint**: `/train/jobs/{job_id}/resume`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Training job ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```
| job_id | string | Job ID |
| status | string | Job status |

---

### 6. Delete Training Job

**Description**: Delete specified training job and related files

**Method**: `DELETE`

**Endpoint**: `/train/jobs/{job_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Training job ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```

---

## Log Management

### 1. SSE Stream Logs

**Description**: Real-time training log push via Server-Sent Events (SSE)

**Method**: `GET`

**Endpoint**: `/logs/stream`

**Content-Type**: None

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Training job ID |

**Response Type**: `text/event-stream`

**Response Format**: SSE format, each log line starts with `data: `

---

### 2. Poll Logs

**Description**: Get incremental logs via polling (fallback when SSE unavailable)

**Method**: `GET`

**Endpoint**: `/logs/tail`

**Content-Type**: None

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| job_id | string | Yes | - | Training job ID |
| offset | integer | No | 0 | Log file read offset in bytes |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| offset | integer | New offset (for next request) |
| lines | array[string] | Log line list (max 50 lines) |

---

### 3. Get Log Lines

**Description**: Get last N lines of log file

**Method**: `GET`

**Endpoint**: `/logs/lines`

**Content-Type**: None

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| job_id | string | Yes | - | Training job ID |
| n | integer | No | 100 | Number of lines to get, 0 means get all logs |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| lines | array[string] | Log line list |
| total | integer | Total number of log lines |
| returned | integer | Number of lines returned this time |

---

## Inference Service

### 1. Image Inference

**Description**: Perform object detection inference on image using specified model

**Method**: `POST`

**Endpoint**: `/infer/{model_id}`

**Content-Type**: `multipart/form-data`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Image file (supports jpg, png, jpeg) |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| image_path | string | Image path (relative path) |
| detections | array[object] | Detection result list |

**Detection Result Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| class_id | integer | Class ID |
| class_name | string | Class name |
| confidence | float | Confidence (0-1) |
| bbox | object | Bounding box coordinates |

**Bounding Box Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| x1 | float | Top-left X coordinate |
| y1 | float | Top-left Y coordinate |
| x2 | float | Bottom-right X coordinate |
| y2 | float | Bottom-right Y coordinate |

---

### 2. Batch Inference

**Description**: Batch inference using multiple models on multiple images

**Method**: `POST`

**Endpoint**: `/infer/batch/run`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_ids | string | Yes | Comma-separated model ID list, e.g., "model_1,model_2" |
| files | array[File] | Yes | Multiple image files |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| results | array[object] | Inference result list |

**Inference Result Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| image_path | string | Image path |
| detections | array[object] | Detection result list (same structure as image inference) |

---

### 3. Video Inference

**Description**: Perform inference on video file, return annotated video

**Method**: `POST`

**Endpoint**: `/infer/video/{model_id}`

**Content-Type**: `multipart/form-data`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file | File | Yes | - | Video file |
| conf | float | No | 0.25 | Confidence threshold (0-1) |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| video_data | string | Processed video data (base64 encoded) |
| stats | object | Detection statistics |

**Statistics Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| total_frames | integer | Total number of frames |
| detections_per_frame | array[integer] | Number of detected objects per frame |

---

### 4. Video Inference Stream

**Description**: Streaming version of video inference, return detection results frame by frame

**Method**: `POST`

**Endpoint**: `/infer/video/{model_id}/stream`

**Content-Type**: `multipart/form-data`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Request Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| file | File | Yes | - | Video file |
| conf | float | No | 0.25 | Confidence threshold (0-1) |

**Response Type**: `text/event-stream`

**Response Format**: SSE format, each frame returns JSON data

---

### 5. Inference and Save Results

**Description**: Perform inference and save results with UUID and CSV

**Method**: `POST`

**Endpoint**: `/infer/{model_id}/export`

**Content-Type**: `multipart/form-data`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| files | array[File] | Yes | Multiple image files |

**Request Example**:

```bash
curl -X POST http://localhost:8000/infer/model_20240115_123456/export \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | string | Inference session ID |
| results | array[object] | Inference results list |
| session_dir | string | Results save directory |

**Result Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| image_uuid | string | Image unique identifier (UUID) |
| image_filename | string | Original filename |
| model_id | string | Model ID |
| image_width | integer | Image width |
| image_height | integer | Image height |
| detection_count | integer | Number of detections |
| detections | array[object] | Detection results list |

---

### 6. Export Inference Results

**Description**: Export inference results as ZIP file with annotated images and CSV

**Method**: `GET`

**Endpoint**: `/infer/results/{session_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | Inference session ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `images/{uuid}.jpg` - Annotated result images
- `results.csv` - Detection results in CSV format
- `metadata.json` - Session metadata

**CSV File Format**:

| Column | Description |
|--------|-------------|
| image_uuid | Image UUID |
| image_filename | Original filename |
| model_id | Model ID |
| image_width | Image width |
| image_height | Image height |
| detection_count | Detection count |
| detection_index | Detection index |
| class_id | Class ID |
| class_name | Class name |
| confidence | Confidence |
| x1, y1, x2, y2 | Bounding box coordinates |

**Request Example**:

```bash
curl -X GET http://localhost:8000/infer/results/session_20240115_123456_a1b2c3d4/export \
  -o inference_results.zip
```

---

## Model Management

### 1. List All Models

**Description**: Get list of all trained models

**Method**: `GET`

**Endpoint**: `/models`

**Content-Type**: None

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| models | array[object] | Model list |

**Model Object Structure**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| description | string | Model description |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| job_id | string | Training job ID |
| dataset_id | string | Dataset ID |
| tags | array[string] | Tag list |

---

### 2. Get Model Details

**Description**: Get detailed information of specified model, including training metrics

**Method**: `GET`

**Endpoint**: `/models/{model_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Parameters**: Same as "List All Models" model object structure, but with more detailed information such as training metrics

---

### 3. Update Model Information

**Description**: Update model name, description, and tags

**Method**: `PUT`

**Endpoint**: `/models/{model_id}`

**Content-Type**: `application/json`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | No | Model name |
| description | string | No | Model description |
| tags | array[string] | No | Tag list |

---

### 4. Delete Model

**Description**: Delete specified model and related files

**Method**: `DELETE`

**Endpoint**: `/models/{model_id}`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| ok | boolean | Success status |
| message | string | Message |

---

### 5. Upload Model

**Description**: Upload an existing model file (ZIP archive format, same as export format)

**Method**: `POST`

**Endpoint**: `/models/upload`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | Yes | Model ZIP archive containing model.json and weights directory |

**ZIP File Structure Requirements**:

The ZIP file should contain one of the following structures:

**Format 1 (Standard Export Format)**:
```
model_20240115_123456/
  ├── model.json
  └── weights/
      └── best.pt
```

**Format 2 (Simplified Format)**:
```
model.json
weights/
  └── best.pt
```

**Notes**:
- The ZIP file must contain a `weights` directory with at least one `.pt` weight file
- If the ZIP contains `model.json`, its metadata (name, classes, description, etc.) will be used
- If the ZIP does not contain `model.json`, new metadata will be automatically created
- If the model_id in the ZIP already exists, a new model_id will be automatically generated

**Request Example**:

```bash
curl -X POST http://localhost:8000/models/upload \
  -F "file=@my_model.zip"
```

**Response Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | Model ID |
| name | string | Model name |
| weights_path | string | Weight file path |
| file_size | integer | File size in bytes |
| file_size_mb | float | File size in MB |
| created_at | string | Creation time |
| source | string | Source (uploaded) |
| classes | array[string] | Class list |
| description | string | Description |
| tags | array[string] | Tags |

---

### 6. Export Model

**Description**: Export model as ZIP file with weights and metadata

**Method**: `GET`

**Endpoint**: `/models/{model_id}/export`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Response Type**: `application/zip`

**Response**: Returns ZIP file stream containing:
- `{model_id}/weights/best.pt` - Model weight file
- `{model_id}/model.json` - Model metadata

**Request Example**:

```bash
curl -X GET http://localhost:8000/models/model_20240115_123456/export \
  -o model_20240115_123456.zip
```

---

### 7. Generate Training Charts

**Description**: Generate visualization charts for model training process

**Method**: `GET`

**Endpoint**: `/models/{model_id}/charts`

**Content-Type**: None

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_id | string | Yes | Model ID |

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| chart_type | string | No | "all" | Chart type: loss, metrics, all |

**Response Type**: `image/png`

**Response**: Returns PNG format chart image

**Request Example**:

```bash
# Get loss chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=loss \
  -o loss_chart.png

# Get metrics chart
curl -X GET http://localhost:8000/models/model_20240115_123456/charts?chart_type=metrics \
  -o metrics_chart.png
```
