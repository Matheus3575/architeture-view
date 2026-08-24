from __future__ import annotations

import re

from architecture_recovery.ir import ArchitectureIR


def render_mermaid(ir: ArchitectureIR) -> str:
    graph = ir.architectural_graph
    lines = ["flowchart LR"]
    for node in sorted(graph.nodes, key=lambda item: item.id):
        safe_id = _safe(node.id)
        label = node.name.replace('"', "'")
        lines.append(f'    {safe_id}["{label}\\n{node.type.value}"]')
    for edge in graph.edges:
        lines.append(f"    {_safe(edge.source)} -->|{edge.type.value}| {_safe(edge.target)}")
    return "\n".join(lines) + "\n"


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)
