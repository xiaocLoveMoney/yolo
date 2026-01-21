from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
from src.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])
dataset_service = DatasetService()

class PrepareRequest(BaseModel):
    split_ratio: Optional[Dict[str, float]] = {"train": 0.8, "val": 0.2}
    classes: Optional[list[str]] = None

class UpdateDatasetRequest(BaseModel):
    description: Optional[str] = None
    tags: Optional[list[str]] = None

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """上传数据集zip文件"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Only zip files are allowed")
    
    result = await dataset_service.upload_dataset(file)
    return result

@router.post("/{dataset_id}/prepare")
async def prepare_dataset(dataset_id: str, request: PrepareRequest):
    """准备数据集：解压、校验、生成配置"""
    result = await dataset_service.prepare_dataset(
        dataset_id, 
        request.split_ratio, 
        request.classes
    )
    return result

@router.get("")
async def list_datasets():
    """列出所有数据集"""
    return await dataset_service.list_datasets()

@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取数据集详情"""
    result = await dataset_service.get_dataset(dataset_id)
    if not result:
        raise HTTPException(404, "Dataset not found")
    return result

@router.put("/{dataset_id}")
async def update_dataset(dataset_id: str, request: UpdateDatasetRequest):
    """更新数据集信息"""
    result = await dataset_service.update_dataset(dataset_id, request)
    if not result:
        raise HTTPException(404, "Dataset not found")
    return result

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """删除数据集"""
    result = await dataset_service.delete_dataset(dataset_id)
    if not result:
        raise HTTPException(404, "Dataset not found")
    return result

@router.get("/{dataset_id}/export/annotated")
async def export_annotated_dataset(
    dataset_id: str,
    version: str = Query("v1", description="数据集版本")
):
    """导出标注后的数据集（包含图片和标签）"""
    zip_path = await dataset_service.export_annotated_dataset(dataset_id, version)
    if not zip_path:
        raise HTTPException(404, "Dataset not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{dataset_id}_annotated.zip",
        headers={"Content-Disposition": f"attachment; filename={dataset_id}_annotated.zip"}
    )

@router.get("/{dataset_id}/export/original")
async def export_original_dataset(
    dataset_id: str,
    version: str = Query("v1", description="数据集版本")
):
    """导出标注前的数据集（仅包含图片）"""
    zip_path = await dataset_service.export_original_dataset(dataset_id, version)
    if not zip_path:
        raise HTTPException(404, "Dataset not found")
    
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{dataset_id}_original.zip",
        headers={"Content-Disposition": f"attachment; filename={dataset_id}_original.zip"}
    )
