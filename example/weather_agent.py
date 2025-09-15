"""Pydantic AI 示例：使用多个工具，LLM需要依次调用这些工具来回答问题。

在这个例子中，我们创建了一个"天气"代理——用户可以询问多个城市的天气，
代理将使用 [get_lat_lng](file://D:\PycharmProjects\VideoCube\example\weather_agent.py#L48-L61) 工具获取位置的纬度和经度，然后使用 [get_weather](file://D:\PycharmProjects\VideoCube\example\weather_agent.py#L65-L89) 工具获取天气信息。

运行方式：

    uv run -m pydantic_ai_examples.weather_agent
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any

import logfire
from httpx import AsyncClient
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

# 'if-token-present' 表示如果没有配置 logfire，将不会发送任何内容（示例仍可正常运行）
logfire.configure(token="pylf_v1_us_xNS6fZMrFGwWSHPgm3CK7h0MKPJQGSVPRzDbSyKRDwzD")
logfire.instrument_pydantic_ai()

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

@dataclass
class Deps:
    client: AsyncClient

generation_model = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)

weather_agent = Agent(
    generation_model,
    # 对于某些模型（如openai），"简洁回答，用一句话回复"就足够了，
    # 但其他模型如anthropic和gemini需要更多的指导。
    instructions='简洁回答，用一句话回复',
    deps_type=Deps,
    retries=2,
)


class LatLng(BaseModel):
    lat: float
    lng: float


@weather_agent.tool
async def get_lat_lng(ctx: RunContext[Deps], location_description: str) -> LatLng:
    """获取位置的纬度和经度。

    参数:
        ctx: 上下文。
        location_description: 位置描述。
    """
    # 注意：这里的响应是随机的，与位置描述无关。
    r = await ctx.deps.client.get(
        'https://demo-endpoints.pydantic.workers.dev/latlng',
        params={'location': location_description},
    )
    r.raise_for_status()
    return LatLng.model_validate_json(r.content)


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """获取位置的天气信息。

    参数:
        ctx: 上下文。
        lat: 位置纬度。
        lng: 位置经度。
    """
    # 注意：这里的响应是随机的，与纬度和经度无关。
    temp_response, descr_response = await asyncio.gather(
        ctx.deps.client.get(
            'https://demo-endpoints.pydantic.workers.dev/number',
            params={'min': 10, 'max': 30},
        ),
        ctx.deps.client.get(
            'https://demo-endpoints.pydantic.workers.dev/weather',
            params={'lat': lat, 'lng': lng},
        ),
    )
    temp_response.raise_for_status()
    descr_response.raise_for_status()
    return {
        'temperature': f'{temp_response.text} °C',
        'description': descr_response.text,
    }


async def main():
    async with AsyncClient() as client:
        logfire.instrument_httpx(client, capture_all=True)
        deps = Deps(client=client)
        result = await weather_agent.run(
            '广州的天气怎么样？', deps=deps
        )
        print('响应:', result.output)


if __name__ == '__main__':
    asyncio.run(main())
