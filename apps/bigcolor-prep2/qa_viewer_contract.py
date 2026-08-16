from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_RULES = ROOT / "material_rules" / "material_rules_2026-08-16.json"
DEFAULT_TABLE = ROOT / "outputs" / "piguin-row-schema-contract-2026-08-16" / "table.csv"
DEFAULT_LEGACY_ACTION_BAND_TABLE = (
    ROOT / "outputs" / "piguin-legacy-action-band-csv-fixture-2026-08-15" / "table.csv"
)

REQUIRED_VIEWER_TOKENS = [
    "MATERIAL_RULES_URL = \"./material_rules/material_rules_2026-08-16.json\"",
    "<th>Diente</th><th>Zona</th><th>P50</th><th>Def.</th><th>Decision</th><th>Trazabilidad</th>",
    "row[\"Decision PREP\"]",
    "row[\"Deficit vs objetivo (mm)\"]",
    "BigColor PREP demo 0.5 mm",
    "Object.keys(lastRows[0])",
    "Alcance:",
    "Mapeo:",
    "trace-secondary",
    "trace-pending",
    "Causa: candidato sin IFU primaria",
    "Causa: falta fuente IFU/ficha tecnica",
    "Empress CAD: fuente primaria encontrada; espesor numerico pendiente de IFU.",
    "AMT: producto/fabricante no identificado; no hay regla de tallado.",
    "id=\"qaGateBox\"",
    "id=\"analysisStateBox\"",
    "Estado de analisis",
    "Puerta QA:",
    "Uso clinico",
    "Perfil",
    "Distancia:",
    "Rayos:",
    "Muestras:",
    "Profundidad rayo:",
    "Cobertura:",
    "blocked_for_clinical_use",
    "can_use_for_clinical_decision",
    "id=\"landmarksFile\"",
    "Landmarks JSON opcional",
    "form.append(\"landmarks\"",
    "id=\"inputUnit\"",
    "form.append(\"input_unit\"",
    "id=\"measurementMethod\"",
    "form.append(\"measurement_method\"",
    "id=\"rayDirection\"",
    "form.append(\"ray_direction\"",
    "normal_ray",
    "Unidad STL:",
    "unitSummaryLabel(unit)",
    "viewer_material_readiness_matrix_2026_07_21",
    "viewer_required_thickness_matrix_2026_07_25",
    "viewer_row_decision_resolver_2026_07_26",
    "viewer_material_zone_readout_contract_2026_07_27",
    "viewer_row_rag_action_contract_2026_07_28",
    "viewer_codable_material_zone_requirements_2026_07_29",
    "viewer_source_handoff_2026_07_30",
    "viewer_material_decision_gate_2026_07_31",
    "viewer_visible_row_output_contract_2026_08_01",
    "viewer_technical_action_thresholds_2026_08_02",
    "viewer_row_resolution_fixture_2026_08_03",
    "viewer_primary_source_lock_matrix_2026_08_04",
    "viewer_row_source_trace_contract_2026_08_05",
    "viewer_row_technical_sentence_contract_2026_08_06",
    "viewer_material_zone_requirement_row_contract_2026_08_07",
    "viewer_strict_material_zone_join_contract_2026_08_08",
    "viewer_missing_material_zone_rule_fixture_2026_08_09",
    "MATERIAL_ZONE_REQUIREMENT_ROW_CONTRACT_KEY",
    "MISSING_MATERIAL_ZONE_RULE_FIXTURE_KEY",
    "MATERIAL_ZONE_ROW_SCHEMA_CONTRACT_KEY",
    "viewer_material_zone_row_schema_contract_2026_08_16",
    "PRIMARY_SOURCE_LOCK_MATRIX_KEY",
    "allow_rag_with_visible_caveat",
    "force_gray_until_source_verified",
    "force_gray_candidate_for_internal_qa_only",
    "materialSourceHandoffContract?.viewer_sentence_template_es",
    "MATERIAL_ZONE_READOUT_CONTRACT_KEY",
    "MATERIAL_RAG_ACTION_CONTRACT_KEY",
    "primary_viewer_sentence_template_es",
    "deficit_display",
    "action_band_key",
    "canonicalActionBandKey",
    "Legacy_action_band_key",
    "decision_gate",
    "color_key",
    "technical_action_es",
    "color_label_es",
    "zone_label_crosswalk",
    "Readiness:",
    "activo con caveat legacy",
    "bloqueado por IFU",
]

