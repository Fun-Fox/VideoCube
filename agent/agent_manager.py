"""动画脚本解析Agent管理器.

该模块负责管理和初始化动画脚本解析过程中的各个Agent。
"""

from typing import Optional
from loguru import logger
from pydantic_ai import Agent

from agent.models import AnimationScriptOutput, ScriptDesignOutput
from agent.config_manager import ConfigManager
from agent.prompt_manager import PromptManager
from agent.model_manager import ModelManager



class AgentManager:
    """Agent管理器"""
    
    def __init__(self, config_manager: ConfigManager, prompt_manager: PromptManager, model_manager: ModelManager):
        """
        初始化Agent管理器
        
        Args:
            config_manager: 配置管理器
            prompt_manager: 提示词管理器
            model_manager: 模型管理器
        """
        self.config_manager = config_manager
        self.prompt_manager = prompt_manager
        self.model_manager = model_manager
        
        # 初始化Agents
        self.story_optimization_agent: Optional[Agent] = None
        self.script_design_agent: Optional[Agent] = None
        self.storyboard_design_agent: Optional[Agent] = None
        self.viewer_agent: Optional[Agent] = None
        self.reviewer_agent: Optional[Agent] = None
        
        self._init_agents()
    
    def _init_agents(self):
        """初始化所有Agents"""
        # 故事优化Agent
        story_optimization_prompt_file = self.config_manager.get_agent_prompt_file("story_optimization")
        story_optimization_model_name = self.config_manager.get_agent_model_name("story_optimization")
        if story_optimization_prompt_file:
            story_optimization_prompt = self.prompt_manager.read_prompt(story_optimization_prompt_file)
            story_optimization_model = self.model_manager.create_model(story_optimization_model_name)
            self.story_optimization_agent = Agent(
                story_optimization_model,
                output_type=str,
                system_prompt=story_optimization_prompt
            )
        
        # 剧本设计Agent
        script_design_prompt_file = self.config_manager.get_agent_prompt_file("script_design")
        script_design_model_name = self.config_manager.get_agent_model_name("script_design")
        if script_design_prompt_file:
            script_design_prompt = self.prompt_manager.read_prompt(script_design_prompt_file)
            script_design_model = self.model_manager.create_model(script_design_model_name)
            self.script_design_agent = Agent(
                script_design_model,
                output_type=ScriptDesignOutput,
                system_prompt=script_design_prompt
            )
        
        # 分镜设计Agent
        storyboard_design_prompt_file = self.config_manager.get_agent_prompt_file("storyboard_design")
        storyboard_design_model_name = self.config_manager.get_agent_model_name("storyboard_design")
        if storyboard_design_prompt_file:
            storyboard_design_prompt = self.prompt_manager.read_prompt(storyboard_design_prompt_file)
            storyboard_design_model = self.model_manager.create_model(storyboard_design_model_name)
            self.storyboard_design_agent = Agent(
                storyboard_design_model,
                output_type=AnimationScriptOutput,
                system_prompt=storyboard_design_prompt
            )
        
        # 观看者Agent
        viewer_prompt_file = self.config_manager.get_agent_prompt_file("viewer")
        viewer_model_name = self.config_manager.get_agent_model_name("viewer")
        if viewer_prompt_file:
            viewer_prompt = self.prompt_manager.read_prompt(viewer_prompt_file)
            viewer_model = self.model_manager.create_model(viewer_model_name)
            self.viewer_agent = Agent(
                viewer_model,
                output_type=str,
                system_prompt=viewer_prompt
            )
        
        # 审核员Agent
        reviewer_prompt_file = self.config_manager.get_agent_prompt_file("reviewer")
        reviewer_model_name = self.config_manager.get_agent_model_name("reviewer")
        if reviewer_prompt_file:
            reviewer_prompt = self.prompt_manager.read_prompt(reviewer_prompt_file)
            reviewer_model = self.model_manager.create_model(reviewer_model_name)
            self.reviewer_agent = Agent(
                reviewer_model,
                output_type=str,
                system_prompt=reviewer_prompt
            )
        
        logger.info("所有Agents初始化完成")