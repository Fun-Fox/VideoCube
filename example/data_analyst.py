from dataclasses import dataclass, field

import datasets
import duckdb
import pandas as pd

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider


@dataclass
class AnalystAgentDeps:
    output: dict[str, pd.DataFrame] = field(default_factory=dict)

    def store(self, value: pd.DataFrame) -> str:
        """将输出存储在deps中并返回引用，如Out[1]供LLM使用。"""
        ref = f'Out[{len(self.output) + 1}]'
        self.output[ref] = value
        return ref

    def get(self, ref: str) -> pd.DataFrame:
        if ref not in self.output:
            raise ModelRetry(
                f'错误: {ref} 不是有效的变量引用。请检查之前的消息并重试。'
            )
        return self.output[ref]

OPENROUTER_API_KEY = "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"
provider = OpenRouterProvider(api_key=OPENROUTER_API_KEY)

model = OpenAIChatModel(model_name='deepseek/deepseek-chat-v3.1:free',provider=provider)

analyst_agent = Agent(
    model,
    deps_type=AnalystAgentDeps,
    instructions='你是一名数据分析师，你的工作是根据用户请求分析数据。',
)


@analyst_agent.tool
def load_dataset(
    ctx: RunContext[AnalystAgentDeps],
    path: str,
    split: str = 'train',
) -> str:
    """从huggingface加载数据集的`split`。

    参数:
        ctx: Pydantic AI代理RunContext
        path: 数据集名称，格式为`<用户名称>/<数据集名称>`
        split: 加载数据集的分割（默认："train"）
    """
    # 开始从hf加载数据
    builder = datasets.load_dataset_builder(path)  # pyright: ignore[reportUnknownMemberType]
    splits: dict[str, datasets.SplitInfo] = builder.info.splits or {}  # pyright: ignore[reportUnknownMemberType]
    if split not in splits:
        raise ModelRetry(
            f'{split} 对数据集 {path} 无效。有效的分割有 {",".join(splits.keys())}'
        )

    builder.download_and_prepare()  # pyright: ignore[reportUnknownMemberType]
    dataset = builder.as_dataset(split=split)
    assert isinstance(dataset, datasets.Dataset)
    dataframe = dataset.to_pandas()
    assert isinstance(dataframe, pd.DataFrame)
    # 结束从hf加载数据

    # 将数据框存储在deps中并获取引用如"Out[1]"
    ref = ctx.deps.store(dataframe)
    # 构建加载数据集的摘要
    output = [
        f'已将数据集加载为 `{ref}`。',
        f'描述: {dataset.info.description}'
        if dataset.info.description
        else None,
        f'特征: {dataset.info.features!r}' if dataset.info.features else None,
    ]
    return '\n'.join(filter(None, output))


@analyst_agent.tool
def run_duckdb(ctx: RunContext[AnalystAgentDeps], dataset: str, sql: str) -> str:
    """在DataFrame上运行DuckDB SQL查询。

    注意，DuckDB SQL中使用的虚拟表名必须是`dataset`。

    参数:
        ctx: Pydantic AI代理RunContext
        dataset: 指向DataFrame的引用字符串
        sql: 要使用DuckDB执行的查询
    """
    data = ctx.deps.get(dataset)
    result = duckdb.query_df(df=data, virtual_table_name='dataset', sql_query=sql)
    # 将结果作为引用传递（因为DuckDB SQL可以选择多行，创建另一个庞大的数据框）
    ref = ctx.deps.store(result.df())  # pyright: ignore[reportUnknownMemberType]
    return f'已执行SQL，结果为 `{ref}`'


@analyst_agent.tool
def display(ctx: RunContext[AnalystAgentDeps], name: str) -> str:
    """显示数据框的最多5行。"""
    dataset = ctx.deps.get(name)
    return dataset.head().to_string()  # pyright: ignore[reportUnknownMemberType]


if __name__ == '__main__':
    deps = AnalystAgentDeps()
    result = analyst_agent.run_sync(
        user_prompt='计算数据集`cornell-movie-review-data/rotten_tomatoes`中有多少条负面评论',
        deps=deps,
    )
    print(result.output)
