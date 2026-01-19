from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.train_service import TrainService

router = APIRouter(prefix="/train", tags=["train"])
train_service = TrainService()

class TrainJobRequest(BaseModel):
    dataset_id: str
    version: str = "v1"
    model_name: str = "yolov8n.pt"  # 可以是预训练模型或已有模型ID
    epochs: int = 10
    imgsz: int = 640
    batch: int = -1
    base_model_id: Optional[str] = None  # 用于微调的已有模型ID

@router.post("/jobs")
async def create_train_job(request: TrainJobRequest):
    """创建训练任务（支持基于已有模型微调）"""
    result = await train_service.create_job(
        dataset_id=request.dataset_id,
        version=request.version,
        model_name=request.model_name,
        epochs=request.epochs,
        imgsz=request.imgsz,
        batch=request.batch,
        base_model_id=request.base_model_id
    )
    return result

@router.get("/jobs")
async def list_train_jobs():
    """列出所有训练任务"""
    return await train_service.list_jobs()

@router.get("/jobs/{job_id}")
async def get_train_job(job_id: str):
    """获取训练任务详情"""
    result = await train_service.get_job(job_id)
    if not result:
        raise HTTPException(404, "Job not found")
    return result

@router.post("/jobs/{job_id}/stop")
async def stop_train_job(job_id: str):
    """停止训练任务"""
    result = await train_service.stop_job(job_id)
    return result

@router.post("/jobs/{job_id}/resume")
async def resume_train_job(job_id: str):
    """继续训练中断的任务（支持正常停止和崩溃恢复）"""
    try:
        result = await train_service.resume_job(job_id)
        if not result:
            raise HTTPException(404, "Job not found")
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to resume training: {str(e)}")

@router.delete("/jobs/{job_id}")
async def delete_train_job(job_id: str):
    """删除训练任务"""
    result = await train_service.delete_job(job_id)
    if not result:
        raise HTTPException(404, "Job not found")
    return result
