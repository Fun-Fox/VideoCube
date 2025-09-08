"""
Subject Matting模块 - 通用主体抠图工具
支持图像、批量图像和视频的背景移除
"""

from .matting_base import SubjectMattingBase
from .image_matting import SubjectImageMatting, BatchImageMatting
from .video_matting import SubjectVideoMatting

__all__ = [
    "SubjectMattingBase",
    "SubjectImageMatting",
    "BatchImageMatting",
    "SubjectVideoMatting"
]