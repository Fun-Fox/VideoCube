"""此示例展示了如何从代理流式传输markdown，并使用`rich`库来显示markdown。

运行方式：

    uv run -m pydantic_ai_examples.stream_markdown
"""

import asyncio
import os

import logfire
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import CodeBlock, Markdown
from rich.syntax import Syntax
from rich.text import Text

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

# 'if-token-present' 表示如果您没有配置logfire，将不会发送任何内容（示例仍可正常运行）
logfire.configure(token="pylf_v1_us_xNS6fZMrFGwWSHPgm3CK7h0MKPJQGSVPRzDbSyKRDwzD")
logfire.instrument_pydantic_ai()

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

model_1 = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)
model_2 = OpenAIChatModel(model_name='qwen/qwen3-coder:free',provider=provider)
model_3 = OpenAIChatModel(model_name='nvidia/nemotron-nano-9b-v2:free',provider=provider)

agent = Agent()

# 要尝试的模型及其对应的环境变量
models: list[tuple[KnownModelName, str]] = [
    model_1,
    model_2,
    model_3,
]


async def main():
    prettier_code_blocks()
    console = Console()
    prompt = '给我展示一个使用Pydantic的简短示例。'
    console.log(f'提问: {prompt}...', style='cyan')
    for model in models:
        console.log(f'使用模型: {model}')
        with Live('', console=console, vertical_overflow='visible') as live:
            async with agent.run_stream(prompt, model=model) as result:
                async for message in result.stream_output():
                    live.update(Markdown(message))
        console.log(result.usage())


def prettier_code_blocks():
    """让rich代码块更美观且更易于复制。

    来源 https://github.com/samuelcolvin/aicli/blob/v0.8.0/samuelcolvin_aicli.py#L22
    """

    class SimpleCodeBlock(CodeBlock):
        def __rich_console__(
            self, console: Console, options: ConsoleOptions
        ) -> RenderResult:
            code = str(self.text).rstrip()
            yield Text(self.lexer_name, style='dim')
            yield Syntax(
                code,
                self.lexer_name,
                theme=self.theme,
                background_color='default',
                word_wrap=True,
            )
            yield Text(f'/{self.lexer_name}', style='dim')

    Markdown.elements['fence'] = SimpleCodeBlock


if __name__ == '__main__':
    asyncio.run(main())
