"""动画脚本解析模板管理器.

该模块负责读取和管理动画脚本解析过程中的参考模板文件。
"""

import os
from agent.log_config import logger
from typing import List, Optional


class TemplateManager:
    """模板管理器"""

    def __init__(self, templates_base_dir: str = "templates"):
        """
        初始化模板管理器
        
        Args:
            templates_base_dir: 模板文件基础目录
        """
        self.templates_base_dir = templates_base_dir
        self.story_templates_dir = os.path.join(templates_base_dir, "story")
        self.storyboard_templates_dir = os.path.join(templates_base_dir, "storyboard")
        
        # 确保目录存在
        os.makedirs(self.story_templates_dir, exist_ok=True)
        os.makedirs(self.storyboard_templates_dir, exist_ok=True)
        
        logger.info(f"模板管理器初始化完成，故事模板目录: {self.story_templates_dir}，分镜模板目录: {self.storyboard_templates_dir}")

    def list_story_templates(self) -> List[str]:
        """
        列出所有故事模板文件名
        
        Returns:
            List[str]: 故事模板文件名列表
        """
        return self._list_templates(self.story_templates_dir)

    def list_storyboard_templates(self) -> List[str]:
        """
        列出所有分镜模板文件名
        
        Returns:
            List[str]: 分镜模板文件名列表
        """
        return self._list_templates(self.storyboard_templates_dir)

    def _list_templates(self, template_dir: str) -> List[str]:
        """
        列出指定目录下的所有模板文件名
        
        Args:
            template_dir: 模板目录路径
            
        Returns:
            List[str]: 模板文件名列表
        """
        try:
            templates = []
            if os.path.exists(template_dir):
                for file in os.listdir(template_dir):
                    if file.endswith('.md'):
                        templates.append(file)
            return templates
        except Exception as e:
            logger.error(f"列出模板文件时出错: {e}")
            return []

    def read_story_template(self, filename: str) -> Optional[str]:
        """
        读取故事模板文件内容
        
        Args:
            filename: 故事模板文件名
            
        Returns:
            str: 故事模板内容，如果文件不存在则返回None
        """
        return self._read_template(self.story_templates_dir, filename)

    def read_storyboard_template(self, filename: str) -> Optional[str]:
        """
        读取分镜模板文件内容
        
        Args:
            filename: 分镜模板文件名
            
        Returns:
            str: 分镜模板内容，如果文件不存在则返回None
        """
        return self._read_template(self.storyboard_templates_dir, filename)

    def _read_template(self, template_dir: str, filename: str) -> Optional[str]:
        """
        读取模板文件内容
        
        Args:
            template_dir: 模板目录路径
            filename: 模板文件名
            
        Returns:
            str: 模板内容，如果文件不存在则返回None
        """
        template_path = os.path.join(template_dir, filename)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"模板文件未找到: {template_path}")
            return None
        except Exception as e:
            logger.error(f"读取模板文件时出错: {e}")
            return None

    def get_template_path(self, template_type: str, filename: str) -> str:
        """
        获取模板文件的完整路径
        
        Args:
            template_type: 模板类型 ('story' 或 'storyboard')
            filename: 模板文件名
            
        Returns:
            str: 模板文件完整路径
        """
        if template_type == 'story':
            return os.path.join(self.story_templates_dir, filename)
        elif template_type == 'storyboard':
            return os.path.join(self.storyboard_templates_dir, filename)
        else:
            raise ValueError(f"不支持的模板类型: {template_type}")