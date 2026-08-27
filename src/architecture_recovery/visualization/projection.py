from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from architecture_recovery.ir import ArchitectureIR, Edge, EdgeType, EvidenceStatus, Node, NodeType, relation_strength
from .context import ContextPropagation, DeploymentProvenance, context_direction_pairs, context_propagation_kind, deployment_provenance


class SignificanceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ArchitecturalSignificance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str
    significance: SignificanceLevel
    role: str | None = None
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    contains_refs: list[str] = Field(default_factory=list)


class ProjectedEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    kind: str
    status: EvidenceStatus = EvidenceStatus.INFERRED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    raw_edge_ids: list[str] = Field(default_factory=list)
    support_count: int = Field(default=1, ge=1)
    supporting_observations: list[dict[str, Any]] = Field(default_factory=list)


class HighLevelArchitectureProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detailed_node_count: int = Field(default=0, ge=0)
    high_level_node_count: int = Field(default=0, ge=0)
    projected_node_ids: list[str] = Field(default_factory=list)
    projected_edges: list[ProjectedEdge] = Field(default_factory=list)
    significances: list[ArchitecturalSignificance] = Field(default_factory=list)
    low_significance_refs: list[str] = Field(default_factory=list)
    unknown_refs: list[str] = Field(default_factory=list)
    context_root_ids: list[str] = Field(default_factory=list)
    context_root_strengths: dict[str, str] = Field(default_factory=dict)
    context_root_kinds: dict[str, str] = Field(default_factory=dict)
    navigation_root_ids: list[str] = Field(default_factory=list)
    weak_evidence_saturation_count: int = Field(default=0, ge=0)

    @property
    def reduction_ratio(self) -> float:
        if not self.detailed_node_count:
            return 0.0
        return round(1.0 - self.high_level_node_count / self.detailed_node_count, 6)


