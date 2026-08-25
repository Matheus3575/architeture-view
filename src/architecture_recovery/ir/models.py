from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"
    UNKNOWN = "unknown"


class SourceOrigin(StrEnum):
    FIRST_PARTY = "first_party"
    THIRD_PARTY = "third_party"
    STANDARD_LIBRARY = "standard_library"
    GENERATED = "generated"
    UNKNOWN = "unknown"


class NodeType(StrEnum):
    REPOSITORY = "repository"
    APPLICATION = "application"
    COMPONENT = "component"
    MODULE = "module"
    FILE = "file"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTION = "function"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    MESSAGE_BROKER = "message_broker"
    EXTERNAL_SERVICE = "external_service"
    EXTERNAL_DEPENDENCY = "external_dependency"
    API = "api"
    ENDPOINT = "endpoint"
    CONTAINER = "container"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"


class EdgeType(StrEnum):
    CALLS = "CALLS"
    IMPORTS = "IMPORTS"
    CONTAINS = "CONTAINS"
    EXTENDS = "EXTENDS"
    IMPLEMENTS = "IMPLEMENTS"
    INSTANTIATES = "INSTANTIATES"
    DEPENDS_ON = "DEPENDS_ON"
    ROUTES_TO = "ROUTES_TO"
    READS = "READS"
    WRITES = "WRITES"
    QUERIES = "QUERIES"
    PUBLISHES = "PUBLISHES"
    CONSUMES = "CONSUMES"
    CONFIGURES = "CONFIGURES"
    DEPLOYS = "DEPLOYS"
    CONNECTS_TO = "CONNECTS_TO"
    SERIALIZES = "SERIALIZES"
    DESERIALIZES = "DESERIALIZES"


