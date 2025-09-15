"""多代理工作流示例，其中一个代理将工作委托给另一个代理。

在这个场景中，一组代理协同工作为用户查找航班。
"""

import datetime
from dataclasses import dataclass
from typing import Literal

import logfire
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from rich.prompt import Prompt

from pydantic_ai import Agent, ModelRetry, RunContext, RunUsage, UsageLimits
from pydantic_ai.messages import ModelMessage

# 'if-token-present' 表示如果您没有配置logfire，将不会发送任何内容（示例仍可正常运行）
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()


class FlightDetails(BaseModel):
    """最合适的航班详情。"""

    flight_number: str
    price: int
    origin: str = Field(description='三字母机场代码')
    destination: str = Field(description='三字母机场代码')
    date: datetime.date


class NoFlightFound(BaseModel):
    """当未找到有效航班时。"""


@c
class Deps:
    web_page_text: str
    req_origin: str
    req_destination: str
    req_date: datetime.date

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

model = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)
# 该代理负责控制对话流程。
search_agent = Agent[Deps, FlightDetails | NoFlightFound](
    model,
    output_type=FlightDetails | NoFlightFound,  # type: ignore
    retries=4,
    system_prompt=(
        '你的工作是在给定日期为用户找到最便宜的航班。'
    ),
)


# 该代理负责从网页文本中提取航班详情。
extraction_agent = Agent(
    model,
    output_type=list[FlightDetails],
    system_prompt='从给定文本中提取所有航班详情。',
)


@search_agent.tool
async def extract_flights(ctx: RunContext[Deps]) -> list[FlightDetails]:
    """获取所有航班的详情。"""
    # 我们将使用情况传递给搜索代理，这样该代理内的请求会被计入
    result = await extraction_agent.run(ctx.deps.web_page_text, usage=ctx.usage)
    logfire.info('找到 {flight_count} 个航班', flight_count=len(result.output))
    return result.output


@search_agent.output_validator
async def validate_output(
    ctx: RunContext[Deps], output: FlightDetails | NoFlightFound
) -> FlightDetails | NoFlightFound:
    """对航班是否符合约束条件进行程序化验证。"""
    if isinstance(output, NoFlightFound):
        return output

    errors: list[str] = []
    if output.origin != ctx.deps.req_origin:
        errors.append(
            f'航班起点应为 {ctx.deps.req_origin}，而不是 {output.origin}'
        )
    if output.destination != ctx.deps.req_destination:
        errors.append(
            f'航班终点应为 {ctx.deps.req_destination}，而不是 {output.destination}'
        )
    if output.date != ctx.deps.req_date:
        errors.append(f'航班日期应为 {ctx.deps.req_date}，而不是 {output.date}')

    if errors:
        raise ModelRetry('\n'.join(errors))
    else:
        return output


class SeatPreference(BaseModel):
    row: int = Field(ge=1, le=30)
    seat: Literal['A', 'B', 'C', 'D', 'E', 'F']


class Failed(BaseModel):
    """无法提取座位选择。"""


# 该代理负责提取用户的座位选择
seat_preference_agent = Agent[None, SeatPreference | Failed](
    model,
    output_type=SeatPreference | Failed,
    system_prompt=(
        "提取用户的座位偏好。"
        'A座和F座是靠窗座位。'
        '第1排是前排，腿部空间更大。'
        '第14排和第20排也有额外腿部空间。'
    ),
)


# 在现实中这会从预订网站下载，
# 可能使用另一个代理来浏览网站
flights_web_page = """
1. 航班 SFO-AK123
- 价格: $350
- 起点: 旧金山国际机场 (SFO)
- 终点: 泰德·史蒂文斯安克雷奇国际机场 (ANC)
- 日期: 2025年1月10日

2. 航班 SFO-AK456
- 价格: $370
- 起点: 旧金山国际机场 (SFO)
- 终点: 费尔班克斯国际机场 (FAI)
- 日期: 2025年1月10日

3. 航班 SFO-AK789
- 价格: $400
- 起点: 旧金山国际机场 (SFO)
- 终点: 朱诺国际机场 (JNU)
- 日期: 2025年1月20日

4. 航班 NYC-LA101
- 价格: $250
- 起点: 旧金山国际机场 (SFO)
- 终点: 泰德·史蒂文斯安克雷奇国际机场 (ANC)
- 日期: 2025年1月10日

5. 航班 CHI-MIA202
- 价格: $200
- 起点: 芝加哥奥黑尔国际机场 (ORD)
- 终点: 迈阿密国际机场 (MIA)
- 日期: 2025年1月12日

6. 航班 BOS-SEA303
- 价格: $120
- 起点: 波士顿洛根国际机场 (BOS)
- 终点: 泰德·史蒂文斯安克雷奇国际机场 (ANC)
- 日期: 2025年1月12日

7. 航班 DFW-DEN404
- 价格: $150
- 起点: 达拉斯/沃斯堡国际机场 (DFW)
- 终点: 丹佛国际机场 (DEN)
- 日期: 2025年1月10日

8. 航班 ATL-HOU505
- 价格: $180
- 起点: 哈茨菲尔德-杰克逊亚特兰大国际机场 (ATL)
- 终点: 乔治·布什洲际机场 (IAH)
- 日期: 2025年1月10日
"""

# 限制此应用程序可以向LLM发出的请求数量
usage_limits = UsageLimits(request_limit=15)


async def main():
    deps = Deps(
        web_page_text=flights_web_page,
        req_origin='SFO',
        req_destination='ANC',
        req_date=datetime.date(2025, 1, 10),
    )
    message_history: list[ModelMessage] | None = None
    usage: RunUsage = RunUsage()
    # 运行代理直到找到满意的航班
    while True:
        result = await search_agent.run(
            f'为我查找从 {deps.req_origin} 到 {deps.req_destination} 于 {deps.req_date} 的航班',
            deps=deps,
            usage=usage,
            message_history=message_history,
            usage_limits=usage_limits,
        )
        if isinstance(result.output, NoFlightFound):
            print('未找到航班')
            break
        else:
            flight = result.output
            print(f'找到航班: {flight}')
            answer = Prompt.ask(
                '您想要购买此航班还是继续搜索？(buy/*search)',
                choices=['buy', 'search', ''],
                show_choices=False,
            )
            if answer == 'buy':
                seat = await find_seat(usage)
                await buy_tickets(flight, seat)
                break
            else:
                message_history = result.all_messages(
                    output_tool_return_content='请推荐另一个航班'
                )


async def find_seat(usage: RunUsage) -> SeatPreference:
    message_history: list[ModelMessage] | None = None
    while True:
        answer = Prompt.ask('您想要哪个座位？')

        result = await seat_preference_agent.run(
            answer,
            message_history=message_history,
            usage=usage,
            usage_limits=usage_limits,
        )
        if isinstance(result.output, SeatPreference):
            return result.output
        else:
            print('无法理解座位偏好。请重试。')
            message_history = result.all_messages()


async def buy_tickets(flight_details: FlightDetails, seat: SeatPreference):
    print(f'正在购买航班 {flight_details=!r} {seat=!r}...')


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
