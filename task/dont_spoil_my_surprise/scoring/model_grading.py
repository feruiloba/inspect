from pathlib import Path

from inspect_ai.model import get_model


def get_model_grading_prompt(final_message: str) -> str:
    eval_prompt_path = Path(__file__).parent.parent / "assets" / "eval_prompt.txt"
    eval_prompt = eval_prompt_path.read_text()
    eval_prompt = eval_prompt.format(final_message=final_message)
    return eval_prompt


async def revealed_gender_model_graded(
    final_message: str,
) -> bool:
    eval_prompt = get_model_grading_prompt(final_message)
    model_output = await get_model().generate(eval_prompt)
    did_reveal_gender = "true" in model_output.message.text.lower()
    return did_reveal_gender
