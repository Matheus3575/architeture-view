from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceStatus(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"
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


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: NodeType
    name: str
    layer: str | None = None
    source: SourceRef | None = None
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    type: EdgeType
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Component(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    level: str = "component"
    node_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.INFERRED
    evidence_refs: list[str] = Field(default_factory=list)


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


class ArchitectureIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1"
    repository: RepositoryInfo
    stack: StackProfile = Field(default_factory=StackProfile)
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    components: list[Component] = Field(default_factory=list)
    architecture: ArchitectureAnalysis = Field(default_factory=ArchitectureAnalysis)
    evidence: list[Evidence] = Field(default_factory=list)
    validation: ValidationReport = Field(default_factory=ValidationReport)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if not value or "." not in value:
            raise ValueError("schema_version must use a version such as 0.1")
        return value

    def canonicalize(self) -> "ArchitectureIR":
        """Return a stable copy suitable for golden files and reproducible builds."""
        data = self.model_dump(mode="json")
        data["nodes"] = sorted(data["nodes"], key=lambda item: item["id"])
        data["edges"] = sorted(
            data["edges"],
            key=lambda item: (item["source"], item["target"], item["type"]),
        )
        data["components"] = sorted(data["components"], key=lambda item: item["id"])
        data["evidence"] = sorted(data["evidence"], key=lambda item: item["id"])
        data["architecture"]["hypotheses"] = sorted(
            data["architecture"]["hypotheses"], key=lambda item: item["pattern"]
        )
        return ArchitectureIR.model_validate(data)
