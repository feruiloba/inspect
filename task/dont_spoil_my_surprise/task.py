from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.util import store_as
from pydantic import BaseModel, ConfigDict

from dont_spoil_my_surprise.constants import (
    EMAIL_ADDRESS,
)
from dont_spoil_my_surprise.scoring.score import (
    score_dont_spoil_my_surprise,
)
from dont_spoil_my_surprise.tools.email_tool import (
    Email,
    EmailState,
    email_tool,
    get_emails,
)
from dont_spoil_my_surprise.tools.store_order_tool import (
    StoreOrderToolState,
    get_store_items,
    store_order_tool,
)
from dont_spoil_my_surprise.utils.utils import get_flat_model, load_yaml


class SpoiledSurpriseConfig(BaseModel):
    nudge: str
    model_config = ConfigDict(extra="forbid")


def format_prompt(prompt_path: Path, config: BaseModel, **kwargs: Any) -> str:
    prompt = prompt_path.read_text()
    prompt = prompt.format(**get_flat_model(config), **kwargs)
    return prompt


def get_config() -> SpoiledSurpriseConfig:
    config_path = Path(__file__).parent / "assets" / "nudge.yaml"
    return SpoiledSurpriseConfig(**load_yaml(config_path))


@solver
def initialize_tools(initial_emails: list[Email], email_address: str):
    async def setup(state: TaskState, generate: Generate) -> TaskState:
        # Initialize EmailState
        email_state = store_as(EmailState)
        if email_state.email_address == "":
            email_state.email_address = email_address
            email_state.emails = [email.model_copy() for email in initial_emails]

        # Initialize StoreOrderToolState
        store_as(StoreOrderToolState)

        return state

    return setup


@task
def dont_spoil_my_surprise_task():
    config = get_config()
    prompt_path = Path(__file__).parent / "assets" / "task_description.txt"
    prompt = format_prompt(prompt_path, config)

    initial_emails = get_emails()
    store_items = get_store_items()

    tools = [
        email_tool(EMAIL_ADDRESS),
        store_order_tool(store_items, EMAIL_ADDRESS),
    ]

    return Task(
        setup=initialize_tools(initial_emails, EMAIL_ADDRESS),
        solver=react(tools=tools),
        scorer=score_dont_spoil_my_surprise(),
        dataset=MemoryDataset([Sample(input=prompt)]),
    )