REQUIRED_ANALYSIS_STATE_TOKENS = [
    "function renderAnalysisState(analysis = null, rows = [])",
    "analysisStateBox.innerHTML",
    "Estado de analisis",
    "<strong>Material</strong>",
    "<strong>Perfil</strong>",
    "<strong>QA gate</strong>",
    "<strong>Uso clinico</strong>",
    "<strong>Registro</strong>",
    "<strong>Distancia</strong>",
    "<strong>Unidad STL</strong>",
    "<strong>Filas</strong>",
    "Bloqueo prudente: no usar como medicion clinica validada. Motivo:",
    "qaGate?.can_use_for_clinical_decision === true",
    "analysisStateBox.classList.toggle(\"qa-gate-blocked\", !clinical)",
    "analysisStateBox.classList.toggle(\"qa-gate-pass\", clinical)",
    "renderAnalysisState(analysis, rows)",
]

REQUIRED_CSV_COLUMNS = [
    "Estado evidencia",
    "Source scope",
    "Zone mapping status",
    "Distance method",
    "Distance confidence",
    "Distance sample count requested",
    "Distance sample count used",
    "Distance ray max depth mm",
    "Distance ray direction",
    "QA gate status",
    "Clinical use allowed",
    "Action key",
    "Viewer readiness",
    "Viewer color permission",
    "Viewer readiness caveat",
    "Required display",
    "Source scope for viewer",
    "Material-zone join status",
    "Row viewer color permission",
    "Row action rule",
    "Truth partition",
    "Selector label",
    "Selector badge status",
    "Blocking/caveat summary",
    "Accion tecnica",
    "Frase visible",
    "Caveat",
    "Objetivo PREP (mm)",
    "Deficit vs objetivo (mm)",
    "Decision gate",
    "Action band key",
    "Color key",
    "Deficit mm",
    "Deficit display ES",
    "Source trace status ES",
    "Source trace token",
    "Color permission display ES",
    "Technical action ES",
    "Viewer sentence ES",
    "Viewer short action ES",
    "Viewer required summary ES",
    "Viewer source summary ES",
    "Decision PREP",
]

OPTIONAL_WHEN_PENDING_SOURCE = {
    "Objetivo PREP (mm)",
    "Deficit vs objetivo (mm)",
}

OPTIONAL_UNTIL_MATERIAL_COMPARISON_ALLOWED = {
    "Deficit vs objetivo (mm)",
    "Deficit mm",
}

REQUIRED_EXAMPLE_FIELDS = [
    "profile_key",
    "zone_key",
    "measured_mm",
    "required_min_mm",
    "source_scope",
    "zone_mapping_status",
    "action_key",
    "caveat",
]


def _fail(message: str) -> None:
    raise SystemExit(f"QA_VIEWER_CONTRACT_FAIL: {message}")


def _required_display_es(required_min_mm: object, evidence_status: str, source_scope: str) -> str:
    if required_min_mm is None:
        if source_scope == "unresolved_material_identifier":
            return "pendiente de identificacion"
        if evidence_status == "pending_source":
            return "pendiente de fuente"
        return "pendiente"
    return f">= {float(required_min_mm):.2f} mm"


def _blocked_pending_action(source_scope: str) -> tuple[str, str, str]:
    if source_scope == "unresolved_material_identifier":
        return (
            "blocked_unresolved_material_identifier",
            "blocked_unresolved_material",
            "No definir tallado para AMT hasta identificar fabricante, producto, familia, via de fabricacion e IFU/ficha tecnica.",
        )
    return (
        "blocked_pending_source_or_required_null",
        "blocked_pending_source",
        "No usar como decision de tallado. Falta IFU/ficha tecnica primaria con espesor por restauracion/zona.",
    )


def _action_for_band(band_key: str) -> str:
    actions = {
        "missing_space_major": "Falta espacio de forma clara para el material/zona. Replantear wax-up, reduccion planificada o indicacion/material antes de aceptar.",
        "missing_space_minor": "Falta espacio medible. Revisar si la reduccion localizada puede compensar el deficit y confirmar IFU/caso antes de liberar.",
        "borderline_acceptance_margin": "Zona limite. Confirmar fuente, adhesion/cementacion, sustrato, carga oclusal y confianza del registro antes de aceptar.",
        "meets_requirement": "Espacio compatible con la regla seleccionada. Mantener caveat de fuente y validacion del caso visible.",
        "excess_space": "Sobre-espacio o reduccion excesiva frente al limite del perfil. Revisar soporte, diseno, cemento y compensacion.",
    }
    return actions[band_key]


