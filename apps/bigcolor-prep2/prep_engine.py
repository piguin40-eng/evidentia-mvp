from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import trimesh


ROOT_DIR = Path(__file__).resolve().parent
MATERIAL_RULES_PATH = ROOT_DIR / "material_rules" / "material_rules_2026-08-16.json"
PRIMARY_SOURCE_LOCK_MATRIX_KEY = "viewer_primary_source_lock_matrix_2026_08_04"
LEGACY_ZONES = ("Cervical", "Medio", "Incisal")
PREP_TARGET_THICKNESS_MM = 0.5
DEFAULT_EXACT_SURFACE_VERTEX_LIMIT = 50_000
DEFAULT_RAY_SAMPLE_COUNT = 5_000
DEFAULT_RAY_MAX_DEPTH_MM = 8.0
NORMAL_RAY_DIRECTIONS = ("bidirectional", "plus_normal", "minus_normal")
DEFAULT_LOCAL_REGISTRATION_SAMPLE_LIMIT = 1000
UNIT_SCALE_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
    "micron": 0.001,
}


def _legacy_demo_profile() -> dict[str, Any]:
    zones = {
        "Cervical": {
            "zone_key": "facial_cervical",
            "required_min_mm": PREP_TARGET_THICKNESS_MM,
            "required_ideal_mm": None,
            "upper_limit_mm": None,
            "evidence_status": "estimated_prep_demo_050",
            "source_refs": ["miguel_bigcolor_prep_demo_target_2026_07_11"],
            "source_scope": "viewer_demo_target_not_material_ifu",
            "zone_mapping_status": "direct_three_thirds_demo_mapping",
            "technical_action": "Si baja de 0.5 mm: tallar mas en esta zona. Si esta en 0.5 mm o mas: espacio compatible para la demo.",
            "caveat": "Objetivo de demo BigColor PREP fijado por Miguel; no sustituye IFU ni validacion de registro.",
        },
        "Medio": {
            "zone_key": "facial_middle",
            "required_min_mm": PREP_TARGET_THICKNESS_MM,
            "required_ideal_mm": None,
            "upper_limit_mm": None,
            "evidence_status": "estimated_prep_demo_050",
            "source_refs": ["miguel_bigcolor_prep_demo_target_2026_07_11"],
            "source_scope": "viewer_demo_target_not_material_ifu",
            "zone_mapping_status": "direct_three_thirds_demo_mapping",
            "technical_action": "Si baja de 0.5 mm: tallar mas en esta zona. Si esta en 0.5 mm o mas: espacio compatible para la demo.",
            "caveat": "Objetivo de demo BigColor PREP fijado por Miguel; no sustituye IFU ni validacion de registro.",
        },
        "Incisal": {
            "zone_key": "incisal_edge",
            "required_min_mm": PREP_TARGET_THICKNESS_MM,
            "required_ideal_mm": None,
            "upper_limit_mm": None,
            "evidence_status": "estimated_prep_demo_050",
            "source_refs": ["miguel_bigcolor_prep_demo_target_2026_07_11"],
            "source_scope": "viewer_demo_target_not_material_ifu",
            "zone_mapping_status": "direct_three_thirds_demo_mapping",
            "technical_action": "Si baja de 0.5 mm: tallar mas en esta zona. Si esta en 0.5 mm o mas: espacio compatible para la demo.",
            "caveat": "Objetivo de demo BigColor PREP fijado por Miguel; no sustituye IFU ni validacion de registro.",
        },
    }
    return {
        "profile_key": "demo_veneer",
        "material_key": "demo_veneer",
        "display_name": "BigColor PREP demo 0.5 mm",
        "restoration_type": "demo_veneer",
        "overall_status": "estimated_prep_demo_target",
        "caveat": "Perfil de demo con objetivo unico 0.5 mm por tercio. No es IFU.",
        "viewer_readiness_label": "demo local",
        "viewer_color_permission": "red_yellow_green_allowed_for_demo_only",
        "viewer_readiness_caveat": "Objetivo local de demo; no es una regla IFU de material.",
        "selector_label": "BigColor PREP demo 0.5 mm",
        "selector_badge_status": "active_primary_legacy_with_caveat",
        "zones": zones,
        "rules_source": "built_in_legacy_fallback",
    }


def _rule_action(status: str) -> str:
    actions = {
        "insufficient_space": "Falta espacio frente al objetivo; tallar mas en esta zona o revisar el encerado.",
        "borderline": "Zona limite; confirmar IFU, cementacion, sustrato y confianza del registro.",
        "within_target": "Espacio compatible con la regla seleccionada, sujeto a validacion de caso.",
        "over_reduced_or_excess_space": "Espesor alto; en la demo PREP no requiere tallar mas.",
        "low_confidence": "No usar como decision tecnica final. Falta fuente, registro fiable o segmentacion validada.",
    }
    return actions[status]


def _format_sentence_mm(value: Any) -> str:
    if value is None or pd.isna(value):
        return "pendiente"
    return f"{float(value):.2f}"


def _visible_zone_sentence(row: pd.Series) -> str:
    tooth = row.get("Diente")
    zone_key = row.get("Zone key") or row.get("Zona") or "zona"
    measured = _format_sentence_mm(row.get("P50 firmado (mm)"))
    required = _format_sentence_mm(row.get("Min requerido (mm)"))
    material = row.get("Material") or row.get("Perfil material") or "material"
    profile = row.get("Perfil material") or material
    evidence = row.get("Estado evidencia")
    action_key = row.get("Action key")
    qa_status = row.get("QA gate status")
    registration_low = row.get("Distance confidence") == "baja"

    prefix = f"Diente {tooth}, {zone_key}: medido {measured} mm."
    if qa_status == "blocked_for_clinical_use" or registration_low or action_key == "validar_registro_o_medicion":
        return (
            f"{prefix} No decidir tallado por color todavia: validar registro, unidades, "
            "segmentacion y metodo de distancia."
        )
    if evidence == "pending_source" or pd.isna(row.get("Min requerido (mm)")) or action_key == "pedir_ifu_no_colorear":
        return (
            f"{prefix} {material}/{profile} no tiene espesor requerido verificado; "
            "requerido: pendiente de IFU/ficha tecnica. Accion: mantener gris y pedir fuente."
        )
    if evidence == "secondary_unconfirmed" or action_key == "candidato_secundario_no_activo":
        return (
            f"{prefix} Hay candidato {required} mm, pero la fuente no es primaria; "
            "accion: mostrar como QA interno, no rojo/verde."
        )
    if action_key == "tallar_mas_o_revisar_indicacion":
        return (
            f"Diente {tooth}, {zone_key}: medido {measured} mm; requerido {required} mm. "
            "Accion: falta espacio tecnico, revisar reduccion, wax-up o indicacion."
        )
    if action_key == "zona_limite_confirmar_caveat":
        return (
            f"Diente {tooth}, {zone_key}: medido {measured} mm; requerido {required} mm. "
            "Accion: zona limite, confirmar IFU/cementacion/sustrato/QA antes de aceptar."
        )
    if action_key == "revisar_sobreespacio_o_soporte":
        upper = _format_sentence_mm(row.get("Limite superior (mm)"))
        return (
            f"Diente {tooth}, {zone_key}: medido {measured} mm supera limite {upper} mm. "
            "Accion: revisar sobreespacio, soporte y diseno."
        )
    return (
        f"Diente {tooth}, {zone_key}: medido {measured} mm; requerido {required} mm. "
        "Accion: espacio compatible como plan tecnico, con caveat de fuente y QA visible."
    )


def _color_label_es(color_key: Any) -> str:
    labels = {
        "red": "rojo - falta espacio",
        "yellow": "amarillo - zona limite",
        "green": "verde - compatible con regla",
        "purple": "morado - sobreespacio",
        "gray": "gris",
    }
    return labels.get(str(color_key or "gray"), "gris")


def _required_summary_es(row: pd.Series) -> str:
    required_display = row.get("Required display")
    required_min = row.get("Min requerido (mm)")
    token = str(row.get("Source trace token") or "")
    if token == "blocked_unidentified_material":
        return "pendiente de identificacion"
    if pd.isna(required_min):
        return "requerido pendiente de IFU/ficha tecnica primaria"
    return f">= {float(required_min):.2f} mm"


def _technical_sentence_outputs(row: pd.Series) -> pd.Series:
    tooth = row.get("Diente")
    zone_label = row.get("Zone key") or row.get("Zona") or "zona"
    measured = _format_sentence_mm(row.get("P50 firmado (mm)"))
    token = str(row.get("Source trace token") or "")
    color_key = "gray" if token.startswith("blocked_") else str(row.get("Color key") or "gray")
    action = str(row.get("Technical action ES") or row.get("Accion tecnica") or _rule_action("low_confidence"))
    caveat = str(row.get("Caveat") or row.get("Viewer readiness caveat") or "").rstrip(".")
    source_status = str(row.get("Source trace status ES") or "")
    required_summary = _required_summary_es(row)
    material_display = str(row.get("Material display") or row.get("Material") or row.get("Perfil material") or "material")
    source_summary = source_status
    if row.get("Source scope for viewer") and not pd.isna(row.get("Source scope for viewer")):
        source_summary = f"{source_summary}: {row.get('Source scope for viewer')}" if source_summary else str(row.get("Source scope for viewer"))

    sentence = (
        f"Diente {tooth}, zona {zone_label}: medido {measured} mm; "
        f"requerido {required_summary}; material {material_display}; color {color_key}; "
        f"accion tecnica {action}; caveat {caveat}."
    )
    if token == "blocked_pending_primary_source":
        short_action = "No decidir tallado por color hasta archivar fuente primaria."
    elif token == "blocked_secondary_candidate":
        short_action = "Usar solo como QA interna; falta IFU primaria."
    elif token == "blocked_unidentified_material":
        short_action = "Pedir identificacion completa del material e IFU/ficha tecnica."
    else:
        short_action = action

    return pd.Series(
        {
            "Viewer sentence ES": sentence,
            "Viewer short action ES": short_action,
            "Viewer required summary ES": required_summary,
            "Viewer source summary ES": source_summary,
        }
    )


def _registration_validation_action(tooth: int, zone_key: str) -> str:
    return (
        f"Diente {tooth} {zone_key}: medicion no apta para decision tecnica. "
        "Validar registro, segmentacion y metodo antes de colorear."
    )


def _viewer_action_key(
    final_status: str,
    material_status: str,
    rule: dict[str, Any],
    registration_confidence: str,
) -> str:
    if registration_confidence == "baja":
        return "validar_registro_o_medicion"
    if rule.get("evidence_status") == "pending_source" or rule.get("required_min_mm") is None or material_status == "low_confidence":
        return "pedir_ifu_no_colorear"
    if rule.get("evidence_status") == "secondary_unconfirmed":
        return "candidato_secundario_no_activo"
    if final_status == "insufficient_space":
        return "tallar_mas_o_revisar_indicacion"
    if final_status == "over_reduced_or_excess_space":
        return "revisar_sobreespacio_o_soporte"
    if final_status == "borderline":
        return "zona_limite_confirmar_caveat"
    if final_status == "within_target":
        return "espacio_compatible_con_caveat"
    return final_status


def _normalize_zone_rule(zone_rule: dict[str, Any]) -> dict[str, Any]:
    required = zone_rule.get("required_mm", {})
    evidence_status = zone_rule.get("evidence_status", "pending_source")
    return {
        "zone_key": zone_rule.get("zone_key", "all_zones"),
        "required_min_mm": required.get("min"),
        "required_ideal_mm": required.get("ideal"),
        "upper_limit_mm": required.get("upper_limit"),
        "evidence_status": evidence_status,
        "source_refs": zone_rule.get("source_refs", []),
        "source_scope": zone_rule.get("source_scope") or _default_source_scope(evidence_status),
        "zone_mapping_status": zone_rule.get("zone_mapping_status") or _default_zone_mapping_status(evidence_status),
        "technical_action": zone_rule.get("technical_action", ""),
        "caveat": zone_rule.get("caveat", ""),
    }


def _flat_required_matrix(data: dict[str, Any]) -> dict[tuple[str, str, str], dict[str, Any]]:
    matrix = data.get("viewer_codable_material_zone_requirements_2026_07_29", {})
    if not matrix:
        matrix = data.get("viewer_required_thickness_matrix_2026_07_25", {})
    rows = matrix.get("rows", [])
    lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        material_key = row.get("material_key")
        profile_key = row.get("profile_key")
        zone_key = row.get("zone_key")
        if not material_key or not profile_key or not zone_key:
            continue
        lookup[(material_key, profile_key, zone_key)] = row
    return lookup


def _default_source_scope(evidence_status: str) -> str:
    if evidence_status == "pending_source":
        return "pending_primary_ifu_or_technical_sheet"
    if evidence_status == "secondary_unconfirmed":
        return "secondary_candidate_pending_primary_ifu"
    if evidence_status == "estimated_legacy_demo":
        return "local_demo_target_not_clinical_ifu"
    return "source_scope_not_declared"


def _default_zone_mapping_status(evidence_status: str) -> str:
    if evidence_status == "pending_source":
        return "not_mapped_until_source_verified"
    if evidence_status == "secondary_unconfirmed":
        return "candidate_mapping_pending_primary_source"
    if evidence_status == "estimated_legacy_demo":
        return "demo_three_thirds_mapping"
    return "mapping_status_not_declared"


