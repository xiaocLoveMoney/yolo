from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["models"])
model_service = ModelService()

class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None

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
