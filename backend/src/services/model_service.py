import json
import shutil
import csv
import os
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


def _delete_directory(path: Path):
    """同步删除目录"""
    shutil.rmtree(path)


class ModelService:
    def __init__(self):
        self.registry_dir = settings.REGISTRY_DIR
        self.jobs_dir = settings.JOBS_DIR
    
    async def list_models(self):
        """列出所有模型"""
        def _list_models_sync():
            models = []
            
            if not self.registry_dir.exists():
                return models
            
            for model_dir in self.registry_dir.iterdir():
                if model_dir.is_dir():
                    model_file = model_dir / "model.json"
                    if model_file.exists():
                        try:
                            model_meta = _load_json(model_file)
                            # 添加模型文件大小
                            weights_path = model_meta.get("weights_path")
                            if weights_path and Path(weights_path).exists():
                                model_meta["file_size"] = os.path.getsize(weights_path)
                                model_meta["file_size_mb"] = round(model_meta["file_size"] / (1024 * 1024), 2)
                            models.append(model_meta)
                        except Exception:
                            continue
            
            return models
        
        models = await asyncio.to_thread(_list_models_sync)
        return {"models": sorted(models, key=lambda x: x.get("created_at", ""), reverse=True)}
    
    async def get_model(self, model_id: str):
        """获取模型详情（包含训练指标）"""
        model_dir = self.registry_dir / model_id
        model_file = model_dir / "model.json"
        
        if not await asyncio.to_thread(lambda: model_file.exists()):
            return None
        
        model_meta = await asyncio.to_thread(_load_json, model_file)
        
        # 添加模型文件大小
        def _get_file_size():
            weights_path = model_meta.get("weights_path")
            if weights_path and Path(weights_path).exists():
                return os.path.getsize(weights_path)
            return None
        
        file_size = await asyncio.to_thread(_get_file_size)
        if file_size:
            model_meta["file_size"] = file_size
            model_meta["file_size_mb"] = round(file_size / (1024 * 1024), 2)
        
        # 尝试加载训练指标
        job_id = model_meta.get("job_id")
        if job_id:
            training_metrics = await self._load_training_metrics(job_id)
            if training_metrics:
                model_meta["training_metrics"] = training_metrics
        
        # 尝试获取模型参数信息
        model_info = await self._get_model_info(model_meta.get("weights_path"))
        if model_info:
            model_meta["model_info"] = model_info
        
        return model_meta
    
    async def _load_training_metrics(self, job_id: str):
        """从训练任务加载训练指标"""
        job_dir = self.jobs_dir / job_id
        
        if not await asyncio.to_thread(lambda: job_dir.exists()):
            return None
        
        def _load_metrics_sync():
            metrics = {}
            
            # 尝试读取 results.csv（YOLO 训练输出）
            # 查找 train 目录下的 results.csv
            results_files = list(job_dir.rglob("results.csv"))
            if results_files:
                results_csv = results_files[0]
                try:
                    metrics["training_history"] = self._parse_results_csv(results_csv)
                except Exception as e:
                    print(f"Error parsing results.csv: {e}")
            
            # 读取训练任务配置
            job_file = job_dir / "job.json"
            if job_file.exists():
                try:
                    job_meta = _load_json(job_file)
                    metrics["job_config"] = {
                        "dataset_id": job_meta.get("dataset_id"),
                        "epochs": job_meta.get("epochs"),
                        "imgsz": job_meta.get("imgsz"),
                        "batch": job_meta.get("batch"),
                        "model_name": job_meta.get("model_name"),
                        "status": job_meta.get("status"),
                        "created_at": job_meta.get("created_at"),
                        "completed_at": job_meta.get("completed_at")
                    }
                except Exception as e:
                    print(f"Error reading job.json: {e}")
            
            return metrics if metrics else None
        
        return await asyncio.to_thread(_load_metrics_sync)
    
    def _parse_results_csv(self, csv_path: Path):
        """解析 YOLO 训练输出的 results.csv（同步方法，在线程中调用）"""
        history = {
            "epochs": [],
            "train_box_loss": [],
            "train_cls_loss": [],
            "train_dfl_loss": [],
            "val_box_loss": [],
            "val_cls_loss": [],
            "val_dfl_loss": [],
            "metrics_precision": [],
            "metrics_recall": [],
            "metrics_mAP50": [],
            "metrics_mAP50_95": []
        }
        
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 清理列名（去除空格）
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    epoch = int(row.get("epoch", len(history["epochs"]) + 1))
                    history["epochs"].append(epoch)
                    
                    # 训练损失
                    if "train/box_loss" in row:
                        history["train_box_loss"].append(float(row["train/box_loss"]))
                    if "train/cls_loss" in row:
                        history["train_cls_loss"].append(float(row["train/cls_loss"]))
                    if "train/dfl_loss" in row:
                        history["train_dfl_loss"].append(float(row["train/dfl_loss"]))
                    
                    # 验证损失
                    if "val/box_loss" in row:
                        history["val_box_loss"].append(float(row["val/box_loss"]))
                    if "val/cls_loss" in row:
                        history["val_cls_loss"].append(float(row["val/cls_loss"]))
                    if "val/dfl_loss" in row:
                        history["val_dfl_loss"].append(float(row["val/dfl_loss"]))
                    
                    # 指标
                    if "metrics/precision(B)" in row:
                        history["metrics_precision"].append(float(row["metrics/precision(B)"]))
                    if "metrics/recall(B)" in row:
                        history["metrics_recall"].append(float(row["metrics/recall(B)"]))
                    if "metrics/mAP50(B)" in row:
                        history["metrics_mAP50"].append(float(row["metrics/mAP50(B)"]))
                    if "metrics/mAP50-95(B)" in row:
                        history["metrics_mAP50_95"].append(float(row["metrics/mAP50-95(B)"]))
            
            # 清理空列表
            history = {k: v for k, v in history.items() if v}
            
            # 添加最终指标摘要
            if history.get("metrics_mAP50"):
                history["final_metrics"] = {
                    "mAP50": history["metrics_mAP50"][-1] if history["metrics_mAP50"] else None,
                    "mAP50_95": history["metrics_mAP50_95"][-1] if history.get("metrics_mAP50_95") else None,
                    "precision": history["metrics_precision"][-1] if history.get("metrics_precision") else None,
                    "recall": history["metrics_recall"][-1] if history.get("metrics_recall") else None
                }
            
            return history
            
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            return None
    
    async def _get_model_info(self, weights_path: str):
        """获取模型参数信息"""
        if not weights_path:
            return None
        
        if not await asyncio.to_thread(lambda: Path(weights_path).exists()):
            return None
        
        def _get_model_info_sync():
            try:
                from ultralytics import YOLO
                model = YOLO(weights_path)
                
                # 获取模型信息
                info = {
                    "task": model.task,
                    "model_type": model.model.yaml.get("yaml_file", "unknown") if hasattr(model.model, "yaml") else "unknown"
                }
                
                # 尝试获取参数数量
                if hasattr(model.model, "model"):
                    total_params = sum(p.numel() for p in model.model.model.parameters())
                    trainable_params = sum(p.numel() for p in model.model.model.parameters() if p.requires_grad)
                    info["total_params"] = total_params
                    info["trainable_params"] = trainable_params
                    info["total_params_m"] = round(total_params / 1e6, 2)  # 百万参数
                
                return info
                
            except Exception as e:
                print(f"Error getting model info: {e}")
                return None
        
        return await asyncio.to_thread(_get_model_info_sync)
    
    async def update_model(self, model_id: str, request):
        """更新模型信息"""
        model_dir = self.registry_dir / model_id
        model_file = model_dir / "model.json"
        
        if not await asyncio.to_thread(lambda: model_file.exists()):
            return None
        
        def _update_model_sync():
            model_meta = _load_json(model_file)
            
            # 更新字段
            if request.name is not None:
                model_meta["name"] = request.name
            if request.description is not None:
                model_meta["description"] = request.description
            if request.tags is not None:
                model_meta["tags"] = request.tags
            
            model_meta["updated_at"] = datetime.now().isoformat()
            
            _save_json(model_file, model_meta)
            
            return model_meta
        
        return await asyncio.to_thread(_update_model_sync)
    
    async def delete_model(self, model_id: str):
        """删除模型"""
        model_dir = self.registry_dir / model_id
        
        if not await asyncio.to_thread(lambda: model_dir.exists()):
            return None
        
        # 删除模型目录
        await asyncio.to_thread(_delete_directory, model_dir)
        
        return {"ok": True, "message": f"Model {model_id} deleted"}
