from __future__ import annotations

import hashlib
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .evidence import EvidenceGroup, EvidencePayloadIndex
from .projection import ArchitecturalProjectionBuilder, ArchitecturalSignificance, HighLevelArchitectureProjection
from architecture_recovery.profiling import AnalysisProfile, profile_stage

from architecture_recovery.ir import (
    ArchitectureIR,
    Edge,
    Evidence,
    EvidenceStatus,
    InfrastructureResource,
    Node,
    RepositoryInfo,
    SourceRef,
)


class VisualizationNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    label: str
    role: str | None = None
    layer: str | None = None
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_group_ref: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    origin_ref: str | None = None
    layout_hints: dict[str, Any] = Field(default_factory=dict)


class VisualizationEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    kind: str
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_group_ref: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    origin_ref: str | None = None
    raw_edge_ids: list[str] = Field(default_factory=list)
    support_count: int = Field(default=1, ge=1)
    supporting_observations: list[dict[str, Any]] = Field(default_factory=list)


class VisualizationHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    status: EvidenceStatus
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_group_ref: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    supporting_evidence_group_ref: str | None = None
    supporting_evidence_count: int = Field(default=0, ge=0)
    contradicting_evidence_group_ref: str | None = None
    contradicting_evidence_count: int = Field(default=0, ge=0)
    explanation: str = ""

class VisualizationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_type: str
    detail: str
    source: SourceRef | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class VisualizationReadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1"
    repository: RepositoryInfo
    nodes: list[VisualizationNode] = Field(default_factory=list)
    edges: list[VisualizationEdge] = Field(default_factory=list)
    hypotheses: list[VisualizationHypothesis] = Field(default_factory=list)
    evidence: list[VisualizationEvidence] = Field(default_factory=list)
    evidence_groups: list[EvidenceGroup] = Field(default_factory=list)
    architectural_significance: list[ArchitecturalSignificance] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def canonicalize(self) -> "VisualizationReadModel":
        data = self.model_dump(mode="json")
        data["nodes"] = sorted(data["nodes"], key=lambda item: item["id"])
        data["edges"] = sorted(
            data["edges"],
            key=lambda item: (item["source"], item["target"], item["kind"], item["id"]),
        )
        data["hypotheses"] = sorted(data["hypotheses"], key=lambda item: item["pattern"])
        data["architectural_significance"] = sorted(data["architectural_significance"], key=lambda item: item["subject"])
        data["evidence"] = sorted(data["evidence"], key=lambda item: item["id"])
        data["evidence_groups"] = sorted(data["evidence_groups"], key=lambda item: item["id"])
        data["unknowns"] = sorted(set(data["unknowns"]))
        return VisualizationReadModel.model_validate(data)


