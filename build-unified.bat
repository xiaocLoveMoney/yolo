@echo off
chcp 65001 >nul
REM YOLO 统一镜像构建脚本 (已修复 Nginx 用户权限替换问题)
REM 将 backend 和 frontend 合并为一个镜像

echo 开始构建 YOLO 统一镜像...

REM 切换到脚本所在目录
cd /d "%~dp0"

REM -------------------------------------------------------
REM 1. 构建 backend 镜像（作为中间镜像）
REM -------------------------------------------------------
echo.
echo [1/4] 构建 backend 中间镜像...
docker build -t yolo-backend:temp -f docker/backend/Dockerfile .
if errorlevel 1 (
    echo Backend 镜像构建失败！
    exit /b 1
)

REM -------------------------------------------------------
REM 2. 构建 frontend 镜像（作为中间镜像）
REM -------------------------------------------------------
echo.
echo [2/4] 构建 frontend 中间镜像...
docker build -t yolo-frontend:temp -f docker/frontend/Dockerfile .
if errorlevel 1 (
    echo Frontend 镜像构建失败！
    exit /b 1
)

REM -------------------------------------------------------
REM 3. 创建临时 Dockerfile
REM -------------------------------------------------------
echo.
echo [3/4] 创建统一镜像 Dockerfile...

(
echo FROM yolo-frontend:temp AS frontend
echo.
echo # 最终镜像基于 backend（保留完整的 Python 环境）
echo FROM yolo-backend:temp
echo.
echo # 安装 nginx 和 supervisor，创建 www-data 用户和目录
echo RUN apt-get update ^&^& apt-get install -y --no-install-recommends nginx supervisor ^&^& \
echo      mkdir -p /var/www/html /var/log/nginx /var/cache/nginx /var/lib/nginx ^&^& \
echo      chown -R www-data:www-data /var/www/html /var/log/nginx /var/cache/nginx /var/lib/nginx ^&^& \
echo      rm -rf /var/lib/apt/lists/*
echo.
echo # 从 frontend 阶段复制前端文件
echo COPY --from=frontend /usr/share/nginx/html /var/www/html
echo COPY --from=frontend /etc/nginx/nginx.conf /etc/nginx/nginx.conf
echo.
echo # 修复 nginx 配置
echo # 注意：这里使用了正则匹配，防止因空格数量不同导致替换失败
echo RUN sed -i "s|^user .*|user www-data;|g" /etc/nginx/nginx.conf ^&^& \
echo      sed -i "s|/usr/share/nginx/html|/var/www/html|g" /etc/nginx/nginx.conf ^&^& \
echo      sed -i "s|proxy_pass .*backend_upstream;|proxy_pass http://127.0.0.1:8000;|g" /etc/nginx/nginx.conf ^&^& \
echo      sed -i "s|proxy_pass .*backend_upstream/static/|proxy_pass http://127.0.0.1:8000/static/|g" /etc/nginx/nginx.conf ^&^& \
echo      sed -i "/resolver/d" /etc/nginx/nginx.conf ^&^& \
echo      sed -i "/set .*backend_upstream/d" /etc/nginx/nginx.conf
echo.
echo # 创建 supervisord 配置目录
echo RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor /var/log/nginx
echo.
echo # 创建 supervisord 配置文件
echo RUN echo '[supervisord]' ^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'nodaemon=true' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'logfile=/var/log/supervisor/supervisord.log' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'pidfile=/var/run/supervisord.pid' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo '' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo '[program:backend]' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'directory=/app' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'autostart=true' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'autorestart=true' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stdout_logfile=/dev/stdout' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stdout_logfile_maxbytes=0' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stderr_logfile=/dev/stderr' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stderr_logfile_maxbytes=0' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo '' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo '[program:frontend]' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'command=nginx -g "daemon off;"' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'autostart=true' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'autorestart=true' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stdout_logfile=/dev/stdout' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stdout_logfile_maxbytes=0' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stderr_logfile=/dev/stderr' ^>^> /etc/supervisor/conf.d/yolo.conf ^&^& \
echo      echo 'stderr_logfile_maxbytes=0' ^>^> /etc/supervisor/conf.d/yolo.conf
echo.
echo EXPOSE 8000 80
echo.
echo CMD ["supervisord", "-c", "/etc/supervisor/conf.d/yolo.conf"]
) > Dockerfile.unified

REM -------------------------------------------------------
REM 4. 构建最终统一镜像
REM -------------------------------------------------------
echo.
echo [4/4] 构建统一镜像 yolo:latest...
docker build -t yolo:latest -f Dockerfile.unified .
if errorlevel 1 (
    echo 统一镜像构建失败！
    del Dockerfile.unified 2>nul
    exit /b 1
)

REM 清理临时文件
del Dockerfile.unified 2>nul

echo.
echo ==========================================
echo 构建完成！
echo 镜像名称: yolo:latest
echo.
echo 运行命令（支持GPU渲染）:
echo    docker run -p 3000:80 -p 8000:8000 ^
echo       --gpus all ^
echo       --shm-size=24gb ^
echo       -e NVIDIA_VISIBLE_DEVICES=all ^
echo       -e NVIDIA_DRIVER_CAPABILITIES=compute,utility ^
echo       yolo:latest
echo.
echo 注意：
echo   - --gpus all: 启用所有GPU支持
echo   - --shm-size=24gb: 增加共享内存大小以支持 PyTorch 多进程数据加载
echo   - NVIDIA_VISIBLE_DEVICES=all: 使所有GPU对容器可见
echo   - NVIDIA_DRIVER_CAPABILITIES=compute,utility: 指定所需的NVIDIA驱动功能
echo ==========================================

pause