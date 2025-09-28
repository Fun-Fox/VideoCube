"""使用Pydantic AI构建银行支持代理的小而完整的示例。

运行方式：

    uv run -m pydantic_ai_examples.bank_support
"""
import os
from dataclasses import dataclass

import logfire
from openai import NOT_GIVEN, APIStatusError, AsyncStream
from openai.types import chat
from openai.types.chat import ChatCompletionChunk
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelSettings, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse

from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv

load_dotenv()
logfire.configure(token="pylf_v1_us_xNS6fZMrFGwWSHPgm3CK7h0MKPJQGSVPRzDbSyKRDwzD")
logfire.instrument_pydantic_ai()

class DatabaseConn:
    """这是一个用于示例目的的假数据库。

    实际上，您会连接到外部数据库
    （例如PostgreSQL）来获取客户信息。
    """

    @classmethod
    async def customer_name(cls, *, id: int) -> str | None:
        if id == 123:
            return 'John'

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        if id == 123:
            if include_pending:
                return 123.45
            else:
                return 100.00
        else:
            raise ValueError('未找到客户')


@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    support_advice: str
    """返回给客户的建议"""
    block_card: bool
    """是否要冻结他们的卡片"""
    risk: int
    """查询的风险等级"""


OPENROUTER_API_KEY = "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"
# provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)
import httpx
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

        # 打印响应详情
        print("=== HTTP Response ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:1000]}...")  # 只打印前1000个字符
        print("===================")

        return response


# 然后在创建 provider 时使用这个自定义客户端
provider = OpenAIProvider(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=LoggingAsyncClient()
)# https://ai.pydantic.dev/output/#streaming-structured-output


model = OpenAIChatModel(model_name='deepgeminipro', provider=provider)

support_agent = Agent(
    model,
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    instructions=(
        '你是我们银行的一名支持代理，请给客户提供支持并判断他们查询的风险等级。'
        '请使用客户的名字进行回复。'
    ),
)


@support_agent.instructions
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"客户的名字是{customer_name!r}"


@support_agent.tool
async def customer_balance(
        ctx: RunContext[SupportDependencies], include_pending: bool
) -> str:
    """返回客户的当前账户余额。"""
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return f'${balance:.2f}'


if __name__ == '__main__':
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())

    result = support_agent.run_stream('我的余额是多少？', deps=deps)
    print(result.output)
    """
    support_advice='你好 John，您包含待处理交易的当前账户余额为 $123.45。' block_card=False risk=1
    """

    result = support_agent.run_sync('我刚刚丢了卡！', deps=deps)
    print(result.output)
    """
    support_advice="很抱歉听到这个消息，John。我们正在临时冻结您的卡片以防止未经授权的交易。" block_card=True risk=8
    """