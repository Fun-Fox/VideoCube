import os
from dotenv import load_dotenv
from httpx import AsyncClient
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from google import genai
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

model_names = [
    "nvidia/nemotron-nano-9b-v2:free",
    "deepseek/deepseek-chat-v3.1:free",
    "openai/gpt-oss-120b:free",
    "qwen/qwen3-235b-a22b:free"
]
load_dotenv()


def main():
    for model_name in model_names:
        try:
            http_client = AsyncClient(proxy=os.getenv("PROXY"))
            model = OpenAIChatModel(
                model_name,
                provider=OpenRouterProvider(api_key=os.getenv("OPENROUTER_API_KEY"),http_client=http_client),
            )

            agent = Agent(model)

            result = agent.run_sync("你好你是谁？")
            print(result.output)
        except Exception as e:
            print(e)
            print(f"{model_name}模型调用异常")


# 使用asyncio.run()运行异步函数
if __name__ == "__main__":
    main()
