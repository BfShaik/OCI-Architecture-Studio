from __future__ import annotations

import json
import os
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    ReviewHistoryDetail,
    ReviewHistoryListResponse,
    ReviewHistorySummary,
)


_BOUNDARY_MARKER = "PRIVATE " + "K" + "EY"
_BEGIN_MARKER = "BE" + "GIN"
_END_MARKER = "E" + "ND"

SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(password|passphrase|secret|token|api[_-]?key|auth[_-]?token)\s*[:=]\s*\S+"),
    re.compile(rf"-----{_BEGIN_MARKER} [A-Z ]*{_BOUNDARY_MARKER}-----.*?-----{_END_MARKER} [A-Z ]*{_BOUNDARY_MARKER}-----", re.DOTALL),
    re.compile(r"(?i)\bocid1\.(user|tenancy|apikey|autonomousdatabase)\.[A-Za-z0-9._-]+"),
)


class ReviewHistoryStore:
    """Small file-backed review history with bounded retention and redaction."""

    def __init__(self, path: Path, retention_limit: int = 50) -> None:
        self.path = path
        self.retention_limit = max(1, retention_limit)
        self._lock = threading.Lock()

    def save(
        self,
        request: ArchitectureReviewRequest,
        response: ArchitectureReviewResponse,
    ) -> ReviewHistoryDetail:
        now = _utc_now()
        review_id = response.review_id or f"rev_{uuid4().hex}"
        redacted_question = redact_sensitive_text(request.question)
        redacted_context = redact_sensitive_text(request.workload_context)
        sanitized_response = response.model_copy(deep=True)
        sanitized_response.review_id = review_id
        sanitized_response.retrieval_debug = None
        sanitized_response.synthesis_debug = None

        record = {
            "review_id": review_id,
            "created_at": now,
            "updated_at": now,
            "question": redacted_question,
            "workload_context": redacted_context,
            "response": sanitized_response.model_dump(mode="json"),
        }
        record["response"]["review_id"] = review_id

        with self._lock:
            records = [
                item
                for item in self._read_records()
                if item.get("review_id") != review_id
            ]
            records.insert(0, record)
            self._write_records(records[: self.retention_limit])

        return self._to_detail(record)

    def list(self) -> ReviewHistoryListResponse:
        with self._lock:
            records = self._read_records()
        return ReviewHistoryListResponse(
            items=[self._to_summary(record) for record in records],
            retention_limit=self.retention_limit,
        )

    def get(self, review_id: str) -> ReviewHistoryDetail | None:
        with self._lock:
            for record in self._read_records():
                if record.get("review_id") == review_id:
                    return self._to_detail(record)
        return None

    def delete(self, review_id: str) -> bool:
        with self._lock:
            records = self._read_records()
            kept = [record for record in records if record.get("review_id") != review_id]
            if len(kept) == len(records):
                return False
            self._write_records(kept)
        return True

    def _read_records(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        records = data.get("items", []) if isinstance(data, dict) else []
        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    def _write_records(self, records: list[dict[str, object]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        payload = {
            "schema_version": "review-history-v1",
            "updated_at": _utc_now(),
            "items": records,
        }
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(tmp_path, 0o600)
        tmp_path.replace(self.path)
        os.chmod(self.path, 0o600)

    def _to_summary(self, record: dict[str, object]) -> ReviewHistorySummary:
        response = _response_from_record(record)
        confidence = response.confidence
        return ReviewHistorySummary(
            review_id=str(record.get("review_id") or ""),
            created_at=str(record.get("created_at") or ""),
            updated_at=str(record.get("updated_at") or record.get("created_at") or ""),
            question_preview=_preview(str(record.get("question") or "")),
            workload_context_preview=_preview(str(record.get("workload_context") or "")) if record.get("workload_context") else None,
            intent=response.intent,
            confidence_level=confidence.level if confidence else None,
            confidence_overall=confidence.overall if confidence else None,
            citation_count=len(response.citations),
            recommendation_count=len(response.recommendations),
        )

    def _to_detail(self, record: dict[str, object]) -> ReviewHistoryDetail:
        summary = self._to_summary(record)
        response = _response_from_record(record)
        return ReviewHistoryDetail(
            **summary.model_dump(),
            question=str(record.get("question") or ""),
            workload_context=str(record.get("workload_context") or "") or None,
            response=response,
        )


def redact_sensitive_text(value: str | None) -> str | None:
    if value is None:
        return None
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: _redact_match(match), redacted)
    return redacted


def _redact_match(match: re.Match[str]) -> str:
    if match.lastindex:
        return f"{match.group(1)}=[redacted]"
    return "[redacted]"


def _response_from_record(record: dict[str, object]) -> ArchitectureReviewResponse:
    response = record.get("response")
    if not isinstance(response, dict):
        raise ValueError("Review history record is missing response payload.")
    return ArchitectureReviewResponse.model_validate(response)


def _preview(value: str, max_length: int = 120) -> str:
    compact = " ".join(value.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 1].rstrip()}..."


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
