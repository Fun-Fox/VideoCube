"""
VideoCube工具包
提供各种视频处理工具
"""

from .human_matting_tool import HumanMattingTool
from .subject_matting_tool import SubjectMattingTool
# 从matting包导入所有类，保持向后兼容

__all__ = [
    'HumanMattingTool',
    'SubjectMattingTool'
]