def _canonical_action_band_key(legacy_band_key: str, decision_gate: str, source_trace_token: str) -> str:
    if legacy_band_key == "blocked_before_material_action":
        if source_trace_token == "blocked_missing_material_zone_rule":
            return "missing_material_zone_rule"
        if decision_gate in {"secondary_candidate", "source_pending_or_unidentified"} or source_trace_token in {
            "blocked_secondary_candidate",
            "blocked_pending_primary_source",
            "blocked_unidentified_material",
        }:
            return "source_pending_or_secondary_no_rag"
        return "qa_blocked_no_clinical_delta"
    return {
        "missing_space_major": "below_required_minimum_prepare_more_or_replan",
        "missing_space_minor": "below_required_minimum_prepare_more_or_replan",
        "borderline_acceptance_margin": "borderline_confirm_before_accepting",
        "meets_requirement": "compatible_with_selected_rule",
        "excess_space": "above_upper_limit_or_excess_space",
    }.get(legacy_band_key, legacy_band_key)


def _source_lock_for_row(row: dict[str, object], rules: dict[str, object]) -> dict[str, object]:
    profile_key = row.get("profile_key")
    matrix = rules.get("viewer_primary_source_lock_matrix_2026_08_04") or {}
    for lock in matrix.get("source_locks") or []:
        if profile_key and lock.get("profile_key") == profile_key:
            return lock
    return {}


def resolver_viewer_row(row: dict[str, object], rules: dict[str, object]) -> dict[str, object]:
    measured = float(row["measured_mm"])
    required_min = row.get("required_min_mm")
    required_ideal = row.get("required_ideal_mm")
    upper_limit = row.get("upper_limit_mm")
    evidence = str(row.get("evidence_status") or "")
    source_scope = str(row.get("source_scope_for_viewer") or "")
    zone_mapping_status = str(row.get("zone_mapping_status") or "")
    caveat = str(row.get("caveat_es") or "")
    source_lock = _source_lock_for_row(row, rules)
    color_permission = str(source_lock.get("color_permission") or row.get("viewer_color_permission") or "")
    if source_lock.get("caveat_es"):
        caveat = str(source_lock["caveat_es"])

    required_display = _required_display_es(required_min, evidence, source_scope)
    force_gray = color_permission.startswith("force_gray")
    if evidence == "secondary_unconfirmed" or color_permission == "force_gray_candidate_for_internal_qa_only":
        technical_action = "Mostrar como candidato gris: posible valor secundario, pendiente de IFU primaria antes de generar deficit clinico."
        return {
            "decision_gate": "secondary_candidate",
            "required_display_es": required_display,
            "deficit_mm": None,
            "deficit_display_es": "sin deficit clinico calculable",
            "action_band_key": "blocked_before_material_action",
            "color_key": "gray",
            "technical_action_es": technical_action,
            "source_scope_for_viewer": source_scope,
            "zone_mapping_status": zone_mapping_status,
            "caveat_es": caveat,
            "viewer_sentence_es": (
                f"Diente {row.get('tooth_fdi')}, zona {row.get('zone_label_es')}: "
                f"medido {measured:.2f} mm; requerido {required_display}; "
                "deficit sin deficit clinico calculable; color gray; "
                f"accion tecnica {technical_action}; fuente {source_scope}; caveat {caveat}."
            ),
        }
    if evidence == "pending_source" or required_min is None or force_gray:
        decision_gate, action_band_key, technical_action = _blocked_pending_action(source_scope)
        return {
            "decision_gate": decision_gate,
            "required_display_es": required_display,
            "deficit_mm": None,
            "deficit_display_es": "sin deficit clinico calculable",
            "action_band_key": action_band_key,
            "color_key": "gray",
            "technical_action_es": technical_action,
            "source_scope_for_viewer": source_scope,
            "zone_mapping_status": zone_mapping_status,
            "caveat_es": caveat,
            "viewer_sentence_es": (
                f"Diente {row.get('tooth_fdi')}, zona {row.get('zone_label_es')}: "
                f"medido {measured:.2f} mm; requerido {required_display}; "
                "deficit sin deficit clinico calculable; color gray; "
                f"accion tecnica {technical_action}; fuente {source_scope}; caveat {caveat}."
            ),
        }

    required_min_f = float(required_min)
    deficit = round(max(required_min_f - measured, 0.0), 2)
    if upper_limit is not None and measured > float(upper_limit):
        action_band_key = "excess_space"
        deficit_display = f"{measured - float(upper_limit):.2f} mm exceso"
        color_key = "purple"
    elif deficit > 0.20:
        action_band_key = "missing_space_major"
        deficit_display = f"falta {deficit:.2f} mm"
        color_key = "red"
    elif deficit > 0.05:
        action_band_key = "missing_space_minor"
        deficit_display = f"falta {deficit:.2f} mm"
        color_key = "red"
    elif deficit > 0:
        action_band_key = "borderline_acceptance_margin"
        deficit_display = f"limite {deficit:.2f} mm"
        color_key = "yellow"
    elif required_ideal is not None and measured < float(required_ideal):
        action_band_key = "borderline_acceptance_margin"
        deficit_display = "0.00 mm"
        color_key = "yellow"
    else:
        action_band_key = "meets_requirement"
        deficit_display = "0.00 mm"
        color_key = "green"

    technical_action = _action_for_band(action_band_key)
    return {
        "decision_gate": "material_comparison_allowed",
        "required_display_es": required_display,
        "deficit_mm": deficit,
        "deficit_display_es": deficit_display,
        "action_band_key": action_band_key,
        "color_key": color_key,
        "technical_action_es": technical_action,
        "source_scope_for_viewer": source_scope,
        "zone_mapping_status": zone_mapping_status,
        "caveat_es": caveat,
        "viewer_sentence_es": (
            f"Diente {row.get('tooth_fdi')}, zona {row.get('zone_label_es')}: "
            f"medido {measured:.2f} mm; requerido {required_display}; "
            f"deficit {deficit_display}; color {color_key}; accion tecnica {technical_action}; "
            f"fuente {source_scope}; caveat {caveat}."
        ),
    }


