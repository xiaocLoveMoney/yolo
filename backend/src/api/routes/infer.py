from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from typing import List
from src.services.infer_service import InferService

router = APIRouter(prefix="/infer", tags=["infer"])
infer_service = InferService()

@router.post("/{model_id}")
async def inference(model_id: str, file: UploadFile = File(...)):
    """使用指定模型进行推理"""
    result = await infer_service.infer(model_id, file)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@router.post("/batch/run")
async def batch_inference(
    model_ids: str = Form(...),  # 逗号分隔的模型ID列表
    files: List[UploadFile] = File(...)
):
    """批量推理：支持多模型、多图片
    
    - model_ids: 逗号分隔的模型ID列表，如 "model_1,model_2"
    - files: 多个图片文件
    """
    # 解析模型ID列表
    model_id_list = [mid.strip() for mid in model_ids.split(",") if mid.strip()]
    
    if not model_id_list:
        raise HTTPException(400, "至少需要选择一个模型")
    
    if not files:
        raise HTTPException(400, "至少需要上传一张图片")
    
    result = await infer_service.batch_infer(model_id_list, files)
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result

@router.post("/video/{model_id}")
async def video_inference(
    model_id: str, 
    file: UploadFile = File(...),
    conf: float = Form(0.25)
):
    """视频推理：处理视频文件并返回带标注的视频
    
    Args:
        model_id: 模型ID
        file: 视频文件
        conf: 置信度阈值，默认0.25
    
    Returns:
        处理后的视频数据（base64编码）和检测统计信息
    """
    result = await infer_service.infer_video(model_id, file, conf)
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result

@router.post("/video/{model_id}/stream")
async def video_inference_stream(
    model_id: str,
    file: UploadFile = File(...),
    conf: float = Form(0.25)
):
    """视频推理流式接口：逐帧返回检测结果
    
    Args:
        model_id: 模型ID
        file: 视频文件
        conf: 置信度阈值，默认0.25
    
    Returns:
        SSE流，每帧返回：帧数据（base64编码的JPEG）和检测结果
    """
    return StreamingResponse(
        infer_service.infer_video_stream(model_id, file, conf),
        media_type="text/event-stream"
    )
