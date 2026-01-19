from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.services.annotation_service import AnnotationService

router = APIRouter(prefix="/annotations", tags=["annotations"])
annotation_service = AnnotationService()

class CreateTaskRequest(BaseModel):
    dataset_id: str
    version: str = "v1"
    classes: Optional[List[str]] = None  # 可选，如果不提供则从 data.yaml 读取

class BBox(BaseModel):
    class_id: int
    x1: float
    y1: float
    x2: float
    y2: float

class SaveAnnotationRequest(BaseModel):
    boxes: List[BBox]

@router.post("/tasks")
async def create_annotation_task(request: CreateTaskRequest):
    """创建标注任务"""
    result = await annotation_service.create_task(
        request.dataset_id,
        request.version,
        request.classes
    )
    return result

@router.get("/tasks/{task_id}/items")
async def get_task_items(task_id: str):
    """获取标注任务的图片列表"""
    result = await annotation_service.get_task_items(task_id)
    if not result:
        raise HTTPException(404, "Task not found")
    return result

@router.post("/tasks/{task_id}/items/{image_id}")
async def save_annotation(task_id: str, image_id: str, request: SaveAnnotationRequest):
    """保存图片标注"""
    result = await annotation_service.save_annotation(
        task_id,
        image_id,
        request.boxes
    )
    return result

@router.get("/tasks/{task_id}/items/{image_id}")
async def get_image_annotation(task_id: str, image_id: str):
    """获取单张图片的标注"""
    result = await annotation_service.get_image_annotation(task_id, image_id)
    if not result:
        raise HTTPException(404, "Image not found")
    return result

@router.get("/tasks/{task_id}/export")
async def export_annotations(task_id: str, format: str = "yolo"):
    """导出标注为YOLO格式"""
    if format != "yolo":
        raise HTTPException(400, "Only yolo format is supported")
    
    result = await annotation_service.export_to_yolo(task_id)
    if not result.get("ok", False):
        raise HTTPException(500, result.get("error", "Export failed"))
    return result
