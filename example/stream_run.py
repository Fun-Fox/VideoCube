import os
from datetime import date

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]

import httpx
import asyncio
from typing import Optional

class LoggingAsyncClient(httpx.AsyncClient):
    async def send(self, request: httpx.Request, *args, **kwargs) -> httpx.Response:
        # 打印请求详情
        print("=== HTTP Request ===")
        print(f"Method: {request.method}")
        print(f"URL: {request.url}")
        print(f"Headers: {dict(request.headers)}")
        if request.content:
            print(f"Body: {request.content.decode('utf-8', errors='ignore')}")
        print("==================")

        # 发送请求
        response = await super().send(request, *args, **kwargs)

        # 对于流式响应，我们需要特殊处理
        if response.headers.get('content-type', '').startswith('text/event-stream'):
            print("Streaming response detected")
        else:
            print("=== HTTP Response ===")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print("===================")

        return response


# 然后在创建 provider 时使用这个自定义客户端
provider = OpenAIProvider(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    # http_client=LoggingAsyncClient()
)
# https://ai.pydantic.dev/output/#streaming-structured-output
model = OpenAIChatModel(model_name='gemini-2.5-pro', provider=provider)
agent = Agent(
    model,
    output_type=UserProfile,
    system_prompt='Extract a user profile from the input',
)
from pydantic import ValidationError

async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    print(agent.run(user_input))
    # async with agent.run_stream(user_input) as result:
    #     async for message, last in result.stream_responses(debounce_by=0.01):
    #         print(message)
    #         print(last)
    #         try:
    #             profile = await result.validate_response_output(
    #                 message,
    #                 allow_partial=not last,
    #             )
    #         except ValidationError:
    #             continue
    #         print(profile)
    #         # > {'name': 'Ben'}
    #         # > {'name': 'Ben'}
    #         # > {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
    #         # > {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
    #         # > {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
    #         # > {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
    #         # > {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}


if __name__ == '__main__':
    # import asyncio
    #
    # asyncio.run(main())
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    print(agent.run_sync(user_input))
