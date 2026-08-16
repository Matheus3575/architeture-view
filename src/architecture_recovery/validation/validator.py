from __future__ import annotations

from architecture_recovery.ir import ArchitectureIR, EdgeType, NodeType, ValidationReport


class ArchitectureValidator:
    def validate(self, ir: ArchitectureIR) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        node_ids = {node.id for node in ir.nodes}
        evidence_ids = {evidence.id for evidence in ir.evidence}

        for edge in ir.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source does not exist: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge target does not exist: {edge.target}")
            if not edge.evidence_refs:
                errors.append(f"Edge has no evidence: {edge.source} -> {edge.target}")
            for ref in edge.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Edge references unknown evidence: {ref}")

        for node in ir.nodes:
            for ref in node.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Node {node.id} references unknown evidence: {ref}")

        for component in ir.components:
            for node_id in component.node_ids:
                if node_id not in node_ids:
                    errors.append(f"Component {component.id} references unknown node: {node_id}")

        connected = {edge.source for edge in ir.edges} | {edge.target for edge in ir.edges}
        for node in ir.nodes:
            if node.id not in connected and node.type not in {
                NodeType.REPOSITORY,
                NodeType.EXTERNAL_SERVICE,
                NodeType.CONFIGURATION,
            }:
                warnings.append(f"Isolated node requires explanation: {node.id}")

        for hypothesis in ir.architecture.hypotheses:
            for ref in hypothesis.evidence_refs:
                if ref not in evidence_ids:
                    errors.append(f"Hypothesis references unknown evidence: {ref}")

        return ValidationReport(valid=not errors, errors=errors, warnings=warnings)
