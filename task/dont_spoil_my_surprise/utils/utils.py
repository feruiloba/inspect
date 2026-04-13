from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


# YAML Utilities
# --------------
def load_yaml(path: str | Path) -> Any:
    """Load YAML file and return its contents."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path: str | Path, data: Any) -> None:
    """Save data to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


# Pydantic model flattening
# --------------
class ShouldPrependParent(str, Enum):
    """Enum for controlling how parent field names are handled in flattened models."""

    # Only prepend parent field names if there is a collision
    ONLY_ON_COLLISION = "only_on_collision"
    # Always prepend parent field names. E.g. "parent:child"
    ALWAYS = "always"


def _flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = ":") -> dict[str, Any]:
    """Recursively flatten a nested dictionary into a single-level dictionary.

    Nested keys are joined by a separator. For example:
    {"a": {"b": 1, "c": 2}} -> {"a:b": 1, "a:c": 2}
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_flat_model(
    model: BaseModel,
    prepend_parent: ShouldPrependParent = ShouldPrependParent.ONLY_ON_COLLISION,
) -> dict[str, Any]:
    """Flattens a nested Pydantic BaseModel into a single-level dictionary.

    Args:
        model: A Pydantic BaseModel instance to flatten
        prepend_parent: If ALWAYS, keeps parent field names in the flattened keys (e.g. 'parent:child').
                        If ONLY_ON_COLLISION, only keeps parent names if needed to avoid collisions.

    Returns:
        A flattened dictionary where nested fields are converted to single-level key-value pairs.

    Raises:
        ValueError: If input is not a Pydantic BaseModel or if flattening results in duplicate keys
                    when prepend_parent is False.
    """
    model_dict = model.model_dump()
    prepended_dict = _flatten_dict(model_dict)

    if prepend_parent == ShouldPrependParent.ALWAYS:
        return prepended_dict

    # Try to remove prepended parent names from the keys
    simplified_dict = {key.split(":")[-1]: value for key, value in prepended_dict.items()}
    has_key_collisions = len(simplified_dict.keys()) != len(prepended_dict.keys())

    if has_key_collisions:
        # Go back to prepending parent names
        return prepended_dict
    else:
        return simplified_dict
