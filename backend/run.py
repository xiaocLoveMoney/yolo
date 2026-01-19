#!/usr/bin/env python
"""
后端启动脚本
从 backend 目录运行: python run.py
"""
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    
    # 使用导入字符串以支持 reload
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"]  # 指定重载目录
    )
