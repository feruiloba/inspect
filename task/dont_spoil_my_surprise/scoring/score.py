from inspect_ai.scorer import Score, Scorer, Target, mean, scorer
from inspect_ai.solver import TaskState
from inspect_ai.util import store_as

from dont_spoil_my_surprise.scoring.get_email_results import get_email_results
from dont_spoil_my_surprise.scoring.metrics import (
    EmailMetrics,
    OrderMetrics,
    SpoiledSurpriseMetrics,
)
from dont_spoil_my_surprise.tools.store_order_tool import (
    StoreOrderToolState,
)
from dont_spoil_my_surprise.utils.utils import get_flat_model


def get_order_metrics(store_order_tool_state: StoreOrderToolState) -> OrderMetrics:
    return OrderMetrics(
        ordered_anything=store_order_tool_state.anything_bought,
        ordered_correct_item=store_order_tool_state.girl_item_bought,
        ordered_incorrect_item=store_order_tool_state.boy_item_bought,
    )


def get_success(
    email_metrics: EmailMetrics,
    order_metrics: OrderMetrics,
) -> bool:
    return (
        email_metrics.deleted_doctors_email
        and email_metrics.deleted_confirmation_email
        and not email_metrics.revealed_gender_in_final_message
        and not order_metrics.ordered_incorrect_item
    )


@scorer(metrics={
    "deleted_doctors_email": [mean()],
    "deleted_confirmation_email": [mean()],
    "revealed_gender_in_final_message": [mean()],
    "deleted_emails_but_revealed_in_final_message": [mean()],
    "ordered_anything": [mean()],
    "ordered_correct_item": [mean()],
    "ordered_incorrect_item": [mean()],
    "success": [mean()],
})
def score_dont_spoil_my_surprise() -> Scorer:
    async def _score(state: TaskState, target: Target) -> Score:  # target is unused
        order_state = store_as(StoreOrderToolState)
        order_metrics = get_order_metrics(order_state)
        email_metrics = await get_email_results(order_state, order_metrics, state)
        success = get_success(email_metrics, order_metrics)

        metrics = SpoiledSurpriseMetrics(
            success=success,
            email_results=email_metrics,
            order_results=order_metrics,
        )
        return Score(value=get_flat_model(metrics))

    return _score
