import json
import os
import subprocess
import signal
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from src.core.settings import settings


def _load_json(path: Path):
    """同步加载 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    """同步保存 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _delete_file(path: Path):
    """同步删除文件"""
    if path.exists():
        path.unlink()


def _delete_directory(path: Path):
    """同步删除目录"""
    if path.exists():
        shutil.rmtree(path)


class TrainService:
    def __init__(self):
        self.jobs_dir = settings.JOBS_DIR
        self.datasets_dir = settings.DATASETS_DIR
        self.registry_dir = settings.REGISTRY_DIR
        self.running_processes = {}
    
    async def create_job(self, dataset_id: str, version: str, model_name: str, 
                         epochs: int, imgsz: int, batch: int, base_model_id: str = None):
        """创建训练任务"""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 检查数据集
        dataset_dir = self.datasets_dir / dataset_id / version
        data_yaml = dataset_dir / "data.yaml"
        
        if not await asyncio.to_thread(lambda: data_yaml.exists()):
            raise ValueError(f"Dataset {dataset_id}/{version} not prepared")
        
        # 处理模型路径：如果提供了 base_model_id，使用已有模型的权重
        actual_model_path = model_name
        if base_model_id:
            base_model_dir = self.registry_dir / base_model_id
            base_model_file = base_model_dir / "model.json"
            if not await asyncio.to_thread(lambda: base_model_file.exists()):
                raise ValueError(f"Base model {base_model_id} not found")
            
            base_model_meta = await asyncio.to_thread(_load_json, base_model_file)
            
            weights_path = Path(base_model_meta["weights_path"])
            if not await asyncio.to_thread(lambda: weights_path.exists()):
                raise ValueError(f"Base model weights not found: {weights_path}")
            
            actual_model_path = str(weights_path)
            model_name = f"{base_model_id}_fine_tuned"
        
        # 创建job元数据
        job_meta = {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "version": version,
            "model_name": model_name,
            "base_model_id": base_model_id,
            "original_model_path": actual_model_path,  # 保存原始模型路径，用于恢复
            "epochs": epochs,
            "imgsz": imgsz,
            "batch": batch,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "log_file": str(self.jobs_dir / f"{job_id}.log")
        }
        
        job_file = self.jobs_dir / f"{job_id}.json"
        await asyncio.to_thread(_save_json, job_file, job_meta)
        
        # 启动训练进程（在线程中执行）
        await asyncio.to_thread(
            self._start_training, job_id, data_yaml, actual_model_path, epochs, imgsz, batch, False
        )
        
        return {"job_id": job_id, "status": "running"}
    
    def _start_training(self, job_id: str, data_yaml: Path, model_name: str,
                       epochs: int, imgsz: int, batch: int, resume: bool = False):
        """启动训练进程（同步方法，在线程中调用）"""
        log_file = self.jobs_dir / f"{job_id}.log"
        job_file = self.jobs_dir / f"{job_id}.json"
        
        # 准备训练脚本
        train_script = settings.BASE_DIR / "src" / "yolo" / "train_script.py"
        
        # 输出目录
        project_dir = self.jobs_dir / job_id
        
        # 启动子进程
        cmd = [
            "python", str(train_script),
            "--data", str(data_yaml),
            "--model", model_name,
            "--epochs", str(epochs),
            "--imgsz", str(imgsz),
            "--batch", str(batch),
            "--project", str(project_dir),
            "--name", "train",
            "--job_id", job_id,
            "--job_file", str(job_file),
            "--registry_dir", str(self.registry_dir)
        ]
        
        if resume:
            cmd.append("--resume")
        
        # 如果是恢复训练，追加日志而不是覆盖
        mode = "a" if resume else "w"
        
        # 使用 UTF-8 编码打开日志文件，确保编码正确
        with open(log_file, mode, encoding="utf-8", errors="replace") as f:
            # 设置环境变量确保 Python 进程输出 UTF-8 编码
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=settings.BASE_DIR,
                env=env
            )
        
        self.running_processes[job_id] = process
    
    async def list_jobs(self):
        """列出所有训练任务（自动检测崩溃的任务）"""
        def _list_jobs_sync():
            jobs = []
            
            if not self.jobs_dir.exists():
                return jobs
            
            for job_file in self.jobs_dir.glob("*.json"):
                try:
                    job_meta = _load_json(job_file)
                except Exception:
                    continue
                
                # 检查是否有运行中的任务实际已崩溃
                job_id = job_meta.get("job_id")
                if job_id and job_meta.get("status") == "running":
                    # 检查进程是否真的在运行
                    if job_id in self.running_processes:
                        process = self.running_processes[job_id]
                        if process.poll() is not None:
                            # 进程已死，但状态还是 running，标记为崩溃
                            job_meta["status"] = "crashed"
                            job_meta["crashed_at"] = datetime.now().isoformat()
                            # 清理进程记录
                            del self.running_processes[job_id]
                            # 保存更新后的状态
                            _save_json(job_file, job_meta)
                    else:
                        # 不在运行进程列表中，但状态是 running，可能是崩溃后重启
                        # 检查是否有 checkpoint，如果有则标记为可恢复
                        train_dir = self.jobs_dir / job_id / "train"
                        checkpoint = train_dir / "weights" / "last.pt"
                        if checkpoint.exists():
                            job_meta["status"] = "crashed"
                            job_meta["crashed_at"] = datetime.now().isoformat()
                            _save_json(job_file, job_meta)
                
                # 检查是否有 checkpoint 但状态不是可恢复状态
                train_dir = self.jobs_dir / job_id / "train"
                checkpoint = train_dir / "weights" / "last.pt"
                best_pt = train_dir / "weights" / "best.pt"
                # 如果有 last.pt 或 best.pt，标记为可恢复
                if (checkpoint.exists() or best_pt.exists()) and job_meta.get("status") not in ["completed", "running"]:
                    # 标记为可恢复
                    if "can_resume" not in job_meta:
                        job_meta["can_resume"] = True
                        # 保存更新
                        _save_json(job_file, job_meta)
                
                jobs.append(job_meta)
            
            return jobs
        
        jobs = await asyncio.to_thread(_list_jobs_sync)
        return {"jobs": sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)}
    
    async def get_job(self, job_id: str):
        """获取训练任务详情"""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        if not await asyncio.to_thread(lambda: job_file.exists()):
            return None
        
        return await asyncio.to_thread(_load_json, job_file)
    
    async def stop_job(self, job_id: str):
        """停止训练任务"""
        if job_id in self.running_processes:
            process = self.running_processes[job_id]
            try:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)
            except:
                process.kill()
            
            del self.running_processes[job_id]
            
            # 更新状态
            job_file = self.jobs_dir / f"{job_id}.json"
            
            def _update_status():
                if job_file.exists():
                    job_meta = _load_json(job_file)
                    job_meta["status"] = "stopped"
                    job_meta["stopped_at"] = datetime.now().isoformat()
                    _save_json(job_file, job_meta)
            
            await asyncio.to_thread(_update_status)
            
            return {"ok": True}
        
        return {"ok": False, "error": "Job not running"}
    
    async def delete_job(self, job_id: str):
        """删除训练任务"""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        if not await asyncio.to_thread(lambda: job_file.exists()):
            return None
        
        # 先停止任务（如果正在运行）
        if job_id in self.running_processes:
            try:
                await self.stop_job(job_id)
            except Exception as e:
                # 停止失败不影响删除，记录错误但继续
                print(f"Warning: Failed to stop job {job_id}: {e}")
        
        def _delete_job_files():
            errors = []
            
            # 删除任务文件
            try:
                _delete_file(job_file)
            except Exception as e:
                errors.append(f"Failed to delete job file: {e}")
            
            # 删除日志文件
            log_file = self.jobs_dir / f"{job_id}.log"
            try:
                _delete_file(log_file)
            except Exception as e:
                errors.append(f"Failed to delete log file: {e}")
            
            # 删除训练输出目录
            train_dir = self.jobs_dir / job_id
            try:
                _delete_directory(train_dir)
            except Exception as e:
                errors.append(f"Failed to delete train directory: {e}")
            
            # 如果有错误，但不影响主要删除操作（文件可能已经被删除或不存在）
            if errors:
                print(f"Warning: Some errors occurred while deleting job {job_id}: {errors}")
            
            return errors
        
        # 执行删除操作（忽略部分文件删除失败的错误）
        await asyncio.to_thread(_delete_job_files)
        
        return {"ok": True, "message": f"Job {job_id} deleted"}
    
    async def resume_job(self, job_id: str):
        """继续训练中断的任务（支持正常停止和崩溃恢复）"""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        if not await asyncio.to_thread(lambda: job_file.exists()):
            raise ValueError(f"Job {job_id} not found")
        
        job_meta = await asyncio.to_thread(_load_json, job_file)
        
        # 检查是否有训练输出目录和 checkpoint
        train_dir = self.jobs_dir / job_id / "train"
        checkpoint = train_dir / "weights" / "last.pt"
        best_pt = train_dir / "weights" / "best.pt"
        
        # 检查 checkpoint 是否存在
        def _check_checkpoints():
            return checkpoint.exists(), best_pt.exists()
        
        checkpoint_exists, best_pt_exists = await asyncio.to_thread(_check_checkpoints)
        
        model_to_use = None
        use_resume = False
        
        if checkpoint_exists:
            # 有 last.pt，可以正常恢复
            model_to_use = str(checkpoint)
            use_resume = True
        elif best_pt_exists:
            # 有 best.pt，可以使用它继续训练
            model_to_use = str(best_pt)
            use_resume = False
        else:
            # 没有 checkpoint，尝试从原始模型重新开始
            original_model_path = job_meta.get("original_model_path")
            base_model_id = job_meta.get("base_model_id")
            
            if base_model_id:
                # 如果是微调任务，从基础模型重新开始
                base_model_dir = self.registry_dir / base_model_id
                base_model_file = base_model_dir / "model.json"
                if await asyncio.to_thread(lambda: base_model_file.exists()):
                    base_model_meta = await asyncio.to_thread(_load_json, base_model_file)
                    weights_path = Path(base_model_meta["weights_path"])
                    if await asyncio.to_thread(lambda: weights_path.exists()):
                        model_to_use = str(weights_path)
                        use_resume = False
                        print(f"Warning: No checkpoint found, restarting from base model {base_model_id}")
                    else:
                        raise ValueError(
                            f"No checkpoint found and base model weights not found. "
                            f"Cannot resume training. Please start a new training job."
                        )
                else:
                    raise ValueError(
                        f"No checkpoint found and base model {base_model_id} not found. "
                        f"Cannot resume training. Please start a new training job."
                    )
            elif original_model_path:
                # 从原始模型路径重新开始
                original_exists = await asyncio.to_thread(lambda: Path(original_model_path).exists())
                if original_exists or original_model_path.endswith('.pt'):
                    # 如果是预训练模型名称（如 yolov8n.pt），YOLO 会自动下载
                    model_to_use = original_model_path
                    use_resume = False
                    print(f"Warning: No checkpoint found, restarting from original model {original_model_path}")
                else:
                    raise ValueError(
                        f"No checkpoint found and original model path invalid: {original_model_path}. "
                        f"Cannot resume training. Please start a new training job."
                    )
            else:
                # 尝试使用 model_name（可能是预训练模型）
                model_name = job_meta.get("model_name", "yolov8n.pt")
                if model_name.endswith('.pt'):
                    model_to_use = model_name
                    use_resume = False
                    print(f"Warning: No checkpoint found, restarting from model {model_name}")
                else:
                    raise ValueError(
                        f"No checkpoint found for job {job_id}. "
                        f"The training was stopped before completing any epoch. "
                        f"Cannot resume training. Please start a new training job."
                    )
        
        # 检查数据集
        dataset_dir = self.datasets_dir / job_meta["dataset_id"] / job_meta["version"]
        data_yaml = dataset_dir / "data.yaml"
        
        if not await asyncio.to_thread(lambda: data_yaml.exists()):
            raise ValueError(f"Dataset {job_meta['dataset_id']}/{job_meta['version']} not found")
        
        # 检查任务是否正在运行（防止重复启动）
        if job_id in self.running_processes:
            process = self.running_processes[job_id]
            # 检查进程是否真的在运行
            if process.poll() is None:
                raise ValueError(f"Job {job_id} is already running")
            else:
                # 进程已结束但未清理，清理它
                del self.running_processes[job_id]
        
        # 记录原始状态（用于判断是否是崩溃恢复）
        original_status = job_meta.get("status")
        was_crashed = original_status == "running" and job_meta.get("resume_count", 0) == 0
        
        # 更新任务状态
        job_meta["status"] = "running"
        job_meta["resumed_at"] = datetime.now().isoformat()
        job_meta["resume_count"] = job_meta.get("resume_count", 0) + 1
        
        # 如果之前是崩溃（状态为 running 但进程已死），记录崩溃恢复
        if was_crashed:
            job_meta["crashed"] = True
            if "crashed_at" not in job_meta:
                job_meta["crashed_at"] = datetime.now().isoformat()
        
        await asyncio.to_thread(_save_json, job_file, job_meta)
        
        # 启动训练进程
        await asyncio.to_thread(
            self._start_training,
            job_id, 
            data_yaml, 
            model_to_use,
            job_meta["epochs"],
            job_meta["imgsz"],
            job_meta["batch"],
            use_resume
        )
        
        return {"job_id": job_id, "status": "running", "message": "Training resumed from checkpoint"}
