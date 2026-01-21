import json
import zipfile
import shutil
import asyncio
import yaml
import os
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from src.core.settings import settings

logger = logging.getLogger(__name__)


def _load_json(path: Path):
    """同步加载 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: dict):
    """同步保存 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_yaml(path: Path):
    """同步加载 YAML 文件"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_yaml(path: Path, data: dict):
    """同步保存 YAML 文件"""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _write_bytes(path: Path, content: bytes):
    """同步写入二进制文件"""
    with open(path, "wb") as f:
        f.write(content)


def _ensure_long_path(path_str: str) -> str:
    """确保路径支持 Windows 长路径（超过 260 字符）
    
    在 Windows 上，如果路径超过 260 字符，需要使用 \\?\ 前缀
    """
    if os.name == 'nt' and len(path_str) > 260:
        if not path_str.startswith('\\\\?\\'):
            # 统一路径格式并转换为绝对路径
            normalized_path = os.path.abspath(os.path.normpath(path_str))
            # 如果是 UNC 路径 (\\server\share)，需要使用 \\?\UNC\ 前缀
            if normalized_path.startswith('\\\\'):
                if not normalized_path.startswith('\\\\?\\'):
                    path_str = '\\\\?\\UNC\\' + normalized_path[2:]
            else:
                path_str = '\\\\?\\' + normalized_path
    return path_str


def _extract_zip(zip_path: Path, extract_to: Path):
    """同步解压 ZIP 文件
    
    修复 Windows 长路径问题：手动创建目录并提取文件
    """
    # 确保目标目录存在
    extract_to_str = _ensure_long_path(str(extract_to.absolute()))
    os.makedirs(extract_to_str, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # 获取所有文件列表
        file_list = zip_ref.namelist()
        logger.info(f"Extracting {len(file_list)} files from {zip_path.name}")
        
        extracted_count = 0
        error_count = 0
        
        for member in file_list:
            try:
                # 安全地处理路径（防止路径遍历攻击）
                member_path = Path(member)
                # 跳过绝对路径或包含 .. 的路径
                if member_path.is_absolute() or '..' in str(member_path):
                    logger.warning(f"Skipping unsafe path: {member}")
                    continue
                
                # 构建目标路径
                target_path = extract_to / member_path
                target_str = str(target_path.absolute())
                
                # 确保使用长路径格式
                target_str = _ensure_long_path(target_str)
                
                # 获取文件信息
                info = zip_ref.getinfo(member)
                
                # 如果是目录
                if info.is_dir():
                    os.makedirs(target_str, exist_ok=True)
                else:
                    # 确保父目录存在（也需要使用长路径）
                    parent_str = _ensure_long_path(str(target_path.parent.absolute()))
                    os.makedirs(parent_str, exist_ok=True)
                    
                    # 提取文件内容
                    with zip_ref.open(member) as source:
                        with open(target_str, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    
                    extracted_count += 1
                    if extracted_count % 100 == 0:
                        logger.debug(f"Extracted {extracted_count} files...")
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error extracting {member}: {e}")
                # 继续处理其他文件，不中断整个解压过程
                continue
        
        logger.info(f"Extraction completed: {extracted_count} files extracted, {error_count} errors")


def _delete_directory(path: Path):
    """同步删除目录"""
    shutil.rmtree(path)


def _delete_file(path: Path):
    """同步删除文件"""
    if path.exists():
        path.unlink()


class DatasetService:
    def __init__(self):
        self.datasets_dir = settings.DATASETS_DIR
        self.uploads_dir = settings.UPLOADS_DIR
        
    async def upload_dataset(self, file: UploadFile):
        """上传数据集文件"""
        dataset_id = f"ds_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dataset_dir = self.datasets_dir / dataset_id
        
        # 异步创建目录
        await asyncio.to_thread(lambda: dataset_dir.mkdir(parents=True, exist_ok=True))
        
        # 保存上传的zip文件
        zip_path = self.uploads_dir / f"{dataset_id}.zip"
        content = await file.read()
        await asyncio.to_thread(_write_bytes, zip_path, content)
        
        # 保存元数据
        meta = {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded"
        }
        
        meta_path = dataset_dir / "meta.json"
        await asyncio.to_thread(_save_json, meta_path, meta)
        
        return meta
    
    async def prepare_dataset(self, dataset_id: str, split_ratio: dict, classes: list = None):
        """准备数据集"""
        dataset_dir = self.datasets_dir / dataset_id
        if not await asyncio.to_thread(lambda: dataset_dir.exists()):
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # 读取元数据
        meta_path = dataset_dir / "meta.json"
        meta = await asyncio.to_thread(_load_json, meta_path)
        
        # 解压数据集
        version = "v1"
        version_dir = dataset_dir / version
        await asyncio.to_thread(lambda: version_dir.mkdir(exist_ok=True))
        
        zip_path = self.uploads_dir / f"{dataset_id}.zip"
        await asyncio.to_thread(_extract_zip, zip_path, version_dir)
        
        # 检查目录结构（在线程中执行）
        images_dir = await asyncio.to_thread(self._find_images_dir, version_dir)
        labels_dir = await asyncio.to_thread(self._find_labels_dir, version_dir)
        
        if not images_dir:
            raise ValueError("No images directory found in dataset")
        
        # 统计图片和标签（在线程中执行）
        def count_files():
            image_files = list(images_dir.rglob("*.jpg")) + list(images_dir.rglob("*.png")) + list(images_dir.rglob("*.jpeg"))
            label_files = list(labels_dir.rglob("*.txt")) if labels_dir else []
            return len(image_files), len(label_files)
        
        image_count, label_count = await asyncio.to_thread(count_files)
        
        # 检测类别：优先从解压后的 data.yaml 中读取，否则从标签文件检测
        detected_classes = classes or []
        
        if not detected_classes:
            # 先检查解压后的目录中是否已经存在 data.yaml 文件
            def load_classes_from_yaml():
                yaml_paths = [
                    version_dir / "data.yaml",
                    version_dir / "dataset.yaml",
                    version_dir / "config.yaml"
                ]
                for yaml_path in yaml_paths:
                    if yaml_path.exists():
                        try:
                            data = _load_yaml(yaml_path)
                            names = data.get('names', [])
                            if names:
                                logger.info(f"Loaded classes from {yaml_path.name}: {names}")
                                return names
                        except Exception as e:
                            logger.warning(f"Failed to load classes from {yaml_path}: {e}")
                            continue
                return None
            
            detected_classes = await asyncio.to_thread(load_classes_from_yaml)
            
            # 如果从 YAML 中没有读取到类别，且存在标签目录，则从标签文件检测
            if not detected_classes and labels_dir:
                detected_classes = await asyncio.to_thread(self._detect_classes, labels_dir)
                logger.info(f"Detected classes from labels: {detected_classes}")
        
        # 确保有类别列表（如果没有检测到，使用空列表）
        if not detected_classes:
            detected_classes = []
        
        # 生成data.yaml
        yaml_content = {
            "path": str(version_dir.absolute()),
            "train": "images/train" if (images_dir / "train").exists() else "images",
            "val": "images/val" if (images_dir / "val").exists() else "images",
            "nc": len(detected_classes),
            "names": detected_classes
        }
        
        yaml_path = version_dir / "data.yaml"
        await asyncio.to_thread(_save_yaml, yaml_path, yaml_content)
        
        # 更新元数据
        meta.update({
            "status": "prepared",
            "version": version,
            "image_count": image_count,
            "label_count": label_count,
            "classes": detected_classes,
            "prepared_at": datetime.now().isoformat()
        })
        
        await asyncio.to_thread(_save_json, meta_path, meta)
        
        return {
            "dataset_id": dataset_id,
            "version": version,
            "image_count": image_count,
            "label_count": label_count,
            "classes": detected_classes
        }
    
    def _find_images_dir(self, root_dir: Path):
        """查找images目录（同步方法，在线程中调用）"""
        candidates = list(root_dir.rglob("images"))
        if candidates:
            return candidates[0]
        # 如果没有images子目录，检查是否根目录直接包含图片
        image_files = list(root_dir.glob("*.jpg")) + list(root_dir.glob("*.png"))
        if image_files:
            imgs_dir = root_dir / "images"
            imgs_dir.mkdir(exist_ok=True)
            for img in image_files:
                shutil.move(str(img), str(imgs_dir / img.name))
            return imgs_dir
        return None
    
    def _find_labels_dir(self, root_dir: Path):
        """查找labels目录（同步方法，在线程中调用）"""
        candidates = list(root_dir.rglob("labels"))
        return candidates[0] if candidates else None
    
    def _detect_classes(self, labels_dir: Path):
        """从标签文件检测类别（同步方法，在线程中调用）"""
        class_ids = set()
        for label_file in labels_dir.rglob("*.txt"):
            try:
                with open(label_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            class_ids.add(int(parts[0]))
            except:
                continue
        
        # 生成默认类别名
        max_id = max(class_ids) if class_ids else 0
        return [f"class_{i}" for i in range(max_id + 1)]
    
    async def list_datasets(self):
        """列出所有数据集"""
        def _list_datasets_sync():
            datasets = []
            if not self.datasets_dir.exists():
                return datasets
            for dataset_dir in self.datasets_dir.iterdir():
                if dataset_dir.is_dir():
                    meta_path = dataset_dir / "meta.json"
                    if meta_path.exists():
                        try:
                            meta = _load_json(meta_path)
                            datasets.append(meta)
                        except Exception:
                            continue
            return datasets
        
        datasets = await asyncio.to_thread(_list_datasets_sync)
        return {"datasets": sorted(datasets, key=lambda x: x.get("uploaded_at", ""), reverse=True)}
    
    async def get_dataset(self, dataset_id: str):
        """获取数据集详情"""
        dataset_dir = self.datasets_dir / dataset_id
        meta_path = dataset_dir / "meta.json"
        
        if not await asyncio.to_thread(lambda: meta_path.exists()):
            return None
        
        meta = await asyncio.to_thread(_load_json, meta_path)
        
        # 添加样例图片（在线程中执行）
        def _get_sample_images():
            version = meta.get("version", "v1")
            version_dir = dataset_dir / version
            images_dir = self._find_images_dir(version_dir)
            
            sample_images = []
            if images_dir:
                image_files = list(images_dir.rglob("*.jpg"))[:5] + list(images_dir.rglob("*.png"))[:5]
                sample_images = [str(img.relative_to(settings.BASE_DIR)) for img in image_files[:5]]
            return sample_images
        
        meta["sample_images"] = await asyncio.to_thread(_get_sample_images)
        return meta
    
    async def update_dataset(self, dataset_id: str, request):
        """更新数据集信息"""
        dataset_dir = self.datasets_dir / dataset_id
        meta_path = dataset_dir / "meta.json"
        
        if not await asyncio.to_thread(lambda: meta_path.exists()):
            return None
        
        meta = await asyncio.to_thread(_load_json, meta_path)
        
        # 更新字段
        if request.description is not None:
            meta["description"] = request.description
        if request.tags is not None:
            meta["tags"] = request.tags
        
        meta["updated_at"] = datetime.now().isoformat()
        
        await asyncio.to_thread(_save_json, meta_path, meta)
        
        return meta
    
    async def delete_dataset(self, dataset_id: str):
        """删除数据集"""
        dataset_dir = self.datasets_dir / dataset_id
        
        if not await asyncio.to_thread(lambda: dataset_dir.exists()):
            return None
        
        # 删除数据集目录
        await asyncio.to_thread(_delete_directory, dataset_dir)
        
        # 删除上传的zip文件
        zip_path = self.uploads_dir / f"{dataset_id}.zip"
        await asyncio.to_thread(_delete_file, zip_path)
        
        return {"ok": True, "message": f"Dataset {dataset_id} deleted"}
    
    async def export_annotated_dataset(self, dataset_id: str, version: str = "v1"):
        """导出标注后的数据集"""
        dataset_dir = self.datasets_dir / dataset_id
        version_dir = dataset_dir / version
        
        if not await asyncio.to_thread(lambda: version_dir.exists()):
            return None
        
        # 创建临时ZIP文件
        def _create_zip():
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加images目录
                images_dir = self._find_images_dir(version_dir)
                if images_dir:
                    for img_file in images_dir.rglob("*"):
                        if img_file.is_file():
                            arcname = img_file.relative_to(version_dir)
                            zipf.write(img_file, arcname)
                
                # 添加labels目录
                labels_dir = self._find_labels_dir(version_dir)
                if labels_dir:
                    for label_file in labels_dir.rglob("*"):
                        if label_file.is_file():
                            arcname = label_file.relative_to(version_dir)
                            zipf.write(label_file, arcname)
                
                # 添加data.yaml
                data_yaml = version_dir / "data.yaml"
                if data_yaml.exists():
                    zipf.write(data_yaml, "data.yaml")
            
            return temp_zip_path
        
        zip_path = await asyncio.to_thread(_create_zip)
        return zip_path
    
    async def export_original_dataset(self, dataset_id: str, version: str = "v1"):
        """导出标注前的数据集（仅图片）"""
        dataset_dir = self.datasets_dir / dataset_id
        version_dir = dataset_dir / version
        
        if not await asyncio.to_thread(lambda: version_dir.exists()):
            return None
        
        # 创建临时ZIP文件
        def _create_zip():
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = temp_zip.name
            temp_zip.close()
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 仅添加images目录
                images_dir = self._find_images_dir(version_dir)
                if images_dir:
                    for img_file in images_dir.rglob("*"):
                        if img_file.is_file():
                            arcname = img_file.relative_to(version_dir)
                            zipf.write(img_file, arcname)
                
                # 可选：添加data.yaml（如果存在）
                data_yaml = version_dir / "data.yaml"
                if data_yaml.exists():
                    zipf.write(data_yaml, "data.yaml")
            
            return temp_zip_path
        
        zip_path = await asyncio.to_thread(_create_zip)
        return zip_path
