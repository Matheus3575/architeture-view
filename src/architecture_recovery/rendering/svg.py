from __future__ import annotations

import html
import re
from collections import defaultdict
from typing import Iterable

from architecture_recovery.visualization import (
    VisualizationEdge,
    VisualizationNode,
    VisualizationReadModel,
    validate_visualization_read_model,
)


class SemanticSvgRenderer:
    """Render only an existing VisualizationReadModel into deterministic SVG."""

    NODE_WIDTH = 150
    NODE_HEIGHT = 58
    X_GAP = 35
    BAND_HEIGHT = 125
    LEFT = 55
    TOP = 42
    RIGHT = 320
    HYPOTHESIS_HEIGHT = 92
    IMPORTANT_RELATIONS = {
        "ROUTES_TO", "DEPENDS_ON", "QUERIES", "CONNECTS_TO", "DEPLOYS",
        "PUBLISHES", "CONSUMES", "FRAMEWORK_DEPENDENCY", "RESPONSE_SCHEMA",
        "ROUTER_INCLUSION",
    }
    STRUCTURAL_RELATIONS = {"IMPORTS", "CONTAINS"}

    def render(self, model: VisualizationReadModel) -> str:
        report = validate_visualization_read_model(
            model,
            {item.id for item in model.evidence},
        )
        if not report.valid:
            raise ValueError("Cannot render invalid VisualizationReadModel: " + "; ".join(report.errors))

        groups = self._groups(model.nodes)
        positions, bands, width, height = self._layout(groups, model.hypotheses)
        hypothesis_refs = self._hypothesis_refs(model)
        svg: list[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
                f'role="img" aria-labelledby="title description">'
            ),
            f'<title id="title">{_escape(model.repository.name)} architecture</title>',
            (
                '<desc id="description">Deterministic semantic architecture projection '
                'rendered from VisualizationReadModel.</desc>'
            ),
            "<defs>",
            (
                '<marker id="arrow-observed" markerWidth="8" markerHeight="8" '
                'refX="7" refY="4" orient="auto" markerUnits="strokeWidth">'
                '<path d="M0,0 L8,4 L0,8 z" fill="#374151"/></marker>'
            ),
            (
                '<marker id="arrow-inferred" markerWidth="8" markerHeight="8" '
                'refX="7" refY="4" orient="auto" markerUnits="strokeWidth">'
                '<path d="M0,0 L8,4 L0,8 z" fill="#2563eb"/></marker>'
            ),
            "</defs>",
            "<style>.inspectable:hover{filter:brightness(0.94)}"
            ".edge-structural{stroke-linecap:round}"
            ".edge-architectural{stroke-linecap:round}</style>",
            '<g id="layout-bands" aria-label="semantic groups">',
        ]

        for group_key, y, group_nodes in bands:
            group_id = f"group-{_safe_id(group_key)}"
            label = _escape(self._group_label(group_key))
            band_width = width - self.LEFT - self.RIGHT
            svg.append(
                f'<g id="{group_id}" data-layout-group="{_escape(group_key)}">'
                f'<rect x="{self.LEFT - 20}" y="{y - 30}" width="{band_width + 40}" '
                f'height="{self.BAND_HEIGHT - 10}" rx="12" fill="#f8fafc" '
                f'stroke="#cbd5e1"/>'
                f'<text x="{self.LEFT - 5}" y="{y - 8}" font-family="sans-serif" '
                f'font-size="13" font-weight="bold" fill="#334155">{label}</text></g>'
            )
        svg.append("</g>")

        ordered_edges = sorted(model.edges, key=lambda item: (item.source, item.target, item.kind, item.id))
        for edge in ordered_edges:
            source = positions.get(edge.source)
            target = positions.get(edge.target)
            if source is None or target is None:
                continue
            svg.append(self._edge_svg(edge, source, target, hypothesis_refs))

        for node in sorted(model.nodes, key=lambda item: item.id):
            x, y = positions[node.id]
            svg.append(self._node_svg(node, x, y, model.edges, hypothesis_refs))

        svg.extend(self._hypotheses_svg(model, width, height))
        svg.append("</svg>")
        return "\n".join(svg) + "\n"

    def _groups(self, nodes: Iterable[VisualizationNode]):
        grouped: dict[str, list[VisualizationNode]] = defaultdict(list)
        for node in nodes:
            grouped[self._group_key(node)].append(node)
        return {
            key: sorted(items, key=lambda item: item.id)
            for key, items in sorted(grouped.items(), key=lambda item: self._group_order(item[0]))
        }

    def _layout(self, groups, hypotheses):
        positions: dict[str, tuple[int, int]] = {}
        bands: list[tuple[str, int, list[VisualizationNode]]] = []
        max_count = max((len(items) for items in groups.values()), default=1)
        content_width = max(
            760,
            self.LEFT + max_count * (self.NODE_WIDTH + self.X_GAP) + self.RIGHT,
        )
        for band_index, (group_key, items) in enumerate(groups.items()):
            y = self.TOP + band_index * self.BAND_HEIGHT
            bands.append((group_key, y, items))
            for index, node in enumerate(items):
                x = self.LEFT + index * (self.NODE_WIDTH + self.X_GAP)
                positions[node.id] = (x, y + 8)
        base_height = self.TOP + max(len(groups), 1) * self.BAND_HEIGHT + 25
        height = base_height + (self.HYPOTHESIS_HEIGHT if hypotheses else 0)
        return positions, bands, content_width, height

    def _edge_svg(
        self,
        edge: VisualizationEdge,
        source,
        target,
        hypothesis_refs: dict[str, set[str]],
    ) -> str:
        sx, sy = source
        tx, ty = target
        path = _orthogonal_path((sx, sy), (tx, ty), self.NODE_WIDTH, self.NODE_HEIGHT)
        stroke, dash, marker = {
            "observed": ("#374151", "", "arrow-observed"),
            "inferred": ("#2563eb", "7 4", "arrow-inferred"),
            "uncertain": ("#d97706", "3 4", "arrow-observed"),
            "unknown": ("#6b7280", "2 5", "arrow-observed"),
        }[edge.status.value]
        relation_class = self._relation_class(edge.kind)
        width = "2.8" if relation_class == "architectural" else "1.2"
        opacity = "1" if relation_class == "architectural" else "0.58"
        style = f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"'
        if dash:
            style += f' stroke-dasharray="{dash}"'
        associations = _hypothesis_associations(edge.evidence_refs, hypothesis_refs)
        return (
            f'<g id="edge-{_safe_id(edge.id)}" data-read-model-id="{_escape(edge.id)}" '
            f'class="inspectable edge-{relation_class}" data-source="{_escape(edge.source)}" '
            f'data-target="{_escape(edge.target)}" data-kind="{_escape(edge.kind)}" '
            f'data-relation-class="{relation_class}" '
            f'data-related-node-ids="{_escape(edge.source + "," + edge.target)}" '
            f'data-hypothesis-associations="{_escape(_refs(associations))}" '
            f'data-origin-ref="{_escape(edge.origin_ref or "")}" '
            f'data-evidence-refs="{_escape(_refs(edge.evidence_refs))}" '
            f'data-status="{edge.status.value}" data-confidence="{edge.confidence}">'
            f'<path d="{path}" fill="none" {style} marker-end="url(#{marker})"/>'
            f'<text x="{(sx + tx + self.NODE_WIDTH) // 2}" '
            f'y="{(sy + ty + self.NODE_HEIGHT) // 2 - 4}" '
            f'font-family="sans-serif" font-size="10" fill="{stroke}" '
            f'text-anchor="middle">{_escape(edge.kind)}</text></g>'
        )

    def _node_svg(self, node: VisualizationNode, x: int, y: int, edges, hypothesis_refs: dict[str, set[str]]) -> str:
        element_id = f"node-{_safe_id(node.id)}"
        related_edges = sorted(
            edge.id for edge in edges
            if edge.source == node.id or edge.target == node.id
        )
        associations = _hypothesis_associations(node.evidence_refs, hypothesis_refs)
        attrs = (
            f'id="{element_id}" data-read-model-id="{_escape(node.id)}" '
            f'class="inspectable node-{_safe_id(node.kind)}" '
            f'data-label="{_escape(node.label)}" data-role="{_escape(node.role or "")}" '
            f'data-layer="{_escape(node.layer or "")}" '
            f'data-related-edge-ids="{_escape(_refs(related_edges))}" '
            f'data-hypothesis-associations="{_escape(_refs(associations))}" '
            f'data-origin-ref="{_escape(node.origin_ref or "")}" '
            f'data-evidence-refs="{_escape(_refs(node.evidence_refs))}" '
            f'data-status="{node.status.value}" data-confidence="{node.confidence}" '
            f'data-kind="{_escape(node.kind)}"'
        )
        label = _escape(node.label)
        sublabel = _escape(node.role or node.kind)
        if node.kind == "endpoint":
            shape = f'<ellipse cx="{x + self.NODE_WIDTH // 2}" cy="{y + 29}" rx="70" ry="25" fill="#dbeafe" stroke="#2563eb"/>'
        elif node.kind == "unknown":
            points = f"{x + 75},{y} {x + 150},{y + 29} {x + 75},{y + 58} {x},{y + 29}"
            shape = f'<polygon points="{points}" fill="#f3f4f6" stroke="#6b7280" stroke-dasharray="3 3"/>'
        elif node.kind in {"database", "cache", "queue", "message_broker"}:
            shape = (
                f'<path d="M{x + 5},{y + 12} a70,10 0 1,0 140,0 a70,10 0 1,0 -140,0 '
                f'v34 a70,10 0 1,0 140,0 v-34" fill="#dcfce7" stroke="#15803d"/>'
            )
        elif node.kind in {"external_dependency", "external_service"}:
            shape = f'<rect x="{x}" y="{y}" width="150" height="58" rx="8" fill="#fef3c7" stroke="#b45309" stroke-dasharray="6 3"/>'
        elif node.layout_hints.get("semantic_kind") == "infrastructure" or node.kind in {"container", "infrastructure"}:
            shape = f'<rect x="{x}" y="{y}" width="150" height="58" rx="4" fill="#dcfce7" stroke="#15803d"/>'
        else:
            shape = f'<rect x="{x}" y="{y}" width="150" height="58" rx="8" fill="#e0e7ff" stroke="#4338ca"/>'
        return (
            f'<g {attrs}>{shape}'
            f'<text x="{x + 75}" y="{y + 25}" font-family="sans-serif" font-size="12" '
            f'font-weight="bold" text-anchor="middle" fill="#111827">{label}</text>'
            f'<text x="{x + 75}" y="{y + 43}" font-family="sans-serif" font-size="9" '
            f'text-anchor="middle" fill="#475569">{sublabel}</text></g>'
        )

    def _hypotheses_svg(self, model: VisualizationReadModel, width: int, height: int) -> list[str]:
        if not model.hypotheses:
            return []
        y = height - self.HYPOTHESIS_HEIGHT + 18
        lines = [
            f'<g id="architecture-hypotheses" aria-label="Architecture hypotheses">',
            f'<rect x="{self.LEFT - 20}" y="{y - 20}" width="{width - self.LEFT - self.RIGHT + 40}" '
            f'height="{self.HYPOTHESIS_HEIGHT - 5}" rx="10" fill="#fff7ed" stroke="#fdba74"/>',
            f'<text x="{self.LEFT - 5}" y="{y}" font-family="sans-serif" font-size="13" '
            f'font-weight="bold" fill="#9a3412">Architecture hypotheses</text>',
        ]
        for index, hypothesis in enumerate(sorted(model.hypotheses, key=lambda item: item.pattern)):
            x = self.LEFT + index * 190
            ref = _refs(hypothesis.evidence_refs)
            lines.append(
                f'<g id="hypothesis-{_safe_id(hypothesis.pattern)}" '
                f'data-read-model-id="{_escape(hypothesis.pattern)}" '
                f'class="inspectable hypothesis" data-pattern="{_escape(hypothesis.pattern)}" '
                f'data-supporting-evidence="{_escape(_refs(hypothesis.supporting_evidence))}" '
                f'data-contradicting-evidence="{_escape(_refs(hypothesis.contradicting_evidence))}" '
                f'data-explanation="{_escape(hypothesis.explanation)}" '
                f'data-evidence-refs="{_escape(ref)}" data-status="{hypothesis.status.value}" '
                f'data-confidence="{hypothesis.confidence}">'
                f'<text x="{x}" y="{y + 25}" font-family="sans-serif" font-size="11" '
                f'font-weight="bold" fill="#7c2d12">{_escape(hypothesis.pattern)}</text>'
                f'<text x="{x}" y="{y + 43}" font-family="sans-serif" font-size="10" '
                f'fill="#7c2d12">{hypothesis.status.value.upper()} '
                f'{hypothesis.confidence:.2f}</text></g>'
            )
        lines.append("</g>")
        return lines

    @staticmethod
    def _group_key(node: VisualizationNode) -> str:
        explicit = node.layout_hints.get("group") or node.layer or node.layout_hints.get("preferred_layer")
        if explicit:
            return str(explicit).lower()
        semantic = str(node.layout_hints.get("semantic_kind") or node.kind).lower()
        if node.layout_hints.get("entrypoint") or semantic in {"endpoint", "http_endpoint", "router"}:
            return "presentation"
        if semantic in {"application", "service", "controller", "controller_like"} or node.role in {"service", "controller"}:
            return "application"
        if semantic in {"repository", "database", "cache", "queue", "message_broker"} or node.role in {"repository", "persistence"}:
            return "persistence"
        if node.layout_hints.get("external") or semantic in {"external", "external_dependency", "external_service"}:
            return "external"
        if node.layout_hints.get("semantic_kind") == "infrastructure" or semantic in {"infrastructure", "container"}:
            return "infrastructure"
        if semantic in {"component", "module", "domain"}:
            return "domain"
        return semantic

    @staticmethod
    def _relation_class(kind: str) -> str:
        if kind in SemanticSvgRenderer.STRUCTURAL_RELATIONS:
            return "structural"
        return "architectural" if kind in SemanticSvgRenderer.IMPORTANT_RELATIONS else "relation"

    @staticmethod
    def _hypothesis_refs(model: VisualizationReadModel):
        return {
            item.pattern: set(item.evidence_refs) | set(item.supporting_evidence) | set(item.contradicting_evidence)
            for item in model.hypotheses
        }

    @staticmethod
    def _group_label(group_key: str) -> str:
        return group_key.replace("_", " ").replace("-", " ").title()

    @staticmethod
    def _group_order(group_key: str):
        order = {
            "presentation": 0,
            "application": 1,
            "domain": 2,
            "persistence": 3,
            "infrastructure": 4,
            "external": 5,
            "unknown": 6,
        }
        return order.get(group_key, 50), group_key


