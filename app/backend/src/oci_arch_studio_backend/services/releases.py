from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from oci_arch_studio_backend.models.architecture import KnowledgeTemporalContext, ReleaseImpactSummary
from oci_arch_studio_backend.services.intents import Intent


RELEASE_QUERY_STOPWORDS = {
    "announced",
    "architecture",
    "change",
    "does",
    "latest",
    "release",
    "service",
    "update",
    "current",
    "historical",
    "previous",
}


@dataclass(frozen=True)
class ReleaseMatch:
    title: str
    service: str
    service_domain: str
    impact_tags: list[str]
    impact_level: str
    source_url: str | None
    release_date: str | None
    summary: str


class ReleaseSnapshotStore:
    def __init__(self, snapshot_path: Path) -> None:
        self.snapshot_path = snapshot_path
        self._releases: list[dict[str, object]] | None = None
        self._payload: dict[str, object] | None = None

    @property
    def exists(self) -> bool:
        return self.snapshot_path.exists()

    def find_matches(self, question: str, limit: int = 3) -> list[ReleaseMatch]:
        if not self.exists:
            return []

        question_terms = {
            token
            for token in question.lower().replace("/", " ").replace("-", " ").split()
            if len(token) >= 4 and token not in RELEASE_QUERY_STOPWORDS
        }
        scored: list[tuple[int, dict[str, object]]] = []
        for release in self._load_releases():
            haystack = " ".join(
                str(release.get(field, ""))
                for field in ("title", "service", "service_domain", "summary")
            ).lower()
            score = sum(1 for term in question_terms if term in haystack)
            if score:
                scored.append((score, release))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._to_match(release) for _, release in scored[:limit]]

    def retrieval_context_terms(self, question: str, limit: int = 3) -> list[str]:
        matches = self.find_matches(question, limit=limit)
        terms = []
        for match in matches:
            terms.extend([match.service, match.service_domain, *match.impact_tags])
        return [term for term in dict.fromkeys(terms) if term]

    def freshness_note(self, intent: Intent, question: str) -> str | None:
        if intent != Intent.RELEASE_AWARENESS and "latest" not in question.lower():
            return None
        if not self.exists:
            return (
                "No local release snapshot is available yet; run the release ingestion pipeline "
                "before making current OCI update claims."
            )
        matches = self.find_matches(question)
        if not matches:
            return (
                "A release snapshot exists, but no matching release item was found for this prompt; "
                "treat the answer as historical/local guidance until the specific release note is provided."
            )
        services = ", ".join(sorted({match.service for match in matches}))
        return (
            "Potential release context found for "
            f"{services}. Compare these release items with the normal knowledge snapshot before changing guidance."
        )

    def impact_summary(self, question: str) -> ReleaseImpactSummary:
        if not self.exists:
            return ReleaseImpactSummary(
                snapshot_path=str(self.snapshot_path),
                maturity_notes=[
                    "Release-awareness is scaffolded, but no local release snapshot is available.",
                ],
            )
        payload = self._load_payload()
        matches = self.find_matches(question)
        impact_categories = sorted({tag for match in matches for tag in match.impact_tags})
        change_categories = sorted(
            {
                str(category)
                for release in self._matched_release_dicts(question)
                for category in release.get("change_categories", [])
            }
        )
        architecture_services = sorted(
            {
                match.service
                for match in matches
                if match.impact_level in {"review", "high"}
                or any(tag in {"architecture", "migration", "dr", "security"} for tag in match.impact_tags)
            }
        )
        recommendation_services = sorted(
            {
                str(release.get("service"))
                for release in self._matched_release_dicts(question)
                if release.get("recommendation_affecting")
            }
        )
        notes = [
            "Release-awareness is snapshot-based scaffolding; it does not yet perform live automated OCI release reconciliation.",
        ]
        if not matches:
            notes.append("No matching release item was found for this prompt in the local snapshot.")
        return ReleaseImpactSummary(
            snapshot_path=str(self.snapshot_path),
            snapshot_generated_at=str(payload.get("generated_at")) if payload.get("generated_at") else None,
            matched_release_count=len(matches),
            architecture_affecting_services=architecture_services,
            impact_categories=impact_categories,
            change_categories=change_categories,
            recommendation_affecting_services=recommendation_services,
            maturity_notes=notes,
        )

    def temporal_context(self, *, knowledge_snapshot_path: Path | None = None, question: str | None = None) -> KnowledgeTemporalContext:
        historical = []
        historical_dir = self.snapshot_path.parent / "historical"
        if historical_dir.exists():
            historical = [
                str(path)
                for path in sorted(historical_dir.glob("historical-*.json"))
            ]
        payload = self._load_payload() if self.exists else {}
        requested_time_context = self._requested_time_context(question or "")
        notes = [
            "Current retrieval uses the active OCI knowledge snapshot with a release snapshot overlay.",
            "Historical snapshots are retained for audit/context; retrieval remains current-first unless the prompt explicitly asks for historical context.",
        ]
        if requested_time_context == "historical":
            notes.append("The prompt appears to request historical context; compare current guidance with retained historical snapshots before making current-state claims.")
        return KnowledgeTemporalContext(
            knowledge_mode="historical_context_requested" if requested_time_context == "historical" else "current_snapshot_with_release_overlay",
            current_knowledge_snapshot=str(knowledge_snapshot_path) if knowledge_snapshot_path else None,
            current_release_snapshot=str(self.snapshot_path) if self.exists else None,
            current_knowledge_as_of=str(payload.get("generated_at")) if payload.get("generated_at") else None,
            requested_time_context=requested_time_context,
            historical_snapshots=historical,
            historical_context_available=bool(historical),
            notes=notes,
        )

    def _load_releases(self) -> list[dict[str, object]]:
        return list(self._load_payload().get("releases", []))

    def _load_payload(self) -> dict[str, object]:
        if self._payload is not None:
            return self._payload
        with self.snapshot_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        self._payload = payload
        self._releases = list(payload.get("releases", []))
        return payload

    def _matched_release_dicts(self, question: str, limit: int = 3) -> list[dict[str, object]]:
        if not self.exists:
            return []
        match_titles = {match.title for match in self.find_matches(question, limit=limit)}
        return [release for release in self._load_releases() if str(release.get("title", "")) in match_titles]

    def _requested_time_context(self, question: str) -> str:
        normalized = question.lower()
        if any(term in normalized for term in ("historical", "previously", "last year", "old behavior", "before the release")):
            return "historical"
        if any(term in normalized for term in ("latest", "current", "now", "recent", "today")):
            return "current"
        return "current"

    def _to_match(self, release: dict[str, object]) -> ReleaseMatch:
        return ReleaseMatch(
            title=str(release.get("title", "")),
            service=str(release.get("service", "Oracle Cloud Infrastructure")),
            service_domain=str(release.get("service_domain", "general")),
            impact_tags=[str(tag) for tag in release.get("impact_tags", [])],
            impact_level=str(release.get("impact_level", "informational")),
            source_url=str(release.get("source_url")) if release.get("source_url") else None,
            release_date=str(release.get("release_date")) if release.get("release_date") else None,
            summary=str(release.get("summary", "")),
        )
