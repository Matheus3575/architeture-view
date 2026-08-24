from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    ArchitecturalGraph,
    Component,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FrameworkFact,
    Node,
    NodeType,
    SourceOrigin,
    SourceRef,
)


@dataclass(frozen=True)
class ComponentDetectionContext:
    """Already-built analysis artifacts consumed by component detection."""

    raw_graph: PropertyGraph
    architectural_graph: ArchitecturalGraph | None = None
    framework_facts: tuple[FrameworkFact, ...] = ()


@dataclass
class ComponentDetectionResult:
    candidates: list[Component] = field(default_factory=list)
    unassigned_node_ids: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    metrics: dict[str, int | float | str] = field(default_factory=dict)


@dataclass
class _PairEvidence:
    score: float = 0.0
    observations: list[dict] = field(default_factory=list)
    directions: set[tuple[str, str]] = field(default_factory=set)


class ComponentDetector:
    """Build conservative first-party component candidates from graph evidence.

    Detection works at module granularity. A pair is eligible for grouping only
    when its accumulated affinity reaches ``MIN_AFFINITY`` through structural
    relations; names and paths never contribute to the score.
    """

    MIN_AFFINITY = 3.0
    WEIGHTS = {
        EdgeType.CALLS: 3.0,
        EdgeType.INSTANTIATES: 3.0,
        EdgeType.EXTENDS: 2.0,
        EdgeType.IMPORTS: 1.0,
    }
    FRAMEWORK_WEIGHTS = {
        "FRAMEWORK_DEPENDENCY": 2.5,
        "ROUTER_INCLUSION": 2.5,
        "RESPONSE_SCHEMA": 1.5,
    }

    def detect(self, context: ComponentDetectionContext) -> ComponentDetectionResult:
        module_nodes = self._first_party_modules(context.raw_graph)
        module_ids = set(module_nodes)
        node_to_module = self._node_module_index(context.raw_graph, module_nodes)
        pairs: dict[tuple[str, str], _PairEvidence] = {}
        roles: dict[str, set[str]] = defaultdict(set)

        for edge in context.raw_graph.edges:
            if edge.type == EdgeType.CONTAINS:
                continue
            source_module = node_to_module.get(edge.source)
            target_module = node_to_module.get(edge.target)
            if not source_module or not target_module or source_module == target_module:
                continue
            weight = self.WEIGHTS.get(edge.type, 0.0)
            if not weight:
                continue
            if edge.type == EdgeType.CALLS and edge.metadata.get("flow_evidence"):
                weight += 1.0
            self._add_pair_observation(
                pairs,
                source_module,
                target_module,
                weight,
                {
                    "type": "DATA_FLOW" if edge.metadata.get("flow_evidence") else edge.type.value,
                    "source": edge.source,
                    "target": edge.target,
                    "raw_edge_id": edge.id,
                    "source_module": source_module,
                    "target_module": target_module,
                    "evidence_refs": sorted(edge.evidence_refs),
                    "weight": weight,
                },
            )

        variable_modules = self._framework_variable_modules(context.framework_facts, node_to_module)
        for fact in context.framework_facts:
            subject_module = self._fact_module(fact.subject, node_to_module)
            target_value = fact.target or fact.attributes.get("schema")
            target_module = self._fact_module(target_value, node_to_module)
            weight = self.FRAMEWORK_WEIGHTS.get(fact.kind, 0.0)
            if fact.kind == "ROUTER_INCLUSION":
                subject_module = variable_modules.get(fact.attributes.get("application"))
                target_module = variable_modules.get(fact.attributes.get("router"))
            if fact.kind == "RESPONSE_SCHEMA":
                subject_module = self._fact_module(fact.attributes.get("endpoint"), node_to_module)
                target_module = self._fact_module(fact.attributes.get("schema"), node_to_module)
            if weight and subject_module and target_module and subject_module != target_module:
                observation = {
                    "type": fact.kind,
                    "source": fact.subject,
                    "target": fact.target or fact.attributes.get("schema"),
                    "framework_fact": fact.kind,
                    "source_module": subject_module,
                    "target_module": target_module,
                    "evidence_refs": sorted(fact.evidence_refs),
                    "weight": weight,
                }
                self._add_pair_observation(
                    pairs, subject_module, target_module, weight, observation
                )
            self._add_fact_roles(fact, node_to_module, roles)

        qualifying = {
            pair: item for pair, item in pairs.items() if item.score >= self.MIN_AFFINITY
        }
        groups = self._groups(module_ids, qualifying)
        candidates: list[Component] = []
        evidence: list[Evidence] = []
        assigned: set[str] = set()
        for members in groups:
            if len(members) < 2:
                continue
            assigned.update(members)
            candidate, candidate_evidence = self._candidate(
                members,
                module_nodes,
                node_to_module,
                pairs,
                context.raw_graph,
                context.framework_facts,
                roles,
            )
            candidates.append(candidate)
            evidence.append(candidate_evidence)

        unassigned = sorted(module_ids - assigned)
        candidates.sort(key=lambda item: item.id)
        result = ComponentDetectionResult(
            candidates=candidates,
            unassigned_node_ids=unassigned,
            evidence=sorted(evidence, key=lambda item: item.id),
            metrics={
                "module_count": len(module_ids),
                "pair_count": len(pairs),
                "qualifying_pair_count": len(qualifying),
                "candidate_count": len(candidates),
                "assigned_module_count": len(assigned),
                "unassigned_module_count": len(unassigned),
                "algorithm": "module-affinity-union-find-v1",
            },
        )
        return result

    @staticmethod
    def _first_party_modules(graph: PropertyGraph) -> dict[str, Node]:
        return {
            node.id: node
            for node in graph.nodes.values()
            if node.type == NodeType.MODULE and node.origin == SourceOrigin.FIRST_PARTY
        }

    @staticmethod
    def _node_module_index(graph: PropertyGraph, module_nodes: dict[str, Node]) -> dict[str, str]:
        by_path = {
            node.source.path: node_id
            for node_id, node in module_nodes.items()
            if node.source
        }
        result: dict[str, str] = {}
        for node in graph.nodes.values():
            if node.id in module_nodes:
                result[node.id] = node.id
            elif node.origin == SourceOrigin.FIRST_PARTY and node.source:
                module_id = by_path.get(node.source.path)
                if module_id:
                    result[node.id] = module_id
        return result

    @staticmethod
    def _fact_module(value: str | None, node_to_module: dict[str, str]) -> str | None:
        if not value or value == "UNKNOWN":
            return None
        return node_to_module.get(value)

    @staticmethod
    def _framework_variable_modules(
        facts: tuple[FrameworkFact, ...], node_to_module: dict[str, str]
    ) -> dict[str, str]:
        result: dict[str, str] = {}
        for fact in facts:
            if fact.kind not in {"APPLICATION", "ROUTER"}:
                continue
            variable = fact.attributes.get("application") or fact.attributes.get("router")
            module = fact.attributes.get("module")
            if variable and module:
                # Framework facts expose the module name, while Raw Graph uses
                # the module node ID. Resolve it without a source scan.
                module_id = next(
                    (node_id for node_id in node_to_module.values() if node_id.endswith(f":{module}")),
                    None,
                )
                if module_id:
                    result[variable] = module_id
        return result

    @staticmethod
    def _add_fact_roles(
        fact: FrameworkFact, node_to_module: dict[str, str], roles: dict[str, set[str]]
    ) -> None:
        role_by_kind = {
            "APPLICATION": "application_entrypoint",
            "ROUTER": "http_router",
            "HTTP_ENDPOINT": "http_entrypoint",
            "FRAMEWORK_DEPENDENCY": "dependency_consumer",
            "RESPONSE_SCHEMA": "response_schema",
            "SCHEMA": "schema",
        }
        role = role_by_kind.get(fact.kind)
        if not role:
            return
        for value in (
            fact.subject,
            fact.target,
            fact.attributes.get("endpoint"),
            fact.attributes.get("schema"),
        ):
            module = node_to_module.get(value) if value else None
            if module:
                roles[module].add(role)

    @staticmethod
    def _add_pair_observation(
        pairs: dict[tuple[str, str], _PairEvidence],
        source: str,
        target: str,
        weight: float,
        observation: dict,
    ) -> None:
        key = tuple(sorted((source, target)))
        pair = pairs.setdefault(key, _PairEvidence())
        pair.score += weight
        pair.directions.add((source, target))
        pair.observations.append(observation)

    @staticmethod
    def _groups(
        module_ids: set[str], qualifying: dict[tuple[str, str], _PairEvidence]
    ) -> list[tuple[str, ...]]:
        parent = {module_id: module_id for module_id in module_ids}

        def find(item: str) -> str:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        for left, right in sorted(qualifying):
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parent[right_root] = left_root
        grouped: dict[str, list[str]] = defaultdict(list)
        for module_id in sorted(module_ids):
            grouped[find(module_id)].append(module_id)
        return [tuple(items) for items in grouped.values() if len(items) > 1]

    def _candidate(
        self,
        members: tuple[str, ...],
        module_nodes: dict[str, Node],
        node_to_module: dict[str, str],
        pairs: dict[tuple[str, str], _PairEvidence],
        graph: PropertyGraph,
        facts: tuple[FrameworkFact, ...],
        roles: dict[str, set[str]],
    ) -> tuple[Component, Evidence]:
        member_set = set(members)
        pair_items = [
            (pair, item)
            for pair, item in pairs.items()
            if pair[0] in member_set and pair[1] in member_set
        ]
        score = sum(item.score for _, item in pair_items)
        internal_edge_ids: set[str] = set()
        external_edge_ids: set[str] = set()
        raw_evidence_refs: set[str] = set()
        observations: list[dict] = []
        for edge in graph.edges:
            if edge.type == EdgeType.CONTAINS:
                continue
            source_module = node_to_module.get(edge.source)
            target_module = node_to_module.get(edge.target)
            if source_module in member_set and target_module in member_set:
                if edge.id:
                    internal_edge_ids.add(edge.id)
                raw_evidence_refs.update(edge.evidence_refs)
            elif source_module in member_set or target_module in member_set:
                if edge.id:
                    external_edge_ids.add(edge.id)

        for _, item in pair_items:
            observations.extend(item.observations)
            directions = item.directions
            if len(directions) > 1:
                observations.append(
                    {
                        "type": "RECIPROCAL_RELATION",
                        "source": sorted(directions)[0][0],
                        "target": sorted(directions)[0][1],
                        "directions": [list(direction) for direction in sorted(directions)],
                    }
                )
            for observation in item.observations:
                raw_evidence_refs.update(observation.get("evidence_refs", []))

        for fact in facts:
            if self._fact_in_group(fact, member_set, node_to_module):
                raw_evidence_refs.update(fact.evidence_refs)
                observations.append(
                    {
                        "type": fact.kind,
                        "source": fact.subject,
                        "target": fact.target,
                        "evidence_refs": sorted(fact.evidence_refs),
                    }
                )

        member_names = [module_nodes[item].name for item in members]
        token = "|".join(members)
        candidate_id = f"component-candidate:{hashlib.sha1(token.encode()).hexdigest()[:16]}"
        detection_evidence = Evidence(
            id=f"evidence:{hashlib.sha1(('component-detection:' + token).encode()).hexdigest()[:16]}",
            source_type=EvidenceSource.COMPONENT_DETECTION,
            detail=(
                f"Candidate grouped modules {', '.join(member_names)} with heuristic affinity "
                f"{score:.2f}; grouping uses structural and semantic evidence, not names."
            ),
            source=SourceRef(path="component-detection", symbol=candidate_id),
        )
        confidence = min(0.9, 0.5 + 0.05 * min(score, 8.0))
        refs = sorted({*raw_evidence_refs, detection_evidence.id})
        candidate = Component(
            id=candidate_id,
            name="candidate(" + ",".join(member_names) + ")",
            level="component_candidate",
            node_ids=list(members),
            confidence=confidence,
            status=EvidenceStatus.UNCERTAIN,
            evidence_refs=refs,
            internal_edge_ids=sorted(internal_edge_ids),
            external_edge_ids=sorted(external_edge_ids),
            roles=sorted({role for member in members for role in roles.get(member, set())}),
            semantic_hints=sorted({
                hint
                for observation in observations
                for hint in ([observation.get("type")] if observation.get("type") else [])
            }),
            supporting_observations=self._unique_observations(observations),
        )
        return candidate, detection_evidence

    @staticmethod
    def _fact_in_group(
        fact: FrameworkFact, member_set: set[str], node_to_module: dict[str, str]
    ) -> bool:
        values = [
            fact.subject,
            fact.target,
            fact.attributes.get("endpoint"),
            fact.attributes.get("schema"),
        ]
        return any(node_to_module.get(value) in member_set for value in values if value)

    @staticmethod
    def _unique_observations(observations: list[dict]) -> list[dict]:
        unique: dict[tuple, dict] = {}
        for observation in observations:
            key = (
                observation.get("type"),
                observation.get("source"),
                observation.get("target"),
                observation.get("raw_edge_id"),
                tuple(observation.get("evidence_refs", [])),
            )
            unique[key] = observation
        return sorted(
            unique.values(),
            key=lambda item: (
                item.get("type", ""),
                item.get("source", "") or "",
                item.get("target", "") or "",
                item.get("raw_edge_id", "") or "",
            ),
        )
