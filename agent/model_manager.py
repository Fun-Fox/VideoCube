"""动画脚本解析模型管理器.

该模块负责管理动画脚本解析过程中使用的AI模型。
"""

import os
from typing import Union
from loguru import logger

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from google import genai
from dotenv import load_dotenv

load_dotenv()


class ModelManager:
    """模型管理器"""

    def __init__(self):
        """初始化模型管理器"""
        self.provider = None
        self.client = None
        self._init_model_provider()

    def _init_model_provider(self):
        """初始化模型提供者"""
        # 检查使用哪种模型提供者
        if os.getenv("MODEL_PROVIDER") == "google":
            # 配置Google模型
            http_options = genai.HttpOptions()
            http_options.client_args = {"proxy": os.getenv("PROXY")}

            self.client = genai.Client(
                api_key=os.getenv("GOOGLE_API_KEY"),
                http_options=http_options
            )
            self.provider = GoogleProvider(client=self.client)
        else:
            # 配置OpenRouter模型
            self.provider = OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"))

    def create_model(self, model_name: str) -> Union[GoogleModel, OpenAIChatModel]:
        """
        根据模型名称创建模型实例
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型实例
        """
        if os.getenv("MODEL_PROVIDER") == "google":
            return GoogleModel(model_name, provider=self.provider)
        else:
            return OpenAIChatModel(model_name, provider=self.provider)
