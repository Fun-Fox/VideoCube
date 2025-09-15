"""关于鲸鱼的信息 —— 结构化响应流验证示例。

此脚本从GPT-4流式获取关于鲸鱼的结构化响应，验证数据并在接收数据时
使用Rich将其显示为动态表格。

运行方式：

    uv run -m pydantic_ai_examples.stream_whales
"""

from typing import Annotated

import logfire
from pydantic import Field
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from rich.console import Console
from rich.live import Live
from rich.table import Table
from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent

# 'if-token-present' 表示如果您没有配置logfire，将不会发送任何内容（示例仍可正常运行）
logfire.configure(token="pylf_v1_us_xNS6fZMrFGwWSHPgm3CK7h0MKPJQGSVPRzDbSyKRDwzD")
logfire.instrument_pydantic_ai()

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

model = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)
class Whale(TypedDict):
    name: str
    length: Annotated[
        float, Field(description='成年鲸鱼的平均长度（米）')
    ]
    weight: NotRequired[
        Annotated[
            float,
            Field(description='成年鲸鱼的平均重量（千克）', ge=50),
        ]
    ]
    ocean: NotRequired[str]
    description: NotRequired[Annotated[str, Field(description='简短描述')]]


agent = Agent(model, output_type=list[Whale])


async def main():
    console = Console()
    with Live('\n' * 36, console=console) as live:
        console.print('正在请求数据...', style='cyan')
        async with agent.run_stream(
            '为我生成5种鲸鱼的详细信息'
        ) as result:
            console.print('响应:', style='green')

            async for whales in result.stream_output(debounce_by=0.01):
                table = Table(
                    title='鲸鱼种类',
                    caption='来自GPT-4的结构化响应流',
                    width=120,
                )
                table.add_column('ID', justify='right')
                table.add_column('名称')
                table.add_column('平均长度 (米)', justify='right')
                table.add_column('平均重量 (千克)', justify='right')
                table.add_column('海洋')
                table.add_column('描述', justify='right')

                for wid, whale in enumerate(whales, start=1):
                    table.add_row(
                        str(wid),
                        whale['name'],
                        f'{whale["length"]:0.0f}',
                        f'{w:0.0f}' if (w := whale.get('weight')) else '…',
                        whale.get('ocean') or '…',
                        whale.get('description') or '…',
                    )
                live.update(table)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
