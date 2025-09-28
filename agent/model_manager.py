"""动画脚本解析模型管理器.

该模块负责管理动画脚本解析过程中使用的AI模型。
"""
import json
import os
from typing import Union, Dict, Any
from agent.log_config import logger
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from google import genai
from dotenv import load_dotenv

load_dotenv()


import httpx


class LoggingAsyncClient(httpx.AsyncClient):
    async def send(self, request: httpx.Request, *args, **kwargs) -> httpx.Response:
        # 打印请求详情
        logger.info("=== HTTP Request ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Headers: {dict(request.headers)}")
        if request.content:
            try:
                # 尝试解析JSON内容以获得更好的可读性
                content = request.content.decode('utf-8', errors='ignore')
                json_content = json.loads(content)
                logger.info(f"Body (JSON): {json.dumps(json_content, indent=2, ensure_ascii=False)}")
            except:
                # 如果不是JSON，直接记录原始内容
                logger.info(f"Body: {request.content.decode('utf-8', errors='ignore')}")
        logger.info("==================")

        # 发送请求
        response = await super().send(request, *args, **kwargs)
        response_text = response.content.decode('utf-8', errors='ignore')

        # 打印响应详情
        logger.info("=== HTTP Response ===")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {dict(response.headers)}")
        try:
            json_response = json.loads(response_text)
            logger.info(f"Response (JSON): {json.dumps(json_response, indent=2, ensure_ascii=False)}")
        except:
            # 如果不是JSON，直接打印文本内容
            logger.info(f"Response: {response_text}")  # 只打印前1000个字符

        logger.info("===================")

        return response

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
            http_options = genai.types.HttpOptions()
            http_options.client_args = {"proxy": os.getenv("PROXY")}

            self.client = genai.Client(
                api_key=os.getenv("GOOGLE_API_KEY"),
                http_options=http_options
            )
            self.provider = GoogleProvider(client=self.client)
        elif os.getenv("MODEL_PROVIDER") == "openrouter":
            # 配置OpenRouter模型
            self.provider = OpenRouterProvider( api_key=os.getenv("OPENROUTER_API_KEY"),http_client=LoggingAsyncClient())
        elif os.getenv("MODEL_PROVIDER") == "openai":
            # 配置OpenAI模型
            self.provider = OpenAIProvider(base_url=os.getenv("OPENAI_BASE_URL"),api_key=os.getenv("OPENAI_API_KEY"),http_client=LoggingAsyncClient())


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
        elif os.getenv("MODEL_PROVIDER") == "openrouter":
            return OpenAIChatModel(model_name, provider=self.provider)
        elif os.getenv("MODEL_PROVIDER") == "openai":
            return OpenAIChatModel(model_name, provider=self.provider)