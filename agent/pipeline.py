"""动画脚本解析Pipeline.

该模块提供了一个基于Pipeline的动画脚本解析系统，将提示词存储在独立的Markdown文件中，
每个Agent对应一个提示词文件，通过Pipeline协调整个解析流程。
"""

import asyncio
from loguru import logger

from typing import Tuple

from agent.models import AnimationScriptOutput, ScriptDesignOutput
from agent.config_manager import ConfigManager
from agent.prompt_manager import PromptManager
from agent.model_manager import ModelManager
from agent.agent_manager import AgentManager


class AnimationScriptPipeline:
    """动画脚本解析Pipeline类"""

    def __init__(self, config_path: str = "agent/config/pipeline_config.json"):
        """
        初始化Pipeline
        
        Args:
            config_path: 配置文件路径
        """
        # 初始化管理器
        self.config_manager = ConfigManager(config_path)
        self.prompt_manager = PromptManager(self.config_manager.get("default_prompts_dir", "agent/prompts"))
        self.model_manager = ModelManager()
        self.agent_manager = AgentManager(self.config_manager, self.prompt_manager, self.model_manager)

        # 创建deps对象用于Agent运行
        self.deps = None  # 根据实际需要初始化

        logger.info("动画脚本解析Pipeline初始化完成")

    async def optimize_story(self, original_story: str) -> str:
        """
        优化故事使其更清晰完整
        
        Args:
            original_story: 原始故事文本
            
        Returns:
            str: 优化后的故事文本
        """
        logger.info("开始优化故事")
        result = await self.agent_manager.story_optimization_agent.run(original_story, deps=self.deps)
        logger.info("故事优化完成")
        return result.output

    async def design_script(self, optimized_story: str) -> ScriptDesignOutput:
        """
        根据优化的故事设计剧本
        
        Args:
            optimized_story: 优化后的故事文本
            
        Returns:
            ScriptDesignOutput: 结构化的剧本设计输出
        """
        logger.info("开始剧本设计")
        result = await self.agent_manager.script_design_agent.run(optimized_story, deps=self.deps)
        logger.info("剧本设计完成")
        return result.output

    async def design_storyboard(self, script_design) -> AnimationScriptOutput:
        """
        根据剧本设计分镜
        
        Args:
            script_design: 剧本设计输出
            
        Returns:
            AnimationScriptOutput: 结构化的动画脚本数据
        """
        logger.info("开始分镜设计")
        try:
            if isinstance(script_design, ScriptDesignOutput):
                logger.info("非优化性分镜设计需求，结构化处理")
                # 将结构化输入转换为文本输入
                script_text = f"""
    角色设计:
    {chr(10).join([f"- {char.name}: {char.characteristics}, 外观: {char.appearance}" for char in script_design.characters])}
    
    情节点:
    {chr(10).join([f"-  {plot.title}: {plot.description}" for plot in script_design.plot_points])}
                """
            #     chr(10) 是换行符的ASCII字符表示，等同于 \n
            else:
                logger.info("优化性分镜设计需求，直接使用输入")
                script_text = script_design

            result = await self.agent_manager.storyboard_design_agent.run(script_text, deps=self.deps)
            logger.info("分镜设计完成")
            return result.output
        except Exception as e:
            logger.error(f"分镜设计时出现错误: {e}")
            raise

    async def viewer_experience(self, storyboard: AnimationScriptOutput) -> str:
        """
        观看者根据分镜体验并描述故事
        
        Args:
            storyboard: 分镜设计结果
            
        Returns:
            str: 观看者描述的故事
        """
        logger.info("开始观看者体验")
        # 构造观看者输入，主要是分镜中的画面和动作描述
        scene_elements = [shot.scene_elements for shot in storyboard.storyboards]
        actions = [shot.actions for shot in storyboard.storyboards]

        viewer_input = "分镜设计中的画面和动作：\n"
        for i, (element, action) in enumerate(zip(scene_elements, actions)):
            viewer_input += f"分镜{i + 1}. 画面一开始的构图描述: {element}\n   画面后续的视觉动态变化: {action}\n"

        result = await self.agent_manager.viewer_agent.run(viewer_input, deps=self.deps)
        logger.info("观看者体验完成")
        return result.output

    async def review_and_suggest(self, original_story: str, viewer_story: str,
                                 storyboard: AnimationScriptOutput) -> Tuple[str, bool]:
        """
        审核员对比原始故事和观看者描述的故事，提出优化建议
        
        Args:
            original_story: 原始故事
            viewer_story: 观看者描述的故事
            storyboard: 分镜设计
            
        Returns:
            tuple: (优化建议, 是否需要继续优化)
        """
        logger.info("开始审核员评审")
        review_input = f"""原始故事：
{original_story}

观看者描述的故事：
{viewer_story}

分镜设计中的关键信息：
画面：{[shot.scene_elements for shot in storyboard.storyboards]}
动作：{[shot.actions for shot in storyboard.storyboards]}
"""

        result = await self.agent_manager.reviewer_agent.run(review_input, deps=self.deps)
        review_output = result.output

        # 判断是否需要继续优化
        need_continue = not review_output.startswith("【审核通过】")
        logger.info(f"审核员评审完成，需要继续优化: {need_continue}")
        return review_output, need_continue

    async def process_animation_story(self, original_story: str, max_iterations: int = 3) -> tuple[
        AnimationScriptOutput, ScriptDesignOutput]:
        """
        完整处理动画故事的优化流程
        
        Args:
            original_story: 原始故事
            max_iterations: 最大迭代次数
            
        Returns:
            tuple: (最终的动画脚本输出, 剧本设计输出)
        """
        logger.info("开始完整处理动画故事...")

        # 步骤1: 优化故事
        optimized_story = await self.optimize_story(original_story)
        logger.info(f"优化后的故事: {optimized_story[:100]}...")

        iteration = 0
        storyboard = None
        review_suggestion = None
        # 步骤2: 剧本设计
        logger.info("开始剧本设计")
        script_design = await self.design_script(optimized_story)
        logger.info("剧本设计完成")

        while iteration < max_iterations:

            # 步骤3: 分镜设计
            if review_suggestion:
                # 如果需要继续优化，则重新进行分镜设计
                logger.info("根据审核员建议重新优化分镜...")
                storyboard = await self.design_storyboard(
                    f"原分镜设计：\n {storyboard}\n\n 优化建议：\n {review_suggestion}")
                logger.info("分镜设计优化完成")
            else:
                # 步骤3: 分镜设计
                storyboard = await self.design_storyboard(script_design)
                logger.info("分镜设计完成")

            # 步骤4: 观看者体验
            viewer_story = await self.viewer_experience(storyboard)
            logger.info(f"观看者体验描述: {viewer_story[:100]}...")

            # 步骤5: 审核员评审
            review_suggestion, need_continue = await self.review_and_suggest(optimized_story, viewer_story,
                                                                             storyboard)
            logger.info(f"审核员建议: {review_suggestion[:100]}...")

            if not need_continue:
                logger.info("审核员认为故事已经符合要求，结束优化循环")
                break

            iteration += 1

            if iteration >= max_iterations:
                logger.info(f"达到最大迭代次数 {max_iterations}，结束优化")
                break

        logger.info("动画故事处理流程完成")
        return storyboard, script_design
