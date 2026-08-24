from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from architecture_recovery.ir import ArchitectureIR


def render_graphml(ir: ArchitectureIR) -> bytes:
    """Render the aggregated Architectural Graph, never inventing relations."""
    graph_data = ir.architectural_graph
    root = Element("graphml", {"xmlns": "http://graphml.graphdrawing.org/xmlns"})
    graph = SubElement(root, "graph", {"id": "architecture", "edgedefault": "directed"})
    for node in sorted(graph_data.nodes, key=lambda item: item.id):
        element = SubElement(graph, "node", {"id": node.id})
        SubElement(element, "data", {"key": "type"}).text = node.type.value
        SubElement(element, "data", {"key": "name"}).text = node.name
    for index, edge in enumerate(graph_data.edges):
        SubElement(
            graph,
            "edge",
            {"id": f"e{index}", "source": edge.source, "target": edge.target},
        )
    return tostring(root, encoding="utf-8", xml_declaration=True)
