from __future__ import annotations

import html
import json
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
    INSPECTION_MIN_HEIGHT = 740
    IMPORTANT_RELATIONS = {
        "ROUTES_TO", "DEPENDS_ON", "QUERIES", "CONNECTS_TO", "DEPLOYS",
        "PUBLISHES", "CONSUMES", "FRAMEWORK_DEPENDENCY", "RESPONSE_SCHEMA",
        "ROUTER_INCLUSION",
    }
    STRUCTURAL_RELATIONS = {"IMPORTS", "CONTAINS"}

    def render(self, model: VisualizationReadModel, mode: str = "static") -> str:
        mode_key = mode.lower()
        if mode_key not in {"static", "animated"}:
            raise ValueError("SVG render mode must be 'static' or 'animated'")
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
                f'class="mode-{mode_key}" data-animation-mode="{mode_key}" '
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
            "<style>"
            ".inspectable:hover{filter:brightness(0.94)}"
            ".edge-structural{stroke-linecap:round}"
            ".edge-architectural{stroke-linecap:round}"
            "@keyframes flowPulse{0%,100%{stroke-opacity:.72}"
            "50%{stroke-opacity:1;stroke-width:3.5}}"
            "@keyframes resourcePulse{0%,100%{opacity:.55}"
            "50%{opacity:1}}"
            ".mode-animated .edge-architectural[data-status=observed] path,"
            ".mode-animated .edge-architectural[data-status=inferred] path"
            "{animation:flowPulse 2.4s ease-in-out infinite}"
            ".mode-animated .node-database[data-status=observed] .activity-indicator,"
            ".mode-animated .node-database[data-status=inferred] .activity-indicator,"
            ".mode-animated .node-cache[data-status=observed] .activity-indicator,"
            ".mode-animated .node-cache[data-status=inferred] .activity-indicator,"
            ".mode-animated .node-queue[data-status=observed] .activity-indicator,"
            ".mode-animated .node-queue[data-status=inferred] .activity-indicator,"
            ".mode-animated .node-message_broker[data-status=observed] .activity-indicator,"
            ".mode-animated .node-message_broker[data-status=inferred] .activity-indicator,"
            ".mode-animated .node-infrastructure[data-status=observed] .activity-indicator,"
            ".mode-animated .node-infrastructure[data-status=inferred] .activity-indicator,"
            ".mode-animated .node-container[data-status=observed] .activity-indicator,"
            ".mode-animated .node-container[data-status=inferred] .activity-indicator"
            "{animation:resourcePulse 1.8s ease-in-out infinite}"
            ".mode-animated .selected path,.mode-animated .selected .activity-indicator"
            "{animation:none!important}"
            "@media (prefers-reduced-motion:reduce){.mode-animated *"
            "{animation:none!important}}</style>",
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
        svg.extend(_inspection_panel(width, height))
        svg.append(_interaction_script(model))
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
        height = max(base_height + (self.HYPOTHESIS_HEIGHT if hypotheses else 0), self.INSPECTION_MIN_HEIGHT)
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
            f'class="inspectable edge-{relation_class}" data-selection-kind="edge" '
            f'data-source="{_escape(edge.source)}" '
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
            f'class="inspectable node-{_safe_id(node.kind)}" data-selection-kind="node" '
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
        activity = _activity_marker(node, x, y)
        return (
            f'<g {attrs}>{shape}{activity}'
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
                f'class="inspectable hypothesis" data-selection-kind="hypothesis" '
                f'data-pattern="{_escape(hypothesis.pattern)}" '
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


def render_svg(model: VisualizationReadModel, mode: str = "static") -> str:
    return SemanticSvgRenderer().render(model, mode=mode)


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


def _activity_marker(node: VisualizationNode, x: int, y: int) -> str:
    known_infrastructure = (
        node.kind in {"database", "cache", "queue", "message_broker", "container", "infrastructure"}
        or node.layout_hints.get("semantic_kind") == "infrastructure"
    )
    if not known_infrastructure or node.status.value not in {"observed", "inferred"}:
        return ""
    return (
        f'<circle class="activity-indicator" data-animation-semantic="resource-identified" '
        f'cx="{x + 136}" cy="{y + 12}" r="4" fill="#15803d" opacity=".55"/>'
    )


def _inspection_panel(width: int, height: int) -> list[str]:
    x = width - SemanticSvgRenderer.RIGHT + 20
    lines = [
        f'<g id="inspection-panel" aria-label="Evidence inspection panel">',
        f'<rect x="{x}" y="20" width="{SemanticSvgRenderer.RIGHT - 40}" '
        f'height="{height - 40}" rx="10" fill="#ffffff" stroke="#94a3b8"/>',
        f'<text x="{x + 16}" y="48" font-family="sans-serif" font-size="14" '
        'font-weight="bold" fill="#1e293b">Inspection</text>',
        f'<text x="{x + 16}" y="70" font-family="sans-serif" font-size="10" '
        'fill="#475569">Animation:</text>',
        f'<rect class="animation-control" data-animation-mode="static" '
        f'x="{x + 82}" y="54" width="58" height="22" rx="4" '
        'fill="#e2e8f0" stroke="#64748b"/>',
        f'<text class="animation-control" data-animation-mode="static" '
        f'x="{x + 111}" y="69" text-anchor="middle" font-family="sans-serif" '
        'font-size="9" fill="#334155">STATIC</text>',
        f'<rect class="animation-control" data-animation-mode="animated" '
        f'x="{x + 146}" y="54" width="72" height="22" rx="4" '
        'fill="#f1f5f9" stroke="#94a3b8"/>',
        f'<text class="animation-control" data-animation-mode="animated" '
        f'x="{x + 182}" y="69" text-anchor="middle" font-family="sans-serif" '
        'font-size="9" fill="#334155">ANIMATED</text>',
        f'<rect class="inspect-clear" x="{x + SemanticSvgRenderer.RIGHT - 105}" '
        'y="30" width="65" height="24" rx="5" fill="#e2e8f0" '
        'stroke="#64748b"/>',
        f'<text class="inspect-clear" x="{x + SemanticSvgRenderer.RIGHT - 72}" '
        'y="47" text-anchor="middle" font-family="sans-serif" font-size="10" '
        'fill="#334155">Clear</text>',
    ]
    for index in range(32):
        lines.append(
            f'<text id="inspection-line-{index}" x="{x + 16}" y="{100 + index * 20}" '
            'font-family="sans-serif" font-size="10" fill="#334155"></text>'
        )
    lines.append("</g>")
    return lines


def _interaction_payload(model: VisualizationReadModel) -> dict:
    edges_by_node: dict[str, list[str]] = {node.id: [] for node in model.nodes}
    for edge in sorted(model.edges, key=lambda item: item.id):
        edges_by_node.setdefault(edge.source, []).append(edge.id)
        edges_by_node.setdefault(edge.target, []).append(edge.id)

    def source_data(item):
        return item.source.model_dump(mode="json") if item.source else None

    hypothesis_refs = SemanticSvgRenderer._hypothesis_refs(model)
    nodes = {}
    for node in sorted(model.nodes, key=lambda item: item.id):
        nodes[node.id] = {
            "label": node.label,
            "kind": node.kind,
            "role": node.role,
            "layer": node.layer,
            "status": node.status.value,
            "confidence": node.confidence,
            "origin_ref": node.origin_ref,
            "evidence_refs": sorted(set(node.evidence_refs)),
            "related_edge_ids": sorted(set(edges_by_node.get(node.id, []))),
            "hypothesis_associations": _hypothesis_associations(
                node.evidence_refs,
                hypothesis_refs,
            ),
        }

    edges = {}
    for edge in sorted(model.edges, key=lambda item: item.id):
        edges[edge.id] = {
            "source": edge.source,
            "target": edge.target,
            "kind": edge.kind,
            "relation_class": SemanticSvgRenderer._relation_class(edge.kind),
            "status": edge.status.value,
            "confidence": edge.confidence,
            "origin_ref": edge.origin_ref,
            "evidence_refs": sorted(set(edge.evidence_refs)),
            "hypothesis_associations": _hypothesis_associations(
                edge.evidence_refs,
                hypothesis_refs,
            ),
        }

    evidence = {}
    for item in sorted(model.evidence, key=lambda item: item.id):
        evidence[item.id] = {
            "source_type": item.source_type,
            "detail": item.detail,
            "source": source_data(item),
            "weight": item.weight,
        }

    hypotheses = {}
    for item in sorted(model.hypotheses, key=lambda item: item.pattern):
        hypotheses[item.pattern] = {
            "status": item.status.value,
            "confidence": item.confidence,
            "explanation": item.explanation,
            "supporting_evidence": sorted(set(item.supporting_evidence)),
            "contradicting_evidence": sorted(set(item.contradicting_evidence)),
            "evidence_refs": sorted(set(item.evidence_refs)),
        }

    return {
        "nodes": nodes,
        "edges": edges,
        "evidence": evidence,
        "hypotheses": hypotheses,
        "related_edges": {
            key: sorted(value) for key, value in sorted(edges_by_node.items())
        },
    }


def _interaction_script(model: VisualizationReadModel, mode: str = "static") -> str:
    payload = json.dumps(
        _interaction_payload(model),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).replace("]]>", "]]\\u003e")
    script = f"""<script type="application/ecmascript"><![CDATA[
(function () {{
  "use strict";
  const DATA = {payload};
  const root = document.documentElement;
  const elements = Array.from(root.querySelectorAll(".inspectable"));
  const byId = new Map(elements.map(function (element) {{
    return [element.getAttribute("data-read-model-id"), element];
  }}));
  const lines = Array.from({{length: 32}}, function (_, index) {{
    return document.getElementById("inspection-line-" + index);
  }});
  const defaultLines = [
    "Select a node, edge or hypothesis.",
    "Click Clear to remove the selection."
  ];
  const animationControls = Array.from(root.querySelectorAll(".animation-control"));

  function value(item) {{
    return item === null || item === undefined || item === "" ? "UNKNOWN" : String(item);
  }}

  function setPanel(items) {{
    lines.forEach(function (line, index) {{
      line.textContent = index < items.length ? items[index] : "";
    }});
  }}

  function sourceText(source) {{
    if (!source) return ["file: UNKNOWN", "line: UNKNOWN", "symbol: UNKNOWN"];
    const line = source.start_line
      ? (source.end_line && source.end_line !== source.start_line
        ? source.start_line + "-" + source.end_line
        : source.start_line)
      : "UNKNOWN";
    return [
      "file: " + value(source.path),
      "line: " + value(line),
      "symbol: " + value(source.symbol)
    ];
  }}

  function evidenceLines(refs, context) {{
    const output = ["Evidence (" + context + "):"];
    if (!refs || refs.length === 0) {{
      output.push("  UNKNOWN");
      return output;
    }}
    refs.forEach(function (ref) {{
      const evidence = DATA.evidence[ref];
      if (!evidence) {{
        output.push("  " + ref + ": UNKNOWN");
        return;
      }}
      output.push("  " + ref + " [" + value(evidence.source_type) + "]");
      output.push("  observation: " + value(evidence.detail));
      output.push("  expression: UNKNOWN");
      output.push("  origin: " + value(evidence.source_type));
      sourceText(evidence.source).forEach(function (part) {{
        output.push("  " + part);
      }});
    }});
    return output;
  }}

  function relatedSet(kind, id) {{
    const keep = new Set([id]);
    if (kind === "node" && DATA.nodes[id]) {{
      DATA.nodes[id].related_edge_ids.forEach(function (edgeId) {{
        keep.add(edgeId);
      }});
    }}
    if (kind === "edge" && DATA.edges[id]) {{
      keep.add(DATA.edges[id].source);
      keep.add(DATA.edges[id].target);
    }}
    if (kind === "hypothesis") {{
      elements.forEach(function (element) {{
        const associations = (element.getAttribute("data-hypothesis-associations") || "").split(",");
        if (associations.indexOf(id) >= 0) {{
          keep.add(element.getAttribute("data-read-model-id"));
        }}
      }});
    }}
    return keep;
  }}

  function select(kind, id) {{
    const item = kind === "node" ? DATA.nodes[id]
      : kind === "edge" ? DATA.edges[id]
      : DATA.hypotheses[id];
    if (!item) {{
      clear();
      return;
    }}
    const keep = relatedSet(kind, id);
    elements.forEach(function (element) {{
      const elementId = element.getAttribute("data-read-model-id");
      element.classList.toggle("dimmed", !keep.has(elementId));
      element.classList.toggle("selected", elementId === id);
    }});
    let output;
    if (kind === "node") {{
      output = [
        "NODE: " + value(item.label),
        "kind: " + value(item.kind),
        "role: " + value(item.role),
        "layer/group: " + value(item.layer),
        "status: " + value(item.status),
        "confidence: " + value(item.confidence),
        "origin: " + value(item.origin_ref),
        "edges: " + value(item.related_edge_ids.join(", ")),
        "hypotheses: " + value(item.hypothesis_associations.join(", "))
      ].concat(evidenceLines(item.evidence_refs, id));
    }} else if (kind === "edge") {{
      output = [
        "EDGE: " + value(id),
        "source: " + value(item.source),
        "target: " + value(item.target),
        "kind: " + value(item.kind),
        "class: " + value(item.relation_class),
        "status: " + value(item.status),
        "confidence: " + value(item.confidence),
        "origin: " + value(item.origin_ref)
      ].concat(evidenceLines(item.evidence_refs, id));
    }} else {{
      output = [
        "HYPOTHESIS: " + value(id),
        "status: " + value(item.status),
        "confidence: " + value(item.confidence),
        "explanation: " + value(item.explanation),
        "supporting: " + value(item.supporting_evidence.join(", ")),
        "contradicting: " + value(item.contradicting_evidence.join(", "))
      ].concat(evidenceLines(item.evidence_refs, id));
      item.supporting_evidence.concat(item.contradicting_evidence).forEach(function (ref) {{
        if (item.evidence_refs.indexOf(ref) < 0) {{
          output.push("evidence ref: " + ref);
        }}
      }});
    }}
    setPanel(output);
  }}

  function setMode(mode) {{
    const normalized = mode === "animated" ? "animated" : "static";
    root.setAttribute("data-animation-mode", normalized);
    root.classList.remove("mode-static", "mode-animated");
    root.classList.add("mode-" + normalized);
    animationControls.forEach(function (control) {{
      const active = control.getAttribute("data-animation-mode") === normalized;
      control.setAttribute("aria-pressed", active ? "true" : "false");
      control.setAttribute("data-active", active ? "true" : "false");
    }});
  }}

  function clear() {{
    elements.forEach(function (element) {{
      element.classList.remove("dimmed");
      element.classList.remove("selected");
    }});
    setPanel(defaultLines);
  }}

  elements.forEach(function (element) {{
    element.addEventListener("click", function (event) {{
      event.stopPropagation();
      select(element.getAttribute("data-selection-kind"),
        element.getAttribute("data-read-model-id"));
    }});
  }});
  animationControls.forEach(function (control) {{
    control.addEventListener("click", function (event) {{
      event.stopPropagation();
      setMode(control.getAttribute("data-animation-mode"));
    }});
  }});
  Array.from(root.querySelectorAll(".inspect-clear")).forEach(function (element) {{
    element.addEventListener("click", function (event) {{
      event.stopPropagation();
      clear();
    }});
  }});
  root.addEventListener("click", function (event) {{
    if (event.target === root) clear();
  }});
  setMode(root.getAttribute("data-animation-mode") || "static");
  clear();
}})();
]]></script>"""
    return script


__all__ = ["SemanticSvgRenderer", "render_svg"]
