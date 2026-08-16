from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "material_rules" / "viewer_exported_missing_rule_fixture_2026-08-10.json"
DEFAULT_TABLE = ROOT / "outputs" / "yolito-missing-rule-export-fixture-2026-08-10" / "table.csv"

REQUIRED_COLUMNS = {
    "tooth_fdi",
    "zone_key",
    "zone_label_es",
    "measured_mm",
    "material_key",
    "profile_key",
    "required_min_mm",
    "required_ideal_mm",
    "upper_limit_mm",
    "deficit_mm",
    "color_key",
    "material_zone_join_status",
    "source_trace_token",
    "technical_action_es",
    "caveat_es",
    "viewer_sentence_es",
}


def _fail(message: str) -> None:
    raise SystemExit(f"QA_MISSING_MATERIAL_ZONE_CONTRACT_FAIL: {message}")


def _load_fixture(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixture = (
        data.get("export_fixture")
        or data.get("viewer_exported_missing_rule_fixture_2026_08_10")
        or data.get("viewer_missing_material_zone_rule_fixture_2026_08_09")
    )
    if not fixture:
        _fail(f"{path} no contiene fixture de regla material/zona ausente")
    rows = fixture.get("row_examples") or fixture.get("fixture_rows") or fixture.get("rows") or []
    if len(rows) < 2:
        _fail("El fixture debe contener al menos dos filas bloqueadas")
    return rows


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            _fail(f"table.csv no exporta columnas obligatorias: {missing}")
        rows = list(reader)
    if len(rows) < 2:
        _fail("table.csv debe contener al menos dos filas bloqueadas")
    return rows


def _check_blocked_row(row: dict[str, str], row_id: str) -> None:
    for field in ("required_min_mm", "required_ideal_mm", "upper_limit_mm", "deficit_mm"):
        if row.get(field):
            _fail(f"{row_id}: {field} debe quedar vacio si falta la regla exacta")
    if row.get("color_key") != "gray":
        _fail(f"{row_id}: color_key debe ser gray")
    if row.get("material_zone_join_status") != "missing_material_profile_zone_matrix_row":
        _fail(f"{row_id}: material_zone_join_status debe bloquear por fila material/perfil/zona ausente")
    if row.get("source_trace_token") != "blocked_missing_material_zone_rule":
        _fail(f"{row_id}: source_trace_token debe ser blocked_missing_material_zone_rule")
    sentence = row.get("viewer_sentence_es") or ""
    if "requerido pendiente de regla material/zona" not in sentence:
        _fail(f"{row_id}: viewer_sentence_es debe explicar requerido pendiente")
    if "sin deficit clinico calculable" not in sentence:
        _fail(f"{row_id}: viewer_sentence_es no debe exponer deficit clinico")


def main() -> None:
    parser = argparse.ArgumentParser(description="QA for exported missing material-zone rule rows.")
    parser.add_argument("--fixture", default=DEFAULT_FIXTURE, type=Path)
    parser.add_argument("--table", default=DEFAULT_TABLE, type=Path)
    args = parser.parse_args()

    _load_fixture(args.fixture)
    rows = _load_csv(args.table)
    for index, row in enumerate(rows, start=1):
        row_id = f"fila {index} diente {row.get('tooth_fdi', '?')} zona {row.get('zone_key', '?')}"
        _check_blocked_row(row, row_id)

    print("QA_MISSING_MATERIAL_ZONE_CONTRACT_OK")
    print(f"fixture={args.fixture}")
    print(f"table={args.table}")


if __name__ == "__main__":
    main()