class VisualizationReadModelBuilder:
    """Project existing ArchitectureIR facts into a renderer-neutral read model."""

    def build(self, ir: ArchitectureIR, profile: AnalysisProfile | None = None) -> VisualizationReadModel:
        with profile_stage(profile, "visualization_read_model") as timer:
            result = self._build(ir, profile)
            if timer:
                timer.set_counts(
                    detailed_nodes=int(result.metadata.get("detailed_node_count", len(result.nodes))),
                    projected_nodes=int(result.metadata.get("high_level_node_count", len(result.nodes))),
                    projected_edges=len(result.edges), projected_edge_count=len(result.edges),
                    evidence_groups=len(result.evidence_groups),
                )
            return result

    def _build(self, ir: ArchitectureIR, profile: AnalysisProfile | None = None) -> VisualizationReadModel:
        arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        raw_to_arch = self._raw_to_arch(ir)
        nodes: dict[str, VisualizationNode] = {}
        edges: dict[str, VisualizationEdge] = {}
        unknowns: set[str] = set()

        for node in sorted(arch_nodes.values(), key=lambda item: item.id):
            nodes[node.id] = self._node_from_ir(node, raw_nodes)

        for resource in sorted(ir.infrastructure_resources, key=lambda item: item.id):
            if resource.id not in nodes:
                nodes[resource.id] = self._resource_node(resource)
            else:
                current = nodes[resource.id]
                nodes[resource.id] = current.model_copy(update={
                    "evidence_refs": sorted(set(current.evidence_refs) | set(resource.evidence_refs)),
                    "role": current.role or resource.kind.lower(),
                    "layout_hints": {
                        **current.layout_hints,
                        "semantic_kind": "infrastructure",
                        "terminal": current.layout_hints.get("terminal", resource.kind in {"DATABASE", "CACHE", "QUEUE", "MESSAGE_BROKER"}),
                    },
                })

        def ensure_unknown(label: str, refs: Iterable[str], origin_ref: str) -> str:
            node_id = _stable_id("unknown", origin_ref, label)
            if node_id not in nodes:
                nodes[node_id] = VisualizationNode(
                    id=node_id,
                    kind="unknown",
                    label=label,
                    status=EvidenceStatus.UNKNOWN,
                    confidence=0.0,
                    evidence_refs=sorted(set(refs)),
                    origin_ref=origin_ref,
                    layout_hints={"semantic_kind": "unknown"},
                )
            unknowns.add(origin_ref)
            return node_id

        def resolve(value: str | None, fact: Any | None = None, role: str | None = None) -> str:
            if value and value in nodes:
                return value
            if value and value in arch_nodes:
                return value
            if value and value in raw_to_arch:
                return raw_to_arch[value]
            if value and value in raw_nodes:
                return raw_to_arch.get(value) or ensure_unknown(value, raw_nodes[value].evidence_refs, value)
            module = (fact.attributes.get("module") if fact is not None else None) if fact else None
            if module:
                module_id = f"module:{module}"
                if module_id in raw_to_arch:
                    return raw_to_arch[module_id]
            if value and value != "UNKNOWN":
                refs = fact.evidence_refs if fact is not None else []
                node_id = _stable_id("semantic", role or "reference", value)
                if node_id not in nodes:
                    nodes[node_id] = VisualizationNode(
                        id=node_id,
                        kind=role or "external_reference",
                        label=value,
                        status=fact.status if fact is not None else EvidenceStatus.UNKNOWN,
                        confidence=fact.confidence if fact is not None else 0.0,
                        evidence_refs=sorted(set(refs)),
                        origin_ref=f"framework:{getattr(fact, 'kind', 'reference')}:{value}",
                        layout_hints={"semantic_kind": role or "external_reference"},
                    )
                return node_id
            return ensure_unknown("UNKNOWN", fact.evidence_refs if fact is not None else [], f"framework:{getattr(fact, 'kind', 'unknown')}:{value or 'UNKNOWN'}")

        def add_edge(
            source: str,
            target: str,
            kind: str,
            status: EvidenceStatus,
            confidence: float,
            refs: Iterable[str],
            origin_ref: str,
        ) -> None:
            if source not in nodes or target not in nodes:
                unknowns.add(origin_ref)
                return
            edge_id = _stable_id("edge", origin_ref, source, target, kind)
            edges[edge_id] = VisualizationEdge(
                id=edge_id,
                source=source,
                target=target,
                kind=kind,
                status=status,
                confidence=confidence,
                evidence_refs=sorted(set(refs)),
                origin_ref=origin_ref,
            )

        for edge in sorted(ir.architectural_graph.edges, key=_edge_key):
            add_edge(
                edge.source,
                edge.target,
                edge.type.value,
                edge.status,
                edge.confidence,
                edge.evidence_refs,
                f"architectural_edge:{edge.id or edge.source + ':' + edge.target}",
            )

        for relation in sorted(
            ir.infrastructure_relations,
            key=lambda item: (item.source, item.target, item.type, item.id),
        ):
            source = resolve(relation.source)
            target = resolve(relation.target)
            add_edge(
                source,
                target,
                relation.type,
                relation.status,
                relation.confidence,
                relation.evidence_refs,
                f"infrastructure_relation:{relation.id}",
            )

        endpoint_nodes: dict[str, str] = {}
        for fact in sorted(ir.framework_facts, key=_fact_key):
            if fact.kind == "HTTP_ENDPOINT":
                endpoint_id = _stable_id("endpoint", fact.subject or fact.target or "UNKNOWN")
                endpoint_nodes[fact.subject or fact.target or "UNKNOWN"] = endpoint_id
                if endpoint_id not in nodes:
                    nodes[endpoint_id] = VisualizationNode(
                        id=endpoint_id,
                        kind="endpoint",
                        label=fact.attributes.get("path", fact.subject or "UNKNOWN"),
                        role="http_endpoint",
                        status=fact.status,
                        confidence=fact.confidence,
                        evidence_refs=sorted(set(fact.evidence_refs)),
                        origin_ref=f"framework_fact:HTTP_ENDPOINT:{fact.subject}",
                        layout_hints={
                            "semantic_kind": "endpoint",
                            "entrypoint": True,
                            "preferred_layer": "presentation",
                        },
                    )
                owner = fact.attributes.get("router") or fact.attributes.get("owner")
                if owner:
                    add_edge(
                        resolve(owner, fact, "router"),
                        endpoint_id,
                        "ROUTES_TO",
                        fact.status,
                        fact.confidence,
                        fact.evidence_refs,
                        f"framework_fact:HTTP_ENDPOINT:{fact.subject}",
                    )
            elif fact.kind == "FRAMEWORK_DEPENDENCY":
                source = endpoint_nodes.get(fact.subject or "") or resolve(fact.subject, fact, "endpoint")
                target = resolve(fact.target, fact, "dependency")
                add_edge(
                    source,
                    target,
                    "FRAMEWORK_DEPENDENCY",
                    fact.status,
                    fact.confidence,
                    fact.evidence_refs,
                    f"framework_fact:FRAMEWORK_DEPENDENCY:{fact.subject}:{fact.target}",
                )
            elif fact.kind == "RESPONSE_SCHEMA":
                source = endpoint_nodes.get(fact.subject or "") or resolve(fact.subject, fact, "endpoint")
                target = resolve(fact.target, fact, "schema")
                add_edge(
                    source,
                    target,
                    "RESPONSE_SCHEMA",
                    fact.status,
                    fact.confidence,
                    fact.evidence_refs,
                    f"framework_fact:RESPONSE_SCHEMA:{fact.subject}:{fact.target}",
                )
            elif fact.kind == "ROUTER_INCLUSION":
                add_edge(
                    resolve(fact.subject, fact, "application"),
                    resolve(fact.target, fact, "router"),
                    "ROUTER_INCLUSION",
                    fact.status,
                    fact.confidence,
                    fact.evidence_refs,
                    f"framework_fact:ROUTER_INCLUSION:{fact.subject}:{fact.target}",
                )

        hypotheses = [
            VisualizationHypothesis(
                pattern=item.pattern,
                status=item.status,
                confidence=item.confidence,
                supporting_evidence=list(item.supporting_evidence),
                contradicting_evidence=list(item.contradicting_evidence),
                evidence_refs=list(item.evidence_refs),
                explanation=item.explanation,
            )
            for item in ir.architecture.hypotheses
        ]
        evidence = [
            VisualizationEvidence(
                id=item.id,
                source_type=item.source_type.value,
                detail=item.detail,
                source=item.source,
                weight=item.weight,
            )
            for item in ir.evidence
        ]
        with profile_stage(profile, "architectural_significance_projection") as timer:
            projection = ArchitecturalProjectionBuilder().build(ir)
            if timer:
                timer.set_counts(
                    detailed_nodes=projection.detailed_node_count,
                    projected_nodes=projection.high_level_node_count,
                    projected_edges=len(projection.projected_edges),
                )
        significance_by_subject = {item.subject: item for item in projection.significances}
        selected_ids = set(projection.projected_node_ids)
        semantic_ids = {
            item.id for item in nodes.values()
            if item.origin_ref and (item.origin_ref.startswith("framework_") or item.origin_ref.startswith("framework:") or item.kind == "unknown")
        }
        retained_ids = selected_ids | semantic_ids
        nodes = {
            node_id: node.model_copy(update={"layout_hints": {
                **node.layout_hints,
                **({
                    "architectural_significance": significance_by_subject[node_id].significance.value,
                    "significance_score": significance_by_subject[node_id].score,
                    "contains_refs": significance_by_subject[node_id].contains_refs,
                } if node_id in significance_by_subject else {}),
            }})
            for node_id, node in nodes.items()
            if node_id in retained_ids
        }
        projected_edges = {
            item.id: VisualizationEdge(
                id=item.id, source=item.source, target=item.target, kind=item.kind,
                status=item.status, confidence=item.confidence, evidence_refs=item.evidence_refs,
                origin_ref=f"projection_edge:{item.id}", raw_edge_ids=item.raw_edge_ids,
                support_count=item.support_count, supporting_observations=item.supporting_observations,
            )
            for item in projection.projected_edges
            if item.source in nodes and item.target in nodes
        }
        projected_keys = {(item.source, item.target, item.kind) for item in projected_edges.values()}
        for edge in edges.values():
            key = (edge.source, edge.target, edge.kind)
            if edge.source in nodes and edge.target in nodes and edge.origin_ref and (
                edge.origin_ref.startswith("framework_fact:") or edge.origin_ref.startswith("infrastructure_relation:")
            ) and key not in projected_keys:
                projected_edges[edge.id] = edge
        edges = projected_edges
        unknowns.update(projection.unknown_refs)
        evidence_ids = {item.id for item in ir.evidence}
        projection_traceability = all(
            ref in evidence_ids
            for item in [*projection.significances, *projection.projected_edges]
            for ref in item.evidence_refs
        )
        projected_edge_validity = all(
            edge.source in nodes and edge.target in nodes for edge in projection.projected_edges
        )
        result = VisualizationReadModel(
            repository=ir.repository,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            hypotheses=hypotheses,
            evidence=evidence,
            architectural_significance=projection.significances,
            unknowns=sorted(unknowns),
            metadata={
                "source_schema_version": ir.schema_version,
                "architectural_graph_node_count": len(ir.architectural_graph.nodes),
                "architectural_graph_edge_count": len(ir.architectural_graph.edges),
                "detailed_node_count": projection.detailed_node_count,
                "high_level_node_count": projection.high_level_node_count,
                "projection_reduction_ratio": projection.reduction_ratio,
                "projected_edge_validity": projected_edge_validity,
                "projection_traceability": projection_traceability,
                "low_significance_preservation": bool(projection.low_significance_refs),
                "projection_mode": "evidence_based_high_level_v1",
                "transformation": "architecture-ir-to-visualization-read-model-v2",
            },
        ).canonicalize()
        result = self._compact_evidence(result)
        validation = validate_visualization_read_model(result, {item.id for item in ir.evidence})
        if not validation.valid:
            raise ValueError("Invalid visualization read model: " + "; ".join(validation.errors))
        return result

    @staticmethod
    def _compact_evidence(model: VisualizationReadModel) -> VisualizationReadModel:
        index = EvidencePayloadIndex(model.evidence)

        def bind(item, field: str, group_field: str, count_field: str):
            binding = index.bind(getattr(item, field))
            return item.model_copy(update={
                field: binding.inline_refs,
                group_field: binding.group_ref,
                count_field: binding.evidence_count,
            })

        nodes = [bind(item, "evidence_refs", "evidence_group_ref", "evidence_count") for item in model.nodes]
        edges = [bind(item, "evidence_refs", "evidence_group_ref", "evidence_count") for item in model.edges]
        hypotheses = []
        for item in model.hypotheses:
            compacted = bind(item, "evidence_refs", "evidence_group_ref", "evidence_count")
            compacted = bind(compacted, "supporting_evidence", "supporting_evidence_group_ref", "supporting_evidence_count")
            compacted = bind(compacted, "contradicting_evidence", "contradicting_evidence_group_ref", "contradicting_evidence_count")
            hypotheses.append(compacted)

        metadata = dict(model.metadata)
        metadata.update({
            "evidence_reference_count": index.original_reference_count,
            "inline_evidence_reference_count": index.inline_reference_count,
            "evidence_group_count": len(index.groups),
            "evidence_inline_limit": index.inline_limit,
        })
        return model.model_copy(update={
            "nodes": nodes,
            "edges": edges,
            "hypotheses": hypotheses,
            "evidence_groups": sorted(index.groups.values(), key=lambda item: item.id),
            "metadata": metadata,
        }).canonicalize()
    @staticmethod
    def _raw_to_arch(ir: ArchitectureIR) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for node in ir.architectural_graph.nodes:
            for raw_id in node.metadata.get("raw_node_ids", []):
                mapping[raw_id] = node.id
        return mapping

    @staticmethod
    def _node_from_ir(node: Node, raw_nodes: dict[str, Node]) -> VisualizationNode:
        raw_refs = {
            ref
            for raw_id in node.metadata.get("raw_node_ids", [])
            if raw_id in raw_nodes
            for ref in raw_nodes[raw_id].evidence_refs
        }
        return VisualizationNode(
            id=node.id,
            kind=node.type.value,
            label=node.name,
            layer=node.layer,
            status=node.status,
            confidence=node.confidence,
            evidence_refs=sorted(set(node.evidence_refs) | raw_refs),
            origin_ref=f"architectural_node:{node.id}",
            layout_hints={
                "semantic_kind": node.type.value,
                "external": node.type.value in {"external_dependency", "external_service"},
                "terminal": node.type.value in {"database", "cache", "queue", "message_broker"},
                **({"preferred_layer": node.layer} if node.layer else {}),
            },
        )

    @staticmethod
    def _resource_node(resource: InfrastructureResource) -> VisualizationNode:
        return VisualizationNode(
            id=resource.id,
            kind="infrastructure",
            label=resource.name,
            role=resource.kind.lower(),
            status=resource.status,
            confidence=resource.confidence,
            evidence_refs=sorted(set(resource.evidence_refs)),
            origin_ref=f"infrastructure_resource:{resource.id}",
            layout_hints={
                "semantic_kind": "infrastructure",
                "terminal": resource.kind in {"DATABASE", "CACHE", "QUEUE", "MESSAGE_BROKER"},
            },
        )


