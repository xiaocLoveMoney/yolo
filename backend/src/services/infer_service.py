import json
import os
import time
import shutil
import base64
import asyncio
import uuid
import csv
import zipfile
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator
from fastapi import UploadFile
from PIL import Image
import tempfile
import cv2
import numpy as np
from datetime import datetime
from src.core.settings import settings

class InferService:
    def __init__(self):
        self.registry_dir = settings.REGISTRY_DIR
        self.jobs_dir = settings.JOBS_DIR
        self.inference_results_dir = settings.INFERENCE_RESULTS_DIR
        self._model_cache: Dict[str, Any] = {}  # 模型缓存
    
    def _get_model(self, model_id: str):
        """获取模型（带缓存）"""
        if model_id in self._model_cache:
            return self._model_cache[model_id]
        
        model_dir = self.registry_dir / model_id
        model_file = model_dir / "model.json"
        
        if not model_file.exists():
            return None, None, "Model not found"
        
        with open(model_file, "r", encoding="utf-8") as f:
            model_meta = json.load(f)
        
        # 处理权重路径：可能是绝对路径或相对路径
        weights_path_str = model_meta.get("weights_path", "")
        if not weights_path_str:
            return None, None, "Model weights_path not found in model.json"
        
        weights_path = Path(weights_path_str)
        
        # 如果不是绝对路径，则相对于 model_dir 解析
        if not weights_path.is_absolute():
            weights_path = model_dir / weights_path
        # 如果是绝对路径，直接使用（但需要确保文件存在）
        
        # 尝试解析路径（处理可能的符号链接等）
        weights_path = weights_path.resolve()
        
        if not weights_path.exists():
            # 提供更详细的错误信息，包括尝试的路径
            error_msg = f"Model weights not found. Expected path: {weights_path}"
            
            # 尝试查找可能的备用位置
            possible_locations = [
                model_dir / "weights" / "best.pt",
                model_dir / "best.pt",
                model_dir / "weights" / weights_path.name if weights_path.name else None
            ]
            
            # 如果模型有 job_id，尝试从训练任务目录查找权重文件
            job_id = model_meta.get("job_id")
            if job_id:
                job_dir = self.jobs_dir / job_id
                if job_dir.exists():
                    # 在 job 目录下递归查找 best.pt
                    for candidate in job_dir.rglob("best.pt"):
                        if "weights" in str(candidate.parent):
                            possible_locations.append(candidate)
                            # 尝试自动修复：复制权重文件到正确位置
                            try:
                                target_dir = model_dir / "weights"
                                target_dir.mkdir(parents=True, exist_ok=True)
                                target_file = target_dir / "best.pt"
                                if not target_file.exists():
                                    shutil.copy(candidate, target_file)
                                    print(f"Auto-fixed: Copied weights from {candidate} to {target_file}")
                                    # 更新 model.json 中的路径
                                    model_meta["weights_path"] = str(target_file.resolve())
                                    with open(model_file, "w", encoding="utf-8") as f:
                                        json.dump(model_meta, f, indent=2, ensure_ascii=False)
                                    weights_path = target_file
                                    break
                                else:
                                    # 文件已存在，直接使用
                                    weights_path = target_file
                                    break
                            except Exception as e:
                                print(f"Warning: Failed to auto-fix weights path: {e}")
                                # 如果复制失败，至少尝试使用找到的文件
                                if candidate.exists():
                                    weights_path = candidate
                                    break
            
            # 检查所有可能的备用位置
            found = False
            for loc in possible_locations:
                if loc and loc.exists():
                    error_msg += f" (Found at: {loc})"
                    weights_path = loc
                    found = True
                    break
            
            if not found:
                return None, None, error_msg
        
        from ultralytics import YOLO
        model = YOLO(str(weights_path))
        
        self._model_cache[model_id] = (model, model_meta, None)
        return model, model_meta, None
    
    async def infer(self, model_id: str, file: UploadFile):
        """执行推理"""
        model, model_meta, error = self._get_model(model_id)
        if error:
            return {"error": error}
        
        # 保存上传的图片到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 获取图片尺寸 (使用 with 确保文件正确关闭)
            with Image.open(tmp_path) as img:
                image_width, image_height = img.size
            
            results = model(tmp_path, verbose=False)
            
            # 解析结果
            detections = self._parse_results(results, model_meta)
            
            return {
                "model_id": model_id,
                "detections": detections,
                "image_width": image_width,
                "image_height": image_height
            }
        
        except Exception as e:
            return {"error": str(e)}
        
        finally:
            self._cleanup_temp_file(tmp_path)
    
    async def batch_infer(self, model_ids: List[str], files: List[UploadFile]):
        """批量推理：支持多模型、多图片"""
        results = []
        temp_files = []
        
        try:
            # 先保存所有图片到临时文件
            image_infos = []
            for file in files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name
                    temp_files.append(tmp_path)
                
                # 获取图片尺寸
                with Image.open(tmp_path) as img:
                    image_width, image_height = img.size
                
                image_infos.append({
                    "filename": file.filename,
                    "path": tmp_path,
                    "width": image_width,
                    "height": image_height
                })
            
            # 对每个模型进行推理
            for model_id in model_ids:
                model, model_meta, error = self._get_model(model_id)
                
                if error:
                    results.append({
                        "model_id": model_id,
                        "error": error,
                        "images": []
                    })
                    continue
                
                model_results = {
                    "model_id": model_id,
                    "model_name": model_meta.get("base_model", model_id),
                    "classes": model_meta.get("classes", []),
                    "images": []
                }
                
                # 对每张图片进行推理
                for img_info in image_infos:
                    try:
                        infer_results = model(img_info["path"], verbose=False)
                        detections = self._parse_results(infer_results, model_meta)
                        
                        model_results["images"].append({
                            "filename": img_info["filename"],
                            "image_width": img_info["width"],
                            "image_height": img_info["height"],
                            "detections": detections,
                            "detection_count": len(detections)
                        })
                    except Exception as e:
                        model_results["images"].append({
                            "filename": img_info["filename"],
                            "error": str(e),
                            "detections": []
                        })
                
                results.append(model_results)
            
            return {
                "results": results,
                "total_models": len(model_ids),
                "total_images": len(files)
            }
        
        except Exception as e:
            return {"error": str(e)}
        
        finally:
            # 清理所有临时文件
            for tmp_path in temp_files:
                self._cleanup_temp_file(tmp_path)
    
    def _parse_results(self, results, model_meta):
        """解析推理结果"""
        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                box = boxes[i]
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                
                classes = model_meta.get("classes", [])
                class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                
                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "conf": conf,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                })
        return detections
    
    def _cleanup_temp_file(self, tmp_path: str):
        """清理临时文件"""
        try:
            time.sleep(0.1)
            os.remove(tmp_path)
        except Exception:
            pass
    
    async def infer_video(self, model_id: str, file: UploadFile, conf_threshold: float = 0.25):
        """视频推理：返回处理后的视频文件"""
        model, model_meta, error = self._get_model(model_id)
        if error:
            return {"error": error}
        
        # 确定视频后缀
        original_filename = file.filename or "video.mp4"
        suffix = Path(original_filename).suffix or ".mp4"
        
        # 保存上传的视频到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            input_path = tmp.name
        
        # 输出视频路径
        output_path = tempfile.mktemp(suffix=".mp4")
        
        try:
            # 打开视频
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return {"error": "无法打开视频文件"}
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            classes = model_meta.get("classes", [])
            frame_count = 0
            all_detections = []
            
            # 处理每一帧
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 使用YOLO进行推理
                results = model(frame, verbose=False, conf=conf_threshold)
                
                # 绘制检测框
                frame_detections = []
                for result in results:
                    boxes = result.boxes
                    for i in range(len(boxes)):
                        box = boxes[i]
                        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                        conf = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                        
                        # 绘制边界框
                        color = self._get_color(class_id)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制标签
                        label = f"{class_name}: {conf:.2f}"
                        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                    (x1 + label_size[0], y1), color, -1)
                        cv2.putText(frame, label, (x1, y1 - 5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        frame_detections.append({
                            "class_id": class_id,
                            "class_name": class_name,
                            "conf": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
                
                all_detections.append({
                    "frame": frame_count,
                    "detections": frame_detections
                })
                
                # 写入处理后的帧
                out.write(frame)
            
            cap.release()
            out.release()
            
            # 读取输出视频为base64
            with open(output_path, "rb") as f:
                video_data = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "model_id": model_id,
                "video_data": video_data,
                "video_info": {
                    "fps": fps,
                    "width": width,
                    "height": height,
                    "total_frames": total_frames,
                    "processed_frames": frame_count
                },
                "summary": {
                    "total_detections": sum(len(f["detections"]) for f in all_detections),
                    "frames_with_detections": sum(1 for f in all_detections if f["detections"])
                }
            }
        
        except Exception as e:
            return {"error": str(e)}
        
        finally:
            self._cleanup_temp_file(input_path)
            self._cleanup_temp_file(output_path)
    
    async def infer_video_stream(self, model_id: str, file: UploadFile, conf_threshold: float = 0.25) -> AsyncGenerator:
        """视频推理流式接口：逐帧返回结果"""
        model, model_meta, error = self._get_model(model_id)
        if error:
            yield f"data: {json.dumps({'error': error})}\n\n"
            return
        
        # 确定视频后缀
        original_filename = file.filename or "video.mp4"
        suffix = Path(original_filename).suffix or ".mp4"
        
        # 保存上传的视频到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            input_path = tmp.name
        
        try:
            # 打开视频
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                yield f"data: {json.dumps({'error': '无法打开视频文件'})}\n\n"
                return
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 发送视频信息
            yield f"data: {json.dumps({'type': 'info', 'fps': fps, 'width': width, 'height': height, 'total_frames': total_frames})}\n\n"
            
            classes = model_meta.get("classes", [])
            frame_count = 0
            
            # 处理每一帧
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 使用YOLO进行推理
                results = model(frame, verbose=False, conf=conf_threshold)
                
                # 解析检测结果
                frame_detections = []
                for result in results:
                    boxes = result.boxes
                    for i in range(len(boxes)):
                        box = boxes[i]
                        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                        conf = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                        
                        # 绘制边界框到帧上
                        color = self._get_color(class_id)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制标签
                        label = f"{class_name}: {conf:.2f}"
                        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                    (x1 + label_size[0], y1), color, -1)
                        cv2.putText(frame, label, (x1, y1 - 5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        frame_detections.append({
                            "class_id": class_id,
                            "class_name": class_name,
                            "conf": conf,
                            "bbox": [x1, y1, x2, y2]
                        })
                
                # 将帧编码为JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # 发送帧数据
                yield f"data: {json.dumps({'type': 'frame', 'frame_number': frame_count, 'frame_data': frame_base64, 'detections': frame_detections})}\n\n"
                
                # 控制帧率，避免处理过快
                await asyncio.sleep(0.01)
            
            cap.release()
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'processed_frames': frame_count})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        finally:
            self._cleanup_temp_file(input_path)
    
    def _get_color(self, class_id: int) -> tuple:
        """根据类别ID生成颜色"""
        colors = [
            (0, 255, 0),    # 绿色
            (255, 0, 0),    # 蓝色
            (0, 0, 255),    # 红色
            (255, 255, 0),  # 青色
            (255, 0, 255),  # 洋红色
            (0, 255, 255),  # 黄色
            (128, 0, 255),  # 紫色
            (255, 128, 0),  # 橙色
            (0, 128, 255),  # 橙黄色
            (255, 0, 128),  # 粉色
        ]
        return colors[class_id % len(colors)]
    
    async def infer_and_save(self, model_id: str, files: List[UploadFile], save_results: bool = True):
        """推理并保存结果图片，生成UUID和CSV"""
        model, model_meta, error = self._get_model(model_id)
        if error:
            return {"error": error}
        
        # 创建会话目录
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        session_dir = self.inference_results_dir / session_id
        images_dir = session_dir / "images"
        
        await asyncio.to_thread(lambda: images_dir.mkdir(parents=True, exist_ok=True))
        
        results_data = []
        temp_files = []
        
        try:
            for file in files:
                # 保存上传的图片到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name
                    temp_files.append(tmp_path)
                
                # 获取图片尺寸
                with Image.open(tmp_path) as img:
                    image_width, image_height = img.size
                    img_array = np.array(img)
                
                # 执行推理
                infer_results = model(tmp_path, verbose=False)
                detections = self._parse_results(infer_results, model_meta)
                
                # 生成UUID
                image_uuid = str(uuid.uuid4())
                
                # 如果需要保存结果
                if save_results:
                    # 在图片上绘制检测框
                    img_with_boxes = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    for det in detections:
                        x1, y1, x2, y2 = int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])
                        class_id = det['class_id']
                        class_name = det['class_name']
                        conf = det['conf']
                        
                        # 绘制边界框
                        color = self._get_color(class_id)
                        cv2.rectangle(img_with_boxes, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制标签
                        label = f"{class_name}: {conf:.2f}"
                        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(img_with_boxes, (x1, y1 - label_size[1] - 10),
                                    (x1 + label_size[0], y1), color, -1)
                        cv2.putText(img_with_boxes, label, (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # 保存结果图片
                    result_image_path = images_dir / f"{image_uuid}.jpg"
                    cv2.imwrite(str(result_image_path), img_with_boxes)
                
                # 记录结果
                results_data.append({
                    "image_uuid": image_uuid,
                    "image_filename": file.filename,
                    "model_id": model_id,
                    "image_width": image_width,
                    "image_height": image_height,
                    "detection_count": len(detections),
                    "detections": detections
                })
            
            # 生成CSV文件
            if save_results and results_data:
                csv_path = session_dir / "results.csv"
                
                def _write_csv():
                    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                        # CSV包含扁平化的检测结果
                        fieldnames = ['image_uuid', 'image_filename', 'model_id', 'image_width', 
                                    'image_height', 'detection_count', 'detection_index', 
                                    'class_id', 'class_name', 'confidence', 'x1', 'y1', 'x2', 'y2']
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for result in results_data:
                            if result['detections']:
                                for idx, det in enumerate(result['detections']):
                                    writer.writerow({
                                        'image_uuid': result['image_uuid'],
                                        'image_filename': result['image_filename'],
                                        'model_id': result['model_id'],
                                        'image_width': result['image_width'],
                                        'image_height': result['image_height'],
                                        'detection_count': result['detection_count'],
                                        'detection_index': idx,
                                        'class_id': det['class_id'],
                                        'class_name': det['class_name'],
                                        'confidence': det['conf'],
                                        'x1': det['x1'],
                                        'y1': det['y1'],
                                        'x2': det['x2'],
                                        'y2': det['y2']
                                    })
                            else:
                                # 没有检测结果的图片也记录一行
                                writer.writerow({
                                    'image_uuid': result['image_uuid'],
                                    'image_filename': result['image_filename'],
                                    'model_id': result['model_id'],
                                    'image_width': result['image_width'],
                                    'image_height': result['image_height'],
                                    'detection_count': 0,
                                    'detection_index': '',
                                    'class_id': '',
                                    'class_name': '',
                                    'confidence': '',
                                    'x1': '',
                                    'y1': '',
                                    'x2': '',
                                    'y2': ''
                                })
                
                await asyncio.to_thread(_write_csv)
                
                # 生成元数据JSON
                metadata = {
                    "session_id": session_id,
                    "model_id": model_id,
                    "created_at": datetime.now().isoformat(),
                    "total_images": len(results_data),
                    "total_detections": sum(r['detection_count'] for r in results_data)
                }
                
                metadata_path = session_dir / "metadata.json"
                
                def _write_metadata():
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                await asyncio.to_thread(_write_metadata)
            
            return {
                "session_id": session_id,
                "results": results_data,
                "session_dir": str(session_dir) if save_results else None
            }
        
        except Exception as e:
            return {"error": str(e)}
        
        finally:
            # 清理临时文件
            for tmp_path in temp_files:
                self._cleanup_temp_file(tmp_path)
    
    async def export_inference_results(self, session_id: str):
        """导出推理结果为ZIP文件"""
        session_dir = self.inference_results_dir / session_id
        
        if not await asyncio.to_thread(lambda: session_dir.exists()):
            return None
        
        # 创建临时ZIP文件
        def _create_zip():
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加所有文件
                for item in session_dir.rglob("*"):
                    if item.is_file():
                        arcname = item.relative_to(session_dir)
                        zipf.write(item, arcname)
            
            return temp_zip_path
        
        zip_path = await asyncio.to_thread(_create_zip)
        return zip_path
