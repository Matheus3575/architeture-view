from __future__ import annotations

from collections import defaultdict

from .builder import PropertyGraph


def graph_metrics(graph: PropertyGraph) -> dict:
    outgoing = defaultdict(int)
    incoming = defaultdict(int)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        outgoing[edge.source] += 1
        incoming[edge.target] += 1
        adjacency[edge.source].add(edge.target)
    return {
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "highest_out_degree": _top(outgoing),
        "highest_in_degree": _top(incoming),
        "strongly_connected_components": _tarjan(adjacency, set(graph.nodes)),
    }


def _top(values):
    return sorted(values.items(), key=lambda item: (-item[1], item[0]))[:10]


def _tarjan(adjacency, nodes):
    index = 0
    indices = {}
    lowlink = {}
    stack = []
    on_stack = set()
    result = []

    def visit(node):
        nonlocal index
        indices[node] = lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency.get(node, set()):
            if target not in indices:
                visit(target)
                lowlink[node] = min(lowlink[node], lowlink[target])
            elif target in on_stack:
                lowlink[node] = min(lowlink[node], indices[target])
        if lowlink[node] == indices[node]:
            component = []
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.append(target)
                if target == node:
                    break
            if len(component) > 1:
                result.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return result
