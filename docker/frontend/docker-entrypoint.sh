#!/bin/sh
set -e

# 设置默认的 backend 主机名
BACKEND_HOST=${BACKEND_HOST:-backend}

# 替换 nginx.conf 中的占位符
sed -i "s/BACKEND_HOST_PLACEHOLDER/$BACKEND_HOST/g" /etc/nginx/nginx.conf

# 执行 nginx 的默认启动命令
# 如果存在原始的 docker-entrypoint.sh，使用它；否则直接启动 nginx
if [ -f /docker-entrypoint.sh ]; then
    exec /docker-entrypoint.sh nginx -g "daemon off;"
else
    exec nginx -g "daemon off;"
fi
