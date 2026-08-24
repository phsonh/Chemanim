from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


CREATION_KINDS = {
    "new_object": "molecule",
    "new_arrow": "arrow",
}


def _is_parameter_node(node_type: str) -> bool:
    return (
        node_type.startswith(("set_", "lerp_", "arrow_set_", "arrow_lerp_"))
        or node_type in {"mol_color", "change_image", "arrow_color", "arrow_width", "arrow_progress"}
    )


def inherited_node_parameters(
    document: dict[str, Any], through_index: int, node_type: str,
) -> dict[str, Any]:
    """Editor-only defaults inherited from previous compatible parameter nodes."""
    if not _is_parameter_node(node_type):
        return {}
    previous_nodes = document.get("nodes", [])[: through_index + 1]
    result: dict[str, Any] = {}
    ignored = {"object", "initialized"}

    # Only an identical node kind contributes defaults.  Set and Lerp are
    # intentionally independent: their values describe different operations.
    for node in reversed(previous_nodes):
        if node.get("enabled", True) and node.get("type") == node_type:
            result.update({
                key: deepcopy(value)
                for key, value in node.get("params", {}).items()
                if key not in ignored
            })
            break
    return result


def live_objects_at(document: dict[str, Any], through_index: int) -> dict[str, str]:
    """Return name -> kind for instances alive after a node index."""
    live: dict[str, str] = {}
    for index, node in enumerate(document.get("nodes", [])):
        if index > through_index:
            break
        if not node.get("enabled", True):
            continue
        node_type = node.get("type")
        params = node.get("params", {})
        if node_type in CREATION_KINDS:
            name = str(params.get("name", ""))
            if name:
                live[name] = CREATION_KINDS[node_type]
        elif node_type in {"delete", "delete_arrow"}:
            live.pop(str(params.get("object", "")), None)
    return live


def next_numbered_object_name(
    document: dict[str, Any], through_index: int, kind: str,
) -> str:
    """Allocate a monotonically increasing name; deleted names stay reserved."""
    prefix = {"molecule": "molecule", "arrow": "arrow"}[kind]
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    highest = 0
    # Scan the whole history, including nodes located after the insertion
    # point. Moving or deleting a node must never make a previously issued
    # identifier available again.
    for node in document.get("nodes", []):
        if node.get("type") not in CREATION_KINDS or CREATION_KINDS[node["type"]] != kind:
            continue
        match = pattern.fullmatch(str(node.get("params", {}).get("name", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}{highest + 1}"
