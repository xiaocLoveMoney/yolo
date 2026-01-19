#!/usr/bin/env python
"""
训练脚本：在独立进程中运行YOLO训练
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

def detect_device():
    """
    自动检测并选择最佳训练设备
    优先级：NVIDIA GPU (CUDA) > Apple M芯片 GPU (MPS) > CPU
    返回设备字符串，如 'cuda', 'mps', 'cpu'
    """
    try:
        import torch
        
        # 优先级1: 检测 NVIDIA GPU (CUDA)
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_count = torch.cuda.device_count()
            print(f"[{datetime.now().isoformat()}] 检测到 NVIDIA GPU: {device_name} (共 {device_count} 个设备)")
            print(f"[{datetime.now().isoformat()}] CUDA 版本: {torch.version.cuda}")
            return "cuda"
        
        # 优先级2: 检测 Apple M芯片 GPU (MPS)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print(f"[{datetime.now().isoformat()}] 检测到 Apple M芯片 GPU (Metal Performance Shaders)")
            return "mps"
        
        # 优先级3: 使用 CPU
        print(f"[{datetime.now().isoformat()}] 未检测到 GPU，将使用 CPU 进行训练")
        return "cpu"
        
    except ImportError:
        # 如果没有安装 torch，默认使用 CPU（YOLO 会自动处理）
        print(f"[{datetime.now().isoformat()}] 警告: 无法导入 torch，将使用默认设备")
        return None
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] 设备检测时出现错误: {e}，将使用默认设备")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--imgsz", type=int, required=True)
    parser.add_argument("--batch", type=int, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--job_id", required=True)
    parser.add_argument("--job_file", required=True)
    parser.add_argument("--registry_dir", required=True)
    parser.add_argument("--resume", action="store_true", help="Resume training from last checkpoint")
    
    args = parser.parse_args()
    
    print(f"[{datetime.now().isoformat()}] Starting training job: {args.job_id}")
    print(f"[{datetime.now().isoformat()}] Dataset: {args.data}")
    print(f"[{datetime.now().isoformat()}] Model: {args.model}")
    print(f"[{datetime.now().isoformat()}] Epochs: {args.epochs}")
    print(f"[{datetime.now().isoformat()}] Image size: {args.imgsz}")
    print(f"[{datetime.now().isoformat()}] Batch size: {args.batch}")
    print(f"[{datetime.now().isoformat()}] Resume: {args.resume}")
    
    try:
        from ultralytics import YOLO
        
        # 自动检测并选择最佳训练设备
        device = detect_device()
        if device:
            print(f"[{datetime.now().isoformat()}] 选择的训练设备: {device.upper()}")
        
        train_dir = Path(args.project) / args.name
        resume_path = None
        
        # 如果是恢复训练，使用 checkpoint 路径
        if args.resume:
            if args.model.endswith("last.pt") and Path(args.model).exists():
                resume_path = args.model
                print(f"[{datetime.now().isoformat()}] Resuming from checkpoint: {resume_path}")
            else:
                last_pt = train_dir / "weights" / "last.pt"
                if last_pt.exists():
                    resume_path = str(last_pt)
                    print(f"[{datetime.now().isoformat()}] Found checkpoint: {resume_path}")
                else:
                    raise FileNotFoundError(f"No checkpoint found at {last_pt}. Cannot resume training.")
        else:
            print(f"[{datetime.now().isoformat()}] Loading model: {args.model}")
            resume_path = args.model
        
        model = YOLO(resume_path)
        
        # 使用传入的 batch size
        batch_size = args.batch
        
        # Windows 兼容性：在 Windows 上使用 workers=0 避免多进程问题
        # Windows 上的 PyTorch multiprocessing 使用 spawn 模式，需要额外内存
        # 如果页面文件不足，会导致错误 1455
        workers = 0 if os.name == 'nt' else 4  # Windows 单进程，Linux/Mac 多进程
        
        train_kwargs = {
            "data": args.data,
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "batch": batch_size,
            # "workers": 0,  # Docker 容器中设为 0，避免共享内存不足问题
            "project": args.project,
            "name": args.name,
            "verbose": True,
        }
        
        # 如果检测到设备，显式指定设备
        if device:
            train_kwargs["device"] = device
        
        print(f"[{datetime.now().isoformat()}] Using workers=0 (single process mode) to avoid shared memory issues in Docker")
        
        # 开始训练
        if args.resume:
            print(f"[{datetime.now().isoformat()}] Resuming training from checkpoint...")
            train_kwargs["resume"] = True
            results = model.train(**train_kwargs)
        else:
            print(f"[{datetime.now().isoformat()}] Starting new training...")
            results = model.train(**train_kwargs)
        
        print(f"[{datetime.now().isoformat()}] Training completed!")
        
        # 训练完成，注册模型
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_dir = Path(args.registry_dir) / model_id
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制权重文件
        weights_dir = model_dir / "weights"
        weights_dir.mkdir(exist_ok=True)
        
        train_dir = Path(args.project) / args.name
        best_pt = train_dir / "weights" / "best.pt"
        
        # 如果默认路径不存在，尝试在 project 目录下查找所有可能的 best.pt
        if not best_pt.exists():
            project_path = Path(args.project)
            # 在 project 目录下递归查找 best.pt
            possible_best_pt = None
            for candidate in project_path.rglob("best.pt"):
                # 优先选择在 weights 目录下的
                if "weights" in str(candidate.parent):
                    possible_best_pt = candidate
                    break
            
            if possible_best_pt:
                print(f"[{datetime.now().isoformat()}] Found best.pt at: {possible_best_pt}")
                best_pt = possible_best_pt
            else:
                raise FileNotFoundError(
                    f"Model weights (best.pt) not found. Expected at: {train_dir / 'weights' / 'best.pt'}. "
                    f"Please check training output in: {args.project}"
                )
        
        if best_pt.exists():
            import shutil
            shutil.copy(best_pt, weights_dir / "best.pt")
            print(f"[{datetime.now().isoformat()}] Model weights saved to {weights_dir / 'best.pt'}")
        else:
            raise FileNotFoundError(f"Model weights file not found: {best_pt}")
        
        # 读取训练配置获取类别信息
        import yaml
        with open(args.data, 'r') as f:
            data_config = yaml.safe_load(f)
        
        # 保存模型元数据（使用绝对路径）
        weights_path_abs = (weights_dir / "best.pt").resolve()
        model_meta = {
            "model_id": model_id,
            "job_id": args.job_id,
            "base_model": args.model,
            "task": "detect",
            "classes": data_config.get("names", []),
            "imgsz": args.imgsz,
            "epochs": args.epochs,
            "created_at": datetime.now().isoformat(),
            "weights_path": str(weights_path_abs)
        }
        
        with open(model_dir / "model.json", "w", encoding="utf-8") as f:
            json.dump(model_meta, f, indent=2, ensure_ascii=False)
        
        print(f"[{datetime.now().isoformat()}] Model registered as {model_id}")
        
        # 更新job状态
        with open(args.job_file, "r") as f:
            job_meta = json.load(f)
        
        job_meta["status"] = "completed"
        job_meta["completed_at"] = datetime.now().isoformat()
        job_meta["model_id"] = model_id
        
        with open(args.job_file, "w") as f:
            json.dump(job_meta, f, indent=2)
        
        print(f"[{datetime.now().isoformat()}] Job status updated")
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {str(e)}", file=sys.stderr)
        
        # 更新job状态为失败
        try:
            with open(args.job_file, "r") as f:
                job_meta = json.load(f)
            
            job_meta["status"] = "failed"
            job_meta["error"] = str(e)
            job_meta["failed_at"] = datetime.now().isoformat()
            
            with open(args.job_file, "w") as f:
                json.dump(job_meta, f, indent=2)
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
