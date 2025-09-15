"""动画脚本解析配置管理器.

该模块负责加载和管理动画脚本解析过程中的配置。
"""

import json
import os
from typing import Dict, Any
from loguru import logger


root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "agent/config/pipeline_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(os.path.join(root_dir, config_path))
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置内容
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"加载配置文件时出错: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项的值
        
        Args:
            key: 配置项键名
            default: 默认值
            
        Returns:
            配置项的值或默认值
        """
        return self.config.get(key, default)
    
    def get_agent_prompt_file(self, agent_name: str) -> str:
        """
        获取指定Agent的提示词文件名
        
        Args:
            agent_name: Agent名称
            
        Returns:
            提示词文件名
        """
        agent_prompt_mapping = self.config.get("agent_prompt_mapping", {})
        return agent_prompt_mapping.get(agent_name)
    
    def get_agent_model_name(self, agent_name: str, default_model: str = "gemini-2.5-flash") -> str:
        """
        获取指定Agent的模型名称
        
        Args:
            agent_name: Agent名称
            default_model: 默认模型名称
            
        Returns:
            模型名称
        """
        agent_model_mapping = self.config.get("agent_model_mapping", {})
        return agent_model_mapping.get(agent_name, default_model)