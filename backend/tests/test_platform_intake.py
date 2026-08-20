from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.platform_intake import scan_read_only_connectors


TETRA_A = b'''solid paciente-a
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
facet normal 0 1 0
 outer loop
  vertex 0 0 0
  vertex 0 1 0
  vertex 0 0 1
 endloop
endfacet
facet normal 1 0 0
 outer loop
  vertex 0 0 0
  vertex 0 0 1
  vertex 1 0 0
 endloop
endfacet
facet normal 1 1 1
 outer loop
  vertex 1 0 0
  vertex 0 0 1
  vertex 0 1 0
 endloop
endfacet
endsolid paciente-a'''
TETRA_B = TETRA_A.replace(b'paciente-a', b'otro-nombre')


def test_read_only_connector_audits_sources_but_counts_geometry_once(tmp_path: Path):
    source = tmp_path / 'platform-export'
    source.mkdir()
    first = source / 'Paciente Uno.stl'
    second = source / 'renombrada.stl'
    first.write_bytes(TETRA_A)
    second.write_bytes(TETRA_B)
    before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (first, second)}
    log_path = tmp_path / 'platform_intake.jsonl'
    connectors = [{
        'connector_id': 'lab-export-1',
        'display_name': 'Exportación laboratorio',
        'source_root': str(source),
        'enabled': True,
        'mode': 'read_only',
    }]

    first_scan = scan_read_only_connectors(connectors, log_path=log_path, now='2026-08-20T00:00:00Z')
    second_scan = scan_read_only_connectors(connectors, log_path=log_path, now='2026-08-20T00:01:00Z')

    assert first_scan == {
        'connectors_scanned': 1,
        'new_source_events': 2,
        'new_unique_geometries': 1,
        'geometry_duplicates': 1,
        'errors': [],
    }
    assert second_scan['new_source_events'] == 0
    assert second_scan['new_unique_geometries'] == 0
    events = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines()]
    assert len(events) == 2
    assert events[0]['source_sha256'] == hashlib.sha256(TETRA_A).hexdigest()
    assert events[1]['source_sha256'] == hashlib.sha256(TETRA_B).hexdigest()
    assert events[0]['geometry_sha256'] == events[1]['geometry_sha256']
    assert events[0]['counts_as_new_training_mesh'] is True
    assert events[1]['counts_as_new_training_mesh'] is False
    assert events[1]['duplicate_reason'] == 'KNOWN_GEOMETRY'
    assert events[0]['public_case_code'].startswith('AIQ-')
    assert not events[0]['public_case_code'].endswith(events[0]['geometry_sha256'][:8].upper())
    assert 'Paciente Uno' not in events[0]['public_case_code']
    assert all('private_source_path' not in event for event in events)
    assert str(source) not in log_path.read_text(encoding='utf-8')
    after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (first, second)}
    assert after == before


def test_connector_enforces_resource_limits_before_mesh_parsing(tmp_path: Path):
    source = tmp_path / 'platform-export'
    source.mkdir()
    for index in range(3):
        (source / f'{index}.stl').write_bytes(TETRA_A)
    result = scan_read_only_connectors([{
        'connector_id': 'lab-export-1',
        'source_root': str(source),
        'enabled': True,
        'mode': 'read_only',
    }], log_path=tmp_path / 'platform_intake.jsonl', max_mesh_bytes=10, max_candidates=2)

    codes = [error['code'] for error in result['errors']]
    assert 'SCAN_CANDIDATE_LIMIT_REACHED' in codes
    assert codes.count('MESH_TOO_LARGE') == 2
    assert result['new_source_events'] == 0


def test_connector_errors_do_not_expose_source_hashes(tmp_path: Path):
    source = tmp_path / 'platform-export'
    source.mkdir()
    (source / 'invalid.stl').write_bytes(b'not-a-mesh')
    result = scan_read_only_connectors([{
        'connector_id': 'lab-export-1',
        'source_root': str(source),
        'enabled': True,
        'mode': 'read_only',
    }], log_path=tmp_path / 'platform_intake.jsonl')

    assert len(result['errors']) == 1
    assert result['errors'][0]['code'] == 'MESH_READ_ERROR'
    assert all('sha' not in key.casefold() for key in result['errors'][0])
