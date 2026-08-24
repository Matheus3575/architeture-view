from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field



INLINE_EVIDENCE_REF_LIMIT = 20


class EvidenceGroup(BaseModel):
    """Shared, deterministic evidence collection used by visual elements."""

    model_config = ConfigDict(extra="forbid")

    id: str
    evidence_count: int = Field(ge=0)
    evidence_refs: list[str] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)
    source_refs: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class EvidenceBinding:
    inline_refs: list[str]
    group_ref: str | None
    evidence_count: int


class EvidencePayloadIndex:
    """Deduplicate and compact evidence associations in one bounded pass."""

    def __init__(self, evidence: Iterable[Any], inline_limit: int = INLINE_EVIDENCE_REF_LIMIT):
        self._evidence = {item.id: item for item in evidence}
        self.inline_limit = inline_limit
        self.groups: dict[str, EvidenceGroup] = {}
        self.original_reference_count = 0
        self.inline_reference_count = 0

    def bind(self, refs: Iterable[str]) -> EvidenceBinding:
        unique_refs = sorted(set(refs))
        self.original_reference_count += len(unique_refs)
        if len(unique_refs) <= self.inline_limit:
            self.inline_reference_count += len(unique_refs)
            return EvidenceBinding(unique_refs, None, len(unique_refs))

        group_id = _group_id(unique_refs)
        if group_id not in self.groups:
            self.groups[group_id] = self._make_group(group_id, unique_refs)
        return EvidenceBinding([], group_id, len(unique_refs))

    def _make_group(self, group_id: str, refs: list[str]) -> EvidenceGroup:
        summary: Counter[str] = Counter()
        source_refs: set[str] = set()
        for ref in refs:
            item = self._evidence.get(ref)
            if item is None:
                summary["UNKNOWN"] += 1
                continue
            summary[item.source_type] += 1
            if item.source is not None:
                source_refs.add(item.source.path)
        return EvidenceGroup(
            id=group_id,
            evidence_count=len(refs),
            evidence_refs=refs,
            summary=dict(sorted(summary.items())),
            source_refs=sorted(source_refs),
        )


def _group_id(refs: list[str]) -> str:
    digest = hashlib.sha1("|".join(refs).encode("utf-8")).hexdigest()[:20]
    return f"evidence-group-{digest}"


__all__ = [
    "EvidenceBinding",
    "EvidenceGroup",
    "EvidencePayloadIndex",
    "INLINE_EVIDENCE_REF_LIMIT",
]