"""动画脚本解析模块.

该模块提供了一个基于Pipeline的动画脚本解析系统，将提示词存储在独立的Markdown文件中，
每个Agent对应一个提示词文件，通过Pipeline协调整个解析流程。
"""

from agent.pipeline import AnimationScriptPipeline
from agent.models import StoryboardInfo, AnimationScriptOutput

__all__ = [
    "AnimationScriptPipeline",
    "StoryboardInfo", 
    "AnimationScriptOutput"
]