def validate_visualization_read_model(
    model: VisualizationReadModel,
    evidence_ids: set[str] | None = None,
):
    errors: list[str] = []
    node_ids = [node.id for node in model.nodes]
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        errors.append("Visualization read model contains duplicate node IDs")
    if any(not node_id for node_id in node_ids):
        errors.append("Visualization read model contains a node without identity")
    edge_ids = [edge.id for edge in model.edges]
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("Visualization read model contains duplicate edge IDs")
    for edge in model.edges:
        if edge.source not in node_id_set:
            errors.append(f"Visualization edge source does not exist: {edge.source}")
        if edge.target not in node_id_set:
            errors.append(f"Visualization edge target does not exist: {edge.target}")
    group_ids = [group.id for group in model.evidence_groups]
    group_by_id = {group.id: group for group in model.evidence_groups}
    if len(group_ids) != len(group_by_id):
        errors.append("Visualization read model contains duplicate evidence group IDs")
    for group in model.evidence_groups:
        if group.evidence_count != len(set(group.evidence_refs)):
            errors.append(f"Evidence group count does not match refs: {group.id}")

    grouped_items = [*model.nodes, *model.edges, *model.hypotheses]
    for item in grouped_items:
        refs = list(item.evidence_refs)
        group_ref = item.evidence_group_ref
        if group_ref:
            group = group_by_id.get(group_ref)
            if group is None:
                errors.append(f"Visualization element references unknown evidence group: {group_ref}")
            elif item.evidence_count != group.evidence_count:
                errors.append(f"Visualization evidence count does not match group: {group_ref}")
        for field, count_field in (("supporting_evidence_group_ref", "supporting_evidence_count"), ("contradicting_evidence_group_ref", "contradicting_evidence_count")):
            support_group_ref = getattr(item, field, None)
            if support_group_ref:
                group = group_by_id.get(support_group_ref)
                if group is None:
                    errors.append(f"Visualization element references unknown evidence group: {support_group_ref}")
                elif getattr(item, count_field) != group.evidence_count:
                    errors.append(f"Visualization evidence count does not match group: {support_group_ref}")
        if evidence_ids is not None:
            for ref in refs:
                if ref not in evidence_ids:
                    errors.append(f"Visualization element references unknown evidence: {ref}")

    if evidence_ids is not None:
        for group in model.evidence_groups:
            for ref in group.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Evidence group references unknown evidence: {ref}")
        for item in model.architectural_significance:
            for ref in item.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Visualization element references unknown evidence: {ref}")
        for item in model.unknowns:
            if not item:
                errors.append("Visualization unknown entry is empty")
    from architecture_recovery.ir import ValidationReport
    return ValidationReport(valid=not errors, errors=errors, warnings=[])


def _stable_id(*parts: str) -> str:
    token = "|".join(parts)
    return hashlib.sha1(token.encode("utf-8")).hexdigest()[:16]


def _edge_key(edge: Edge) -> tuple[str, str, str, str]:
    return edge.source, edge.target, edge.type.value, edge.id or ""


def _fact_key(fact: Any) -> tuple[str, str, str]:
    return fact.kind, fact.subject or "", fact.target or ""


__all__ = [
    "VisualizationEdge",
    "EvidenceGroup",
    "VisualizationEvidence",
    "VisualizationHypothesis",
    "VisualizationNode",
    "VisualizationReadModel",
    "VisualizationReadModelBuilder",
    "validate_visualization_read_model",
]
