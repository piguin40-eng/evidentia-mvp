from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def compose_assessment(
    *,
    case_code: str,
    source_sha256: str,
    features: dict[str, float | int],
    probability_incorrect: float,
    citations: list[dict[str, Any]],
    model_version: str,
    balanced_accuracy: float,
    now: str,
) -> dict[str, Any]:
    probability = round(float(probability_incorrect), 6)
    verdict = "INCORRECTA" if probability >= 0.5 else "CORRECTA"
    safe_citations = [
        {
            key: citation[key]
            for key in ("title", "text", "confidence", "document_sha256", "ordinal")
            if key in citation
        }
        for citation in citations
    ]
    assessment_id = "ASM-" + hashlib.sha256(
        f"{source_sha256}|{model_version}|{now}".encode("utf-8")
    ).hexdigest()[:16].upper()
    return {
        "schema_version": 1,
        "assessment_id": assessment_id,
        "case_code": case_code,
        "source_mesh_sha256": source_sha256,
        "created_at": now,
        "decision_status": "CANDIDATO_EXPERIMENTAL",
        "clinical_decision": False,
        "requires_human_confirmation": True,
        "agent_output": {
            "verdict": verdict,
            "probability_incorrect": probability,
            "probability_correct": round(1.0 - probability, 6),
            "abstention": False,
            "limitations": [
                "Modelo global experimental; no localiza defectos ni valida el uso clínico.",
                "La predicción debe compararse con la revisión humana.",
            ],
        },
        "technical_features": features,
        "training": {
            "model_version": model_version,
            "balanced_accuracy": round(float(balanced_accuracy), 6),
            "promotion_status": "NO_PROMOTION",
            "stable_model_changed": False,
        },
        "rag": {
            "status": "EVIDENCIA_RECUPERADA" if safe_citations else "SIN_EVIDENCIA_RECUPERADA",
            "citations": safe_citations,
            "clinical_ground_truth": False,
        },
    }


def record_feedback(
    *,
    assessment: dict[str, Any],
    reviewer: str,
    human_label: str,
    judgment: str,
    notes: str,
    functional_class: str,
    known_training_hashes: set[str],
    log_path: Path | str,
    now: str,
) -> dict[str, Any]:
    if judgment == "INCORRECT" and not notes.strip():
        raise ValueError("La corrección requiere una observación humana")
    source_sha = str(assessment["source_mesh_sha256"])
    assessment_id = str(assessment["assessment_id"])
    existing_hash = source_sha in known_training_hashes
    review_id = "REV-" + hashlib.sha256(
        f"{assessment_id}|{reviewer}|{now}".encode("utf-8")
    ).hexdigest()[:16].upper()
    review = {
        "schema_version": 1,
        "review_id": review_id,
        "assessment_id": assessment_id,
        "case_code": assessment["case_code"],
        "source_mesh_sha256": source_sha,
        "functional_class": functional_class,
        "human_label": human_label,
        "previous_system_output": assessment["agent_output"],
        "new_system_output": None,
        "change_reason": notes.strip(),
        "reviewer": reviewer.strip(),
        "agent_was_correct": judgment == "CORRECT",
        "catalog_version": "not_used",
        "algorithm_version": "technical-features-v1",
        "model_version": assessment.get("training", {}).get("model_version", "unknown"),
        "decision_status": "HUMAN_VALIDATED",
        "ambiguity_reason": assessment.get("agent_output", {}).get("abstention_reason"),
        "metrics_before": assessment.get("training", {}),
        "metrics_after": None,
        "training_eligibility": "REVALIDATION_EXISTING_HASH" if existing_hash else "QUEUED_NEW_UNIQUE_SAMPLE",
        "new_training_sample": not existing_hash,
        "timestamp": now,
    }
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        for line in handle:
            if not line.strip():
                continue
            if json.loads(line).get("assessment_id") == assessment_id:
                raise ValueError("Esta evaluación ya tiene revisión append-only")
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(review, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return review