class ArchitecturalProjectionBuilder:
    """Build a traceable high-level view without changing ArchitectureIR.

    Structural observations and architectural significance are intentionally
    separate.  The builder uses semantic signals first and applies one bounded
    contextual pass; raw degree and generic import aggregation never promote a
    node on their own.
    """

    _STRONG_NODE_TYPES = {
        NodeType.API,

        NodeType.EXTERNAL_SERVICE,
        NodeType.INFRASTRUCTURE,
    }
    _MEDIUM_NODE_TYPES: set[NodeType] = set()
    _STRONG_FRAMEWORK_FACTS = {"APPLICATION", "HTTP_ENDPOINT", "CONTROLLER_LIKE", "ROUTER"}
    _MEDIUM_FRAMEWORK_FACTS = {"ROUTER_INCLUSION", "FRAMEWORK_DEPENDENCY", "RESPONSE_SCHEMA", "SCHEMA"}
    _STRONG_EDGE_TYPES = {
        EdgeType.ROUTES_TO,
        EdgeType.QUERIES,
        EdgeType.PUBLISHES,
        EdgeType.CONSUMES,
    }
    _MEDIUM_EDGE_TYPES = {EdgeType.CONNECTS_TO, EdgeType.DEPLOYS}
    _INFRASTRUCTURE_KINDS = {"DATABASE", "CACHE", "QUEUE", "MESSAGE_BROKER", "CONTAINER", "SERVICE"}
    _SEMANTIC_ROLES = {
        "application",
        "application_entrypoint",
        "http_endpoint",
        "http_entrypoint",
        "database",
        "database_driver",
        "message_broker",
        "cache",
        "runtime",
        "external_service",
        "framework",
    }
    _PACKAGE_TOKEN_RE = re.compile(r"[a-z0-9]+")

    def build(self, ir: ArchitectureIR) -> HighLevelArchitectureProjection:
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
        raw_to_arch = self._raw_to_arch(ir)
        evidence_ids = {item.id for item in ir.evidence}
        resource_ids = {resource.id for resource in ir.infrastructure_resources}
        raw_edges = {edge.id: edge for edge in ir.raw_graph.edges if edge.id}
        evidence_by_id = {item.id: item for item in ir.evidence}
        resources_by_id = {resource.id: resource for resource in ir.infrastructure_resources}

        def subject_type(subject: str | None) -> NodeType | None:
            node = arch_nodes.get(subject or "")
            if node:
                return node.type
            resource = resources_by_id.get(subject or "")
            return resource.kind if resource else None

        def deployment_kind(edge: Any, source: str, target: str) -> DeploymentProvenance:
            return deployment_provenance(
                edge.type,
                source_id=source,
                target_id=target,
                source_type=subject_type(source),
                target_type=subject_type(target),
                metadata=edge.metadata,
                evidence_sources=(
                    evidence_by_id[ref].source_type.value
                    for ref in edge.evidence_refs
                    if ref in evidence_by_id
                ),
            )
        strong: dict[str, list[tuple[float, str]]] = defaultdict(list)
        medium: dict[str, list[tuple[float, str]]] = defaultdict(list)
        weak: dict[str, list[tuple[float, str]]] = defaultdict(list)
        refs: dict[str, set[str]] = defaultdict(set)
        reasons: dict[str, list[str]] = defaultdict(list)
        contains: dict[str, list[str]] = defaultdict(list)
        dependency_roles: dict[str, str] = {
            node.id: "GENERAL_LIBRARY"
            for node in arch_nodes.values()
            if node.type == NodeType.EXTERNAL_DEPENDENCY
        }
        dependency_edges: list[Edge] = []
        navigation_root_ids = {
            node.id for node in arch_nodes.values() if node.type == NodeType.REPOSITORY
        }

        def explicit_framework_boundary(fact: Any) -> bool:
            return bool(
                fact.attributes.get("architectural_boundary")
                or fact.metadata.get("architectural_boundary")
                or fact.attributes.get("entrypoint")
                or fact.metadata.get("entrypoint")
            )

        def explicitly_boundary_node(node: Node) -> bool:
            role = str(node.metadata.get("architectural_role", node.metadata.get("role", ""))).lower()
            return bool(
                node.metadata.get("architectural_boundary")
                or role in {"http_endpoint", "http_entrypoint", "architectural_boundary"}
            )
        def application_boundary_info(node: Node) -> tuple[bool, str, str]:
            """Return admission, provenance kind and evidence kind for an application."""
            metadata = node.metadata
            provenance = str(metadata.get("application_provenance", "")).lower()
            if provenance == "repository_aggregate":
                return (
                    bool(metadata.get("architectural_boundary") or metadata.get("entrypoint")),
                    provenance,
                    str(metadata.get("boundary_evidence_kind", "repository_membership")),
                )
            if metadata.get("architectural_boundary") or metadata.get("entrypoint") or metadata.get("executable"):
                return True, provenance or "explicit_application", str(metadata.get("boundary_evidence_kind", "explicit_metadata"))
            # Standalone application nodes are retained for compatibility with
            # hand-authored IR fixtures. Aggregation-created nodes always carry
            # raw_node_ids and are therefore not admitted by this fallback.
            if not metadata.get("raw_node_ids") and node.status == EvidenceStatus.OBSERVED:
                return True, provenance or "standalone_application", str(metadata.get("boundary_evidence_kind", "standalone_node"))
            return False, provenance or "detected_application", str(metadata.get("boundary_evidence_kind", "insufficient_boundary_evidence"))

        def is_architectural_ownership(edge: Edge) -> bool:
            return bool(
                edge.metadata.get("architectural_ownership")
                or edge.metadata.get("ownership_kind") == "architectural"
            )

        def dependency_role(subject: str, relation_type: EdgeType | str | None = None) -> str:
            node = arch_nodes.get(subject)
            explicit = str(node.metadata.get("architectural_role", node.metadata.get("role", ""))).lower() if node else ""
            explicit_roles = {
                "framework": "APPLICATION_FRAMEWORK",
                "application_framework": "APPLICATION_FRAMEWORK",
                "database": "DATABASE_ACCESS",
                "database_driver": "PERSISTENCE_TECHNOLOGY",
                "persistence": "PERSISTENCE_TECHNOLOGY",
                "persistence_technology": "PERSISTENCE_TECHNOLOGY",
                "message_broker": "MESSAGE_TRANSPORT",
                "message_transport": "MESSAGE_TRANSPORT",
                "cache": "CACHE_TECHNOLOGY",
                "cache_technology": "CACHE_TECHNOLOGY",
                "runtime": "DEPLOYMENT_RUNTIME",
                "deployment_runtime": "DEPLOYMENT_RUNTIME",
                "external_service": "EXTERNAL_SERVICE_CLIENT",
                "external_service_client": "EXTERNAL_SERVICE_CLIENT",
            }
            role = explicit_roles.get(explicit)
            if role:
                dependency_roles[subject] = role
                return role
            relation_roles = {
                EdgeType.QUERIES: "PERSISTENCE_TECHNOLOGY",
                EdgeType.READS: "PERSISTENCE_TECHNOLOGY",
                EdgeType.WRITES: "PERSISTENCE_TECHNOLOGY",
                EdgeType.PUBLISHES: "MESSAGE_TRANSPORT",
                EdgeType.CONSUMES: "MESSAGE_TRANSPORT",
                EdgeType.CONNECTS_TO: "EXTERNAL_SERVICE_CLIENT",
                EdgeType.DEPLOYS: "DEPLOYMENT_RUNTIME",
                EdgeType.ROUTES_TO: "APPLICATION_FRAMEWORK",
            }
            role = relation_roles.get(relation_type)
            if role:
                dependency_roles[subject] = role
                return role
            return dependency_roles.get(subject, "GENERAL_LIBRARY")

        def add_signal(
            subject: str,
            category: str,
            weight: float,
            reason: str,
            signal_refs: set[str] | list[str] = (),
        ) -> None:
            if subject not in arch_nodes and subject not in resource_ids:
                return
            target = {"strong": strong, "medium": medium, "weak": weak}[category]
            target[subject].append((weight, reason))
            reasons[subject].append(reason)
            refs[subject].update(set(signal_refs) & evidence_ids)

        for node in arch_nodes.values():
            contains[node.id] = sorted(set(node.metadata.get("raw_node_ids", [])))
            node_refs = set(node.evidence_refs)
            for raw_id in contains[node.id]:
                raw = raw_nodes.get(raw_id)
                if raw:
                    node_refs.update(raw.evidence_refs)
            refs[node.id].update(node_refs & evidence_ids)
            if node.type in self._STRONG_NODE_TYPES:
                add_signal(node.id, "strong", 0.55, f"strong semantic node type: {node.type.value}", node_refs)
            elif node.type in self._MEDIUM_NODE_TYPES:
                add_signal(node.id, "medium", 0.20, f"medium infrastructure node type: {node.type.value}", node_refs)
            elif node.type == NodeType.REPOSITORY:
                # The repository root remains selected as navigation context,
                # but its significance is not fabricated from its existence.
                reasons[node.id].append("repository context retained for navigation")

            explicit_role = str(node.metadata.get("architectural_role", node.metadata.get("role", ""))).lower()
            if node.type == NodeType.EXTERNAL_DEPENDENCY:
                role = dependency_role(node.id)
                reasons[node.id].append(f"dependency role candidate: {role}")
            elif explicit_role in self._SEMANTIC_ROLES:
                add_signal(node.id, "strong", 0.45, f"explicit architectural role: {explicit_role}", node_refs)

        for resource in ir.infrastructure_resources:
            kind = resource.kind.upper()
            refs[resource.id].update(set(resource.evidence_refs) & evidence_ids)
            if kind in self._INFRASTRUCTURE_KINDS:
                # Resource observation is retained as evidence; relation
                # context below decides whether it is high-level.
                reasons[resource.id].append(f"observed infrastructure candidate: {kind}")

        for candidate in ir.component_candidates:
            candidate_refs = set(candidate.evidence_refs) & evidence_ids
            for member in candidate.node_ids:
                subject = self._resolve(member, arch_nodes, raw_to_arch)
                if subject:
                    # Detection is valuable traceability, but a candidate is a
                    # structural hypothesis and is not a high-level promotion.
                    refs[subject].update(candidate_refs)
                    reasons[subject].append("component detection evidence (structural, not sufficient alone)")

        application_ids = {node.id for node in arch_nodes.values() if node.type == NodeType.APPLICATION}
        application_provenance: dict[str, tuple[str, str, bool]] = {}
        context_root_ids: set[str] = set()
        context_root_strengths: dict[str, str] = {}
        context_root_kinds: dict[str, str] = {}
        for application_id in sorted(application_ids):
            application = arch_nodes[application_id]
            admitted, provenance, evidence_kind = application_boundary_info(application)
            application_provenance[application_id] = (provenance, evidence_kind, admitted)
            if not admitted:
                reasons[application_id].append(f"application boundary rejected: {evidence_kind}")
                continue
            context_root_ids.add(application_id)
            context_root_strengths[application_id] = "strong"
            context_root_kinds[application_id] = "APPLICATION_BOUNDARY"
            add_signal(application_id, "strong", 0.55, f"application boundary: {evidence_kind}", set(application.evidence_refs))
        for root_id in sorted(context_root_ids):
            reasons[root_id].append("architectural context root: independently justified application boundary")
        component_main_context: set[str] = set()
        component_semantic_flow: set[str] = set()
        for edge in ir.architectural_graph.edges:
            source = arch_nodes.get(edge.source)
            target = arch_nodes.get(edge.target)
            if not source or not target:
                continue
            deployment_can_context = edge.type != EdgeType.DEPLOYS or context_propagation_kind(
                edge.type, deployment_provenance=deployment_kind(edge, edge.source, edge.target)
            ) == ContextPropagation.CAN_PROPAGATE_CONTEXT
            if source.type == NodeType.APPLICATION and target.type == NodeType.COMPONENT:
                if source.id in context_root_ids and (edge.type != EdgeType.DEPLOYS or deployment_can_context) and edge.type in {EdgeType.ROUTES_TO, EdgeType.DEPLOYS, EdgeType.CALLS, EdgeType.INSTANTIATES}:
                    component_main_context.add(target.id)
            elif target.type == NodeType.APPLICATION and source.type == NodeType.COMPONENT:
                if target.id in context_root_ids and (edge.type != EdgeType.DEPLOYS or deployment_can_context) and edge.type in {EdgeType.ROUTES_TO, EdgeType.DEPLOYS, EdgeType.CALLS, EdgeType.INSTANTIATES}:
                    component_main_context.add(source.id)
            if source.type == NodeType.COMPONENT and target.type == NodeType.COMPONENT:
                if edge.type in self._STRONG_EDGE_TYPES or any(
                    raw_edges.get(raw_id) and raw_edges[raw_id].type in {EdgeType.CALLS, EdgeType.INSTANTIATES, EdgeType.EXTENDS}
                    for raw_id in edge.raw_edge_ids
                ):
                    component_semantic_flow.update({source.id, target.id})

        framework_boundary_subjects = {
            resolved
            for fact in ir.framework_facts
            if fact.kind in self._STRONG_FRAMEWORK_FACTS
            for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module"))
            for resolved in [self._resolve(value, arch_nodes, raw_to_arch)]
            if resolved
        }
        for edge in ir.architectural_graph.edges:
            if edge.type not in {EdgeType.ROUTES_TO, EdgeType.CALLS, EdgeType.INSTANTIATES}:
                continue
            source = arch_nodes.get(edge.source)
            target = arch_nodes.get(edge.target)
            if not source or not target:
                continue
            if (
                edge.source in framework_boundary_subjects
                and (edge.source in context_root_ids or source.type != NodeType.COMPONENT)
                and target.type == NodeType.COMPONENT
            ):
                component_main_context.add(target.id)
            if (
                edge.target in framework_boundary_subjects
                and (edge.target in context_root_ids or target.type != NodeType.COMPONENT)
                and source.type == NodeType.COMPONENT
            ):
                component_main_context.add(source.id)
        root_context_component_ids = set(component_main_context)
        context_component_ids = root_context_component_ids | set(component_semantic_flow)
        framework_assessments = self._framework_boundary_assessments(ir, arch_nodes, raw_to_arch)
        framework_application_components = set(framework_assessments)
        for subject, assessment in sorted(framework_assessments.items()):
            if not assessment["global_qualified"]:
                continue
            context_root_ids.add(subject)
            context_root_strengths[subject] = "strong"
            context_root_kinds[subject] = "FRAMEWORK_APPLICATION_BOUNDARY"
            refs_for_subject = set(assessment["application_refs"]) | set(assessment["boundary_refs"])
            add_signal(subject, "strong", 0.55, "application boundary: owned framework application", refs_for_subject)
            reasons[subject].append("architectural context root: owned framework application boundary")
        # Repository aggregation CONTAINS remains structural. Only explicit
        # architectural ownership can associate another component with a root.
        for edge in ir.architectural_graph.edges:
            if edge.type != EdgeType.CONTAINS:
                continue
            if (
                edge.source in context_root_ids
                and edge.target in framework_application_components
                and edge.target in component_semantic_flow
                and is_architectural_ownership(edge)
            ):
                root_context_component_ids.add(edge.target)
        semantic_subjects: set[str] = set()
        framework_boundary_candidates: set[str] = set()
        framework_context_components: set[str] = set()
        principal_framework_packages: set[str] = set()
        router_context_subjects = {
            fact.target
            for fact in ir.framework_facts
            if fact.kind == "ROUTER_INCLUSION" and fact.target
        }
        for fact in ir.framework_facts:
            fact_refs = set(fact.evidence_refs) & evidence_ids
            resolved_values = [
                self._resolve(value, arch_nodes, raw_to_arch)
                for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module"))
            ]
            fact_context = any(
                subject in context_root_ids
                or subject in root_context_component_ids
                for subject in resolved_values
                if subject
            ) or explicit_framework_boundary(fact)
            if fact.kind == "ROUTER" and fact.subject in router_context_subjects:
                fact_context = True
            for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module")):
                subject = self._resolve(value, arch_nodes, raw_to_arch)
                if not subject:
                    continue
                if explicit_framework_boundary(fact) and subject in arch_nodes:
                    context_root_ids.add(subject)
                    context_root_strengths[subject] = "strong"
                    context_root_kinds[subject] = (
                        "EXECUTION_BOUNDARY"
                        if fact.attributes.get("entrypoint") or fact.metadata.get("entrypoint")
                        else "EXPLICIT_ARCHITECTURAL_BOUNDARY"
                    )
                    reasons[subject].append("architectural context root: explicit framework boundary")
                # A short module-name fallback must not attach an application fact to an external aggregate.
                if arch_nodes.get(subject) and arch_nodes[subject].type == NodeType.EXTERNAL_DEPENDENCY:
                    continue
                semantic_subjects.add(subject)
                refs[subject].update(fact_refs)
                if arch_nodes.get(subject) and arch_nodes[subject].type == NodeType.COMPONENT:
                    # Framework evidence is a candidate on a component. It
                    # becomes architectural only with independent context.
                    if fact.kind in self._STRONG_FRAMEWORK_FACTS:
                        framework_boundary_candidates.add(subject)
                    if fact_context:
                        framework_context_components.add(subject)
                    reasons[subject].append(f"framework fact candidate: {fact.kind}")
                elif fact.kind in self._STRONG_FRAMEWORK_FACTS:
                    node = arch_nodes.get(subject)
                    if not node or node.type != NodeType.ENDPOINT or explicitly_boundary_node(node):
                        add_signal(subject, "strong", 0.55, f"strong framework fact: {fact.kind}", fact_refs)
                elif fact.kind in self._MEDIUM_FRAMEWORK_FACTS:
                    add_signal(subject, "medium", 0.22, f"semantic framework fact: {fact.kind}", fact_refs)
            if fact_context and fact.kind in {"APPLICATION", "ROUTER"}:
                symbol = fact.attributes.get("symbol")
                if symbol:
                    principal_framework_packages.add(str(symbol).split(".", 1)[0].lower())

        external_dependency_ids = {
            node.id for node in arch_nodes.values()
            if node.type == NodeType.EXTERNAL_DEPENDENCY
        }
        for edge in ir.architectural_graph.edges:
            if not edge.evidence_refs:
                continue
            if edge.source in external_dependency_ids or edge.target in external_dependency_ids:
                dependency_edges.append(edge)
            strength = relation_strength(edge.type)
            if strength == "strong":
                category, weight = "strong", 0.40
            elif strength == "medium":
                category, weight = "medium", 0.20
            else:
                # DEPENDS_ON normally represents imports after aggregation.
                # Keep it for traceability and context, never promotion alone.
                category, weight = "weak", 0.04
            for subject in (edge.source, edge.target):
                if subject in arch_nodes:
                    node = arch_nodes[subject]
                    if node.type in {NodeType.EXTERNAL_DEPENDENCY, NodeType.ENDPOINT} and not explicitly_boundary_node(node):
                        continue
                    add_signal(subject, category, weight, f"evidence-backed architectural relation: {edge.type.value}", edge.evidence_refs)

        infrastructure_subjects = {
            node.id
            for node in arch_nodes.values()
            if node.type in {
                NodeType.DATABASE,
                NodeType.CACHE,
                NodeType.QUEUE,
                NodeType.MESSAGE_BROKER,
                NodeType.CONTAINER,
                NodeType.INFRASTRUCTURE,
                NodeType.EXTERNAL_SERVICE,
            }
        } | {
            resource.id
            for resource in ir.infrastructure_resources
            if resource.kind.upper() in self._INFRASTRUCTURE_KINDS
        }
        for relation in ir.infrastructure_relations:
            source = relation.source if relation.source in resource_ids else self._resolve(relation.source, arch_nodes, raw_to_arch)
            target = relation.target if relation.target in resource_ids else self._resolve(relation.target, arch_nodes, raw_to_arch)
            endpoints = [item for item in (source, target) if item]
            for subject in endpoints:
                refs[subject].update(set(relation.evidence_refs) & evidence_ids)
            if not endpoints or not set(endpoints) & infrastructure_subjects:
                continue
            for subject in endpoints:
                if subject in infrastructure_subjects:
                    add_signal(subject, "strong", 0.55, "explicit infrastructure boundary relation", relation.evidence_refs)
                elif arch_nodes.get(subject) and arch_nodes[subject].type in {
                                NodeType.COMPONENT,
                    NodeType.API,
                    NodeType.MODULE,
                }:
                    if subject in context_root_ids or subject in context_component_ids or explicitly_boundary_node(arch_nodes[subject]):
                        add_signal(subject, "strong", 0.45, "component owns an explicitly related infrastructure resource", relation.evidence_refs)
                    else:
                        reasons[subject].append("infrastructure relation observed outside justified architectural context")
        hypothesis_refs = {
            ref
            for hypothesis in ir.architecture.hypotheses
            for ref in hypothesis.evidence_refs
        }
        for subject in set(strong) | set(medium):
            if refs[subject] & hypothesis_refs:
                add_signal(subject, "medium", 0.15, "participates in an architecture hypothesis", refs[subject] & hypothesis_refs)

        external_by_package = {
            str(node.metadata.get("external_package", "")).lower(): node.id
            for node in arch_nodes.values()
            if node.type == NodeType.EXTERNAL_DEPENDENCY and node.metadata.get("external_package")
        }
        for package, subject in sorted(external_by_package.items()):
            if package in principal_framework_packages:
                dependency_roles[subject] = "APPLICATION_FRAMEWORK"
                add_signal(subject, "strong", 0.55, "principal framework used by an application or router", refs[subject])

        for subject in sorted(framework_context_components):
            add_signal(subject, "medium", 0.20, "framework fact associated with the principal application context", refs[subject])

        # Establish principal framework components only when a boundary fact
        # also participates in an observed cross-component flow.
        for edge in ir.architectural_graph.edges:
            source = arch_nodes.get(edge.source)
            target = arch_nodes.get(edge.target)
            if not source or not target or source.type != NodeType.COMPONENT or target.type != NodeType.COMPONENT:
                continue
            semantic_flow = edge.type in self._STRONG_EDGE_TYPES or any(
                raw_edges.get(raw_id) and raw_edges[raw_id].type in {EdgeType.CALLS, EdgeType.INSTANTIATES, EdgeType.EXTENDS}
                for raw_id in edge.raw_edge_ids
            )
            if not semantic_flow:
                continue
            if source.id in framework_boundary_candidates and source.id in framework_context_components:
                add_signal(source.id, "strong", 0.55, "framework boundary has observed cross-component flow", edge.evidence_refs)
            if target.id in framework_boundary_candidates and target.id in framework_context_components:
                add_signal(target.id, "strong", 0.55, "framework boundary has observed cross-component flow", edge.evidence_refs)

        # One bounded contextual pass.  Only component-level relations can
        # support another component; module degree and raw imports do not.
        direct_significant = set(strong)
        for edge in ir.architectural_graph.edges:
            raw_types = [
                raw_edges[raw_id].type
                for raw_id in edge.raw_edge_ids
                if raw_id in raw_edges
            ]
            propagation = context_propagation_kind(
                edge.type,
                raw_relation_types=raw_types,
            )
            if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
                continue
            source = arch_nodes.get(edge.source)
            target = arch_nodes.get(edge.target)
            if not source or not target or source.type != NodeType.COMPONENT or target.type != NodeType.COMPONENT:
                continue
            if source.id in direct_significant and target.id not in direct_significant:
                add_signal(target.id, "medium", 0.18, "bounded support from a significant component relation", edge.evidence_refs)
            if target.id in direct_significant and source.id not in direct_significant:
                add_signal(source.id, "medium", 0.18, "bounded support from a significant component relation", edge.evidence_refs)

        # A dependency is promoted only in this single bounded pass, after
        # its opposite endpoint has independent architectural significance.
        contextual_significant = set(strong) | set(medium)
        for edge in dependency_edges:
            if edge.type not in self._STRONG_EDGE_TYPES | self._MEDIUM_EDGE_TYPES:
                continue
            dependency_id = next((item for item in (edge.source, edge.target) if item in external_dependency_ids), None)
            if dependency_id is None:
                continue
            opposite = edge.target if edge.source == dependency_id else edge.source
            if opposite not in contextual_significant:
                continue
            role = dependency_role(dependency_id, edge.type)
            if edge.type in self._STRONG_EDGE_TYPES:
                add_signal(dependency_id, "strong", 0.55, f"{role} relation to a significant component: {edge.type.value}", edge.evidence_refs)
            else:
                add_signal(dependency_id, "medium", 0.30, f"{role} relation to a significant component: {edge.type.value}", edge.evidence_refs)

        weak_evidence_saturation_count = sum(
            1
            for subject in set(strong) | set(medium) | set(weak)
            if sum(weight for weight, _ in weak.get(subject, [])) > 0.12
        )
        # Compute a bounded context membership set independently from raw
        # significance. Generic relations may remain valid, but only semantic
        # propagation or observed semantic provenance can establish membership.
        contextual_subjects = set(context_root_ids) | set(root_context_component_ids) | set(framework_context_components)
        deployment_boundary_components = {
            edge.target
            for edge in ir.architectural_graph.edges
            if edge.type == EdgeType.DEPLOYS
            and edge.target in arch_nodes
            and arch_nodes[edge.target].type in {NodeType.COMPONENT, NodeType.CONTAINER}
        }
        context_frontier = set(contextual_subjects)
        context_candidates: list[tuple[str, str, EdgeType | str, list[EdgeType | str], bool, DeploymentProvenance | None]] = []
        for edge in ir.architectural_graph.edges:
            source = self._resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
            target = self._resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
            raw_types = [
                raw_edges[raw_id].type
                for raw_id in edge.raw_edge_ids
                if raw_id in raw_edges
            ]
            ownership = (
                edge.type == EdgeType.CONTAINS
                and source in context_root_ids
                and is_architectural_ownership(edge)
            )
            context_candidates.append((source, target, edge.type, raw_types, bool(ownership), deployment_kind(edge, source, target) if edge.type == EdgeType.DEPLOYS else None))
        for relation in ir.infrastructure_relations:
            source = relation.source if relation.source in resource_ids or relation.source in arch_nodes else self._resolve(relation.source, arch_nodes, raw_to_arch)
            target = relation.target if relation.target in resource_ids or relation.target in arch_nodes else self._resolve(relation.target, arch_nodes, raw_to_arch)
            if source and target:
                context_candidates.append((source, target, relation.type, [], False, deployment_provenance(
                    relation.type,
                    source_id=source,
                    target_id=target,
                    source_type=subject_type(source),
                    target_type=subject_type(target),
                    metadata=relation.metadata,
                    evidence_sources=(
                        evidence_by_id[ref].source_type.value
                        for ref in relation.evidence_refs
                        if ref in evidence_by_id
                    ),
                ) if relation.type == EdgeType.DEPLOYS else None))
        for _ in range(2):
            next_frontier: set[str] = set()
            for source, target, relation_type, raw_types, ownership, deployment_kind_value in context_candidates:
                propagation = context_propagation_kind(
                    relation_type,
                    raw_relation_types=raw_types,
                    semantic_ownership=ownership,
                    deployment_provenance=deployment_kind_value,
                )
                if propagation != ContextPropagation.CAN_PROPAGATE_CONTEXT:
                    continue
                for origin, destination in context_direction_pairs(source, target, relation_type):
                    if origin in context_frontier and destination not in contextual_subjects:
                        next_frontier.add(destination)
            contextual_subjects.update(next_frontier)
            context_frontier = next_frontier
            if not context_frontier:
                break

        # The earlier context set also contains local component-flow seeds used
        # for bounded significance support. Recompute a root-anchored frontier
        # for the final projection gate without changing those semantics.
        root_contextual_subjects = set(context_root_ids) | set(root_context_component_ids)
        root_frontier = set(root_contextual_subjects)
        for _ in range(2):
            next_root_frontier: set[str] = set()
            for source, target, relation_type, raw_types, ownership, deployment_kind_value in context_candidates:
                propagation = context_propagation_kind(
                    relation_type,
                    raw_relation_types=raw_types,
                    semantic_ownership=ownership,
                    deployment_provenance=deployment_kind_value,
                )
                if propagation != ContextPropagation.CAN_PROPAGATE_CONTEXT:
                    continue
                for origin, destination in context_direction_pairs(source, target, relation_type):
                    if origin in root_frontier and destination not in root_contextual_subjects:
                        next_root_frontier.add(destination)
            root_contextual_subjects.update(next_root_frontier)
            root_frontier = next_root_frontier
            if not root_frontier:
                break
        independent_global_subjects: set[str] = set()
        for subject in strong:
            node = arch_nodes.get(subject)
            if subject in context_root_ids or (node and node.type in {
                NodeType.API,
                NodeType.EXTERNAL_SERVICE,
            }):
                independent_global_subjects.add(subject)
            if any(
                token in reason
                for reason in reasons.get(subject, [])
                for token in (
                    "principal framework",
                    "strong framework fact",
                    "explicit architectural role",
                    "observed application boundary",
                    "explicit architectural boundary",
                )
            ):
                independent_global_subjects.add(subject)

        strong_subjects = set(strong)
        for source, target, relation_type, raw_types, ownership, deployment_kind_value in context_candidates:
            propagation = context_propagation_kind(
                relation_type,
                raw_relation_types=raw_types,
                semantic_ownership=ownership,
                deployment_provenance=deployment_kind_value,
            )
            if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
                # A generic infrastructure observation can justify a boundary
                # only when its directional source is independently significant.
                for origin, destination in context_direction_pairs(source, target, relation_type):
                    if origin in resource_ids and destination in strong_subjects | set(medium):
                        independent_global_subjects.add(origin)
                continue
            for origin, destination in context_direction_pairs(source, target, relation_type):
                if origin in strong_subjects and destination in strong_subjects:
                    independent_global_subjects.update((origin, destination))
                if origin in strong_subjects and destination in medium:
                    independent_global_subjects.add(destination)

        # Significance is local evidence; projection eligibility is a separate final gate.
        # Navigation roots remain available for detailed/read-model navigation,
        # but their existence must not satisfy this gate.
        independently_global_resource_subjects = {
            destination
            for source, target, relation_type, raw_types, ownership, deployment_kind_value in context_candidates
            for origin, destination in context_direction_pairs(source, target, relation_type)
            if destination in resource_ids and origin in root_contextual_subjects
        }
        independently_global_role_subjects = {
            subject
            for subject in independent_global_subjects
            if arch_nodes.get(subject)
            and arch_nodes[subject].type in {NodeType.API, NodeType.EXTERNAL_SERVICE}
        }
        globally_eligible_subjects = (
            root_contextual_subjects | independently_global_role_subjects | independently_global_resource_subjects
        ) - set(navigation_root_ids)

        significances: list[ArchitecturalSignificance] = []
        for subject in sorted(set(arch_nodes) | resource_ids):
            node = arch_nodes.get(subject)
            weak_total = sum(weight for weight, _ in weak.get(subject, []))
            weak_contribution = min(weak_total, 0.12)
            score = min(
                sum(weight for weight, _ in strong.get(subject, []))
                + sum(weight for weight, _ in medium.get(subject, []))
                + weak_contribution,
                1.0,
            )
            has_refs = bool(refs.get(subject))
            strong_support = bool(strong.get(subject))
            medium_support = bool(medium.get(subject))
            if strong_support and has_refs and score >= 0.55:
                level = SignificanceLevel.HIGH
            elif (strong_support or medium_support) and has_refs and score >= 0.15:
                level = SignificanceLevel.MEDIUM
            elif has_refs:
                level = SignificanceLevel.LOW
            else:
                level = SignificanceLevel.UNKNOWN
            significances.append(ArchitecturalSignificance(
                subject=subject,
                significance=level,
                role=dependency_roles.get(subject),
                score=round(score, 6),
                supporting_evidence=sorted(refs.get(subject, set())),
                evidence_refs=sorted(refs.get(subject, set())),
                reasons=sorted(set(reasons.get(subject, []))),
                contains_refs=contains.get(subject, []),
            ))

        selected = {
            item.subject
            for item in significances
            if item.significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM}
            and item.subject in globally_eligible_subjects
            and not (arch_nodes.get(item.subject) and arch_nodes[item.subject].type == NodeType.CONFIGURATION)
        }

        selected &= set(arch_nodes) | resource_ids
        projected_edges = self._project_edges(ir, selected, arch_nodes, raw_to_arch)
        low_refs = sorted({ref for item in significances if item.significance == SignificanceLevel.LOW for ref in item.contains_refs or [item.subject]})
        unknown_refs = sorted({ref for item in significances if item.significance == SignificanceLevel.UNKNOWN for ref in item.contains_refs or [item.subject]})
        return HighLevelArchitectureProjection(
            detailed_node_count=len(arch_nodes) + len(ir.infrastructure_resources),
            high_level_node_count=len(selected),
            projected_node_ids=sorted(selected),
            projected_edges=projected_edges,
            significances=significances,
            low_significance_refs=low_refs,
            unknown_refs=unknown_refs,
            context_root_ids=sorted(context_root_ids),
            context_root_strengths={
                root: context_root_strengths.get(root, "strong")
                for root in sorted(context_root_ids)
            },
            context_root_kinds={
                root: context_root_kinds.get(root, "EXPLICIT_ARCHITECTURAL_BOUNDARY")
                for root in sorted(context_root_ids)
            },
            navigation_root_ids=sorted(navigation_root_ids),
            weak_evidence_saturation_count=weak_evidence_saturation_count,
        )

    @classmethod
    def _tokens(cls, value: str) -> set[str]:
        return set(cls._PACKAGE_TOKEN_RE.findall(value.lower()))

    @classmethod
    def _matches_stack_technology(cls, package: str, technologies: list[Any]) -> bool:
        package_tokens = cls._tokens(package)
        return any(package_tokens & cls._tokens(item.name) for item in technologies)

    def _project_edges(self, ir: ArchitectureIR, selected: set[str], arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> list[ProjectedEdge]:
        grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for edge in ir.architectural_graph.edges:
            source = self._selected_owner(edge.source, selected, arch_nodes, raw_to_arch)
            target = self._selected_owner(edge.target, selected, arch_nodes, raw_to_arch)
            if not source or not target or source == target:
                continue
            key = (source, target, edge.type.value)
            item = grouped.setdefault(key, {"refs": set(), "raw": set(), "edges": [], "confidence": 1.0, "status": edge.status})
            item["refs"].update(edge.evidence_refs)
            item["raw"].update(edge.raw_edge_ids or ([edge.id] if edge.id else []))
            item["edges"].append(edge)
            item["confidence"] = min(item["confidence"], edge.confidence)
            if edge.status == EvidenceStatus.UNCERTAIN:
                item["status"] = edge.status
        for relation in ir.infrastructure_relations:
            source = self._selected_owner(relation.source, selected, arch_nodes, raw_to_arch)
            target = self._selected_owner(relation.target, selected, arch_nodes, raw_to_arch)
            if not source or not target or source == target:
                continue
            key = (source, target, relation.type)
            item = grouped.setdefault(key, {"refs": set(), "raw": set(), "edges": [], "confidence": 1.0, "status": relation.status})
            item["refs"].update(relation.evidence_refs)
            item["raw"].add(relation.id)
            item["confidence"] = min(item["confidence"], relation.confidence)
            if relation.status == EvidenceStatus.UNCERTAIN:
                item["status"] = relation.status
        result: list[ProjectedEdge] = []
        for (source, target, kind), item in sorted(grouped.items()):
            result.append(ProjectedEdge(
                id=f"projection-edge:{source}:{target}:{kind}",
                source=source,
                target=target,
                kind=kind,
                status=item["status"],
                confidence=round(item["confidence"], 6),
                evidence_refs=sorted(item["refs"]),
                raw_edge_ids=sorted(item["raw"]),
                support_count=len(item["edges"]) or len(item["raw"]),
                supporting_observations=[{"edge_id": edge.id, "source": edge.source, "target": edge.target, "kind": edge.type.value} for edge in sorted(item["edges"], key=lambda value: value.id or "")],
            ))
        return result

    @staticmethod
    def _raw_to_arch(ir: ArchitectureIR) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for node in ir.architectural_graph.nodes:
            for raw_id in node.metadata.get("raw_node_ids", []):
                mapping[raw_id] = node.id
        return mapping

    @staticmethod
    def _resolve(value: str | None, arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> str | None:
        if not value:
            return None
        if value in arch_nodes:
            return value
        if value in raw_to_arch:
            return raw_to_arch[value]
        if value.startswith("module:") and value in raw_to_arch:
            return raw_to_arch[value]
        module_name = value.split(":", 1)[-1].split(".", 1)[0]
        for raw_id, arch_id in raw_to_arch.items():
            if raw_id.endswith(f":{module_name}"):
                return arch_id
        return None

    def _framework_boundary_assessments(self, ir: ArchitectureIR, arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> dict[str, dict[str, Any]]:
        """Classify framework facts by boundary ownership, without scoring."""
        facts_by_component: dict[str, list[Any]] = defaultdict(list)
        candidate_subjects: set[str] = set()
        strong_fact_kinds = {"APPLICATION", "HTTP_ENDPOINT", "ROUTER", "CONTROLLER_LIKE"}

        for fact in ir.framework_facts:
            subjects = {
                resolved
                for value in (
                    fact.subject,
                    fact.target,
                    fact.attributes.get("module"),
                    fact.attributes.get("endpoint"),
                    fact.attributes.get("owner"),
                    fact.attributes.get("application"),
                    fact.attributes.get("router"),
                )
                for resolved in [self._resolve(value, arch_nodes, raw_to_arch)]
                if resolved and arch_nodes.get(resolved) and arch_nodes[resolved].type == NodeType.COMPONENT
            }
            for subject in subjects:
                facts_by_component[subject].append(fact)
                if fact.kind in strong_fact_kinds:
                    candidate_subjects.add(subject)

        assessments: dict[str, dict[str, Any]] = {}
        def explicit_deployment(edge: Edge) -> bool:
            source = arch_nodes.get(edge.source)
            target = arch_nodes.get(edge.target)
            provenance = deployment_provenance(
                edge.type,
                source_id=edge.source,
                target_id=edge.target,
                source_type=source.type if source else None,
                target_type=target.type if target else None,
                metadata=edge.metadata,
            )
            return provenance in {
                DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT,
                DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP,
            }
        for subject in sorted(facts_by_component):
            facts = facts_by_component[subject]
            applications = [fact for fact in facts if fact.kind == "APPLICATION"]
            boundary_facts = [
                fact for fact in facts
                if fact.kind in {"HTTP_ENDPOINT", "ROUTER", "CONTROLLER_LIKE", "ROUTER_INCLUSION"}
            ]
            explicit = any(
                fact.attributes.get("architectural_boundary")
                or fact.metadata.get("architectural_boundary")
                or fact.attributes.get("entrypoint")
                or fact.metadata.get("entrypoint")
                for fact in applications
            )
            coherent = False
            associated_refs: set[str] = set()
            for application in applications:
                application_name = application.attributes.get("application") or application.subject
                application_module = application.attributes.get("module")
                for boundary in boundary_facts:
                    boundary_module = boundary.attributes.get("module")
                    same_module = bool(application_module and boundary_module and application_module == boundary_module)
                    same_application = boundary.attributes.get("application") == application_name
                    owned_endpoint = boundary.attributes.get("owner") == application_name
                    owned_router = boundary.attributes.get("router") == application_name
                    if same_module or same_application or owned_endpoint or owned_router:
                        coherent = True
                        associated_refs.update(boundary.evidence_refs)
            deployment = any(
                edge.type == EdgeType.DEPLOYS
                and subject in {edge.source, edge.target}
                and explicit_deployment(edge)
                for edge in ir.architectural_graph.edges
            )
            executable = any(
                fact.attributes.get("entrypoint")
                or fact.metadata.get("entrypoint")
                or fact.attributes.get("executable")
                or fact.metadata.get("executable")
                for fact in applications
            )
            raw_type_by_id = {edge.id: edge.type for edge in ir.raw_graph.edges if edge.id}
            semantic_flow = any(
                edge.type in {EdgeType.ROUTES_TO, EdgeType.QUERIES, EdgeType.PUBLISHES, EdgeType.CONSUMES, EdgeType.CONNECTS_TO}
                or any(raw_type_by_id.get(raw_id) in {EdgeType.CALLS, EdgeType.INSTANTIATES, EdgeType.EXTENDS} for raw_id in edge.raw_edge_ids)
                for edge in ir.architectural_graph.edges
                if subject in {edge.source, edge.target}
                and any(
                    arch_nodes.get(endpoint) and arch_nodes[endpoint].type == NodeType.COMPONENT
                    for endpoint in (edge.source, edge.target)
                    if endpoint != subject
                )
            )
            qualified = bool(applications and (explicit or coherent or deployment))
            global_qualified = bool(qualified and (explicit or deployment or semantic_flow))
            if qualified:
                ownership = "OWNED_APPLICATION_BOUNDARY"
                boundary_evidence = []
                if explicit:
                    boundary_evidence.append("explicit_application_boundary")
                if coherent:
                    boundary_evidence.append("application_router_endpoint_association")
                if deployment:
                    boundary_evidence.append("deployment_execution_boundary")
            elif applications:
                ownership = "LOCAL_FRAMEWORK_USAGE"
                boundary_evidence = []
            elif boundary_facts:
                ownership = "RELATED_FRAMEWORK_BOUNDARY"
                boundary_evidence = []
            else:
                ownership = "UNRESOLVED"
                boundary_evidence = []
            assessments[subject] = {
                "candidate": subject in candidate_subjects,
                "qualified": qualified,
                "global_qualified": global_qualified,
                "ownership": ownership,
                "boundary_evidence": sorted(boundary_evidence),
                "application_fact_count": len(applications),
                "framework_fact_count": len(facts),
                "application_refs": sorted({ref for fact in applications for ref in fact.evidence_refs}),
                "boundary_refs": sorted(associated_refs),
                "executable": bool(executable),
                "deployment": bool(deployment),
                "boundary_scope": "global" if global_qualified else "local" if (qualified or applications or boundary_facts) else "unresolved",
            }
        return assessments
    def _selected_owner(self, value: str, selected: set[str], arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> str | None:
        resolved = self._resolve(value, arch_nodes, raw_to_arch) or value
        if resolved in selected:
            return resolved
        node = arch_nodes.get(resolved)
        if not node:
            return None
        raw_ids = set(node.metadata.get("raw_node_ids", []))
        for candidate in sorted(selected):
            parent = arch_nodes.get(candidate)
            if parent and raw_ids & set(parent.metadata.get("raw_node_ids", [])):
                return candidate
        return None


__all__ = [
    "ArchitecturalSignificance",
    "ArchitecturalProjectionBuilder",
    "HighLevelArchitectureProjection",
    "ProjectedEdge",
    "SignificanceLevel",
]
