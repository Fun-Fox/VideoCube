"""动画脚本解析数据模型.

该模块定义了动画脚本解析过程中使用的数据模型。
"""

from typing import List
from pydantic import BaseModel, Field

class StoryboardInfo(BaseModel):
    """分镜脚本信息"""
    shot_id: str = Field(description="镜号")
    plot_title: str = Field(description="情节标题")
    scene_elements: str = Field(description="画面一开始的构图描述")
    actions: str = Field(description="画面后续的动作")
    bgm_description: str = Field(description="BGM描述")
    sound_effect: str = Field(description="特效音描述")
    duration: str = Field(description="建议时长")


class CharacterDesign(BaseModel):
    """角色设计信息"""
    name: str = Field(description="角色名称")
    characteristics: str = Field(description="角色性格特点")
    appearance: str = Field(description="角色外貌描述")




class PlotPoint(BaseModel):
    """情节点信息"""
    title: str = Field(description="情节点标题")
    description: str = Field(description="情节点详细描述")


class ScriptDesignOutput(BaseModel):
    """剧本设计输出"""
    characters: List[CharacterDesign] = Field(description="角色设计列表")
    plot_points: List[PlotPoint] = Field(description="情节点列表")


class AnimationScriptOutput(BaseModel):
    """动画脚本解析输出"""
    storyboards: List[StoryboardInfo] = Field(description="分镜脚本板块信息")