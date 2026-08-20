from backend.agent_service import compose_assessment


def test_compose_assessment_exposes_candidate_prediction_rag_and_human_gate():
    assessment = compose_assessment(
        case_code="AIQ-DEMO-SYNTHETIC",
        source_sha256="f676e8436ce55b8e3b37a5391d94c954cdf0227e021ded27b90d0bec460b6b62",
        features={"faces": 209153, "boundary_edges": 955, "watertight": 0},
        probability_incorrect=0.3253324626,
        citations=[{
            "title": "Congruence between scanbody meshes",
            "text": "La congruencia geométrica requiere referencia CAD exacta.",
            "confidence": "ACADEMIC_PROVENANCE_UNVERIFIED",
            "document_sha256": "abc123",
        }],
        model_version="2026-08-16-baseline-v1",
        balanced_accuracy=0.576923,
        now="2026-08-18T23:59:00Z",
    )

    assert assessment["agent_output"]["verdict"] == "CORRECTA"
    assert assessment["agent_output"]["probability_incorrect"] == 0.325332
    assert assessment["decision_status"] == "CANDIDATO_EXPERIMENTAL"
    assert assessment["requires_human_confirmation"] is True
    assert assessment["clinical_decision"] is False
    assert assessment["training"]["balanced_accuracy"] == 0.576923
    assert assessment["rag"]["status"] == "EVIDENCIA_RECUPERADA"
    assert assessment["rag"]["citations"][0]["title"] == "Congruence between scanbody meshes"
    assert "source_uri" not in assessment["rag"]["citations"][0]


def test_record_feedback_is_append_only_and_does_not_recount_known_mesh(tmp_path):
    from backend.agent_service import record_feedback

    assessment = {
        "assessment_id": "ASM-001",
        "case_code": "AIQ-DEMO-SYNTHETIC",
        "source_mesh_sha256": "known-sha",
        "agent_output": {"verdict": "CORRECTA", "probability_incorrect": 0.325332},
        "training": {"model_version": "baseline-v1"},
    }
    log_path = tmp_path / "reviews.jsonl"
    review = record_feedback(
        assessment=assessment,
        reviewer="Revisor Técnico",
        human_label="INCORRECTA",
        judgment="INCORRECT",
        notes="Malla doble, scanbody defectuoso y muñones con arrastre.",
        functional_class="implantologia_scanbody",
        known_training_hashes={"known-sha"},
        log_path=log_path,
        now="2026-08-19T00:10:00Z",
    )

    assert review["previous_system_output"]["verdict"] == "CORRECTA"
    assert review["human_label"] == "INCORRECTA"
    assert review["agent_was_correct"] is False
    assert review["training_eligibility"] == "REVALIDATION_EXISTING_HASH"
    assert review["new_training_sample"] is False
    assert log_path.read_text(encoding="utf-8").count("\n") == 1

    try:
        record_feedback(
            assessment=assessment,
            reviewer="Revisor Técnico",
            human_label="INCORRECTA",
            judgment="INCORRECT",
            notes="Segundo intento",
            functional_class="implantologia_scanbody",
            known_training_hashes={"known-sha"},
            log_path=log_path,
            now="2026-08-19T00:11:00Z",
        )
    except ValueError as exc:
        assert "ya tiene revisión" in str(exc)
    else:
        raise AssertionError("La misma evaluación no puede revisarse dos veces")
