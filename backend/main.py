"""
Inkling 后端启动入口

使用方式:
    cd D:\\Inkling
    python -m backend.main          # 开发模式
    uvicorn backend.main:app        # 生产模式
"""
import sys
import os

# 确保项目根目录和 backend 目录在 sys.path 中
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_backend_dir = os.path.dirname(os.path.abspath(__file__))

if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
