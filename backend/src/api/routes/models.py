from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from src.services.model_service import ModelService
import os

router = APIRouter(prefix="/models", tags=["models"])
model_service = ModelService()

class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None

class UploadModelRequest(BaseModel):
    name: Optional[str] = None
    classes: Optional[list[str]] = None

@router.get("")
async def list_models():
    """列出所有模型"""
    return await model_service.list_models()

@router.get("/{model_id}")
async def get_model(model_id: str):
    """获取模型详情"""
    result = await model_service.get_model(model_id)
    if not result:
        raise HTTPException(404, "Model not found")
    return result

@router.put("/{model_id}")
async def update_model(model_id: str, request: UpdateModelRequest):
    """更新模型信息"""
    result = await model_service.update_model(model_id, request)
    if not result:
        raise HTTPException(404, "Model not found")
    return result

@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """删除模型"""
    result = await model_service.delete_model(model_id)
    if not result:
        raise HTTPException(404, "Model not found")
    return result

@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...)
):
    """上传已有模型（ZIP格式，与导出格式相同）
    
    Args:
        file: ZIP格式的模型压缩包，包含model.json和weights目录
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Only .zip files are allowed")
    
    try:
        result = await model_service.upload_model(file)
        return result
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/{model_id}/export")
async def export_model(model_id: str):
    """导出模型为ZIP文件"""
    zip_path = await model_service.export_model(model_id)
    if not zip_path:
        raise HTTPException(404, "Model not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{model_id}.zip",
        headers={"Content-Disposition": f"attachment; filename={model_id}.zip"}
    )

@router.get("/{model_id}/charts")
async def generate_training_charts(
    model_id: str,
    chart_type: str = Query("all", description="图表类型: loss, metrics, all")
):
    """生成训练图表
    
    Args:
        model_id: 模型ID
        chart_type: 图表类型 - loss（损失曲线）, metrics（指标曲线）, all（所有图表）
    
    Returns:
        图表图片文件
    """
    try:
        chart_paths = await model_service.generate_training_charts(model_id, chart_type)
        if not chart_paths:
            raise HTTPException(404, "Model not found")
        
        # 如果只有一个图表，直接返回
        if chart_type == "loss":
            return FileResponse(
                chart_paths["loss_chart"],
                media_type="image/png",
                filename=f"{model_id}_loss.png"
            )
        elif chart_type == "metrics":
            return FileResponse(
                chart_paths["metrics_chart"],
                media_type="image/png",
                filename=f"{model_id}_metrics.png"
            )
        else:
            # 返回损失曲线图（默认），前端可以分别请求
            return FileResponse(
                chart_paths["loss_chart"],
                media_type="image/png",
                filename=f"{model_id}_loss.png"
            )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
