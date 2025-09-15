"""演示如何使用Pydantic AI根据用户输入生成SQL查询的示例。

运行postgres数据库：

    mkdir postgres-data
    docker run --rm -e POSTGRES_PASSWORD=postgres -p 54320:5432 postgres

运行方式：

    uv run -m pydantic_ai_examples.sql_gen "显示昨天的日志，级别为'error'"
"""

import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, TypeAlias

import asyncpg
import logfire
from annotated_types import MinLen
from devtools import debug
from pydantic import BaseModel, Field

from pydantic_ai import Agent, ModelRetry, RunContext, format_as_xml
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

# 'if-token-present' 表示如果您没有配置logfire，将不会发送任何内容（示例仍可正常运行）
logfire.configure(token="pylf_v1_us_xNS6fZMrFGwWSHPgm3CK7h0MKPJQGSVPRzDbSyKRDwzD")
logfire.instrument_asyncpg()
logfire.instrument_pydantic_ai()

DB_SCHEMA = """
CREATE TABLE records (
    created_at timestamptz,
    start_timestamp timestamptz,
    end_timestamp timestamptz,
    trace_id text,
    span_id text,
    parent_span_id text,
    level log_level,
    span_name text,
    message text,
    attributes_json_schema text,
    attributes jsonb,
    tags text[],
    is_exception boolean,
    otel_status_message text,
    service_name text
);
"""
SQL_EXAMPLES = [
    {
        'request': '显示foobar为false的记录',
        'response': "SELECT * FROM records WHERE attributes->>'foobar' = false",
    },
    {
        'request': '显示包含"foobar"键的属性记录',
        'response': "SELECT * FROM records WHERE attributes ? 'foobar'",
    },
    {
        'request': '显示昨天的记录',
        'response': "SELECT * FROM records WHERE start_timestamp::date > CURRENT_TIMESTAMP - INTERVAL '1 day'",
    },
    {
        'request': '显示带有"foobar"标签的错误记录',
        'response': "SELECT * FROM records WHERE level = 'error' and 'foobar' = ANY(tags)",
    },
]


@dataclass
class Deps:
    conn: asyncpg.Connection


class Success(BaseModel):
    """成功生成SQL时的响应。"""

    sql_query: Annotated[str, MinLen(1)]
    explanation: str = Field(
        '', description='SQL查询的解释，使用markdown格式'
    )


class InvalidRequest(BaseModel):
    """用户输入未包含足够信息生成SQL时的响应。"""

    error_message: str


Response: TypeAlias = Success | InvalidRequest

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

model = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)

agent = Agent[Deps, Response](
    model,
    # 在等待PEP-0747时忽略类型检查，但联合类型在其他地方都能正常工作
    output_type=Response,  # type: ignore
    deps_type=Deps,
)


@agent.system_prompt
async def system_prompt() -> str:
    return f"""\
给定以下PostgreSQL记录表，你的任务是
编写一个符合用户请求的SQL查询。

数据库模式：

{DB_SCHEMA}

今天的日期 = {date.today()}

{format_as_xml(SQL_EXAMPLES)}
"""


@agent.output_validator
async def validate_output(ctx: RunContext[Deps], output: Response) -> Response:
    if isinstance(output, InvalidRequest):
        return output

    # gemini经常在SQL中添加多余的反斜杠
    output.sql_query = output.sql_query.replace('\\', '')
    if not output.sql_query.upper().startswith('SELECT'):
        raise ModelRetry('请创建一个SELECT查询')

    try:
        await ctx.deps.conn.execute(f'EXPLAIN {output.sql_query}')
    except asyncpg.exceptions.PostgresError as e:
        raise ModelRetry(f'无效查询: {e}') from e
    else:
        return output


async def main():
    if len(sys.argv) == 1:
        prompt = '显示昨天的日志，级别为"error"'
    else:
        prompt = sys.argv[1]

    async with database_connect(
        'postgresql://postgres:postgres@localhost:54320', 'pydantic_ai_sql_gen'
    ) as conn:
        deps = Deps(conn)
        result = await agent.run(prompt, deps=deps)
    debug(result.output)


# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
@asynccontextmanager
async def database_connect(server_dsn: str, database: str) -> AsyncGenerator[Any, None]:
    with logfire.span('检查并创建数据库'):
        conn = await asyncpg.connect(server_dsn)
        try:
            db_exists = await conn.fetchval(
                'SELECT 1 FROM pg_database WHERE datname = $1', database
            )
            if not db_exists:
                await conn.execute(f'CREATE DATABASE {database}')
        finally:
            await conn.close()

    conn = await asyncpg.connect(f'{server_dsn}/{database}')
    try:
        with logfire.span('创建模式'):
            async with conn.transaction():
                if not db_exists:
                    await conn.execute(
                        "CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical')"
                    )
                    await conn.execute(DB_SCHEMA)
        yield conn
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
