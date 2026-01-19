# PyTorch 安装说明（RTX 5070）

RTX 5070 显卡需要安装支持 CUDA 12.x 的 PyTorch 版本。

## 推荐安装方式

### 方式一：使用 pip 安装（推荐）

```bash
# 激活虚拟环境
conda activate yoloapi

# 安装支持 CUDA 12.1 的 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 方式二：使用 conda 安装

```bash
conda activate yoloapi
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia
```

## 验证安装

安装完成后，运行以下命令验证 CUDA 是否可用：

```python
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}'); print(f'CUDA版本: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'GPU设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

如果输出显示 `CUDA可用: True` 和你的 GPU 名称，说明安装成功。

## 注意事项

1. **确保已安装 NVIDIA 驱动**: RTX 5070 需要 NVIDIA 驱动版本 >= 535.x
2. **CUDA Toolkit**: PyTorch 会自带 CUDA runtime，通常不需要单独安装 CUDA Toolkit
3. **如果遇到问题**: 访问 https://pytorch.org/get-started/locally/ 获取最新的安装命令
