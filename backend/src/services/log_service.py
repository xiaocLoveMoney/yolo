import asyncio
import json
import re
from pathlib import Path
from src.core.settings import settings


# ANSI 转义码处理函数（保留 ANSI 码，供前端解析）
# 前端会解析这些转义码并渲染为彩色


def _read_log_lines(log_file: Path, offset: int, max_lines: int = None):
    """同步读取日志文件（尝试多种编码）
    
    Args:
        log_file: 日志文件路径
        offset: 读取起始位置
        max_lines: 最多读取的行数，None表示读取所有
    """
    lines = []
    new_offset = offset
    
    # 尝试多种编码方式
    encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(log_file, "r", encoding=encoding, errors="replace") as f:
                f.seek(offset)
                
                # 如果指定了最大行数，逐行读取并限制数量
                if max_lines is not None and max_lines > 0:
                    lines = []
                    for _ in range(max_lines):
                        line = f.readline()
                        if not line:  # 到达文件末尾
                            break
                        lines.append(line)
                    new_offset = f.tell()
                else:
                    # 读取所有剩余行
                    lines = f.readlines()
                    new_offset = f.tell()
                
                # 如果成功读取，跳出循环
                break
        except (UnicodeDecodeError, UnicodeError):
            # 如果编码失败，尝试下一个
            continue
        except Exception:
            # 其他错误（如文件不存在），返回空结果
            return [], offset
    
    return lines, new_offset


def _get_file_tail_offset(log_file: Path, n_lines: int = 50):
    """获取文件最后N行的起始位置（字节偏移量）
    
    Args:
        log_file: 日志文件路径
        n_lines: 要获取的最后N行，默认50行
    
    Returns:
        int: 最后N行的起始位置（字节偏移量），如果文件总行数少于N行，返回0
    """
    # 尝试多种编码方式
    encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(log_file, "r", encoding=encoding, errors="replace") as f:
                # 读取所有行
                all_lines = f.readlines()
                total_lines = len(all_lines)
                
                # 如果总行数少于等于n_lines，返回0（从开头开始）
                if total_lines <= n_lines:
                    return 0
                
                # 计算前 (total_lines - n_lines) 行的总字节数
                # 重新打开文件，逐行读取并计算字节数
                f.seek(0)
                offset = 0
                for i in range(total_lines - n_lines):
                    line = f.readline()
                    offset = f.tell()
                
                return offset
                
        except (UnicodeDecodeError, UnicodeError):
            # 如果编码失败，尝试下一个
            continue
        except Exception:
            # 其他错误（如文件不存在），返回0
            return 0
    
    # 如果所有编码都失败，返回0
    return 0


class LogService:
    def __init__(self):
        self.jobs_dir = settings.JOBS_DIR
    
    async def stream_logs(self, job_id: str):
        """SSE流式日志 - 只推送增量日志（从末尾50条之后开始）"""
        log_file = self.jobs_dir / f"{job_id}.log"
        
        # 如果日志文件不存在，等待创建
        for _ in range(10):
            if log_file.exists():
                break
            await asyncio.sleep(0.5)
        
        if not log_file.exists():
            yield f"data: Log file not found\n\n"
            return
        
        # 获取最后50行的起始位置作为初始offset，只推送增量日志
        offset = await asyncio.to_thread(_get_file_tail_offset, log_file, 50)
        
        while True:
            try:
                # 在线程中读取日志（支持多种编码），每次最多读取50条
                lines, new_offset = await asyncio.to_thread(_read_log_lines, log_file, offset, 50)
                
                # 只推送新增的日志行（增量）
                for line in lines:
                    # 清理行内容：只移除空字符和替换字符，保留 ANSI 转义码
                    cleaned_line = line.rstrip().replace('\x00', '').replace('\ufffd', '')
                    if cleaned_line:
                        yield f"data: {cleaned_line}\n\n"
                
                offset = new_offset
                
                # 检查任务是否完成
                job_file = self.jobs_dir / f"{job_id}.json"
                if await asyncio.to_thread(lambda: job_file.exists()):
                    def _check_job_status():
                        if job_file.exists():
                            with open(job_file, "r", encoding="utf-8") as f:
                                return json.load(f)
                        return None
                    
                    job_meta = await asyncio.to_thread(_check_job_status)
                    
                    if job_meta and job_meta.get("status") in ["completed", "failed", "stopped"]:
                        # 任务结束，再等待一小段时间确保日志全部输出
                        await asyncio.sleep(1)
                        # 任务结束时，读取剩余所有日志（不限制行数）
                        lines, new_offset = await asyncio.to_thread(_read_log_lines, log_file, offset, None)
                        for line in lines:
                            # 清理行内容：只移除空字符和替换字符，保留 ANSI 转义码
                            cleaned_line = line.rstrip().replace('\x00', '').replace('\ufffd', '')
                            if cleaned_line:
                                yield f"data: {cleaned_line}\n\n"
                        break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                yield f"data: Error reading log: {str(e)}\n\n"
                break
    
    async def tail_logs(self, job_id: str, offset: int):
        """轮询获取增量日志，每次最多返回50条"""
        log_file = self.jobs_dir / f"{job_id}.log"
        
        if not await asyncio.to_thread(lambda: log_file.exists()):
            return {"offset": offset, "lines": []}
        
        try:
            # 在线程中读取日志（支持多种编码），限制最多50条
            lines, new_offset = await asyncio.to_thread(_read_log_lines, log_file, offset, 50)
            
            # 清理每一行：只移除空字符和替换字符，保留 ANSI 转义码
            cleaned_lines = [
                line.rstrip().replace('\x00', '').replace('\ufffd', '')
                for line in lines
                if line.rstrip()
            ]
            
            return {"offset": new_offset, "lines": cleaned_lines}
        
        except Exception as e:
            return {"offset": offset, "lines": [], "error": str(e)}
    
    async def get_log_lines(self, job_id: str, n: int = 100):
        """获取日志文件的最后N行，n=0表示获取所有日志"""
        log_file = self.jobs_dir / f"{job_id}.log"
        
        if not await asyncio.to_thread(lambda: log_file.exists()):
            return {"lines": [], "total": 0, "error": "Log file not found"}
        
        try:
            def _read_last_n_lines():
                # 尝试多种编码方式
                encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin-1']
                all_lines = []
                
                for encoding in encodings:
                    try:
                        with open(log_file, "r", encoding=encoding, errors="replace") as f:
                            all_lines = f.readlines()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                    except Exception:
                        return [], 0
                
                # 清理每一行
                cleaned_lines = [
                    line.rstrip().replace('\x00', '').replace('\ufffd', '')
                    for line in all_lines
                    if line.rstrip()
                ]
                
                total = len(cleaned_lines)
                
                # n=0 表示返回所有日志
                if n == 0 or n >= total:
                    return cleaned_lines, total
                else:
                    # 返回最后 n 行
                    return cleaned_lines[-n:], total
            
            lines, total = await asyncio.to_thread(_read_last_n_lines)
            
            return {"lines": lines, "total": total, "returned": len(lines)}
        
        except Exception as e:
            return {"lines": [], "total": 0, "error": str(e)}
