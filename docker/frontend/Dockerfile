# YOLO Training Platform - Frontend Dockerfile
# Node 22 Build + Nginx Serve

# ==================== 构建阶段 ====================
FROM node:22-alpine AS builder

# 配置 npm 镜像源（npmmirror.com）
# RUN npm config set registry https://registry.npmmirror.com

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY frontend/package.json frontend/package-lock.json ./

# 安装依赖
RUN npm ci

# 复制前端源代码和配置文件
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./
COPY frontend/tsconfig.node.json ./
COPY frontend/.env.production ./

# 构建生产版本
RUN npm run build:prod

# ==================== 运行阶段 ====================
FROM nginx:alpine

# 复制构建产物到 nginx html 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置文件
COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
