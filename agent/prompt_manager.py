"""动画脚本解析提示词管理器.

该模块负责读取和管理动画脚本解析过程中的提示词文件。
"""

import os
from agent.log_config import logger

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PromptManager:
    """提示词管理器"""

    def __init__(self, prompts_dir: str = "agent/prompts"):
        """
        初始化提示词管理器
        
        Args:
            prompts_dir: 提示词文件目录
        """
        self.prompts_dir = os.path.join(root_dir, prompts_dir)

    def read_prompt(self, filename: str) -> str:
        """
        读取提示词文件内容
        
        Args:
            filename: 提示词文件名
            
        Returns:
            str: 提示词内容
        """
        prompt_path = os.path.join(self.prompts_dir, filename)
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.error(f"提示词文件未找到: {prompt_path}")
            raise
        except Exception as e:
            logger.error(f"读取提示词文件时出错: {e}")
            raise