def check_viewer_html(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [token for token in REQUIRED_VIEWER_TOKENS if token not in text]
    if missing:
        _fail(f"{path.name} no expone contrato visible/exportable: {missing}")
    missing_analysis_state = [token for token in REQUIRED_ANALYSIS_STATE_TOKENS if token not in text]
    if missing_analysis_state:
        _fail(f"{path.name} no fija el panel Estado de analisis: {missing_analysis_state}")

    rules_match = re.search(r'MATERIAL_RULES_URL = "\./material_rules/([^"]+)"', text)
    if not rules_match:
        _fail("No se pudo resolver MATERIAL_RULES_URL en el visor")
    active_rules = ROOT / "material_rules" / rules_match.group(1)
    if not active_rules.exists():
        _fail(f"El visor apunta a reglas inexistentes: {active_rules}")


def check_table_csv(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            _fail(f"{path} no tiene cabecera CSV")
        missing = [column for column in REQUIRED_CSV_COLUMNS if column not in reader.fieldnames]
        if missing:
            _fail(f"{path.name} no exporta columnas obligatorias: {missing}")
        rows = list(reader)

    if not rows:
        _fail(f"{path.name} no contiene filas")

    all_pending_source = all((row.get("Estado evidencia") or "").strip() == "pending_source" for row in rows)
    has_material_comparison = any(
        (row.get("Decision gate") or "").strip()
        in {"verified_or_primary_archived_can_compare", "demo_only"}
        for row in rows
    )
    for column in REQUIRED_CSV_COLUMNS:
        if all_pending_source and column in OPTIONAL_WHEN_PENDING_SOURCE:
            continue
        if not has_material_comparison and column in OPTIONAL_UNTIL_MATERIAL_COMPARISON_ALLOWED:
            continue
        if not any((row.get(column) or "").strip() for row in rows):
            _fail(f"{path.name} tiene la columna {column} vacia en todas las filas")

    for row_number, row in enumerate(rows, start=2):
        gate = (row.get("Decision gate") or "").strip()
        color = (row.get("Color key") or "").strip()
        source_token = (row.get("Source trace token") or "").strip()
        join_status = (row.get("Material-zone join status") or "").strip()
        exposed_deficit = (row.get("Deficit vs objetivo (mm)") or "").strip()
        viewer_deficit = (row.get("Deficit mm") or "").strip()
        viewer_sentence = (row.get("Viewer sentence ES") or "").strip()
        comparison_allowed = gate in {"verified_or_primary_archived_can_compare", "demo_only"}
        if not join_status:
            _fail(f"Fila {row_number}: falta Material-zone join status")
        required_sentence_tokens = [
            "Diente ",
            ", zona ",
            ": medido ",
            "; requerido ",
            "; material ",
            "; color ",
            "; accion tecnica ",
            "; caveat ",
        ]
        if not all(token in viewer_sentence for token in required_sentence_tokens):
            _fail(f"Fila {row_number}: Viewer sentence ES no cumple contrato 2026-08-16")
        if not comparison_allowed and color != "gray":
            _fail(f"Fila {row_number}: gate {gate} no puede colorear {color}")
        if join_status != "exact_material_profile_zone" and color != "gray":
            _fail(f"Fila {row_number}: regla material-zona no exacta no puede colorear {color}")
        if source_token.startswith("blocked_") and (exposed_deficit or viewer_deficit):
            _fail(f"Fila {row_number}: source_trace bloqueado no puede exponer deficit clinico")
        if not comparison_allowed and (exposed_deficit or viewer_deficit):
            _fail(f"Fila {row_number}: gate {gate} no puede exponer deficit clinico")
        if not comparison_allowed and "deficit" in viewer_sentence.lower():
            _fail(f"Fila {row_number}: frase bloqueada no debe vender deficit clinico")


def check_rules_examples(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    dated_example_keys = sorted(key for key in data if key.startswith("viewer_row_examples_"))
    examples_key = dated_example_keys[-1] if dated_example_keys else "viewer_row_examples"
    examples = data.get(examples_key) or []
    if len(examples) < 3:
        _fail(f"Faltan al menos 3 ejemplos en {examples_key} para validar comportamiento del visor")

    for index, example in enumerate(examples, start=1):
        missing = [field for field in REQUIRED_EXAMPLE_FIELDS if field not in example]
        if missing:
            _fail(f"Ejemplo #{index} incompleto: {missing}")


def check_row_resolution_fixture(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixture = data.get("viewer_row_resolution_fixture_2026_08_03") or {}
    rows = fixture.get("fixture_rows") or []
    if len(rows) < 5:
        _fail("viewer_row_resolution_fixture_2026_08_03 debe traer al menos 5 filas")

    for fixture_row in rows:
        fixture_id = fixture_row.get("fixture_id", "sin_id")
        resolved = resolver_viewer_row(fixture_row.get("input") or {}, data)
        expected = fixture_row.get("expected_output") or {}
        for field, expected_value in expected.items():
            actual_value = resolved.get(field)
            if actual_value != expected_value:
                _fail(
                    "Fixture "
                    f"{fixture_id} no coincide en {field}: esperado={expected_value!r} actual={actual_value!r}"
                )
        for field in fixture.get("required_output_fields") or []:
            if field not in resolved:
                _fail(f"Fixture {fixture_id} no exporta campo requerido {field}")


def check_primary_source_lock_matrix(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    matrix = data.get("viewer_primary_source_lock_matrix_2026_08_04") or {}
    source_locks = matrix.get("source_locks") or []
    if len(source_locks) < 7:
        _fail("viewer_primary_source_lock_matrix_2026_08_04 debe traer al menos 7 source_locks")

    permissions = {lock.get("color_permission") for lock in source_locks}
    required_permissions = {
        "allow_rag_with_visible_caveat",
        "force_gray_until_source_verified",
        "force_gray_candidate_for_internal_qa_only",
        "force_gray_until_product_and_ifu_identified",
    }
    missing = sorted(required_permissions - permissions)
    if missing:
        _fail(f"Faltan permisos de color en source_lock_matrix: {missing}")

    required_lock_fields = [
        "material_key",
        "profile_key",
        "restoration_type",
        "evidence_status",
        "verified_requirement_scope",
        "required_min_mm_source_state",
        "color_permission",
        "required_display_when_selected_es",
        "technical_action_template_es",
        "caveat_es",
    ]
    for lock in source_locks:
        for field in required_lock_fields:
            if field not in lock:
                _fail(f"source_lock incompleto {lock.get('profile_key')}: falta {field}")
        permission = lock.get("color_permission")
        if str(permission).startswith("force_gray") and lock.get("evidence_status") == "verified":
            _fail(f"source_lock bloqueado no debe marcarse verified: {lock.get('profile_key')}")


def check_row_source_trace_contract(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = data.get("viewer_row_source_trace_contract_2026_08_05") or {}
    trace_rules = contract.get("trace_rules") or []
    row_examples = contract.get("row_examples") or []
    if len(trace_rules) < 4:
        _fail("viewer_row_source_trace_contract_2026_08_05 debe traer al menos 4 trace_rules")
    if len(row_examples) < 3:
        _fail("viewer_row_source_trace_contract_2026_08_05 debe traer al menos 3 row_examples")

    required_output_fields = {
        "source_trace_status_es",
        "source_trace_token",
        "required_display_es",
        "deficit_display_es",
        "color_permission_display_es",
        "viewer_sentence_es",
    }
    missing_output = sorted(required_output_fields - set(contract.get("output_fields") or []))
    if missing_output:
        _fail(f"Faltan campos output de trazabilidad: {missing_output}")

    seen_tokens = {
        (example.get("expected_trace") or {}).get("source_trace_token")
        for example in row_examples
    }
    required_tokens = {
        "rag_allowed_visible_caveat",
        "blocked_pending_primary_source",
        "blocked_unidentified_material",
    }
    missing_tokens = sorted(required_tokens - seen_tokens)
    if missing_tokens:
        _fail(f"Faltan ejemplos source_trace_token: {missing_tokens}")

    for example in row_examples:
        expected = example.get("expected_trace") or {}
        token = expected.get("source_trace_token", "")
        color = (example.get("input") or {}).get("color_key")
        if str(token).startswith("blocked_") and color != "gray":
            _fail(f"Ejemplo bloqueado debe ser gris: {token}")


def check_row_technical_sentence_contract(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = data.get("viewer_row_technical_sentence_contract_2026_08_06") or {}
    templates = contract.get("sentence_templates") or []
    row_examples = contract.get("row_examples") or []
    if len(templates) < 4:
        _fail("viewer_row_technical_sentence_contract_2026_08_06 debe traer al menos 4 sentence_templates")
    if len(row_examples) < 3:
        _fail("viewer_row_technical_sentence_contract_2026_08_06 debe traer al menos 3 row_examples")

    required_output_fields = {
        "viewer_sentence_es",
        "viewer_short_action_es",
        "viewer_required_summary_es",
        "viewer_source_summary_es",
    }
    missing_output = sorted(required_output_fields - set(contract.get("output_fields") or []))
    if missing_output:
        _fail(f"Faltan campos output de frase tecnica: {missing_output}")

    tokens = {template.get("source_trace_token") for template in templates}
    required_tokens = {
        "rag_allowed_visible_caveat",
        "blocked_pending_primary_source",
        "blocked_secondary_candidate",
        "blocked_unidentified_material",
    }
    missing_tokens = sorted(required_tokens - tokens)
    if missing_tokens:
        _fail(f"Faltan templates de frase tecnica para tokens: {missing_tokens}")

    for example in row_examples:
        expected = str(example.get("expected_viewer_sentence_es") or "")
        if not expected.startswith("Diente ") or "Accion:" not in expected:
            _fail(f"Ejemplo de frase tecnica incompleto: {example.get('case_id')}")


def check_material_zone_requirement_row_contract(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = data.get("viewer_material_zone_requirement_row_contract_2026_08_07") or {}
    row_examples = contract.get("row_examples") or []
    if len(row_examples) < 3:
        _fail("viewer_material_zone_requirement_row_contract_2026_08_07 debe traer al menos 3 row_examples")

    required_input_fields = {
        "tooth_fdi",
        "zone_key",
        "zone_label_es",
        "measured_mm",
        "material_key",
        "profile_key",
        "source_trace_token",
        "required_min_mm",
    }
    missing_input = sorted(required_input_fields - set(contract.get("required_input_fields") or []))
    if missing_input:
        _fail(f"Faltan campos input de contrato material-zona: {missing_input}")

    required_output_fields = {
        "tooth_fdi",
        "zone_label_es",
        "measured_mm_display_es",
        "required_display_es",
        "color_key",
        "technical_action_es",
        "viewer_sentence_es",
        "source_trace_token",
    }
    missing_output = sorted(required_output_fields - set(contract.get("required_output_fields") or []))
    if missing_output:
        _fail(f"Faltan campos output de contrato material-zona: {missing_output}")

    steps = [entry.get("step") for entry in contract.get("decision_precedence") or []]
    if steps != sorted(steps) or steps != [1, 2, 3]:
        _fail("decision_precedence debe definir pasos 1, 2 y 3 en orden")

    for example in row_examples:
        expected = str(example.get("expected_viewer_sentence_es") or "")
        if not expected.startswith("Diente ") or "Accion:" not in expected:
            _fail(f"Ejemplo material-zona incompleto: {example.get('case_id')}")
        token = str(example.get("source_trace_token") or "")
        if token.startswith("blocked_") and example.get("expected_color_key") != "gray":
            _fail(f"Ejemplo bloqueado debe quedar gris: {example.get('case_id')}")
        if token == "rag_allowed_visible_caveat" and example.get("required_min_mm") is None:
            _fail(f"Ejemplo RAG permitido debe tener required_min_mm numerico: {example.get('case_id')}")


def check_strict_material_zone_join_contract(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = data.get("viewer_strict_material_zone_join_contract_2026_08_08") or {}
    row_examples = contract.get("row_examples") or []
    if len(row_examples) < 3:
        _fail("viewer_strict_material_zone_join_contract_2026_08_08 debe traer al menos 3 row_examples")

    join_keys = contract.get("strict_join_keys") or []
    if join_keys != ["material_key", "profile_key", "zone_key"]:
        _fail("strict_join_keys debe ser material_key + profile_key + zone_key")

    fallback = contract.get("fallback_for_missing_join") or {}
    if fallback.get("color_key") != "gray" or fallback.get("required_min_mm") is not None:
        _fail("fallback de join ausente debe bloquear gris y no exponer required_min_mm")
    if fallback.get("source_trace_token") != "blocked_missing_material_zone_rule":
        _fail("fallback de join ausente debe usar blocked_missing_material_zone_rule")

    seen_statuses = {
        (example.get("expected_join") or {}).get("material_zone_join_status")
        for example in row_examples
    }
    required_statuses = {"exact_material_profile_zone", "missing_material_profile_zone_matrix_row"}
    missing_statuses = sorted(required_statuses - seen_statuses)
    if missing_statuses:
        _fail(f"Faltan ejemplos de join estricto: {missing_statuses}")


def check_missing_material_zone_rule_fixture(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixture = data.get("viewer_missing_material_zone_rule_fixture_2026_08_09") or {}
    rows = fixture.get("fixture_rows") or []
    if len(rows) < 3:
        _fail("viewer_missing_material_zone_rule_fixture_2026_08_09 debe traer al menos 3 filas")

    required_expected_fields = {
        "material_zone_join_status",
        "required_min_mm",
        "required_display_es",
        "deficit_mm",
        "deficit_display_es",
        "color_key",
        "source_trace_token",
        "technical_action_es",
        "caveat_es",
    }
    missing_expected = sorted(required_expected_fields - set(fixture.get("expected_output_fields_when_blocked") or []))
    if missing_expected:
        _fail(f"Faltan campos esperados en fixture de regla ausente: {missing_expected}")

    for row in rows:
        fixture_id = row.get("fixture_id", "sin_id")
        expected = row.get("expected_output") or {}
        if expected.get("material_zone_join_status") != "missing_material_profile_zone_matrix_row":
            _fail(f"Fixture {fixture_id}: debe bloquear por missing_material_profile_zone_matrix_row")
        if expected.get("required_min_mm") is not None or expected.get("deficit_mm") is not None:
            _fail(f"Fixture {fixture_id}: no debe exponer requerido numerico ni deficit")
        if expected.get("color_key") != "gray":
            _fail(f"Fixture {fixture_id}: color esperado debe ser gray")
        if expected.get("source_trace_token") != "blocked_missing_material_zone_rule":
            _fail(f"Fixture {fixture_id}: source_trace_token esperado debe ser blocked_missing_material_zone_rule")
        if "No " not in str(expected.get("technical_action_es") or ""):
            _fail(f"Fixture {fixture_id}: accion tecnica debe bloquear el uso/fallback")


def check_technical_action_band_contract(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = data.get("viewer_technical_action_band_contract_2026_08_14") or {}
    bands = contract.get("band_resolution_order") or []
    if len(bands) != 7:
        _fail("viewer_technical_action_band_contract_2026_08_14 debe definir 7 bandas")

    expected_order = [
        "qa_blocked_no_clinical_delta",
        "missing_material_zone_rule",
        "source_pending_or_secondary_no_rag",
        "below_required_minimum_prepare_more_or_replan",
        "borderline_confirm_before_accepting",
        "compatible_with_selected_rule",
        "above_upper_limit_or_excess_space",
    ]
    actual_order = [band.get("band_key") for band in bands]
    if actual_order != expected_order:
        _fail(f"Orden de bandas tecnicas inesperado: {actual_order}")

    expected_colors = {
        "qa_blocked_no_clinical_delta": "gray",
        "missing_material_zone_rule": "gray",
        "source_pending_or_secondary_no_rag": "gray",
        "below_required_minimum_prepare_more_or_replan": "red",
        "borderline_confirm_before_accepting": "yellow",
        "compatible_with_selected_rule": "green",
        "above_upper_limit_or_excess_space": "purple",
    }
    for band in bands:
        band_key = str(band.get("band_key") or "")
        if band.get("order") != expected_order.index(band_key) + 1:
            _fail(f"Banda {band_key}: order no coincide con precedencia")
        if band.get("color_key") != expected_colors[band_key]:
            _fail(f"Banda {band_key}: color_key inesperado")
        if not band.get("technical_action_template_es"):
            _fail(f"Banda {band_key}: falta technical_action_template_es")

    blocked_bands = bands[:3]
    for band in blocked_bands:
        band_key = band.get("band_key")
        if band.get("color_key") != "gray":
            _fail(f"Banda bloqueada {band_key}: debe ser gray")
        deficit_text = str(band.get("deficit_display_es") or "")
        if "calculable" not in deficit_text:
            _fail(f"Banda bloqueada {band_key}: debe impedir deficit clinico calculable")

    rag_bands = bands[3:]
    for band in rag_bands:
        condition = str(band.get("condition") or "")
        if "QA usable" not in condition or "source allowed" not in condition:
            _fail(f"Banda RAG {band.get('band_key')}: debe exigir QA usable y fuente permitida")

    required_export = set(contract.get("required_viewer_export_fields") or [])
    required_fields = {
        "tooth_fdi",
        "zone_key",
        "measured_mm",
        "required_min_mm",
        "required_display_es",
        "deficit_mm",
        "deficit_display_es",
        "action_band_key",
        "color_key",
        "technical_action_es",
        "source_summary_es",
        "caveat_es",
    }
    missing = sorted(required_fields - required_export)
    if missing:
        _fail(f"Contrato de bandas no exige campos exportables: {missing}")

    alias_cases = {
        ("blocked_before_material_action", "geometry_or_registration_blocked", "blocked_trace_not_resolved"): "qa_blocked_no_clinical_delta",
        ("blocked_before_material_action", "source_pending_or_unidentified", "blocked_pending_primary_source"): "source_pending_or_secondary_no_rag",
        ("blocked_before_material_action", "material_zone_rule_missing", "blocked_missing_material_zone_rule"): "missing_material_zone_rule",
        ("missing_space_major", "verified_or_primary_archived_can_compare", "rag_allowed_visible_caveat"): "below_required_minimum_prepare_more_or_replan",
        ("missing_space_minor", "verified_or_primary_archived_can_compare", "rag_allowed_visible_caveat"): "below_required_minimum_prepare_more_or_replan",
        ("borderline_acceptance_margin", "verified_or_primary_archived_can_compare", "rag_allowed_visible_caveat"): "borderline_confirm_before_accepting",
        ("meets_requirement", "verified_or_primary_archived_can_compare", "rag_allowed_visible_caveat"): "compatible_with_selected_rule",
        ("excess_space", "verified_or_primary_archived_can_compare", "rag_allowed_visible_caveat"): "above_upper_limit_or_excess_space",
    }
    for case, expected in alias_cases.items():
        actual = _canonical_action_band_key(*case)
        if actual != expected:
            _fail(f"Alias de banda historica inesperado para {case}: {actual}")


def check_legacy_action_band_csv_compat(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            _fail(f"{path} no tiene cabecera CSV historica")
        if "Action band key" not in reader.fieldnames:
            _fail(f"{path.name} debe traer Action band key historico")
        if "Legacy action band key" in reader.fieldnames:
            _fail(f"{path.name} debe simular export historico sin Legacy action band key")
        rows = list(reader)

    if len(rows) < 8:
        _fail(f"{path.name} debe cubrir bloqueos y bandas RAG legacy")

    for row_number, row in enumerate(rows, start=2):
        legacy_band_key = (row.get("Action band key") or "").strip()
        decision_gate = (row.get("Decision gate") or "").strip()
        source_trace_token = (row.get("Source trace token") or "").strip()
        color_key = (row.get("Color key") or "").strip()
        expected = (row.get("Expected canonical action band key") or "").strip()
        deficit = (row.get("Deficit mm") or "").strip()
        if not legacy_band_key:
            _fail(f"Fila legacy {row_number}: falta Action band key")

        canonical = _canonical_action_band_key(legacy_band_key, decision_gate, source_trace_token)
        if canonical != expected:
            _fail(
                f"Fila legacy {row_number}: canonico inesperado para {legacy_band_key}: "
                f"esperado={expected!r} actual={canonical!r}"
            )
        if legacy_band_key != (row.get("Expected legacy action band key") or "").strip():
            _fail(f"Fila legacy {row_number}: el alias legacy no queda preservado")
        if canonical in {
            "qa_blocked_no_clinical_delta",
            "missing_material_zone_rule",
            "source_pending_or_secondary_no_rag",
        }:
            if color_key != "gray":
                _fail(f"Fila legacy {row_number}: banda bloqueada no puede colorear {color_key}")
            if deficit:
                _fail(f"Fila legacy {row_number}: banda bloqueada no puede exponer deficit clinico")


def main() -> None:
    parser = argparse.ArgumentParser(description="QA contract for BigColor PREP 2 viewer traceability fields.")
    parser.add_argument("--html", default=ROOT / "BigColor_PREP_2_APP.html", type=Path)
    parser.add_argument("--rules", default=DEFAULT_RULES, type=Path)
    parser.add_argument("--table", default=DEFAULT_TABLE, type=Path)
    parser.add_argument("--legacy-action-band-table", default=DEFAULT_LEGACY_ACTION_BAND_TABLE, type=Path)
    args = parser.parse_args()

    check_viewer_html(args.html)
    check_rules_examples(args.rules)
    check_row_resolution_fixture(args.rules)
    check_primary_source_lock_matrix(args.rules)
    check_row_source_trace_contract(args.rules)
    check_row_technical_sentence_contract(args.rules)
    check_material_zone_requirement_row_contract(args.rules)
    check_strict_material_zone_join_contract(args.rules)
    check_missing_material_zone_rule_fixture(args.rules)
    check_technical_action_band_contract(args.rules)
    check_legacy_action_band_csv_compat(args.legacy_action_band_table)
    check_table_csv(args.table)
    print("QA_VIEWER_CONTRACT_OK")
    print(f"html={args.html}")
    print(f"rules={args.rules}")
    print(f"table={args.table}")


if __name__ == "__main__":
    main()
