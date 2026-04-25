"""Pytest 全局配置 - 自动将项目根目录添加到 sys.path"""
import sys
import os

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# backend 目录（使 from app.xxx 可以工作）
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
