from __future__ import annotations

import argparse
import csv
from pathlib import Path

from prep_engine import (
    DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
    DEFAULT_RAY_MAX_DEPTH_MM,
    DEFAULT_RAY_SAMPLE_COUNT,
    MATERIAL_PROFILES,
    NORMAL_RAY_DIRECTIONS,
    UNIT_SCALE_TO_MM,
    analyze_case,
    write_outputs,
)


LOCAL_RANKING_NUMERIC_COLUMNS = {
    "neighborhood_radius_mm",
    "before_ray_hit_ratio",
    "after_ray_hit_ratio",
    "hit_ratio_delta",
    "local_icp_p95_mm",
    "local_icp_rotation_deg",
    "local_icp_translation_mm",
}


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _format_float(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _load_local_ranking_summary(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows: list[dict[str, object]] = []
        for row in csv.DictReader(handle):
            parsed: dict[str, object] = dict(row)
            for column in LOCAL_RANKING_NUMERIC_COLUMNS:
                parsed[column] = _parse_float(row.get(column))
            rows.append(parsed)
    return rows


def _reason_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        raw = str(row.get("candidate_reason") or "")
        for reason in [part.strip() for part in raw.split(",") if part.strip()]:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _sorted_local_ranking_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    def key(row: dict[str, object]) -> tuple[float, float, float, float, int, str]:
        p95 = row.get("local_icp_p95_mm")
        rotation = row.get("local_icp_rotation_deg")
        translation = row.get("local_icp_translation_mm")
        after = row.get("after_ray_hit_ratio")
        samples = row.get("preop_sample_count")
        try:
            sample_count = int(str(samples))
        except ValueError:
            sample_count = 0
        return (
            float(p95) if isinstance(p95, float) else 999999.0,
            -(float(after) if isinstance(after, float) else -1.0),
            float(rotation) if isinstance(rotation, float) else 999999.0,
            float(translation) if isinstance(translation, float) else 999999.0,
            -sample_count,
            str(row.get("run") or ""),
        )

    return sorted(rows, key=key)


def build_local_ranking_markdown(rows: list[dict[str, object]], source: Path, top: int) -> str:
    total = len(rows)
    status_counts: dict[str, int] = {}
    safe_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("candidate_status") or "unknown")
        safe = str(row.get("safe_to_apply_local_transform") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        safe_counts[safe] = safe_counts.get(safe, 0) + 1

    sorted_rows = _sorted_local_ranking_rows(rows)
    best = sorted_rows[0] if sorted_rows else {}
    reasons = _reason_counts(rows)
    top = max(1, top)

    lines = [
        "# BigColor PREP 2 - Local ICP Ranking QA Panel",
        "",
        "## Scope",
        "",
        f"- Source CSV: `{source}`",
        f"- Rows evaluated: {total}",
        "- Purpose: QA ranking only. Local ICP transforms remain non-applied to the main measurement.",
        "- Clinical caveat: this artifact does not validate clinical precision or authorize clinical use.",
        "",
        "## Gate",
        "",
        f"- Candidate status counts: {status_counts}",
        f"- Safe-to-apply counts: {safe_counts}",
    ]
    if best:
        lines.extend(
            [
                (
                    "- Best numeric patch: "
                    f"tooth {best.get('Diente')} {best.get('Zona local')} "
                    f"radius {_format_float(best.get('neighborhood_radius_mm') if isinstance(best.get('neighborhood_radius_mm'), float) else None, 1)} mm, "
                    f"P95 {_format_float(best.get('local_icp_p95_mm') if isinstance(best.get('local_icp_p95_mm'), float) else None)} mm, "
                    f"rotation {_format_float(best.get('local_icp_rotation_deg') if isinstance(best.get('local_icp_rotation_deg'), float) else None, 2)} deg, "
                    f"translation {_format_float(best.get('local_icp_translation_mm') if isinstance(best.get('local_icp_translation_mm'), float) else None)} mm, "
                    f"status {best.get('candidate_status')}, safe_to_apply {best.get('safe_to_apply_local_transform')}."
                )
            ]
        )
    lines.extend(["", "## Main Rejection Reasons", ""])
    for reason, count in list(reasons.items())[:12]:
        lines.append(f"- {reason}: {count}")

    lines.extend(
        [
            "",
            f"## Top {min(top, len(sorted_rows))} Patches By Lowest P95",
            "",
            "| Rank | Run | Tooth | Zone | Radius mm | Status | P95 mm | Rotation deg | Translation mm | Before hit | After hit | Safe | Reason |",
            "| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for rank, row in enumerate(sorted_rows[:top], start=1):
        radius = row.get("neighborhood_radius_mm")
        p95 = row.get("local_icp_p95_mm")
        rotation = row.get("local_icp_rotation_deg")
        translation = row.get("local_icp_translation_mm")
        before = row.get("before_ray_hit_ratio")
        after = row.get("after_ray_hit_ratio")
        reason = str(row.get("candidate_reason") or "").replace("|", "/")
        lines.append(
            "| "
            f"{rank} | {row.get('run')} | {row.get('Diente')} | {row.get('Zona local')} | "
            f"{_format_float(radius if isinstance(radius, float) else None, 1)} | "
            f"{row.get('candidate_status')} | "
            f"{_format_float(p95 if isinstance(p95, float) else None)} | "
            f"{_format_float(rotation if isinstance(rotation, float) else None, 2)} | "
            f"{_format_float(translation if isinstance(translation, float) else None)} | "
            f"{_format_float(before if isinstance(before, float) else None, 4)} | "
            f"{_format_float(after if isinstance(after, float) else None, 4)} | "
            f"{row.get('safe_to_apply_local_transform')} | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Keep `safe_to_apply_local_transform=no` for this ranking.",
            "- Use the panel to discard unstable tooth/zone/radius patches before any repeatability study.",
            "- Do not feed local ICP transforms back into the clinical measurement pipeline until repeated scans meet explicit thresholds.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prep_cli", description="BigColor PREP 2 technical analysis CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze preop and wax-up STL thickness")
    analyze.add_argument("--preop", required=True, help="Path to preoperative STL")
    analyze.add_argument("--waxup", required=True, help="Path to wax-up STL")
    analyze.add_argument("--material", default="demo_veneer", choices=sorted(MATERIAL_PROFILES))
    analyze.add_argument("--arch", default="S", choices=["S", "I"], help="S=superior, I=inferior")
    analyze.add_argument(
        "--input-unit",
        default="mm",
        choices=sorted(UNIT_SCALE_TO_MM),
        help="Unit used by STL coordinates; meshes and landmarks are converted to mm before analysis",
    )
    analyze.add_argument("--out", default="outputs/latest", help="Output directory")
    icp_group = analyze.add_mutually_exclusive_group()
    icp_group.add_argument("--icp", action="store_true", help="Apply experimental global ICP before measuring")
    icp_group.add_argument(
        "--icp-report-only",
        action="store_true",
        help="Run ICP QA and export transform metrics without applying it to the measurement mesh",
    )
    icp_group.add_argument(
        "--landmarks",
        help="JSON with paired manual landmarks; applies rigid transform before measuring",
    )
    analyze.add_argument("--exact-surface", action="store_true", help="Use exact trimesh surface signed distance; can be slow on dense STL")
    analyze.add_argument(
        "--measurement-method",
        default="fast_vertex",
        choices=["fast_vertex", "exact_surface", "normal_ray"],
        help="Distance/clearance method. normal_ray is the precision-oriented directional clearance mode.",
    )
    analyze.add_argument(
        "--ray-sample-count",
        type=int,
        default=DEFAULT_RAY_SAMPLE_COUNT,
        help="Maximum deterministic preop face-centroid samples for --measurement-method normal_ray. Use 0 for all faces.",
    )
    analyze.add_argument(
        "--ray-max-depth-mm",
        type=float,
        default=DEFAULT_RAY_MAX_DEPTH_MM,
        help="Maximum ray depth in mm for --measurement-method normal_ray.",
    )
    analyze.add_argument(
        "--ray-direction",
        default="bidirectional",
        choices=NORMAL_RAY_DIRECTIONS,
        help="Diagnostic ray direction for --measurement-method normal_ray.",
    )
    analyze.add_argument(
        "--local-registration-diagnostic-tooth",
        type=int,
        action="append",
        default=[],
        help=(
            "Run non-applied local ICP QA for one tooth and export local_registration_diagnostic.csv. "
            "Repeat for multiple teeth. Requires --measurement-method normal_ray."
        ),
    )
    analyze.add_argument(
        "--local-registration-diagnostic-zone",
        choices=["Cervical", "Medio", "Incisal"],
        action="append",
        default=[],
        help=(
            "Limit non-applied local ICP QA to one local tooth zone. Repeat for multiple zones. "
            "Requires --local-registration-diagnostic-tooth and --measurement-method normal_ray."
        ),
    )
    analyze.add_argument(
        "--local-registration-neighborhood-radius-mm",
        type=float,
        default=None,
        help=(
            "Optional radius in mm to narrow non-applied local ICP QA around the tooth/zone centroid. "
            "Requires --local-registration-diagnostic-tooth and --measurement-method normal_ray."
        ),
    )
    analyze.add_argument(
        "--exact-surface-max-vertices",
        type=int,
        default=DEFAULT_EXACT_SURFACE_VERTEX_LIMIT,
        help=(
            "Maximum combined preop+waxup vertices allowed for --exact-surface before falling back "
            "to the fast signed vertex method. Use 0 to disable the guardrail."
        ),
    )

    ranking = sub.add_parser(
        "local-ranking-report",
        help="Convert a consolidated local ICP ranking CSV into a readable QA markdown panel",
    )
    ranking.add_argument("--summary", required=True, help="Path to consolidated local registration summary CSV")
    ranking.add_argument("--out", required=True, help="Output markdown path")
    ranking.add_argument("--top", type=int, default=15, help="Number of lowest-P95 rows to show")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "analyze":
        if args.exact_surface_max_vertices < 0:
            parser.error("--exact-surface-max-vertices must be >= 0")
        if args.ray_sample_count < 0:
            parser.error("--ray-sample-count must be >= 0")
        if args.ray_max_depth_mm <= 0:
            parser.error("--ray-max-depth-mm must be > 0")
        if args.local_registration_diagnostic_tooth and args.measurement_method != "normal_ray":
            parser.error("--local-registration-diagnostic-tooth requires --measurement-method normal_ray")
        if args.local_registration_diagnostic_zone and not args.local_registration_diagnostic_tooth:
            parser.error("--local-registration-diagnostic-zone requires --local-registration-diagnostic-tooth")
        if args.local_registration_neighborhood_radius_mm is not None:
            if args.local_registration_neighborhood_radius_mm <= 0:
                parser.error("--local-registration-neighborhood-radius-mm must be > 0")
            if not args.local_registration_diagnostic_tooth:
                parser.error("--local-registration-neighborhood-radius-mm requires --local-registration-diagnostic-tooth")
        analysis, table = analyze_case(
            preop_path=Path(args.preop),
            waxup_path=Path(args.waxup),
            material=args.material,
            arch=args.arch,
            apply_icp=args.icp,
            icp_report_only=args.icp_report_only,
            exact_surface=args.exact_surface,
            exact_surface_vertex_limit=None if args.exact_surface_max_vertices == 0 else args.exact_surface_max_vertices,
            landmarks_path=Path(args.landmarks) if args.landmarks else None,
            input_unit=args.input_unit,
            measurement_method="exact_surface" if args.exact_surface else args.measurement_method,
            ray_sample_count=args.ray_sample_count,
            ray_max_depth_mm=args.ray_max_depth_mm,
            ray_direction=args.ray_direction,
            local_registration_diagnostic_teeth=args.local_registration_diagnostic_tooth,
            local_registration_diagnostic_zones=args.local_registration_diagnostic_zone,
            local_registration_neighborhood_radius_mm=args.local_registration_neighborhood_radius_mm,
        )
        outputs = write_outputs(analysis, table, args.out)
        print(f"analysis={outputs['analysis']}")
        print(f"table={outputs['table']}")
        if "normal_ray_zone_coverage_csv" in outputs:
            print(f"normal_ray_zone_coverage_csv={outputs['normal_ray_zone_coverage_csv']}")
        if "normal_ray_zone_bbox_diagnostic_csv" in outputs:
            print(f"normal_ray_zone_bbox_diagnostic_csv={outputs['normal_ray_zone_bbox_diagnostic_csv']}")
        if "normal_ray_mesh_zone_bbox_diagnostic_csv" in outputs:
            print(f"normal_ray_mesh_zone_bbox_diagnostic_csv={outputs['normal_ray_mesh_zone_bbox_diagnostic_csv']}")
        if "normal_ray_local_zone_bbox_diagnostic_csv" in outputs:
            print(f"normal_ray_local_zone_bbox_diagnostic_csv={outputs['normal_ray_local_zone_bbox_diagnostic_csv']}")
        if "normal_ray_arc_axis_diagnostic_csv" in outputs:
            print(f"normal_ray_arc_axis_diagnostic_csv={outputs['normal_ray_arc_axis_diagnostic_csv']}")
        if "local_registration_diagnostic_csv" in outputs:
            print(f"local_registration_diagnostic_csv={outputs['local_registration_diagnostic_csv']}")
        if "local_registration_summary_csv" in outputs:
            print(f"local_registration_summary_csv={outputs['local_registration_summary_csv']}")
        if "normal_ray_samples_csv" in outputs:
            print(f"normal_ray_samples_csv={outputs['normal_ray_samples_csv']}")
        if "normal_ray_samples_ply" in outputs:
            print(f"normal_ray_samples_ply={outputs['normal_ray_samples_ply']}")
        print(f"confidence={analysis['registration']['confidence']}")
        print(f"distance_confidence={analysis['distance'].get('confidence', 'not_reported')}")
        print(f"registration_method={analysis['registration']['method']}")
        print(f"distance_method={analysis['distance']['method']}")
        print(f"measurement={analysis['distance']['measurement']}")
        if "ray_direction" in analysis["distance"]:
            print(f"ray_direction={analysis['distance']['ray_direction']}")
        print(f"input_unit={analysis['units']['input_unit']} scale_to_mm={analysis['units']['scale_to_mm']}")
        print(f"qa_gate={analysis['qa_gate']['status']}")
        if analysis["qa_gate"]["blockers"]:
            print(f"qa_blockers={','.join(analysis['qa_gate']['blockers'])}")
    elif args.command == "local-ranking-report":
        summary_path = Path(args.summary)
        out_path = Path(args.out)
        rows = _load_local_ranking_summary(summary_path)
        if not rows:
            parser.error("--summary contains no rows")
        markdown = build_local_ranking_markdown(rows, summary_path, args.top)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        safe_yes = sum(1 for row in rows if str(row.get("safe_to_apply_local_transform") or "") == "yes")
        candidates = sum(1 for row in rows if str(row.get("candidate_status") or "").startswith("candidate"))
        rejects = sum(1 for row in rows if str(row.get("candidate_status") or "") == "reject")
        print(f"local_ranking_report={out_path}")
        print(f"rows={len(rows)} rejects={rejects} candidates={candidates} safe_to_apply_yes={safe_yes}")


if __name__ == "__main__":
    main()
