# YOLO Training Platform - Backend Dockerfile
# Python 3.11 + GPU Support (CUDA 12.8 for RTX 5070 Blackwell)

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 配置 APT 镜像源（中科大镜像）
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's@http://.*debian.org@http://mirrors.ustc.edu.cn@g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's@http://security.debian.org@http://mirrors.ustc.edu.cn/debian-security@g' /etc/apt/sources.list 2>/dev/null || true && \
    if [ -d /etc/apt/sources.list.d ]; then \
        sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/*.sources 2>/dev/null || true; \
    fi

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    # Pillow 构建依赖
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 镜像源（清华镜像）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt
COPY backend/requirements.txt /app/requirements.txt

# 先安装 PyTorch 和 torchvision（使用 nightly 版本，CUDA 12.8 支持 RTX 5070 Blackwell sm_120）
# 增加超时时间和重试次数以应对网络问题
RUN pip install --default-timeout=300 --retries=5 --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128

# 安装其他依赖（从清华镜像，排除 torch 和 torchvision）
RUN grep -v "^torch" /app/requirements.txt | grep -v "^#" | grep -v "^$" > /tmp/requirements_no_torch.txt && \
    pip install -r /tmp/requirements_no_torch.txt && \
    rm /tmp/requirements_no_torch.txt

# 复制后端源代码
COPY backend/src /app/src
COPY backend/run.py /app/run.py

# 创建数据目录
RUN mkdir -p /app/data /app/models

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