class EvidenceSource(StrEnum):
    AST = "AST"
    IMPORT = "IMPORT"
    SYMBOL_RESOLUTION = "SYMBOL_RESOLUTION"
    CALL_GRAPH = "CALL_GRAPH"
    CONFIGURATION = "CONFIGURATION"
    DEPENDENCY_FILE = "DEPENDENCY_FILE"
    DOCKERFILE = "DOCKERFILE"
    DOCKER_COMPOSE = "DOCKER_COMPOSE"
    CI_CONFIGURATION = "CI_CONFIGURATION"
    FRAMEWORK_CONVENTION = "FRAMEWORK_CONVENTION"
    DIRECTORY_STRUCTURE = "DIRECTORY_STRUCTURE"
    DOCUMENTATION = "DOCUMENTATION"
    GRAPH_AGGREGATION = "GRAPH_AGGREGATION"
    FRAMEWORK_ADAPTER = "FRAMEWORK_ADAPTER"
    COMPONENT_DETECTION = "COMPONENT_DETECTION"


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    start_line: int | None = Field(default=None, ge=1)
    end_line: int | None = Field(default=None, ge=1)
    symbol: str | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_type: EvidenceSource
    detail: str
    source: SourceRef | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class FrameworkFact(BaseModel):
    """Framework-neutral semantic fact produced after raw observations."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    subject: str | None = None
    target: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    source: SourceRef | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: NodeType
    name: str
    origin: SourceOrigin = SourceOrigin.UNKNOWN
    layer: str | None = None
    source: SourceRef | None = None
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    source: str
    target: str
    type: EdgeType
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    raw_edge_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnresolvedCall(BaseModel):
    """Observed call whose destination could not be determined safely."""

    model_config = ConfigDict(extra="forbid")

    caller: str
    callee: str
    source: SourceRef
    status: EvidenceStatus = EvidenceStatus.UNKNOWN
    reason: str = "unresolved_symbol"


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    level: str = "component"
    node_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.INFERRED
    evidence_refs: list[str] = Field(default_factory=list)
    internal_edge_ids: list[str] = Field(default_factory=list)
    external_edge_ids: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    semantic_hints: list[str] = Field(default_factory=list)
    supporting_observations: list[dict[str, Any]] = Field(default_factory=list)


class Technology(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)


class StackProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    languages: list[Technology] = Field(default_factory=list)
    runtimes: list[Technology] = Field(default_factory=list)
    frameworks: list[Technology] = Field(default_factory=list)
    databases: list[Technology] = Field(default_factory=list)
    infrastructure: list[Technology] = Field(default_factory=list)


class ArchitectureHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    status: EvidenceStatus = EvidenceStatus.UNCERTAIN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explanation: str = ""


class ArchitectureAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypotheses: list[ArchitectureHypothesis] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    smells: list[dict[str, Any]] = Field(default_factory=list)


class RepositoryInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    commit: str | None = None
    source_url: str | None = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GraphSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)


class RawCodeGraph(GraphSnapshot):
    """Observed source-level graph, including external symbols."""

    unresolved_calls: list[UnresolvedCall] = Field(default_factory=list)


class ArchitecturalGraph(GraphSnapshot):
    """Aggregated graph intended for architectural analysis and rendering."""


class ClassificationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    origin: SourceOrigin
    reason: str
    package: str | None = None


class ClassificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[ClassificationRecord] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)


class InfrastructureResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: str  # DATABASE, CACHE, MESSAGE_BROKER, SERVICE, CONTAINER, STORAGE, NETWORK, UNKNOWN
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    source: SourceRef | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


def canonical_relation_type(value: str | EdgeType) -> str:
    """Return the single IR identity for a known relation vocabulary item."""

    raw = value.value if isinstance(value, EdgeType) else str(value)
    canonical = raw.upper()
    return canonical if canonical in {item.value for item in EdgeType} else raw


def relation_strength(value: str | EdgeType) -> str:
    """Classify a canonical relation without changing its semantic identity."""

    canonical = canonical_relation_type(value)
    if canonical in {"ROUTES_TO", "QUERIES", "PUBLISHES", "CONSUMES"}:
        return "strong"
    if canonical in {"CONNECTS_TO", "DEPLOYS"}:
        return "medium"
    return "weak"


class InfrastructureRelation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    type: str
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def canonicalize_relation_identity(cls, value: Any) -> Any:
        if not isinstance(value, dict) or "type" not in value:
            return value
        raw_type = value["type"].value if isinstance(value["type"], EdgeType) else str(value["type"])
        canonical = canonical_relation_type(raw_type)
        if canonical == raw_type:
            return value
        metadata = dict(value.get("metadata") or {})
        metadata.setdefault("source_relation_type", raw_type)
        return {**value, "type": canonical, "metadata": metadata}


class ArchitectureIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.2"
    repository: RepositoryInfo
    raw_graph: RawCodeGraph = Field(default_factory=RawCodeGraph)
    architectural_graph: ArchitecturalGraph = Field(default_factory=ArchitecturalGraph)
    classifications: ClassificationReport = Field(default_factory=ClassificationReport)
    # Backward-compatible aliases for consumers that still inspect the raw graph directly.
    stack: StackProfile = Field(default_factory=StackProfile)
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    # M4 candidates are separate from the legacy structural components created
    # by ArchitecturalGraphBuilder. They are hypotheses, not architecture facts.
    component_candidates: list[Component] = Field(default_factory=list)
    component_unassigned_node_ids: list[str] = Field(default_factory=list)
    component_detection_metrics: dict[str, Any] = Field(default_factory=dict)
    architecture: ArchitectureAnalysis = Field(default_factory=ArchitectureAnalysis)
    evidence: list[Evidence] = Field(default_factory=list)
    # Additive optional extension: framework facts are not graph nodes or
    # architecture hypotheses, and older consumers may safely ignore them.
    framework_facts: list[FrameworkFact] = Field(default_factory=list)
    # Additive optional extension for M5: infrastructure resources and relations
    infrastructure_resources: list[InfrastructureResource] = Field(default_factory=list)
    infrastructure_relations: list[InfrastructureRelation] = Field(default_factory=list)
    validation: ValidationReport = Field(default_factory=ValidationReport)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value or "." not in value:
            raise ValueError("schema_version must use a version such as 0.1")
        return value

    def model_post_init(self, __context: Any) -> None:
        if not self.raw_graph.nodes and not self.raw_graph.edges and (self.nodes or self.edges):
            self.raw_graph = RawCodeGraph(nodes=list(self.nodes), edges=list(self.edges))
        if not self.nodes:
            self.nodes = list(self.raw_graph.nodes)
        if not self.edges:
            self.edges = list(self.raw_graph.edges)

    def canonicalize(self) -> "ArchitectureIR":
        """Return a stable copy suitable for golden files and reproducible builds."""
        data = self.model_dump(mode="json")
        data["nodes"] = sorted(data["nodes"], key=lambda item: item["id"])
        data["edges"] = sorted(
            data["edges"],
            key=lambda item: (item["source"], item["target"], item["type"]),
        )
        data["components"] = sorted(data["components"], key=lambda item: item["id"])
        data["component_candidates"] = sorted(
            data["component_candidates"], key=lambda item: item["id"]
        )
        data["component_unassigned_node_ids"] = sorted(
            data["component_unassigned_node_ids"]
        )
        data["evidence"] = sorted(data["evidence"], key=lambda item: item["id"])
        data["framework_facts"] = sorted(
            data["framework_facts"],
            key=lambda item: (
                item["kind"],
                item.get("subject") or "",
                item.get("target") or "",
                item.get("source", {}).get("path", "") if item.get("source") else "",
                item.get("source", {}).get("start_line", 0) if item.get("source") else 0,
            ),
        )
        data["infrastructure_resources"] = sorted(
            data.get("infrastructure_resources", []),
            key=lambda item: item["id"]
        )
        data["infrastructure_relations"] = sorted(
            data.get("infrastructure_relations", []),
            key=lambda item: (item["source"], item["target"], item["type"], item.get("id") or "")
        )
        data["architecture"]["hypotheses"] = sorted(
            data["architecture"]["hypotheses"], key=lambda item: item["pattern"]
        )
        data["raw_graph"]["nodes"] = sorted(data["raw_graph"]["nodes"], key=lambda item: item["id"])
        data["raw_graph"]["edges"] = sorted(
            data["raw_graph"]["edges"],
            key=lambda item: (item["source"], item["target"], item["type"], item.get("id") or ""),
        )
        data["raw_graph"]["unresolved_calls"] = sorted(
            data["raw_graph"].get("unresolved_calls", []),
            key=lambda item: (item["source"]["path"], item["source"].get("start_line") or 0, item["callee"]),
        )
        data["architectural_graph"]["nodes"] = sorted(
            data["architectural_graph"]["nodes"], key=lambda item: item["id"]
        )
        data["architectural_graph"]["edges"] = sorted(
            data["architectural_graph"]["edges"],
            key=lambda item: (item["source"], item["target"], item["type"], item.get("id") or ""),
        )
        data["classifications"]["records"] = sorted(
            data["classifications"]["records"], key=lambda item: item["node_id"]
        )
        return ArchitectureIR.model_validate(data)