def render_svg(model: VisualizationReadModel) -> str:
    return SemanticSvgRenderer().render(model)


def _refs(refs: Iterable[str]) -> str:
    return ",".join(sorted(set(refs)))


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", value)
    if not safe or safe[0].isdigit():
        safe = "x-" + safe
    return safe


def _hypothesis_associations(evidence_refs: Iterable[str], hypothesis_refs: dict[str, set[str]]) -> list[str]:
    refs = set(evidence_refs)
    return sorted(pattern for pattern, associated in hypothesis_refs.items() if refs & associated)


def _orthogonal_path(source, target, width: int, height: int) -> str:
    sx, sy = source
    tx, ty = target
    if sy == ty:
        start_x = sx + width if sx <= tx else sx
        end_x = tx if sx <= tx else tx + width
        y = sy + height // 2
        return f"M{start_x} {y} L{end_x} {y}"
    if sy < ty:
        start = (sx + width // 2, sy + height)
        end = (tx + width // 2, ty)
    else:
        start = (sx + width // 2, sy)
        end = (tx + width // 2, ty + height)
    mid_y = (start[1] + end[1]) // 2
    return f"M{start[0]} {start[1]} L{start[0]} {mid_y} L{end[0]} {mid_y} L{end[0]} {end[1]}"


__all__ = ["SemanticSvgRenderer", "render_svg"]
