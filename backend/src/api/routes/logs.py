from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["logs"])
log_service = LogService()

@router.get("/stream")
async def stream_logs(job_id: str):
    """SSE流式日志"""
    return StreamingResponse(
        log_service.stream_logs(job_id),
        media_type="text/event-stream"
    )

@router.get("/tail")
async def tail_logs(job_id: str, offset: int = 0):
    """轮询日志"""
    result = await log_service.tail_logs(job_id, offset)
    return result

@router.get("/lines")
async def get_log_lines(job_id: str, n: int = 100):
    """获取日志文件的最后N行
    
    Args:
        job_id: 任务ID
        n: 要获取的行数，默认100，设为0表示获取所有日志
    """
    result = await log_service.get_log_lines(job_id, n)
    return result