def _normalize_json_profile(
    material: dict[str, Any],
    profile: dict[str, Any],
    required_matrix: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    zones: dict[str, dict[str, Any]] = {}
    all_zones_rule: dict[str, Any] | None = None
    for zone_rule in profile.get("zones", []):
        normalized = _normalize_zone_rule(zone_rule)
        matrix_row = (required_matrix or {}).get(
            (material["material_key"], profile["profile_key"], normalized["zone_key"])
        )
        if matrix_row:
            required_min = matrix_row.get("required_min_mm")
            required_ideal = matrix_row.get("required_ideal_mm")
            upper_limit = matrix_row.get("upper_limit_mm")
            normalized.update(
                {
                    "required_min_mm": required_min if "required_min_mm" in matrix_row else normalized.get("required_min_mm"),
                    "required_ideal_mm": required_ideal if "required_ideal_mm" in matrix_row else normalized.get("required_ideal_mm"),
                    "upper_limit_mm": upper_limit if "upper_limit_mm" in matrix_row else normalized.get("upper_limit_mm"),
                    "evidence_status": matrix_row.get("evidence_status", normalized.get("evidence_status")),
                    "source_refs": matrix_row.get("source_refs", normalized.get("source_refs", [])),
                    "source_scope": matrix_row.get("source_scope_for_viewer", normalized.get("source_scope")),
                    "zone_mapping_status": matrix_row.get("zone_mapping_status", normalized.get("zone_mapping_status")),
                    "required_display": matrix_row.get("required_display_es") or matrix_row.get("required_display"),
                    "source_scope_for_viewer": matrix_row.get("source_scope_for_viewer"),
                    "row_viewer_color_permission": matrix_row.get("viewer_color_permission"),
                    "row_action_rule": matrix_row.get("action_rule_es") or matrix_row.get("row_action_rule"),
                    "truth_partition": matrix_row.get("truth_partition"),
                    "caveat": matrix_row.get("caveat_es", normalized.get("caveat")),
                    "material_zone_join_status": "exact_material_profile_zone",
                }
            )
        else:
            normalized["material_zone_join_status"] = "missing_material_profile_zone_matrix_row"
        legacy_zone = zone_rule.get("legacy_zone_map")
        if legacy_zone in LEGACY_ZONES and legacy_zone not in zones:
            zones[legacy_zone] = normalized
        elif zone_rule.get("zone_key") == "all_zones":
            all_zones_rule = normalized

    if all_zones_rule:
        for legacy_zone in LEGACY_ZONES:
            zones.setdefault(legacy_zone, dict(all_zones_rule))

    return {
        "profile_key": profile["profile_key"],
        "material_key": material["material_key"],
        "display_name": material.get("display_name", material["material_key"]),
        "restoration_type": profile.get("restoration_type", ""),
        "overall_status": material.get("overall_status", ""),
        "caveat": material.get("caveat", ""),
        "zones": zones,
        "rules_source": str(MATERIAL_RULES_PATH),
    }


def _profile_readiness_entries(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    selector_contract = data.get("viewer_selector_display_contract_2026_07_22", {})
    selector_options = selector_contract.get("options", [])
    if selector_options:
        entries: dict[str, dict[str, Any]] = {}
        for entry in selector_options:
            profile_key = entry.get("profile_key")
            if not profile_key:
                continue
            entries[profile_key] = {
                "viewer_readiness_label": entry.get("selector_badge", ""),
                "viewer_color_permission": entry.get("viewer_color_permission", ""),
                "viewer_readiness_caveat": entry.get("blocking_or_caveat_summary", ""),
                "selector_label": entry.get("selector_label", ""),
                "selector_badge_status": entry.get("selector_badge_status", ""),
            }
        return entries

    matrix = data.get("viewer_material_readiness_matrix_2026_07_21", {})
    entries: dict[str, dict[str, Any]] = {}
    for group_key, label in [
        ("verified_data", "activo con fuente"),
        ("secondary_unconfirmed_data", "candidato secundario"),
        ("pending_source_data", "bloqueado por IFU"),
    ]:
        for entry in matrix.get(group_key, []):
            profile_key = entry.get("profile_key")
            if not profile_key:
                continue
            entries[profile_key] = {
                "viewer_readiness_label": label,
                "viewer_color_permission": entry.get("viewer_color_permission", ""),
                "viewer_readiness_caveat": entry.get("required_visible_caveat") or entry.get("blocking_reason", ""),
            }
    for entry in entries.values():
        permission = entry["viewer_color_permission"]
        if permission == "red_yellow_green_allowed_with_legacy_source_caveat":
            entry["viewer_readiness_label"] = "activo con caveat legacy"
    return entries


def _primary_source_locks(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    matrix = data.get(PRIMARY_SOURCE_LOCK_MATRIX_KEY, {})
    return {
        lock["profile_key"]: lock
        for lock in matrix.get("source_locks", [])
        if lock.get("profile_key")
    }


def load_material_profiles(path: Path = MATERIAL_RULES_PATH) -> dict[str, dict[str, Any]]:
    profiles = {"demo_veneer": _legacy_demo_profile()}
    if not path.exists():
        return profiles

    data = json.loads(path.read_text(encoding="utf-8"))
    readiness_entries = _profile_readiness_entries(data)
    required_matrix = _flat_required_matrix(data)
    source_locks = _primary_source_locks(data)
    for material in data.get("materials", []):
        default_profile_key: str | None = None
        material_profile_keys: list[str] = []
        for profile in material.get("profiles", []):
            normalized = _normalize_json_profile(material, profile, required_matrix)
            normalized.update(
                readiness_entries.get(
                    normalized["profile_key"],
                    {
                        "viewer_readiness_label": "",
                        "viewer_color_permission": "",
                        "viewer_readiness_caveat": "",
                        "selector_label": "",
                        "selector_badge_status": "",
                    },
                )
            )
            source_lock = source_locks.get(normalized["profile_key"])
            if source_lock:
                normalized["viewer_color_permission"] = source_lock.get(
                    "color_permission",
                    normalized.get("viewer_color_permission", ""),
                )
                normalized["viewer_readiness_caveat"] = source_lock.get(
                    "caveat_es",
                    normalized.get("viewer_readiness_caveat", ""),
                )
                for rule in normalized["zones"].values():
                    rule["row_viewer_color_permission"] = source_lock.get(
                        "color_permission",
                        rule.get("row_viewer_color_permission", ""),
                    )
                    rule["row_action_rule"] = source_lock.get(
                        "technical_action_template_es",
                        rule.get("row_action_rule", ""),
                    )
                    rule["caveat"] = source_lock.get("caveat_es", rule.get("caveat", ""))
            profiles[normalized["profile_key"]] = normalized
            material_profile_keys.append(normalized["profile_key"])
            if profile.get("default_for_viewer"):
                default_profile_key = normalized["profile_key"]

        if default_profile_key:
            profiles[material["material_key"]] = profiles[default_profile_key]
        elif len(material_profile_keys) == 1:
            profiles[material["material_key"]] = profiles[material_profile_keys[0]]

    if "demo_veneer_legacy_current_engine_map" in profiles:
        profiles["demo_veneer"] = {
            **profiles["demo_veneer_legacy_current_engine_map"],
            "profile_key": "demo_veneer",
            "viewer_readiness_label": "demo local",
            "viewer_color_permission": "red_yellow_green_allowed_for_demo_only",
            "viewer_readiness_caveat": "Objetivo local de demo; no es una regla IFU de material.",
            "selector_label": "BigColor PREP demo 0.5 mm",
            "selector_badge_status": "active_primary_legacy_with_caveat",
        }
    return profiles


MATERIAL_PROFILES: dict[str, dict[str, Any]] = load_material_profiles()

FDI_BY_ARCH = {
    "S": [15, 14, 13, 12, 11, 21, 22, 23, 24, 25],
    "I": [45, 44, 43, 42, 41, 31, 32, 33, 34, 35],
}


@dataclass
class RegistrationReport:
    enabled: bool
    method: str
    applied_to_waxup: bool
    transform_matrix: list[list[float]] | None
    rms_mm: float | None
    p95_mm: float | None
    confidence: str
    notes: list[str]
    landmarks_used: int | None = None
    landmarks_unit: str | None = None
    landmarks_unit_source: str | None = None
    landmark_errors_mm: list[dict[str, float | str]] | None = None
    landmark_geometry: dict[str, Any] | None = None


@dataclass
class UnitReport:
    input_unit: str
    scale_to_mm: float
    scaled_to_mm: bool
    assumed_unit: str
    bbox_diagonal: float
    confidence: str
    notes: list[str]


def build_quality_gate(
    unit_report: UnitReport,
    registration_report: RegistrationReport,
    distance_report: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if unit_report.confidence == "baja":
        blockers.append("unit_confidence_low")
    elif unit_report.confidence != "alta":
        warnings.append("unit_confidence_not_high")

    if registration_report.confidence == "baja":
        blockers.append("registration_confidence_low")
    elif registration_report.confidence != "alta":
        warnings.append("registration_confidence_not_high")

    if registration_report.method == "assume_aligned":
        blockers.append("registration_assumed_aligned")
    if registration_report.method == "global_icp_vertex_sample_applied":
        warnings.append("global_icp_applied_without_stable_zone_validation")
    if registration_report.method == "global_icp_vertex_sample_report_only":
        warnings.append("global_icp_report_only_not_applied")

    landmark_geometry = registration_report.landmark_geometry or {}
    surface_proximity = landmark_geometry.get("surface_proximity") or {}
    if landmark_geometry.get("status") == "invalid":
        blockers.append("landmark_geometry_invalid")
    elif landmark_geometry.get("status") == "weak":
        warnings.append("landmark_geometry_weak")
    if surface_proximity.get("status") == "invalid":
        blockers.append("landmark_surface_proximity_invalid")
    elif surface_proximity.get("status") == "weak":
        warnings.append("landmark_surface_proximity_weak")

    if distance_report.get("fallback"):
        warnings.append("distance_method_fallback")
    if distance_report.get("method") == "normal_ray_surface_hybrid":
        coverage = float(distance_report.get("ray_hit_ratio", 0.0))
        fallback_ratio = float(distance_report.get("fallback_ratio", 0.0))
        if coverage < 0.70:
            blockers.append("normal_ray_coverage_low")
        elif coverage < 0.90:
            warnings.append("normal_ray_coverage_not_high")
        if fallback_ratio > 0.30:
            blockers.append("normal_ray_fallback_high")
        elif fallback_ratio > 0.10:
            warnings.append("normal_ray_fallback_not_low")
    if distance_report.get("method") == "nearest_vertex_normal_fast":
        warnings.append("distance_method_fast_vertex_signed")

    status = "blocked_for_clinical_use" if blockers else "technical_qa_pass_with_caveats"
    return {
        "status": status,
        "can_use_for_clinical_decision": False,
        "can_use_for_demo_or_qa": True,
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "notes": [
            "Puerta tecnica para automatizacion y QA; no es validacion clinica.",
            "Para uso clinico faltan landmarks anatomicos revisados, repetibilidad y validacion contra criterio experto.",
        ],
    }


def load_mesh(path: str | Path) -> trimesh.Trimesh:
    mesh = trimesh.load(Path(path), process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = mesh.dump().sum()
    if mesh.vertices.size == 0 or mesh.faces.size == 0:
        raise ValueError(f"Mesh is empty or invalid: {path}")
    return mesh


def assess_units(meshes: list[trimesh.Trimesh], input_unit: str, scale_to_mm: float) -> UnitReport:
    bounds = np.vstack([mesh.bounds for mesh in meshes])
    diagonal = float(np.linalg.norm(bounds[1] - bounds[0]))
    notes: list[str] = []
    confidence = "media"
    assumed = "mm"

    if scale_to_mm != 1.0:
        notes.append(f"Coordenadas convertidas desde {input_unit} a mm con factor {scale_to_mm}.")
    else:
        notes.append("Coordenadas interpretadas directamente como mm.")

    if diagonal < 5:
        confidence = "baja"
        notes.append("Diagonal muy pequena para una arcada dental; puede venir en metros o escala normalizada.")
    elif diagonal > 250:
        confidence = "baja"
        notes.append("Diagonal muy grande para una arcada dental; revisar si el STL esta en micras u otra unidad.")
    else:
        notes.append("Escala compatible con milimetros para una arcada parcial/completa.")

    return UnitReport(
        input_unit=input_unit,
        scale_to_mm=scale_to_mm,
        scaled_to_mm=scale_to_mm != 1.0,
        assumed_unit=assumed,
        bbox_diagonal=round(diagonal, 3),
        confidence=confidence,
        notes=notes,
    )


def _sample_vertices(mesh: trimesh.Trimesh, max_points: int = 5000) -> np.ndarray:
    verts = np.asarray(mesh.vertices)
    if len(verts) <= max_points:
        return verts
    step = max(1, len(verts) // max_points)
    return verts[::step][:max_points]


def _sample_points(points: np.ndarray, max_points: int = DEFAULT_LOCAL_REGISTRATION_SAMPLE_LIMIT) -> np.ndarray:
    if len(points) <= max_points:
        return points
    indices = np.linspace(0, len(points) - 1, max_points, dtype=int)
    return points[indices]


def _rounded_matrix(matrix: np.ndarray) -> list[list[float]]:
    return [[round(float(value), 8) for value in row] for row in matrix]


def _patch_stability_metrics(points: np.ndarray, prefix: str) -> dict[str, Any]:
    if len(points) == 0:
        return {
            f"{prefix}_bbox_x_mm": None,
            f"{prefix}_bbox_y_mm": None,
            f"{prefix}_bbox_z_mm": None,
            f"{prefix}_bbox_max_extent_mm": None,
            f"{prefix}_bbox_min_extent_mm": None,
            f"{prefix}_sv1_mm": None,
            f"{prefix}_sv2_mm": None,
            f"{prefix}_sv3_mm": None,
            f"{prefix}_inplane_condition": None,
            f"{prefix}_planarity_ratio": None,
            f"{prefix}_spatial_rank": 0,
        }

    spans = np.ptp(points, axis=0)
    centered = points - np.mean(points, axis=0)
    _, singular_values, _ = np.linalg.svd(centered, full_matrices=False)
    padded = np.pad(singular_values, (0, max(0, 3 - len(singular_values))))[:3]
    max_sv = float(padded[0])
    rank_threshold = max(max_sv * 0.03, 1e-6)
    spatial_rank = int(np.sum(padded > rank_threshold))
    inplane_condition = float(padded[0] / padded[1]) if padded[1] > 1e-9 else None
    planarity_ratio = float(padded[2] / padded[0]) if padded[0] > 1e-9 else None
    return {
        f"{prefix}_bbox_x_mm": round(float(spans[0]), 4),
        f"{prefix}_bbox_y_mm": round(float(spans[1]), 4),
        f"{prefix}_bbox_z_mm": round(float(spans[2]), 4),
        f"{prefix}_bbox_max_extent_mm": round(float(np.max(spans)), 4),
        f"{prefix}_bbox_min_extent_mm": round(float(np.min(spans)), 4),
        f"{prefix}_sv1_mm": round(float(padded[0]), 4),
        f"{prefix}_sv2_mm": round(float(padded[1]), 4),
        f"{prefix}_sv3_mm": round(float(padded[2]), 4),
        f"{prefix}_inplane_condition": round(inplane_condition, 4) if inplane_condition is not None else None,
        f"{prefix}_planarity_ratio": round(planarity_ratio, 4) if planarity_ratio is not None else None,
        f"{prefix}_spatial_rank": spatial_rank,
    }


def _rotation_angle_degrees(matrix: np.ndarray) -> float:
    rotation = np.asarray(matrix[:3, :3], dtype=float)
    cosine = (float(np.trace(rotation)) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def _local_patch_stability_status(record: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    cautions: list[str] = []
    if int(record.get("preop_sample_count") or 0) < 12:
        blockers.append("preop_samples_lt_12")
    if int(record.get("waxup_vertex_count") or 0) < 12:
        blockers.append("waxup_vertices_lt_12")
    if (record.get("preop_bbox_max_extent_mm") or 0) < 1.0:
        blockers.append("preop_patch_extent_lt_1mm")
    if (record.get("waxup_bbox_max_extent_mm") or 0) < 1.0:
        blockers.append("waxup_patch_extent_lt_1mm")
    if int(record.get("preop_spatial_rank") or 0) < 2:
        blockers.append("preop_patch_rank_lt_2")
    if int(record.get("waxup_spatial_rank") or 0) < 2:
        blockers.append("waxup_patch_rank_lt_2")

    for prefix in ("preop", "waxup"):
        condition = record.get(f"{prefix}_inplane_condition")
        if condition is not None and condition > 8.0:
            cautions.append(f"{prefix}_inplane_condition_gt_8")

    p95 = record.get("local_icp_p95_mm")
    rotation = record.get("local_icp_rotation_deg")
    translation = record.get("local_icp_translation_mm")
    if p95 is not None and p95 > 2.0:
        blockers.append("local_icp_p95_gt_2mm")
    elif p95 is not None and p95 > 1.0:
        cautions.append("local_icp_p95_gt_1mm")
    if rotation is not None and rotation > 15.0:
        blockers.append("local_icp_rotation_gt_15deg")
    elif rotation is not None and rotation > 8.0:
        cautions.append("local_icp_rotation_gt_8deg")
    if translation is not None and translation > 3.0:
        blockers.append("local_icp_translation_gt_3mm")
    elif translation is not None and translation > 1.5:
        cautions.append("local_icp_translation_gt_1_5mm")

    if blockers:
        return "reject", blockers + cautions
    if cautions:
        return "caution", cautions
    return "stable", []


def _load_landmark_pairs(
    path: str | Path,
    input_unit: str,
    scale_to_mm: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, list[str], str, str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    pairs = data.get("pairs", data) if isinstance(data, dict) else data
    declared_unit = data.get("unit") or data.get("input_unit") if isinstance(data, dict) else None
    unit_source = "landmark_file" if declared_unit else "inherited_from_cli_input_unit"
    landmarks_unit = str(declared_unit or input_unit)
    if landmarks_unit not in UNIT_SCALE_TO_MM:
        raise ValueError(f"Unknown landmark unit: {landmarks_unit}. Available: {', '.join(UNIT_SCALE_TO_MM)}")
    if landmarks_unit != input_unit:
        raise ValueError(
            "Landmark unit must match --input-unit for this run. "
            f"landmarks={landmarks_unit} input_unit={input_unit}"
        )
    if not isinstance(pairs, list) or len(pairs) < 3:
        raise ValueError("Landmark registration requires at least 3 paired points.")

    preop_points: list[list[float]] = []
    waxup_points: list[list[float]] = []
    labels: list[str] = []
    for index, pair in enumerate(pairs, start=1):
        if not isinstance(pair, dict):
            raise ValueError(f"Landmark pair {index} must be an object.")
        preop_point = pair.get("preop") or pair.get("fixed")
        waxup_point = pair.get("waxup") or pair.get("moving")
        if not _is_point3(preop_point) or not _is_point3(waxup_point):
            raise ValueError(f"Landmark pair {index} must include preop/waxup 3D coordinates.")
        preop_points.append([float(value) * scale_to_mm for value in preop_point])
        waxup_points.append([float(value) * scale_to_mm for value in waxup_point])
        labels.append(str(pair.get("label") or pair.get("id") or f"LM{index}"))

    return np.asarray(preop_points, dtype=float), np.asarray(waxup_points, dtype=float), labels, landmarks_unit, unit_source


def _landmark_geometry_report(fixed: np.ndarray, moving: np.ndarray) -> dict[str, Any]:
    fixed_distances = _pairwise_distances(fixed)
    moving_distances = _pairwise_distances(moving)
    fixed_rank, fixed_singular_values = _point_cloud_rank(fixed)
    moving_rank, moving_singular_values = _point_cloud_rank(moving)
    fixed_extent = float(np.linalg.norm(fixed.max(axis=0) - fixed.min(axis=0)))
    moving_extent = float(np.linalg.norm(moving.max(axis=0) - moving.min(axis=0)))
    min_pair_distance = min(float(fixed_distances.min()), float(moving_distances.min()))
    notes: list[str] = []
    status = "ok"

    if len(fixed) < 4:
        status = "weak"
        notes.append("Menos de 4 landmarks: matematicamente puede registrar, pero no es suficiente para QA diario revisable.")
    if min_pair_distance < 0.5:
        status = "invalid"
        notes.append("Hay landmarks duplicados o casi duplicados; revisar el archivo antes de confiar en el registro.")
    if min(fixed_rank, moving_rank) < 2:
        status = "invalid"
        notes.append("Los landmarks son colineales o degenerados; la transformacion rigida no es fiable.")
    if min(fixed_extent, moving_extent) < 5.0:
        status = "weak" if status == "ok" else status
        notes.append("Los landmarks cubren una extension pequena; pueden ajustar localmente sin validar la arcada.")
    if not notes:
        notes.append("Distribucion de landmarks suficiente para QA tecnico inicial; no valida precision clinica.")

    return {
        "status": status,
        "pair_count": int(len(fixed)),
        "min_pair_distance_mm": round(min_pair_distance, 4),
        "fixed_extent_mm": round(fixed_extent, 4),
        "moving_extent_mm": round(moving_extent, 4),
        "fixed_rank": int(fixed_rank),
        "moving_rank": int(moving_rank),
        "fixed_singular_values": [round(float(value), 4) for value in fixed_singular_values],
        "moving_singular_values": [round(float(value), 4) for value in moving_singular_values],
        "notes": notes,
    }


def _landmark_surface_report(
    preop: trimesh.Trimesh,
    waxup: trimesh.Trimesh,
    fixed: np.ndarray,
    moving: np.ndarray,
    labels: list[str],
) -> dict[str, Any]:
    from scipy.spatial import cKDTree

    preop_tree = cKDTree(np.asarray(preop.vertices))
    waxup_tree = cKDTree(np.asarray(waxup.vertices))
    preop_distances, _ = preop_tree.query(fixed, k=1)
    waxup_distances, _ = waxup_tree.query(moving, k=1)
    max_distance = float(max(preop_distances.max(), waxup_distances.max()))
    notes: list[str] = []
    status = "ok"

    if max_distance > 1.0:
        status = "invalid"
        notes.append("Al menos un landmark esta a mas de 1.0 mm de su malla; no debe usarse para registrar.")
    elif max_distance > 0.25:
        status = "weak"
        notes.append("Al menos un landmark esta a mas de 0.25 mm de su malla; revisar el marcado manual.")
    else:
        notes.append("Landmarks cercanos a vertices de sus mallas; valida solo proximidad tecnica, no anatomia.")

    return {
        "status": status,
        "method": "nearest_mesh_vertex_distance",
        "max_distance_mm": round(max_distance, 4),
        "preop_max_distance_mm": round(float(preop_distances.max()), 4),
        "waxup_max_distance_mm": round(float(waxup_distances.max()), 4),
        "preop_mean_distance_mm": round(float(preop_distances.mean()), 4),
        "waxup_mean_distance_mm": round(float(waxup_distances.mean()), 4),
        "per_landmark": [
            {
                "label": label,
                "preop_surface_distance_mm": round(float(preop_distance), 4),
                "waxup_surface_distance_mm": round(float(waxup_distance), 4),
            }
            for label, preop_distance, waxup_distance in zip(labels, preop_distances, waxup_distances, strict=True)
        ],
        "notes": notes,
    }


def _pairwise_distances(points: np.ndarray) -> np.ndarray:
    distances: list[float] = []
    for index in range(len(points)):
        for other_index in range(index + 1, len(points)):
            distances.append(float(np.linalg.norm(points[index] - points[other_index])))
    return np.asarray(distances, dtype=float)


def _point_cloud_rank(points: np.ndarray) -> tuple[int, np.ndarray]:
    _, singular_values, _ = np.linalg.svd(points - points.mean(axis=0), full_matrices=False)
    tolerance = max(points.shape) * np.finfo(float).eps * float(singular_values.max() if singular_values.size else 0.0)
    return int(np.sum(singular_values > tolerance)), singular_values


def _cap_landmark_confidence(confidence: str, geometry_status: str) -> str:
    if geometry_status == "invalid":
        return "baja"
    if geometry_status == "weak" and confidence == "alta":
        return "media"
    return confidence


def _is_point3(value: Any) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return False
    return all(isinstance(item, (int, float)) for item in value)


def _rigid_transform_from_points(moving: np.ndarray, fixed: np.ndarray) -> np.ndarray:
    moving_centroid = moving.mean(axis=0)
    fixed_centroid = fixed.mean(axis=0)
    moving_centered = moving - moving_centroid
    fixed_centered = fixed - fixed_centroid
    covariance = moving_centered.T @ fixed_centered
    u, _, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0:
        vt[-1, :] *= -1
        rotation = vt.T @ u.T
    translation = fixed_centroid - rotation @ moving_centroid
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return matrix


def _apply_transform_to_points(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    homogeneous = np.column_stack([points, np.ones(len(points))])
    return (homogeneous @ matrix.T)[:, :3]


def landmark_registration_report(
    preop: trimesh.Trimesh,
    waxup: trimesh.Trimesh,
    landmarks_path: str | Path,
    input_unit: str = "mm",
    landmark_scale_to_mm: float = 1.0,
) -> RegistrationReport:
    fixed, moving, labels, landmarks_unit, unit_source = _load_landmark_pairs(
        landmarks_path,
        input_unit=input_unit,
        scale_to_mm=landmark_scale_to_mm,
    )
    geometry = _landmark_geometry_report(fixed, moving)
    surface = _landmark_surface_report(preop, waxup, fixed, moving, labels)
    matrix = _rigid_transform_from_points(moving, fixed)
    transformed = _apply_transform_to_points(moving, matrix)
    errors = np.linalg.norm(transformed - fixed, axis=1)
    rms = float(np.sqrt(np.mean(np.square(errors))))
    p95 = float(np.percentile(errors, 95))
    confidence = "alta" if rms <= 0.1 and p95 <= 0.2 else "media" if rms <= 0.25 and p95 <= 0.5 else "baja"
    confidence = _cap_landmark_confidence(confidence, str(geometry["status"]))
    confidence = _cap_landmark_confidence(confidence, str(surface["status"]))
    waxup.apply_transform(matrix)
    return RegistrationReport(
        enabled=True,
        method="manual_landmark_rigid_transform_applied",
        applied_to_waxup=True,
        transform_matrix=_rounded_matrix(matrix),
        rms_mm=round(rms, 4),
        p95_mm=round(p95, 4),
        confidence=confidence,
        notes=[
            "Transformacion rigida calculada desde landmarks manuales pareados.",
            f"Landmarks interpretados en {landmarks_unit}; origen de unidad: {unit_source}.",
            "La confianza refleja error entre landmarks, no validacion clinica de superficie.",
            *geometry["notes"],
            *surface["notes"],
        ],
        landmarks_used=len(labels),
        landmarks_unit=landmarks_unit,
        landmarks_unit_source=unit_source,
        landmark_errors_mm=[
            {"label": label, "error_mm": round(float(error), 4)}
            for label, error in zip(labels, errors, strict=True)
        ],
        landmark_geometry={**geometry, "surface_proximity": surface},
    )


def registration_report(
    preop: trimesh.Trimesh,
    waxup: trimesh.Trimesh,
    enable_icp: bool,
    apply_transform: bool,
) -> RegistrationReport:
    notes = [
        "El informe mide correspondencia geometrica, no valida precision clinica.",
        "ICP global puede degradar el resultado si no se limitan zonas estables.",
    ]
    if not enable_icp:
        return RegistrationReport(False, "assume_aligned", False, None, None, None, "baja", notes + ["ICP no aplicado; se asume que los STL ya estan alineados."])

    try:
        from scipy.spatial import cKDTree
        from trimesh.registration import icp

        src = _sample_vertices(waxup)
        dst = _sample_vertices(preop)
        matrix, transformed, _ = icp(src, dst, max_iterations=30, threshold=1e-5, scale=False, reflection=False)
        if apply_transform:
            waxup.apply_transform(matrix)
            notes.append("Transformacion ICP aplicada al wax-up antes de medir distancia.")
        else:
            notes.append("Transformacion ICP reportada pero no aplicada; la medicion conserva la alineacion original.")

        tree = cKDTree(np.asarray(preop.vertices))
        distances, _ = tree.query(transformed, k=1)
        rms = float(np.sqrt(np.mean(np.square(distances))))
        p95 = float(np.percentile(distances, 95))
        confidence = "alta" if rms <= 0.15 and p95 <= 0.35 else "media" if rms <= 0.35 and p95 <= 0.8 else "baja"
        method = "global_icp_vertex_sample_applied" if apply_transform else "global_icp_vertex_sample_report_only"
        return RegistrationReport(True, method, apply_transform, _rounded_matrix(matrix), round(rms, 4), round(p95, 4), confidence, notes)
    except Exception as exc:
        return RegistrationReport(False, "icp_failed_assume_aligned", False, None, None, None, "baja", notes + [f"ICP fallo: {type(exc).__name__}: {exc}"])


def signed_distances(
    preop: trimesh.Trimesh,
    waxup: trimesh.Trimesh,
    prefer_exact_surface: bool = False,
    exact_surface_vertex_limit: int | None = DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
) -> tuple[np.ndarray, dict[str, Any]]:
    if not prefer_exact_surface:
        return _fast_signed_vertex_distances(preop, waxup), {
            "method": "nearest_vertex_normal_fast",
            "fallback": False,
            "notes": [
                "Distancia firmada rapida para QA tecnico.",
                "No sustituye distancia exacta a superficie ni validacion clinica.",
            ],
        }

    total_vertices = int(len(preop.vertices) + len(waxup.vertices))
    if exact_surface_vertex_limit is not None and total_vertices > exact_surface_vertex_limit:
        return _fast_signed_vertex_distances(preop, waxup), {
            "method": "nearest_vertex_normal_fallback",
            "fallback": True,
            "reason": "exact_surface_skipped_mesh_too_dense",
            "vertex_count": {
                "preop": int(len(preop.vertices)),
                "waxup": int(len(waxup.vertices)),
                "total": total_vertices,
                "limit": int(exact_surface_vertex_limit),
            },
            "notes": [
                "Se pidio distancia exacta, pero la malla supera el limite configurado para evitar bloqueo del CLI.",
                "Usa --exact-surface-max-vertices 0 solo en QA controlado si aceptas tiempos largos.",
            ],
        }

    try:
        from trimesh.proximity import ProximityQuery

        pq = ProximityQuery(preop)
        signed = pq.signed_distance(waxup.vertices)
        return np.asarray(signed, dtype=float), {
            "method": "trimesh_signed_surface",
            "fallback": False,
            "vertex_count": {
                "preop": int(len(preop.vertices)),
                "waxup": int(len(waxup.vertices)),
                "total": total_vertices,
                "limit": exact_surface_vertex_limit,
            },
        }
    except Exception as exc:
        return _fast_signed_vertex_distances(preop, waxup), {
            "method": "nearest_vertex_normal_fallback",
            "fallback": True,
            "reason": f"{type(exc).__name__}: {exc}",
            "vertex_count": {
                "preop": int(len(preop.vertices)),
                "waxup": int(len(waxup.vertices)),
                "total": total_vertices,
                "limit": exact_surface_vertex_limit,
            },
        }


def _deterministic_face_samples(
    mesh: trimesh.Trimesh,
    max_samples: int = DEFAULT_RAY_SAMPLE_COUNT,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    points = np.asarray(mesh.triangles_center, dtype=float)
    normals = np.asarray(mesh.face_normals, dtype=float)
    areas = np.asarray(mesh.area_faces, dtype=float)
    if max_samples > 0 and len(points) > max_samples:
        indices = np.linspace(0, len(points) - 1, max_samples, dtype=int)
        points = points[indices]
        normals = normals[indices]
        areas = areas[indices]
    return points, normals, areas


def _closest_surface_distances(mesh: trimesh.Trimesh, points: np.ndarray) -> np.ndarray:
    if len(points) == 0:
        return np.asarray([], dtype=float)
    _, distances, _ = trimesh.proximity.closest_point(mesh, points)
    return np.asarray(distances, dtype=float)


def _closest_surface_signed_distances(mesh: trimesh.Trimesh, points: np.ndarray, normals: np.ndarray) -> np.ndarray:
    if len(points) == 0:
        return np.asarray([], dtype=float)
    closest, distances, _ = trimesh.proximity.closest_point(mesh, points)
    direction = np.einsum("ij,ij->i", np.asarray(closest) - points, normals)
    sign = np.sign(direction)
    sign[sign == 0] = 1
    return np.asarray(distances * sign, dtype=float)


def _first_ray_hits(
    mesh: trimesh.Trimesh,
    origins: np.ndarray,
    directions: np.ndarray,
    max_depth_mm: float,
) -> np.ndarray:
    distances = np.full(len(origins), np.inf, dtype=float)
    if len(origins) == 0:
        return distances
    locations, ray_index, _ = mesh.ray.intersects_location(
        ray_origins=origins,
        ray_directions=directions,
        multiple_hits=False,
    )
    if len(ray_index) == 0:
        return distances
    t_values = np.einsum("ij,ij->i", locations - origins[ray_index], directions[ray_index])
    valid = (t_values > 0.0) & (t_values <= max_depth_mm)
    if np.any(valid):
        np.minimum.at(distances, ray_index[valid], t_values[valid])
    return distances


def _normal_ray_confidence(ray_hit_ratio: float, fallback_ratio: float) -> str:
    if ray_hit_ratio >= 0.90 and fallback_ratio <= 0.10:
        return "alta"
    if ray_hit_ratio >= 0.70 and fallback_ratio <= 0.30:
        return "media"
    return "baja"


def normal_ray_surface_distances(
    preop: trimesh.Trimesh,
    waxup: trimesh.Trimesh,
    sample_count: int = DEFAULT_RAY_SAMPLE_COUNT,
    max_depth_mm: float = DEFAULT_RAY_MAX_DEPTH_MM,
    ray_direction: str = "bidirectional",
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if ray_direction not in NORMAL_RAY_DIRECTIONS:
        raise ValueError(f"ray_direction must be one of: {', '.join(NORMAL_RAY_DIRECTIONS)}")
    points, normals, area_weights = _deterministic_face_samples(preop, sample_count)
    plus = np.full(len(points), np.inf, dtype=float)
    minus = np.full(len(points), np.inf, dtype=float)
    if ray_direction in {"bidirectional", "plus_normal"}:
        origins_plus = points + normals * 0.02
        plus = _first_ray_hits(waxup, origins_plus, normals, max_depth_mm=max_depth_mm)
    if ray_direction in {"bidirectional", "minus_normal"}:
        origins_minus = points - normals * 0.02
        minus = _first_ray_hits(waxup, origins_minus, -normals, max_depth_mm=max_depth_mm)
    if ray_direction == "plus_normal":
        ray_distances = plus
    elif ray_direction == "minus_normal":
        ray_distances = minus
    else:
        ray_distances = np.minimum(plus, minus)
    ray_valid = np.isfinite(ray_distances)
    signed_distances = np.where(plus <= minus, plus, -minus)

    distances = np.array(ray_distances, copy=True)
    fallback_ratio = 0.0
    if not np.all(ray_valid):
        fallback_signed = _closest_surface_signed_distances(waxup, points[~ray_valid], normals[~ray_valid])
        signed_distances[~ray_valid] = fallback_signed
        distances[~ray_valid] = np.abs(fallback_signed)
        fallback_ratio = float(np.mean(~ray_valid))

    ray_hit_ratio = float(np.mean(ray_valid)) if len(ray_valid) else 0.0
    fallback_count = int(np.sum(~ray_valid))
    ray_hit_count = int(np.sum(ray_valid))
    plus_hit_count = int(np.sum(np.isfinite(plus)))
    minus_hit_count = int(np.sum(np.isfinite(minus)))
    confidence = _normal_ray_confidence(ray_hit_ratio, fallback_ratio)
    signed_summary = {
        "min": round(float(np.min(signed_distances)), 4),
        "p5": round(float(np.percentile(signed_distances, 5)), 4),
        "p50": round(float(np.percentile(signed_distances, 50)), 4),
        "p95": round(float(np.percentile(signed_distances, 95)), 4),
        "max": round(float(np.max(signed_distances)), 4),
        "negative_sample_ratio": round(float(np.mean(signed_distances < 0)), 4),
    }
    report = {
        "method": "normal_ray_surface_hybrid",
        "fallback": fallback_ratio > 0.0,
        "measurement": "directional_clearance_from_preop_to_waxup_mm",
        "signed_summary_mm": signed_summary,
        "confidence": confidence,
        "ray_hit_ratio": round(ray_hit_ratio, 4),
        "fallback_ratio": round(fallback_ratio, 4),
        "ray_hit_count": ray_hit_count,
        "fallback_count": fallback_count,
        "plus_normal_hit_count": plus_hit_count,
        "minus_normal_hit_count": minus_hit_count,
        "plus_normal_hit_ratio": round(float(plus_hit_count / len(points)), 4) if len(points) else 0.0,
        "minus_normal_hit_ratio": round(float(minus_hit_count / len(points)), 4) if len(points) else 0.0,
        "ray_max_depth_mm": float(max_depth_mm),
        "ray_direction": ray_direction,
        "sample_count_requested": int(sample_count),
        "sample_count_used": int(len(points)),
        "source_surface": "preop_face_centroids",
        "direction": f"{ray_direction}_preop_face_normals_first_valid_hit",
        "area_weight_sum": round(float(np.sum(area_weights)), 4),
        "notes": [
            "Mide clearance direccional desde la superficie preoperatoria hacia el wax-up.",
            "El modo bidirectional usa ambas direcciones para tolerar normales STL inconsistentes; plus_normal/minus_normal son diagnosticos QA.",
            "El resumen firmado conserva direccion: positivo sigue la normal de preop, negativo va contra la normal.",
            "Los puntos sin interseccion usan closest-surface fallback y bajan la confianza de la zona.",
        ],
        "_sample_quality": {
            "ray_valid": ray_valid,
            "fallback_used": ~ray_valid,
            "plus_hit": np.isfinite(plus),
            "minus_hit": np.isfinite(minus),
            "points": points,
            "normals": normals,
            "distances_mm": distances,
            "signed_distances_mm": signed_distances,
        },
    }
    return distances, points, report


def _fast_signed_vertex_distances(preop: trimesh.Trimesh, waxup: trimesh.Trimesh) -> np.ndarray:
    from scipy.spatial import cKDTree

    tree = cKDTree(np.asarray(preop.vertices))
    unsigned, idx = tree.query(np.asarray(waxup.vertices), k=1)
    normals = np.asarray(preop.vertex_normals)[idx]
    vectors = np.asarray(waxup.vertices) - np.asarray(preop.vertices)[idx]
    sign = np.sign(np.einsum("ij,ij->i", vectors, normals))
    sign[sign == 0] = 1
    return np.asarray(unsigned * sign, dtype=float)


def segment_teeth_and_zones(vertices: np.ndarray, arch: str) -> tuple[np.ndarray, np.ndarray]:
    if arch not in FDI_BY_ARCH:
        raise ValueError("arch must be S or I")

    span = vertices.max(axis=0) - vertices.min(axis=0)
    horizontal_axis = int(np.argmax(span))
    horizontal = vertices[:, horizontal_axis]
    limits = np.linspace(horizontal.min(), horizontal.max(), 11)
    indices = np.digitize(horizontal, limits) - 1
    indices = np.clip(indices, 0, 9)
    teeth = np.asarray([FDI_BY_ARCH[arch][i] for i in indices])

    z = vertices[:, 2]
    zones = np.empty(len(z), dtype=object)
    if float(z.max()) == float(z.min()):
        zones[:] = "Medio"
        return teeth, zones

    zn = (z - z.min()) / (z.max() - z.min())
    zones[zn <= (1.0 / 3.0)] = "Incisal"
    zones[(zn > (1.0 / 3.0)) & (zn <= (2.0 / 3.0))] = "Medio"
    zones[zn > (2.0 / 3.0)] = "Cervical"
    return teeth, zones


def segment_teeth_and_local_zones(vertices: np.ndarray, arch: str) -> tuple[np.ndarray, np.ndarray]:
    teeth, _ = segment_teeth_and_zones(vertices, arch)
    zones = np.empty(len(vertices), dtype=object)
    z = vertices[:, 2]
    for tooth in sorted(set(teeth), key=int):
        mask = teeth == tooth
        tooth_z = z[mask]
        if len(tooth_z) == 0:
            continue
        if float(tooth_z.max()) == float(tooth_z.min()):
            zones[mask] = "Medio"
            continue
        zn = (tooth_z - tooth_z.min()) / (tooth_z.max() - tooth_z.min())
        local_zones = np.empty(len(tooth_z), dtype=object)
        local_zones[zn <= (1.0 / 3.0)] = "Incisal"
        local_zones[(zn > (1.0 / 3.0)) & (zn <= (2.0 / 3.0))] = "Medio"
        local_zones[zn > (2.0 / 3.0)] = "Cervical"
        zones[mask] = local_zones
    return teeth, zones


def classify_thickness(value: float, rule: dict[str, Any]) -> str:
    min_mm = rule.get("required_min_mm")
    ideal_mm = rule.get("required_ideal_mm")
    upper_mm = rule.get("upper_limit_mm")
    if rule.get("evidence_status") in {"pending_source", "secondary_unconfirmed"} or min_mm is None:
        return "low_confidence"
    if value < min_mm:
        return "insufficient_space"
    if upper_mm is not None and value > upper_mm:
        return "over_reduced_or_excess_space"
    if ideal_mm is not None and value < ideal_mm:
        return "borderline"
    return "within_target"


def prep_decision_label(material_status: str) -> str:
    if material_status == "insufficient_space":
        return "TALLAR"
    if material_status == "low_confidence":
        return "SIN FUENTE"
    if material_status == "borderline":
        return "REVISAR"
    return "OK"


def prep_decision_label_for_rule(material_status: str, rule: dict[str, Any]) -> str:
    if rule.get("evidence_status") == "secondary_unconfirmed":
        return "CANDIDATO"
    if rule.get("evidence_status") == "pending_source" or rule.get("required_min_mm") is None:
        return "SIN FUENTE"
    return prep_decision_label(material_status)


def _viewer_color_key(material_status: str, rule: dict[str, Any]) -> str:
    if rule.get("evidence_status") in {"pending_source", "secondary_unconfirmed"} or rule.get("required_min_mm") is None:
        return "gray"
    return {
        "insufficient_space": "red",
        "borderline": "yellow",
        "within_target": "green",
        "over_reduced_or_excess_space": "purple",
        "low_confidence": "gray",
    }.get(material_status, "gray")


def _viewer_decision_gate(
    material_status: str,
    rule: dict[str, Any],
    registration_confidence: str,
    profile: dict[str, Any],
) -> tuple[str, str, bool]:
    if rule.get("material_zone_join_status") == "missing_material_profile_zone_matrix_row":
        return "material_zone_rule_missing", "gray", False
    evidence = rule.get("evidence_status")
    permission = rule.get("row_viewer_color_permission") or profile.get("viewer_color_permission", "")
    truth_partition = rule.get("truth_partition", "")
    if registration_confidence == "baja":
        return "geometry_or_registration_blocked", "gray", False
    force_gray_permissions = {
        "force_gray_pending_source",
        "force_gray_until_source_verified",
        "force_gray_candidate_for_internal_qa_only",
        "force_gray_until_product_and_ifu_identified",
        "gray_internal_candidate_only",
    }
    if evidence == "secondary_unconfirmed" or permission in {
        "force_gray_candidate_for_internal_qa_only",
        "gray_internal_candidate_only",
    }:
        return "secondary_candidate", "gray", False
    if evidence == "pending_source" or rule.get("required_min_mm") is None or permission in force_gray_permissions:
        return "source_pending_or_unidentified", "gray", False
    if truth_partition == "estimated_demo_not_clinical" or permission == "allow_demo_colors_only":
        return "demo_only", _viewer_color_key(material_status, rule), True
    if permission in {"allow_rag_with_visible_caveat", "red_yellow_green_allowed_with_legacy_source_caveat"}:
        return "verified_or_primary_archived_can_compare", _viewer_color_key(material_status, rule), True
    return "source_pending_or_unidentified", "gray", False


def _viewer_action_band(
    decision_gate: str,
    measured_mm: float,
    required_min_mm: Any,
    required_ideal_mm: Any,
    upper_limit_mm: Any,
    deficit_mm: float | None,
) -> tuple[str, str]:
    comparison_allowed = decision_gate in {"verified_or_primary_archived_can_compare", "demo_only"}
    if not comparison_allowed:
        return "blocked_before_material_action", "no calculable como delta clinico"
    if upper_limit_mm is not None and measured_mm > float(upper_limit_mm):
        return "excess_space", f"{measured_mm - float(upper_limit_mm):.2f} mm exceso"
    if deficit_mm is None or required_min_mm is None:
        return "blocked_before_material_action", "no calculable"
    if deficit_mm > 0.20:
        return "missing_space_major", f"{deficit_mm:.2f} mm"
    if deficit_mm > 0.05:
        return "missing_space_minor", f"{deficit_mm:.2f} mm"
    if deficit_mm > 0:
        return "borderline_acceptance_margin", f"{deficit_mm:.2f} mm"
    if required_ideal_mm is not None and measured_mm < float(required_ideal_mm):
        return "borderline_acceptance_margin", "0.00 mm"
    return "meets_requirement", "0.00 mm"


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


def _source_trace_for_row(
    material: str,
    profile: dict[str, Any],
    rule: dict[str, Any],
    decision_gate: str,
    color_key: str,
    deficit_display_es: str,
) -> dict[str, str]:
    evidence = rule.get("evidence_status")
    permission = rule.get("row_viewer_color_permission") or profile.get("viewer_color_permission", "")
    required_min = rule.get("required_min_mm")
    if rule.get("material_zone_join_status") == "missing_material_profile_zone_matrix_row":
        status = "Bloqueado: falta regla exacta material/perfil/zona"
        token = "blocked_missing_material_zone_rule"
    elif material == "amt_pending" or permission == "force_gray_until_product_and_ifu_identified":
        status = "Bloqueado: material no identificado"
        token = "blocked_unidentified_material"
    elif evidence == "secondary_unconfirmed" or permission == "force_gray_candidate_for_internal_qa_only":
        status = "Candidato secundario: solo QA interna"
        token = "blocked_secondary_candidate"
    elif str(permission).startswith("force_gray") or evidence == "pending_source" or required_min is None:
        status = "Bloqueado: falta IFU/ficha tecnica primaria"
        token = "blocked_pending_primary_source"
    elif permission == "allow_rag_with_visible_caveat" and required_min is not None:
        status = "Fuente permite RAG con caveat visible"
        token = "rag_allowed_visible_caveat"
    elif decision_gate == "demo_only":
        status = "Demo tecnica: no clinico"
        token = "demo_only_visible_caveat"
    else:
        status = "Bloqueado: trazabilidad insuficiente"
        token = "blocked_trace_not_resolved"

    if token.startswith("blocked_"):
        color_key = "gray"
        deficit_display_es = "sin deficit clinico calculable"

    color_permission_labels = {
        "allow_rag_with_visible_caveat": "RAG permitido con caveat visible",
        "force_gray_until_source_verified": "gris obligatorio hasta IFU/ficha tecnica primaria",
        "force_gray_candidate_for_internal_qa_only": "gris obligatorio: candidato solo QA interna",
        "force_gray_until_product_and_ifu_identified": "gris obligatorio: material no identificado",
        "allow_demo_colors_only": "color solo demo, no clinico",
    }
    return {
        "source_trace_status_es": status,
        "source_trace_token": token,
        "color_permission_display_es": color_permission_labels.get(str(permission), str(permission) or "sin permiso de color trazable"),
        "color_key": color_key,
        "deficit_display_es": deficit_display_es,
    }


def build_zone_table(
    teeth: np.ndarray,
    zones: np.ndarray,
    distances: np.ndarray,
    material: str,
    registration_confidence: str,
) -> pd.DataFrame:
    profile = MATERIAL_PROFILES[material]
    df = pd.DataFrame({"Diente": teeth, "Zona": zones, "Distancia firmada (mm)": distances})
    records = []
    for tooth in sorted(df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            sub = df[(df["Diente"] == tooth) & (df["Zona"] == zone)]
            if sub.empty:
                continue
            vals = sub["Distancia firmada (mm)"].to_numpy(dtype=float)
            rule = profile["zones"].get(
                zone,
                {
                    "zone_key": zone,
                    "required_min_mm": None,
                    "required_ideal_mm": None,
                    "upper_limit_mm": None,
                    "evidence_status": "pending_source",
                    "source_refs": [],
                    "source_scope": "",
                    "zone_mapping_status": "",
                    "material_zone_join_status": "missing_material_profile_zone_matrix_row",
                    "technical_action": "",
                    "caveat": "No hay regla cargada para esta zona/perfil.",
                },
            )
            p50 = float(np.percentile(vals, 50))
            material_status = classify_thickness(p50, rule)
            final_status = "low_confidence" if registration_confidence == "baja" or material_status == "low_confidence" else material_status
            action_key = _viewer_action_key(final_status, material_status, rule, registration_confidence)
            if action_key == "validar_registro_o_medicion":
                technical_action = _registration_validation_action(int(tooth), str(rule.get("zone_key") or zone))
            else:
                technical_action = rule.get("technical_action") or _rule_action(final_status)
            if final_status == "low_confidence" and material_status != "low_confidence" and action_key != "validar_registro_o_medicion":
                technical_action = _rule_action("low_confidence") + " Lectura material orientativa: " + _rule_action(material_status)
            min_required = rule.get("required_min_mm")
            legacy_deficit = round(max(0.0, float(min_required) - p50), 3) if min_required is not None else None
            decision_gate, color_key, expose_material_deficit = _viewer_decision_gate(
                material_status, rule, registration_confidence, profile
            )
            deficit = legacy_deficit if expose_material_deficit else None
            export_deficit = legacy_deficit if expose_material_deficit else None
            legacy_action_band_key, deficit_display_es = _viewer_action_band(
                decision_gate,
                p50,
                min_required,
                rule.get("required_ideal_mm"),
                rule.get("upper_limit_mm"),
                deficit,
            )
            source_trace = _source_trace_for_row(
                material,
                profile,
                rule,
                decision_gate,
                color_key,
                deficit_display_es,
            )
            action_band_key = _canonical_action_band_key(
                legacy_action_band_key,
                decision_gate,
                source_trace["source_trace_token"],
            )
            if source_trace["source_trace_token"].startswith("blocked_"):
                color_key = source_trace["color_key"]
                deficit = None
                export_deficit = None
                deficit_display_es = source_trace["deficit_display_es"]
            records.append(
                {
                    "Diente": int(tooth),
                    "Zona": zone,
                    "Material": material,
                    "Perfil material": profile["profile_key"],
                    "Material display": profile["display_name"],
                    "Tipo restauracion": profile["restoration_type"],
                    "Zone key": rule.get("zone_key"),
                    "P5 firmado (mm)": round(float(np.percentile(vals, 5)), 3),
                    "P50 firmado (mm)": round(p50, 3),
                    "P95 firmado (mm)": round(float(np.percentile(vals, 95)), 3),
                    "Media firmada (mm)": round(float(np.mean(vals)), 3),
                    "Min requerido (mm)": min_required,
                    "Required display": rule.get("required_display"),
                    "Ideal requerido (mm)": rule.get("required_ideal_mm"),
                    "Limite superior (mm)": rule.get("upper_limit_mm"),
                    "Ideal/limite max (mm)": rule.get("upper_limit_mm") if rule.get("upper_limit_mm") is not None else rule.get("required_ideal_mm"),
                    "Objetivo PREP (mm)": min_required,
                    "Deficit vs objetivo (mm)": export_deficit,
                    "Decision gate": decision_gate,
                    "Action band key": action_band_key,
                    "Legacy action band key": legacy_action_band_key,
                    "Color key": color_key,
                    "Deficit mm": deficit,
                    "Deficit display ES": deficit_display_es,
                    "Source trace status ES": source_trace["source_trace_status_es"],
                    "Source trace token": source_trace["source_trace_token"],
                    "Color permission display ES": source_trace["color_permission_display_es"],
                    "Technical action ES": technical_action,
                    "Decision PREP": prep_decision_label_for_rule(material_status, rule),
                    "Estado evidencia": rule.get("evidence_status"),
                    "Fuentes": ";".join(rule.get("source_refs", [])),
                    "Source scope": rule.get("source_scope"),
                    "Source scope for viewer": rule.get("source_scope_for_viewer") or rule.get("source_scope"),
                    "Material-zone join status": rule.get("material_zone_join_status", ""),
                    "Zone mapping status": rule.get("zone_mapping_status"),
                    "Row viewer color permission": rule.get("row_viewer_color_permission") or profile.get("viewer_color_permission", ""),
                    "Row action rule": rule.get("row_action_rule", ""),
                    "Truth partition": rule.get("truth_partition", ""),
                    "Evaluacion material": material_status,
                    "Evaluacion": final_status,
                    "Action key": action_key,
                    "Viewer readiness": profile.get("viewer_readiness_label", ""),
                    "Viewer color permission": profile.get("viewer_color_permission", ""),
                    "Viewer readiness caveat": profile.get("viewer_readiness_caveat", ""),
                    "Selector label": profile.get("selector_label", ""),
                    "Selector badge status": profile.get("selector_badge_status", ""),
                    "Blocking/caveat summary": profile.get("viewer_readiness_caveat", ""),
                    "Accion tecnica": technical_action,
                    "Caveat": rule.get("caveat") or profile.get("caveat"),
                    "Vertices": int(len(vals)),
                }
            )
    return pd.DataFrame(records)


def build_normal_ray_zone_coverage(
    teeth: np.ndarray,
    zones: np.ndarray,
    sample_quality: dict[str, np.ndarray] | None,
) -> list[dict[str, Any]]:
    if not sample_quality:
        return []
    ray_valid = np.asarray(sample_quality["ray_valid"], dtype=bool)
    fallback_used = np.asarray(sample_quality["fallback_used"], dtype=bool)
    plus_hit = np.asarray(sample_quality["plus_hit"], dtype=bool)
    minus_hit = np.asarray(sample_quality["minus_hit"], dtype=bool)
    distances_mm = np.asarray(sample_quality["distances_mm"], dtype=float)
    signed_distances_mm = np.asarray(sample_quality["signed_distances_mm"], dtype=float)
    df = pd.DataFrame(
        {
            "Diente": teeth,
            "Zona": zones,
            "ray_valid": ray_valid,
            "fallback_used": fallback_used,
            "plus_hit": plus_hit,
            "minus_hit": minus_hit,
            "both_direction_hit": plus_hit & minus_hit,
            "plus_only_hit": plus_hit & ~minus_hit,
            "minus_only_hit": minus_hit & ~plus_hit,
            "no_direction_hit": ~plus_hit & ~minus_hit,
            "distance_mm": distances_mm,
            "signed_distance_mm": signed_distances_mm,
        }
    )
    records: list[dict[str, Any]] = []
    for tooth in sorted(df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            sub = df[(df["Diente"] == tooth) & (df["Zona"] == zone)]
            if sub.empty:
                continue
            records.append(
                {
                    "Diente": int(tooth),
                    "Zona": zone,
                    "normal_ray_sample_count": int(len(sub)),
                    "normal_ray_hit_ratio": round(float(sub["ray_valid"].mean()), 4),
                    "normal_ray_fallback_ratio": round(float(sub["fallback_used"].mean()), 4),
                    "plus_normal_hit_ratio": round(float(sub["plus_hit"].mean()), 4),
                    "minus_normal_hit_ratio": round(float(sub["minus_hit"].mean()), 4),
                    "both_direction_hit_ratio": round(float(sub["both_direction_hit"].mean()), 4),
                    "plus_only_hit_ratio": round(float(sub["plus_only_hit"].mean()), 4),
                    "minus_only_hit_ratio": round(float(sub["minus_only_hit"].mean()), 4),
                    "no_direction_hit_ratio": round(float(sub["no_direction_hit"].mean()), 4),
                    "distance_p50_mm": round(float(sub["distance_mm"].median()), 4),
                    "signed_distance_p50_mm": round(float(sub["signed_distance_mm"].median()), 4),
                }
            )
    return records


def build_normal_ray_sample_audit(
    teeth: np.ndarray,
    zones: np.ndarray,
    sample_quality: dict[str, np.ndarray] | None,
) -> pd.DataFrame | None:
    if not sample_quality:
        return None
    points = np.asarray(sample_quality["points"], dtype=float)
    normals = np.asarray(sample_quality["normals"], dtype=float)
    return pd.DataFrame(
        {
            "sample_id": np.arange(1, len(points) + 1),
            "Diente": teeth.astype(int),
            "Zona": zones,
            "x_mm": np.round(points[:, 0], 5),
            "y_mm": np.round(points[:, 1], 5),
            "z_mm": np.round(points[:, 2], 5),
            "normal_x": np.round(normals[:, 0], 6),
            "normal_y": np.round(normals[:, 1], 6),
            "normal_z": np.round(normals[:, 2], 6),
            "ray_valid": np.asarray(sample_quality["ray_valid"], dtype=bool),
            "fallback_used": np.asarray(sample_quality["fallback_used"], dtype=bool),
            "plus_hit": np.asarray(sample_quality["plus_hit"], dtype=bool),
            "minus_hit": np.asarray(sample_quality["minus_hit"], dtype=bool),
            "distance_mm": np.round(np.asarray(sample_quality["distances_mm"], dtype=float), 5),
            "signed_distance_mm": np.round(np.asarray(sample_quality["signed_distances_mm"], dtype=float), 5),
        }
    )


def _point_bbox(prefix: str, points: np.ndarray) -> dict[str, Any]:
    if len(points) == 0:
        return {
            f"{prefix}_count": 0,
            f"{prefix}_x_min_mm": None,
            f"{prefix}_x_max_mm": None,
            f"{prefix}_y_min_mm": None,
            f"{prefix}_y_max_mm": None,
            f"{prefix}_z_min_mm": None,
            f"{prefix}_z_max_mm": None,
            f"{prefix}_centroid_x_mm": None,
            f"{prefix}_centroid_y_mm": None,
            f"{prefix}_centroid_z_mm": None,
            f"{prefix}_extent_x_mm": None,
            f"{prefix}_extent_y_mm": None,
            f"{prefix}_extent_z_mm": None,
        }
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centroid = points.mean(axis=0)
    extent = maxs - mins
    return {
        f"{prefix}_count": int(len(points)),
        f"{prefix}_x_min_mm": round(float(mins[0]), 5),
        f"{prefix}_x_max_mm": round(float(maxs[0]), 5),
        f"{prefix}_y_min_mm": round(float(mins[1]), 5),
        f"{prefix}_y_max_mm": round(float(maxs[1]), 5),
        f"{prefix}_z_min_mm": round(float(mins[2]), 5),
        f"{prefix}_z_max_mm": round(float(maxs[2]), 5),
        f"{prefix}_centroid_x_mm": round(float(centroid[0]), 5),
        f"{prefix}_centroid_y_mm": round(float(centroid[1]), 5),
        f"{prefix}_centroid_z_mm": round(float(centroid[2]), 5),
        f"{prefix}_extent_x_mm": round(float(extent[0]), 5),
        f"{prefix}_extent_y_mm": round(float(extent[1]), 5),
        f"{prefix}_extent_z_mm": round(float(extent[2]), 5),
    }


def _bbox_bounds(points: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    if len(points) == 0:
        return None
    return points.min(axis=0), points.max(axis=0)


def _bbox_overlap_report(prefix: str, reference_points: np.ndarray, target_points: np.ndarray) -> dict[str, Any]:
    reference_bounds = _bbox_bounds(reference_points)
    target_bounds = _bbox_bounds(target_points)
    if reference_bounds is None or target_bounds is None:
        return {
            f"{prefix}_has_overlap_xyz": None,
            f"{prefix}_overlap_x_mm": None,
            f"{prefix}_overlap_y_mm": None,
            f"{prefix}_overlap_z_mm": None,
            f"{prefix}_centroid_delta_x_mm": None,
            f"{prefix}_centroid_delta_y_mm": None,
            f"{prefix}_centroid_delta_z_mm": None,
            f"{prefix}_target_points_inside_reference_bbox": None,
            f"{prefix}_target_points_inside_reference_ratio": None,
            f"{prefix}_relationship": "insufficient_points",
        }

    reference_min, reference_max = reference_bounds
    target_min, target_max = target_bounds
    overlap_min = np.maximum(reference_min, target_min)
    overlap_max = np.minimum(reference_max, target_max)
    overlap_extent = np.maximum(0.0, overlap_max - overlap_min)
    has_overlap_xyz = bool(np.all(overlap_extent > 0))
    reference_centroid = reference_points.mean(axis=0)
    target_centroid = target_points.mean(axis=0)
    inside = np.all((target_points >= reference_min) & (target_points <= reference_max), axis=1)
    relationship = "bbox_overlaps_waxup_zone" if has_overlap_xyz else "bbox_outside_or_edge_only_vs_waxup_zone"
    return {
        f"{prefix}_has_overlap_xyz": has_overlap_xyz,
        f"{prefix}_overlap_x_mm": round(float(overlap_extent[0]), 5),
        f"{prefix}_overlap_y_mm": round(float(overlap_extent[1]), 5),
        f"{prefix}_overlap_z_mm": round(float(overlap_extent[2]), 5),
        f"{prefix}_centroid_delta_x_mm": round(float(target_centroid[0] - reference_centroid[0]), 5),
        f"{prefix}_centroid_delta_y_mm": round(float(target_centroid[1] - reference_centroid[1]), 5),
        f"{prefix}_centroid_delta_z_mm": round(float(target_centroid[2] - reference_centroid[2]), 5),
        f"{prefix}_target_points_inside_reference_bbox": int(inside.sum()),
        f"{prefix}_target_points_inside_reference_ratio": round(float(inside.mean()), 4),
        f"{prefix}_relationship": relationship,
    }


def build_normal_ray_zone_bbox_diagnostic(
    teeth: np.ndarray,
    zones: np.ndarray,
    sample_quality: dict[str, np.ndarray] | None,
) -> list[dict[str, Any]]:
    if not sample_quality:
        return []
    points = np.asarray(sample_quality["points"], dtype=float)
    plus_hit = np.asarray(sample_quality["plus_hit"], dtype=bool)
    minus_hit = np.asarray(sample_quality["minus_hit"], dtype=bool)
    ray_valid = np.asarray(sample_quality["ray_valid"], dtype=bool)
    signed_distances_mm = np.asarray(sample_quality["signed_distances_mm"], dtype=float)
    df = pd.DataFrame(
        {
            "Diente": teeth,
            "Zona": zones,
            "x_mm": points[:, 0],
            "y_mm": points[:, 1],
            "z_mm": points[:, 2],
            "ray_valid": ray_valid,
            "no_direction_hit": ~plus_hit & ~minus_hit,
            "signed_distance_mm": signed_distances_mm,
        }
    )
    records: list[dict[str, Any]] = []
    for tooth in sorted(df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            sub = df[(df["Diente"] == tooth) & (df["Zona"] == zone)]
            if sub.empty:
                continue
            all_points = sub[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            no_hit = sub[sub["no_direction_hit"]]
            no_hit_points = no_hit[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            record: dict[str, Any] = {
                "Diente": int(tooth),
                "Zona": zone,
                "sample_count": int(len(sub)),
                "ray_hit_count": int(sub["ray_valid"].sum()),
                "no_direction_hit_count": int(no_hit["no_direction_hit"].sum()),
                "no_direction_hit_ratio": round(float(no_hit["no_direction_hit"].sum() / len(sub)), 4),
                "no_direction_signed_distance_p50_mm": (
                    round(float(no_hit["signed_distance_mm"].median()), 4) if not no_hit.empty else None
                ),
            }
            record.update(_point_bbox("all_samples_bbox", all_points))
            record.update(_point_bbox("no_direction_bbox", no_hit_points))
            records.append(record)
    return records


def build_normal_ray_mesh_zone_bbox_diagnostic(
    teeth: np.ndarray,
    zones: np.ndarray,
    sample_quality: dict[str, np.ndarray] | None,
    waxup: trimesh.Trimesh,
    arch: str,
) -> list[dict[str, Any]]:
    if not sample_quality:
        return []
    sample_points = np.asarray(sample_quality["points"], dtype=float)
    plus_hit = np.asarray(sample_quality["plus_hit"], dtype=bool)
    minus_hit = np.asarray(sample_quality["minus_hit"], dtype=bool)
    no_direction_hit = ~plus_hit & ~minus_hit
    waxup_vertices = np.asarray(waxup.vertices, dtype=float)
    waxup_teeth, waxup_zones = segment_teeth_and_zones(waxup_vertices, arch)

    sample_df = pd.DataFrame(
        {
            "Diente": teeth,
            "Zona": zones,
            "x_mm": sample_points[:, 0],
            "y_mm": sample_points[:, 1],
            "z_mm": sample_points[:, 2],
            "no_direction_hit": no_direction_hit,
        }
    )
    waxup_df = pd.DataFrame(
        {
            "Diente": waxup_teeth,
            "Zona": waxup_zones,
            "x_mm": waxup_vertices[:, 0],
            "y_mm": waxup_vertices[:, 1],
            "z_mm": waxup_vertices[:, 2],
        }
    )
    records: list[dict[str, Any]] = []
    for tooth in sorted(sample_df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            samples = sample_df[(sample_df["Diente"] == tooth) & (sample_df["Zona"] == zone)]
            if samples.empty:
                continue
            waxup_zone = waxup_df[(waxup_df["Diente"] == tooth) & (waxup_df["Zona"] == zone)]
            sample_points_zone = samples[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            no_hit_points = samples[samples["no_direction_hit"]][["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            waxup_points_zone = waxup_zone[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            record: dict[str, Any] = {
                "Diente": int(tooth),
                "Zona": zone,
                "sample_count": int(len(samples)),
                "no_direction_hit_count": int(samples["no_direction_hit"].sum()),
                "waxup_vertex_count": int(len(waxup_zone)),
                "diagnostic_caveat": (
                    "Comparacion de cajas por segmentacion heuristica de arcada; sirve para QA tecnico, "
                    "no para validar precision clinica."
                ),
            }
            record.update(_point_bbox("preop_sample_bbox", sample_points_zone))
            record.update(_point_bbox("preop_no_direction_bbox", no_hit_points))
            record.update(_point_bbox("waxup_zone_bbox", waxup_points_zone))
            record.update(_bbox_overlap_report("all_samples_vs_waxup_zone", sample_points_zone, waxup_points_zone))
            record.update(_bbox_overlap_report("no_direction_vs_waxup_zone", no_hit_points, waxup_points_zone))
            records.append(record)
    return records


def build_normal_ray_local_zone_bbox_diagnostic(
    sample_quality: dict[str, np.ndarray] | None,
    waxup: trimesh.Trimesh,
    arch: str,
) -> list[dict[str, Any]]:
    if not sample_quality:
        return []
    sample_points = np.asarray(sample_quality["points"], dtype=float)
    plus_hit = np.asarray(sample_quality["plus_hit"], dtype=bool)
    minus_hit = np.asarray(sample_quality["minus_hit"], dtype=bool)
    no_direction_hit = ~plus_hit & ~minus_hit
    waxup_vertices = np.asarray(waxup.vertices, dtype=float)
    sample_teeth, sample_zones = segment_teeth_and_local_zones(sample_points, arch)
    waxup_teeth, waxup_zones = segment_teeth_and_local_zones(waxup_vertices, arch)

    sample_df = pd.DataFrame(
        {
            "Diente": sample_teeth,
            "Zona local": sample_zones,
            "x_mm": sample_points[:, 0],
            "y_mm": sample_points[:, 1],
            "z_mm": sample_points[:, 2],
            "no_direction_hit": no_direction_hit,
        }
    )
    waxup_df = pd.DataFrame(
        {
            "Diente": waxup_teeth,
            "Zona local": waxup_zones,
            "x_mm": waxup_vertices[:, 0],
            "y_mm": waxup_vertices[:, 1],
            "z_mm": waxup_vertices[:, 2],
        }
    )
    records: list[dict[str, Any]] = []
    for tooth in sorted(sample_df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            samples = sample_df[(sample_df["Diente"] == tooth) & (sample_df["Zona local"] == zone)]
            if samples.empty:
                continue
            waxup_zone = waxup_df[(waxup_df["Diente"] == tooth) & (waxup_df["Zona local"] == zone)]
            sample_points_zone = samples[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            no_hit_points = samples[samples["no_direction_hit"]][["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            waxup_points_zone = waxup_zone[["x_mm", "y_mm", "z_mm"]].to_numpy(dtype=float)
            record: dict[str, Any] = {
                "Diente": int(tooth),
                "Zona local": zone,
                "sample_count": int(len(samples)),
                "no_direction_hit_count": int(samples["no_direction_hit"].sum()),
                "waxup_vertex_count": int(len(waxup_zone)),
                "diagnostic_caveat": (
                    "Comparacion de cajas con tercios Z recalculados dentro de cada diente heuristico; "
                    "QA tecnico para contrastar contra zonas globales, no validacion clinica."
                ),
            }
            record.update(_point_bbox("preop_sample_bbox", sample_points_zone))
            record.update(_point_bbox("preop_no_direction_bbox", no_hit_points))
            record.update(_point_bbox("waxup_zone_bbox", waxup_points_zone))
            record.update(_bbox_overlap_report("all_samples_vs_waxup_local_zone", sample_points_zone, waxup_points_zone))
            record.update(_bbox_overlap_report("no_direction_vs_waxup_local_zone", no_hit_points, waxup_points_zone))
            records.append(record)
    return records


def _axis_name(axis_index: int) -> str:
    return ("x", "y", "z")[axis_index]


def _centroid_distance_2d(a: pd.Series, b: pd.Series) -> float:
    return float(np.linalg.norm([a["centroid_x_mm"] - b["centroid_x_mm"], a["centroid_y_mm"] - b["centroid_y_mm"]]))


def _axis_centroids(points: np.ndarray, source: str, arch: str) -> pd.DataFrame:
    teeth, zones = segment_teeth_and_local_zones(points, arch)
    df = pd.DataFrame(
        {
            "source": source,
            "Diente": teeth.astype(int),
            "Zona local": zones,
            "x_mm": points[:, 0],
            "y_mm": points[:, 1],
            "z_mm": points[:, 2],
        }
    )
    records: list[dict[str, Any]] = []
    for tooth in sorted(df["Diente"].unique(), key=int):
        for zone in ["Cervical", "Medio", "Incisal"]:
            sub = df[(df["Diente"] == tooth) & (df["Zona local"] == zone)]
            if sub.empty:
                continue
            records.append(
                {
                    "source": source,
                    "Diente": int(tooth),
                    "Zona local": zone,
                    "point_count": int(len(sub)),
                    "centroid_x_mm": round(float(sub["x_mm"].mean()), 5),
                    "centroid_y_mm": round(float(sub["y_mm"].mean()), 5),
                    "centroid_z_mm": round(float(sub["z_mm"].mean()), 5),
                    "x_min_mm": round(float(sub["x_mm"].min()), 5),
                    "x_max_mm": round(float(sub["x_mm"].max()), 5),
                    "y_min_mm": round(float(sub["y_mm"].min()), 5),
                    "y_max_mm": round(float(sub["y_mm"].max()), 5),
                    "z_min_mm": round(float(sub["z_mm"].min()), 5),
                    "z_max_mm": round(float(sub["z_mm"].max()), 5),
                }
            )
    return pd.DataFrame(records)


def build_normal_ray_arc_axis_diagnostic(
    sample_quality: dict[str, np.ndarray] | None,
    waxup: trimesh.Trimesh,
    arch: str,
) -> list[dict[str, Any]]:
    if not sample_quality:
        return []
    sample_points = np.asarray(sample_quality["points"], dtype=float)
    plus_hit = np.asarray(sample_quality["plus_hit"], dtype=bool)
    minus_hit = np.asarray(sample_quality["minus_hit"], dtype=bool)
    no_direction_hit = ~plus_hit & ~minus_hit
    waxup_vertices = np.asarray(waxup.vertices, dtype=float)
    sample_spans = sample_points.max(axis=0) - sample_points.min(axis=0)
    waxup_spans = waxup_vertices.max(axis=0) - waxup_vertices.min(axis=0)
    sample_axis = int(np.argmax(sample_spans))
    waxup_axis = int(np.argmax(waxup_spans))

    sample_centroids = _axis_centroids(sample_points, "preop_samples", arch)
    waxup_centroids = _axis_centroids(waxup_vertices, "waxup_vertices", arch)
    sample_teeth, sample_zones = segment_teeth_and_local_zones(sample_points, arch)
    no_hit_df = pd.DataFrame({"Diente": sample_teeth.astype(int), "Zona local": sample_zones, "no_direction_hit": no_direction_hit})

    records: list[dict[str, Any]] = []
    for _, sample_row in sample_centroids.iterrows():
        same_zone = waxup_centroids[waxup_centroids["Zona local"] == sample_row["Zona local"]]
        same_tooth = same_zone[same_zone["Diente"] == sample_row["Diente"]]
        nearest_tooth = None
        nearest_distance = None
        if not same_zone.empty:
            distances = same_zone.apply(lambda row: _centroid_distance_2d(sample_row, row), axis=1)
            nearest = same_zone.loc[distances.idxmin()]
            nearest_tooth = int(nearest["Diente"])
            nearest_distance = round(float(distances.min()), 5)
        same_tooth_distance = None
        if not same_tooth.empty:
            same_tooth_distance = round(float(_centroid_distance_2d(sample_row, same_tooth.iloc[0])), 5)

        misses = no_hit_df[
            (no_hit_df["Diente"] == sample_row["Diente"])
            & (no_hit_df["Zona local"] == sample_row["Zona local"])
        ]
        if same_tooth_distance is None or nearest_distance is None:
            relationship = "insufficient_waxup_points_for_zone"
        elif nearest_tooth != int(sample_row["Diente"]) and nearest_distance + 0.25 < same_tooth_distance:
            relationship = "neighbor_tooth_centroid_closer_than_assigned_tooth"
        elif sample_axis != waxup_axis:
            relationship = "preop_waxup_arc_axis_disagree"
        elif same_tooth_distance > 8.0 and not misses.empty and float(misses["no_direction_hit"].mean()) >= 0.70:
            relationship = "assigned_tooth_nearest_but_large_local_xy_delta"
        else:
            relationship = "assigned_tooth_centroid_is_nearest_or_tied"

        records.append(
            {
                "Diente": int(sample_row["Diente"]),
                "Zona local": sample_row["Zona local"],
                "preop_sample_count": int(sample_row["point_count"]),
                "preop_no_direction_hit_count": int(misses["no_direction_hit"].sum()) if not misses.empty else 0,
                "preop_no_direction_hit_ratio": round(float(misses["no_direction_hit"].mean()), 4) if not misses.empty else None,
                "preop_arc_axis": _axis_name(sample_axis),
                "waxup_arc_axis": _axis_name(waxup_axis),
                "preop_span_x_mm": round(float(sample_spans[0]), 5),
                "preop_span_y_mm": round(float(sample_spans[1]), 5),
                "waxup_span_x_mm": round(float(waxup_spans[0]), 5),
                "waxup_span_y_mm": round(float(waxup_spans[1]), 5),
                "preop_centroid_x_mm": sample_row["centroid_x_mm"],
                "preop_centroid_y_mm": sample_row["centroid_y_mm"],
                "preop_centroid_z_mm": sample_row["centroid_z_mm"],
                "same_tooth_waxup_centroid_xy_delta_mm": same_tooth_distance,
                "nearest_waxup_tooth_same_zone": nearest_tooth,
                "nearest_waxup_same_zone_centroid_xy_delta_mm": nearest_distance,
                "nearest_waxup_is_assigned_tooth": nearest_tooth == int(sample_row["Diente"]) if nearest_tooth is not None else None,
                "axis_diagnostic_relationship": relationship,
                "diagnostic_caveat": (
                    "Comparacion 2D de centroides por diente/zona local para diagnosticar eje de arcada "
                    "y asignacion heuristica. No modifica mediciones ni valida precision clinica."
                ),
            }
        )
    return records


def _ray_hits_for_direction(
    mesh: trimesh.Trimesh,
    points: np.ndarray,
    normals: np.ndarray,
    max_depth_mm: float,
    ray_direction: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    plus = np.full(len(points), np.inf, dtype=float)
    minus = np.full(len(points), np.inf, dtype=float)
    if ray_direction in {"bidirectional", "plus_normal"}:
        plus = _first_ray_hits(mesh, points + normals * 0.02, normals, max_depth_mm=max_depth_mm)
    if ray_direction in {"bidirectional", "minus_normal"}:
        minus = _first_ray_hits(mesh, points - normals * 0.02, -normals, max_depth_mm=max_depth_mm)
    if ray_direction == "plus_normal":
        ray_valid = np.isfinite(plus)
    elif ray_direction == "minus_normal":
        ray_valid = np.isfinite(minus)
    else:
        ray_valid = np.isfinite(plus) | np.isfinite(minus)
    return ray_valid, plus, minus


def build_local_registration_diagnostic(
    sample_quality: dict[str, np.ndarray] | None,
    waxup: trimesh.Trimesh,
    arch: str,
    diagnostic_teeth: list[int] | None,
    diagnostic_zones: list[str] | None,
    neighborhood_radius_mm: float | None,
    ray_max_depth_mm: float,
    ray_direction: str,
) -> list[dict[str, Any]]:
    if not sample_quality or not diagnostic_teeth:
        return []
    try:
        from scipy.spatial import cKDTree
        from trimesh.registration import icp
    except Exception as exc:
        return [
            {
                "diagnostic_status": "failed_dependency",
                "diagnostic_error": f"{type(exc).__name__}: {exc}",
                "diagnostic_caveat": "QA local no ejecutado; no modifica medicion ni semaforo clinico.",
            }
        ]

    sample_points = np.asarray(sample_quality["points"], dtype=float)
    sample_normals = np.asarray(sample_quality["normals"], dtype=float)
    before_ray_valid = np.asarray(sample_quality["ray_valid"], dtype=bool)
    sample_teeth, sample_zones = segment_teeth_and_local_zones(sample_points, arch)
    waxup_vertices = np.asarray(waxup.vertices, dtype=float)
    waxup_teeth, waxup_zones = segment_teeth_and_local_zones(waxup_vertices, arch)
    records: list[dict[str, Any]] = []
    zone_scopes = diagnostic_zones or [None]

    for tooth in diagnostic_teeth:
        for zone in zone_scopes:
            sample_mask = sample_teeth == tooth
            waxup_mask = waxup_teeth == tooth
            if zone is not None:
                sample_mask &= sample_zones == zone
                waxup_mask &= waxup_zones == zone
            scope_sample_points = sample_points[sample_mask]
            scope_waxup_points = waxup_vertices[waxup_mask]
            if neighborhood_radius_mm is not None and len(scope_sample_points) > 0 and len(scope_waxup_points) > 0:
                sample_centroid = np.mean(scope_sample_points, axis=0)
                waxup_centroid = np.mean(scope_waxup_points, axis=0)
                sample_distances = np.linalg.norm(scope_sample_points - sample_centroid, axis=1)
                waxup_distances = np.linalg.norm(scope_waxup_points - waxup_centroid, axis=1)
                sample_scope_indices = np.flatnonzero(sample_mask)
                waxup_scope_indices = np.flatnonzero(waxup_mask)
                narrowed_sample_indices = sample_scope_indices[sample_distances <= neighborhood_radius_mm]
                narrowed_waxup_indices = waxup_scope_indices[waxup_distances <= neighborhood_radius_mm]
                sample_mask = np.zeros_like(sample_mask, dtype=bool)
                waxup_mask = np.zeros_like(waxup_mask, dtype=bool)
                sample_mask[narrowed_sample_indices] = True
                waxup_mask[narrowed_waxup_indices] = True
            local_samples = sample_points[sample_mask]
            local_normals = sample_normals[sample_mask]
            local_waxup = waxup_vertices[waxup_mask]
            scope_label = f"tooth_{tooth}_{zone}" if zone is not None else f"tooth_{tooth}_all_local_zones"
            if neighborhood_radius_mm is not None:
                scope_label = f"{scope_label}_radius_{neighborhood_radius_mm:g}mm"
            record: dict[str, Any] = {
                "Diente": int(tooth),
                "Zona local": zone or "ALL",
                "diagnostic_scope": scope_label,
                "neighborhood_radius_mm": neighborhood_radius_mm,
                "preop_sample_count": int(len(local_samples)),
                "waxup_vertex_count": int(len(local_waxup)),
                "before_ray_hit_ratio": round(float(before_ray_valid[sample_mask].mean()), 4) if np.any(sample_mask) else None,
                "diagnostic_caveat": (
                    "ICP local por diente/zona/vecindad para QA tecnico. El transform no se aplica a la medicion "
                    "principal ni habilita uso clinico."
                ),
            }
            record.update(_patch_stability_metrics(local_samples, "preop"))
            record.update(_patch_stability_metrics(local_waxup, "waxup"))
            if len(local_samples) < 3 or len(local_waxup) < 3:
                stability_status, stability_reasons = _local_patch_stability_status(record)
                record.update(
                    {
                        "diagnostic_status": "insufficient_points",
                        "patch_stability_status": stability_status,
                        "patch_stability_reasons": ",".join(stability_reasons),
                        "after_ray_hit_ratio": None,
                        "hit_ratio_delta": None,
                    }
                )
                records.append(record)
                continue

            fixed = _sample_points(local_samples)
            moving = _sample_points(local_waxup)
            try:
                matrix, transformed_moving, _ = icp(
                    moving,
                    fixed,
                    max_iterations=30,
                    threshold=1e-5,
                    scale=False,
                    reflection=False,
                )
                tree = cKDTree(fixed)
                icp_distances, _ = tree.query(transformed_moving, k=1)
                waxup_local_copy = waxup.copy()
                waxup_local_copy.apply_transform(matrix)
                after_ray_valid, after_plus, after_minus = _ray_hits_for_direction(
                    waxup_local_copy,
                    local_samples,
                    local_normals,
                    max_depth_mm=ray_max_depth_mm,
                    ray_direction=ray_direction,
                )
                before_ratio = float(before_ray_valid[sample_mask].mean())
                after_ratio = float(after_ray_valid.mean())
                rms = float(np.sqrt(np.mean(np.square(icp_distances))))
                p95 = float(np.percentile(icp_distances, 95))
                rotation_deg = _rotation_angle_degrees(matrix)
                translation_mm = float(np.linalg.norm(matrix[:3, 3]))
                record.update(
                    {
                        "diagnostic_status": "ok",
                        "local_icp_rms_mm": round(rms, 4),
                        "local_icp_p95_mm": round(p95, 4),
                        "local_icp_rotation_deg": round(rotation_deg, 4),
                        "local_icp_translation_mm": round(translation_mm, 4),
                        "after_ray_hit_ratio": round(after_ratio, 4),
                        "hit_ratio_delta": round(after_ratio - before_ratio, 4),
                        "after_plus_normal_hit_ratio": round(float(np.isfinite(after_plus).mean()), 4),
                        "after_minus_normal_hit_ratio": round(float(np.isfinite(after_minus).mean()), 4),
                        "relationship": "local_registration_improves_ray_coverage" if after_ratio > before_ratio + 0.10 else "local_registration_no_clear_coverage_gain",
                        "transform_matrix": json.dumps(_rounded_matrix(matrix), separators=(",", ":")),
                    }
                )
                stability_status, stability_reasons = _local_patch_stability_status(record)
                record.update(
                    {
                        "patch_stability_status": stability_status,
                        "patch_stability_reasons": ",".join(stability_reasons),
                        "local_transform_recommendation": (
                            "do_not_apply_local_transform"
                            if stability_status == "reject"
                            else "diagnostic_only_review_before_any_application"
                        ),
                    }
                )
            except Exception as exc:
                stability_status, stability_reasons = _local_patch_stability_status(record)
                record.update(
                    {
                        "diagnostic_status": "failed_runtime",
                        "patch_stability_status": stability_status,
                        "patch_stability_reasons": ",".join(stability_reasons),
                        "diagnostic_error": f"{type(exc).__name__}: {exc}",
                        "after_ray_hit_ratio": None,
                        "hit_ratio_delta": None,
                    }
                )
            records.append(record)
    return records


def build_local_registration_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for record in records:
        if record.get("diagnostic_status") == "failed_dependency":
            summary.append(
                {
                    "Diente": record.get("Diente"),
                    "Zona local": record.get("Zona local"),
                    "diagnostic_scope": record.get("diagnostic_scope"),
                    "patch_stability_status": "reject",
                    "candidate_status": "diagnostic_unavailable",
                    "candidate_reason": record.get("diagnostic_error"),
                    "safe_to_apply_local_transform": "no",
                    "clinical_caveat": "No habilita uso clinico; falta validacion de registro, unidades, segmentacion y repetibilidad.",
                }
            )
            continue

        stability = record.get("patch_stability_status") or "unknown"
        recommendation = record.get("local_transform_recommendation") or ""
        hit_delta = record.get("hit_ratio_delta")
        after_hit_ratio = record.get("after_ray_hit_ratio")
        p95 = record.get("local_icp_p95_mm")
        rotation = record.get("local_icp_rotation_deg")
        translation = record.get("local_icp_translation_mm")

        if stability == "reject":
            candidate_status = "reject"
            safe_to_apply = "no"
        elif stability == "review" and recommendation == "diagnostic_only_review_before_any_application":
            candidate_status = "investigate_with_repeatability"
            safe_to_apply = "no"
        elif stability == "accept":
            candidate_status = "candidate_for_repeatability_study"
            safe_to_apply = "no"
        else:
            candidate_status = "insufficient_or_unknown"
            safe_to_apply = "no"

        reasons = record.get("patch_stability_reasons") or ""
        summary.append(
            {
                "Diente": record.get("Diente"),
                "Zona local": record.get("Zona local"),
                "diagnostic_scope": record.get("diagnostic_scope"),
                "neighborhood_radius_mm": record.get("neighborhood_radius_mm"),
                "preop_sample_count": record.get("preop_sample_count"),
                "waxup_vertex_count": record.get("waxup_vertex_count"),
                "before_ray_hit_ratio": record.get("before_ray_hit_ratio"),
                "after_ray_hit_ratio": after_hit_ratio,
                "hit_ratio_delta": hit_delta,
                "local_icp_p95_mm": p95,
                "local_icp_rotation_deg": rotation,
                "local_icp_translation_mm": translation,
                "patch_stability_status": stability,
                "candidate_status": candidate_status,
                "candidate_reason": reasons,
                "safe_to_apply_local_transform": safe_to_apply,
                "clinical_caveat": "No habilita uso clinico; falta validacion de registro, unidades, segmentacion y repetibilidad.",
            }
        )
    return summary


def _write_normal_ray_samples_ply(sample_audit: pd.DataFrame, path: Path) -> None:
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(sample_audit)}",
        "property float x",
        "property float y",
        "property float z",
        "property uchar red",
        "property uchar green",
        "property uchar blue",
        "end_header",
    ]
    for row in sample_audit.itertuples(index=False):
        if bool(row.fallback_used):
            red, green, blue = 220, 55, 47
        elif bool(row.plus_hit) and bool(row.minus_hit):
            red, green, blue = 38, 139, 210
        else:
            red, green, blue = 133, 153, 0
        lines.append(f"{row.x_mm} {row.y_mm} {row.z_mm} {red} {green} {blue}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def analyze_case(
    preop_path: str | Path,
    waxup_path: str | Path,
    material: str = "demo_veneer",
    arch: str = "S",
    apply_icp: bool = False,
    icp_report_only: bool = False,
    exact_surface: bool = False,
    exact_surface_vertex_limit: int | None = DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
    landmarks_path: str | Path | None = None,
    input_unit: str = "mm",
    measurement_method: str = "fast_vertex",
    ray_sample_count: int = DEFAULT_RAY_SAMPLE_COUNT,
    ray_max_depth_mm: float = DEFAULT_RAY_MAX_DEPTH_MM,
    ray_direction: str = "bidirectional",
    local_registration_diagnostic_teeth: list[int] | None = None,
    local_registration_diagnostic_zones: list[str] | None = None,
    local_registration_neighborhood_radius_mm: float | None = None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    if material not in MATERIAL_PROFILES:
        raise ValueError(f"Unknown material profile: {material}. Available: {', '.join(MATERIAL_PROFILES)}")
    if input_unit not in UNIT_SCALE_TO_MM:
        raise ValueError(f"Unknown input unit: {input_unit}. Available: {', '.join(UNIT_SCALE_TO_MM)}")

    preop = load_mesh(preop_path)
    waxup = load_mesh(waxup_path)
    scale_to_mm = UNIT_SCALE_TO_MM[input_unit]
    if scale_to_mm != 1.0:
        preop.apply_scale(scale_to_mm)
        waxup.apply_scale(scale_to_mm)
    unit_report = assess_units([preop, waxup], input_unit=input_unit, scale_to_mm=scale_to_mm)
    if landmarks_path:
        if apply_icp or icp_report_only:
            raise ValueError("Use either manual landmarks or ICP in one run, not both.")
        reg_report = landmark_registration_report(
            preop,
            waxup,
            landmarks_path,
            input_unit=input_unit,
            landmark_scale_to_mm=scale_to_mm,
        )
    else:
        reg_report = registration_report(preop, waxup, apply_icp or icp_report_only, apply_transform=apply_icp and not icp_report_only)
    if exact_surface and measurement_method == "fast_vertex":
        measurement_method = "exact_surface"
    if measurement_method == "normal_ray":
        distances, measurement_points, distance_report = normal_ray_surface_distances(
            preop,
            waxup,
            sample_count=ray_sample_count,
            max_depth_mm=ray_max_depth_mm,
            ray_direction=ray_direction,
        )
        distance_sample_quality = distance_report.pop("_sample_quality", None)
        signed_summary = distance_report.get("signed_summary_mm")
        distance_report = {
            **distance_report,
            "notes": [
                *distance_report.get("notes", []),
                "Para BigColor PREP esta es la metrica preferente de precision porque mide clearance direccional, no vecino mas cercano.",
            ],
        }
    elif measurement_method in {"fast_vertex", "exact_surface"}:
        distance_sample_quality = None
        signed, distance_report = signed_distances(
            preop,
            waxup,
            prefer_exact_surface=measurement_method == "exact_surface",
            exact_surface_vertex_limit=exact_surface_vertex_limit,
        )
        signed_summary = {
            "min": round(float(np.min(signed)), 4),
            "p5": round(float(np.percentile(signed, 5)), 4),
            "p50": round(float(np.percentile(signed, 50)), 4),
            "p95": round(float(np.percentile(signed, 95)), 4),
            "max": round(float(np.max(signed)), 4),
            "negative_vertex_ratio": round(float(np.mean(signed < 0)), 4),
        }
        distances = np.abs(signed)
        measurement_points = np.asarray(waxup.vertices)
        distance_report = {
            **distance_report,
            "measurement": "absolute_thickness_mm",
            "signed_summary_mm": signed_summary,
            "notes": [
                *distance_report.get("notes", []),
                "Para BigColor PREP se usa espesor absoluto entre preoperatorio y encerado; el signo no se usa como decision de tallado.",
            ],
        }
    else:
        raise ValueError("measurement_method must be fast_vertex, exact_surface or normal_ray")
    teeth, zones = segment_teeth_and_zones(measurement_points, arch)
    normal_ray_zone_coverage = build_normal_ray_zone_coverage(teeth, zones, distance_sample_quality)
    normal_ray_sample_audit = build_normal_ray_sample_audit(teeth, zones, distance_sample_quality)
    normal_ray_zone_bbox_diagnostic = build_normal_ray_zone_bbox_diagnostic(teeth, zones, distance_sample_quality)
    normal_ray_mesh_zone_bbox_diagnostic = build_normal_ray_mesh_zone_bbox_diagnostic(
        teeth,
        zones,
        distance_sample_quality,
        waxup,
        arch,
    )
    normal_ray_local_zone_bbox_diagnostic = build_normal_ray_local_zone_bbox_diagnostic(
        distance_sample_quality,
        waxup,
        arch,
    )
    normal_ray_arc_axis_diagnostic = build_normal_ray_arc_axis_diagnostic(
        distance_sample_quality,
        waxup,
        arch,
    )
    local_registration_diagnostic = build_local_registration_diagnostic(
        distance_sample_quality,
        waxup,
        arch,
        local_registration_diagnostic_teeth,
        local_registration_diagnostic_zones,
        local_registration_neighborhood_radius_mm,
        ray_max_depth_mm=ray_max_depth_mm,
        ray_direction=ray_direction,
    )
    local_registration_summary = build_local_registration_summary(local_registration_diagnostic)
    table = build_zone_table(teeth, zones, distances, material, reg_report.confidence)
    if normal_ray_zone_coverage:
        coverage_df = pd.DataFrame(normal_ray_zone_coverage)
        table = table.merge(coverage_df, on=["Diente", "Zona"], how="left")
    quality_gate = build_quality_gate(unit_report, reg_report, distance_report)
    table = table.assign(
        **{
            "Distance method": distance_report.get("method"),
            "Distance confidence": distance_report.get("confidence", "not_reported"),
            "Distance fallback ratio": distance_report.get("fallback_ratio"),
            "Distance ray hit ratio": distance_report.get("ray_hit_ratio"),
            "Distance ray hits": distance_report.get("ray_hit_count"),
            "Distance fallback count": distance_report.get("fallback_count"),
            "Distance sample count requested": distance_report.get("sample_count_requested"),
            "Distance sample count used": distance_report.get("sample_count_used"),
            "Distance ray max depth mm": distance_report.get("ray_max_depth_mm"),
            "Distance ray direction": distance_report.get("ray_direction"),
            "QA gate status": quality_gate["status"],
            "QA gate blockers": ";".join(quality_gate["blockers"]),
            "QA gate warnings": ";".join(quality_gate["warnings"]),
            "Clinical use allowed": quality_gate["can_use_for_clinical_decision"],
        }
    )
    technical_sentence = table.apply(_technical_sentence_outputs, axis=1)
    table = pd.concat([table, technical_sentence], axis=1)
    table["Frase visible"] = table.apply(_visible_zone_sentence, axis=1)

    analysis = {
        "preop": str(preop_path),
        "waxup": str(waxup_path),
        "material": material,
        "material_profile": {
            key: value
            for key, value in MATERIAL_PROFILES[material].items()
            if key != "zones"
        },
        "arch": arch,
        "units": asdict(unit_report),
        "registration": asdict(reg_report),
        "distance": distance_report,
        "normal_ray_zone_coverage": normal_ray_zone_coverage,
        "normal_ray_zone_bbox_diagnostic": normal_ray_zone_bbox_diagnostic,
        "normal_ray_mesh_zone_bbox_diagnostic": normal_ray_mesh_zone_bbox_diagnostic,
        "normal_ray_local_zone_bbox_diagnostic": normal_ray_local_zone_bbox_diagnostic,
        "normal_ray_arc_axis_diagnostic": normal_ray_arc_axis_diagnostic,
        "local_registration_diagnostic": local_registration_diagnostic,
        "local_registration_summary": local_registration_summary,
        "_normal_ray_sample_audit": normal_ray_sample_audit,
        "qa_gate": quality_gate,
        "distance_summary_mm": {
            "basis": "directional_clearance" if measurement_method == "normal_ray" else "absolute_values_except_negative_vertex_ratio",
            "min": round(float(np.min(distances)), 4),
            "p5": round(float(np.percentile(distances, 5)), 4),
            "p50": round(float(np.percentile(distances, 50)), 4),
            "p95": round(float(np.percentile(distances, 95)), 4),
            "max": round(float(np.max(distances)), 4),
            "negative_vertex_ratio": signed_summary.get("negative_vertex_ratio") if signed_summary else None,
            "negative_sample_ratio": signed_summary.get("negative_sample_ratio") if signed_summary else None,
        },
        "clinical_caveat": "Demo tecnica: requiere validacion de registro, unidades, segmentacion y repetibilidad antes de uso clinico.",
    }
    return analysis, table


def write_outputs(analysis: dict[str, Any], table: pd.DataFrame, out_dir: str | Path) -> dict[str, str]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    analysis_path = out_path / "analysis.json"
    table_path = out_path / "table.csv"
    sample_audit = analysis.get("_normal_ray_sample_audit")
    export_analysis = {key: value for key, value in analysis.items() if not key.startswith("_")}
    outputs = {"analysis": str(analysis_path), "table": str(table_path)}
    zone_coverage = analysis.get("normal_ray_zone_coverage") or []
    zone_bbox_diagnostic = analysis.get("normal_ray_zone_bbox_diagnostic") or []
    mesh_zone_bbox_diagnostic = analysis.get("normal_ray_mesh_zone_bbox_diagnostic") or []
    local_zone_bbox_diagnostic = analysis.get("normal_ray_local_zone_bbox_diagnostic") or []
    arc_axis_diagnostic = analysis.get("normal_ray_arc_axis_diagnostic") or []
    local_registration_diagnostic = analysis.get("local_registration_diagnostic") or []
    local_registration_summary = analysis.get("local_registration_summary") or []
    if zone_coverage:
        coverage_path = out_path / "normal_ray_zone_coverage.csv"
        pd.DataFrame(zone_coverage).to_csv(coverage_path, index=False)
        export_analysis["normal_ray_zone_coverage_csv"] = str(coverage_path)
        outputs["normal_ray_zone_coverage_csv"] = str(coverage_path)
    if zone_bbox_diagnostic:
        bbox_path = out_path / "normal_ray_zone_bbox_diagnostic.csv"
        pd.DataFrame(zone_bbox_diagnostic).to_csv(bbox_path, index=False)
        export_analysis["normal_ray_zone_bbox_diagnostic_csv"] = str(bbox_path)
        outputs["normal_ray_zone_bbox_diagnostic_csv"] = str(bbox_path)
    if mesh_zone_bbox_diagnostic:
        mesh_bbox_path = out_path / "normal_ray_mesh_zone_bbox_diagnostic.csv"
        pd.DataFrame(mesh_zone_bbox_diagnostic).to_csv(mesh_bbox_path, index=False)
        export_analysis["normal_ray_mesh_zone_bbox_diagnostic_csv"] = str(mesh_bbox_path)
        outputs["normal_ray_mesh_zone_bbox_diagnostic_csv"] = str(mesh_bbox_path)
    if local_zone_bbox_diagnostic:
        local_bbox_path = out_path / "normal_ray_local_zone_bbox_diagnostic.csv"
        pd.DataFrame(local_zone_bbox_diagnostic).to_csv(local_bbox_path, index=False)
        export_analysis["normal_ray_local_zone_bbox_diagnostic_csv"] = str(local_bbox_path)
        outputs["normal_ray_local_zone_bbox_diagnostic_csv"] = str(local_bbox_path)
    if arc_axis_diagnostic:
        arc_axis_path = out_path / "normal_ray_arc_axis_diagnostic.csv"
        pd.DataFrame(arc_axis_diagnostic).to_csv(arc_axis_path, index=False)
        export_analysis["normal_ray_arc_axis_diagnostic_csv"] = str(arc_axis_path)
        outputs["normal_ray_arc_axis_diagnostic_csv"] = str(arc_axis_path)
    if local_registration_diagnostic:
        local_registration_path = out_path / "local_registration_diagnostic.csv"
        pd.DataFrame(local_registration_diagnostic).to_csv(local_registration_path, index=False)
        export_analysis["local_registration_diagnostic_csv"] = str(local_registration_path)
        outputs["local_registration_diagnostic_csv"] = str(local_registration_path)
    if local_registration_summary:
        local_summary_path = out_path / "local_registration_summary.csv"
        pd.DataFrame(local_registration_summary).to_csv(local_summary_path, index=False)
        export_analysis["local_registration_summary_csv"] = str(local_summary_path)
        outputs["local_registration_summary_csv"] = str(local_summary_path)
    if isinstance(sample_audit, pd.DataFrame) and not sample_audit.empty:
        sample_csv_path = out_path / "normal_ray_samples.csv"
        sample_ply_path = out_path / "normal_ray_samples.ply"
        sample_audit.to_csv(sample_csv_path, index=False)
        _write_normal_ray_samples_ply(sample_audit, sample_ply_path)
        export_analysis["normal_ray_sample_audit"] = {
            "csv": str(sample_csv_path),
            "ply": str(sample_ply_path),
            "sample_count": int(len(sample_audit)),
            "color_legend": {
                "green": "ray_hit_single_direction",
                "blue": "ray_hit_both_directions",
                "red": "closest_surface_fallback",
            },
            "caveat": "Nube de puntos QA para localizar fallos de cobertura; no cambia la medicion ni valida precision clinica.",
        }
        outputs["normal_ray_samples_csv"] = str(sample_csv_path)
        outputs["normal_ray_samples_ply"] = str(sample_ply_path)
    analysis_path.write_text(json.dumps(export_analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    table.to_csv(table_path, index=False)
    return outputs
