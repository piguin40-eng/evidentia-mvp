import json
from pathlib import Path

from connectors.folder_bridge import FolderBridge, UploadResult


MESH = b'''solid tetra
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
endsolid tetra'''


def make_case(root: Path) -> Path:
    case = root / 'Paciente visible solo localmente'
    case.mkdir(parents=True)
    (case / '.abutmentiq-case.json').write_text(json.dumps({
        'patient_name': 'Paciente Privado',
        'clinic_reference': 'CLINICA-PRIVADA-01',
        'order_reference': 'PEDIDO-001',
    }), encoding='utf-8')
    mesh = case / 'Paciente Privado superior.stl'
    mesh.write_bytes(MESH)
    return mesh


def test_bridge_waits_for_stability_uploads_pseudonymized_and_never_repeats(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    mesh = make_case(source)
    original = mesh.read_bytes()
    uploads = []

    def sender(candidate):
        uploads.append(candidate)
        return UploadResult(status_code=201, status='ENQUEUED', case_code='AIQ-SYNTHETIC')

    bridge = FolderBridge(
        source_root=source,
        state_path=tmp_path / 'private-state/bridge.json',
        platform='medit',
        connector_id='lab-medit-01',
        stable_window_seconds=30,
        sender=sender,
    )

    assert bridge.run_once(now=100.0) == []
    assert bridge.run_once(now=129.0) == []
    events = bridge.run_once(now=131.0)
    assert [event['status'] for event in events] == ['ENQUEUED']
    assert len(uploads) == 1
    assert uploads[0].patient_name == 'Paciente Privado'
    assert uploads[0].clinic_reference == 'CLINICA-PRIVADA-01'
    assert uploads[0].upload_filename == 'mesh.stl'
    assert uploads[0].source_event_id.startswith('BRIDGE-')
    assert bridge.run_once(now=200.0) == []
    assert len(uploads) == 1
    assert mesh.read_bytes() == original

    serialized_state = (tmp_path / 'private-state/bridge.json').read_text(encoding='utf-8')
    assert 'Paciente' not in serialized_state
    assert 'CLINICA' not in serialized_state
    assert str(source) not in serialized_state


def test_bridge_resets_stability_clock_when_file_changes(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    mesh = make_case(source)
    uploads = []
    bridge = FolderBridge(
        source_root=source,
        state_path=tmp_path / 'state.json',
        platform='medit',
        connector_id='lab-medit-01',
        stable_window_seconds=30,
        sender=lambda candidate: uploads.append(candidate) or UploadResult(201, 'ENQUEUED', 'AIQ-1'),
    )

    bridge.run_once(now=100.0)
    mesh.write_bytes(MESH + b'\n')
    assert bridge.run_once(now=131.0) == []
    assert bridge.run_once(now=160.0) == []
    assert bridge.run_once(now=162.0)[0]['status'] == 'ENQUEUED'
    assert len(uploads) == 1


def test_bridge_quarantines_missing_identity_and_geometry_duplicate(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir()
    orphan = source / 'orphan.ply'
    orphan.write_text('ply\nformat ascii 1.0\nelement vertex 0\nelement face 0\nend_header\n', encoding='utf-8')
    uploads = []
    bridge = FolderBridge(
        source_root=source,
        state_path=tmp_path / 'state.json',
        platform='medit',
        connector_id='lab-medit-01',
        stable_window_seconds=0,
        sender=lambda candidate: uploads.append(candidate) or UploadResult(409, 'DUPLICATE_GEOMETRY', None),
    )
    assert bridge.run_once(now=100.0)[0]['status'] == 'QUARANTINED_IDENTITY_REQUIRED'
    assert uploads == []

    identity = source / '.abutmentiq-case.json'
    identity.write_text(json.dumps({'patient_name': 'P', 'clinic_reference': 'C'}), encoding='utf-8')
    events = bridge.run_once(now=101.0)
    assert events[0]['status'] == 'QUARANTINED_DUPLICATE_GEOMETRY'
    assert bridge.run_once(now=102.0) == []
