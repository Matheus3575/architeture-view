from __future__ import annotations

from architecture_recovery.ir import ArchitectureIR, EdgeType, NodeType, ValidationReport


class ArchitectureValidator:
    def validate(self, ir: ArchitectureIR) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        evidence_ids = {evidence.id for evidence in ir.evidence}
        raw_node_ids = self._validate_graph(
            "Raw Code Graph", ir.raw_graph.nodes, ir.raw_graph.edges, evidence_ids, errors
        )
        raw_edge_ids = {edge.id for edge in ir.raw_graph.edges if edge.id}
        architectural_node_ids = self._validate_graph(
            "Architectural Graph",
            ir.architectural_graph.nodes,
            ir.architectural_graph.edges,
            evidence_ids,
            errors,
        )
        for edge in ir.architectural_graph.edges:
            for raw_edge_id in edge.raw_edge_ids:
                if raw_edge_id not in raw_edge_ids:
                    errors.append(f"Architectural edge references unknown raw edge: {raw_edge_id}")

        for node in [*ir.raw_graph.nodes, *ir.architectural_graph.nodes]:
            for ref in node.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Node {node.id} references unknown evidence: {ref}")

        for component in ir.components:
            for node_id in component.node_ids:
                if node_id not in raw_node_ids:
                    errors.append(f"Component {component.id} references unknown node: {node_id}")

        for component in ir.component_candidates:
            for node_id in component.node_ids:
                if node_id not in raw_node_ids:
                    errors.append(f"Component candidate {component.id} references unknown node: {node_id}")
            for ref in component.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Component candidate {component.id} references unknown evidence: {ref}")
            for edge_id in [*component.internal_edge_ids, *component.external_edge_ids]:
                if edge_id not in raw_edge_ids:
                    errors.append(f"Component candidate {component.id} references unknown raw edge: {edge_id}")

        candidate_members = [
            node_id
            for component in ir.component_candidates
            for node_id in component.node_ids
        ]
        if len(candidate_members) != len(set(candidate_members)):
            errors.append("Component candidates overlap on member nodes")
        for node_id in ir.component_unassigned_node_ids:
            if node_id not in raw_node_ids:
                errors.append(f"Unassigned component node does not exist: {node_id}")

        for record in ir.classifications.records:
            if record.node_id not in raw_node_ids:
                errors.append(f"Classification references unknown node: {record.node_id}")

        connected = {edge.source for edge in ir.architectural_graph.edges} | {
            edge.target for edge in ir.architectural_graph.edges
        }
        for node in ir.architectural_graph.nodes:
            if node.id not in connected and node.type not in {
                NodeType.REPOSITORY,
                NodeType.EXTERNAL_SERVICE,
                NodeType.EXTERNAL_DEPENDENCY,
                NodeType.CONFIGURATION,
            }:
                warnings.append(f"Isolated node requires explanation: {node.id}")

        for hypothesis in ir.architecture.hypotheses:
            for ref in hypothesis.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Hypothesis references unknown evidence: {ref}")

        for fact in ir.framework_facts:
            for ref in fact.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Framework fact {fact.kind} references unknown evidence: {ref}")

        return ValidationReport(valid=not errors, errors=errors, warnings=warnings)

    @staticmethod
    def _validate_graph(label, nodes, edges, evidence_ids, errors):
        node_ids = {node.id for node in nodes}
        for edge in edges:
            if edge.source not in node_ids:
                errors.append(f"{label} edge source does not exist: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"{label} edge target does not exist: {edge.target}")
            if not edge.evidence_refs:
                errors.append(f"{label} edge has no evidence: {edge.source} -> {edge.target}")
            for ref in edge.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"{label} edge references unknown evidence: {ref}")
        return node_ids
