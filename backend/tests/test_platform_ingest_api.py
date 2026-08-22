import hashlib
import json
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

import backend.app as app_module
from backend.app import create_app
from backend.identity_vault import load_private_identity


ROOT = Path(__file__).resolve().parents[2]
TRAIN_RUN = ROOT / 'deploy_assets'
KNOWLEDGE_DB = TRAIN_RUN / 'knowledge.db'

TETRAHEDRON = b'''solid tetra
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

IDENTITY_KEY = Fernet.generate_key().decode('ascii')


def build_app(tmp_path: Path, **kwargs):
    return create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
        daily_state_path=tmp_path / 'state.json',
        daily_outgoing_root=tmp_path / 'queue',
        daily_history_path=tmp_path / 'history.json',
        platform_ingest_token='test-secret-token',
        identity_encryption_key=IDENTITY_KEY,
        **kwargs,
    )


def test_platform_mesh_ingest_is_authenticated_pseudonymized_and_idempotent(tmp_path: Path) -> None:
    app = build_app(tmp_path)
    request = {
        'data': {
            'platform': 'medit',
            'connector_id': 'lab-medit-01',
            'source_event_id': 'medit-case-0001',
            'patient_name': 'Paciente Apellidos',
            'clinic_reference': 'CLINICA-BILBAO-01',
            'order_reference': 'PEDIDO-2026-0001',
        },
        'files': {'mesh': ('Paciente Apellidos 123.stl', TETRAHEDRON, 'model/stl')},
    }

    with TestClient(app) as client:
        unauthenticated = client.post('/api/platform-intake/mesh', **request)
        first = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            **request,
        )
        repeated = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            **request,
        )
        conflicting_event = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={**request['data'], 'source_event_id': 'medit-case-0002'},
            files=request['files'],
        )
        conflicting_identity = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={
                **request['data'],
                'source_event_id': 'medit-case-other-person',
                'patient_name': 'Otra Persona',
                'clinic_reference': 'OTRA-CLINICA',
                'order_reference': 'OTRO-PEDIDO',
            },
            files=request['files'],
        )
        renamed_geometry = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={**request['data'], 'source_event_id': 'medit-case-renamed-copy'},
            files={'mesh': ('paciente-renombrado.stl', TETRAHEDRON.replace(b'solid tetra', b'solid renamed').replace(b'endsolid tetra', b'endsolid renamed'), 'model/stl')},
        )
        case_code = first.json()['case']['case_code']
        identity_endpoint = client.get(f'/api/private/cases/{case_code}/identity')
        queue = client.get('/api/review-queue')

    assert unauthenticated.status_code == 401
    assert first.status_code == 201
    assert first.json()['status'] == 'ENQUEUED'
    assert first.json()['case']['daily_total'] == 0
    assert first.json()['case']['review_status'] == 'AWAITING_HUMAN_REVIEW'
    assert repeated.status_code == 200
    assert repeated.json()['status'] == 'ALREADY_ENQUEUED'
    assert repeated.json()['case']['case_code'] == first.json()['case']['case_code']
    assert conflicting_event.status_code == 409
    assert conflicting_event.json()['detail']['code'] == 'SOURCE_IDENTITY_CONFLICT'
    assert conflicting_identity.status_code == 409
    assert conflicting_identity.json()['detail']['code'] == 'SOURCE_IDENTITY_CONFLICT'
    assert 'Otra Persona' not in json.dumps(conflicting_identity.json(), ensure_ascii=False)
    assert renamed_geometry.status_code == 409
    assert renamed_geometry.json()['detail']['code'] == 'DUPLICATE_GEOMETRY'
    assert len(queue.json()['cases']) == 1
    assert queue.json()['cases'][0]['case_code'] == first.json()['case']['case_code']
    assert 'source_mesh_sha256' not in queue.json()['cases'][0]
    assert identity_endpoint.status_code == 404
    private_identity = load_private_identity(
        path=tmp_path / 'runtime/private_identities.jsonl',
        encryption_key=IDENTITY_KEY,
        case_code=case_code,
    )
    assert private_identity is not None
    assert private_identity['patient_name'] == 'Paciente Apellidos'
    assert private_identity['clinic_reference'] == 'CLINICA-BILBAO-01'
    assert private_identity['order_reference'] == 'PEDIDO-2026-0001'
    assert private_identity['source_event_id'] == 'medit-case-0001'

    state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
    assert len(state['prepared']) == 1
    assert case_code != f"AIQ-{state['prepared'][0]['geometry_sha256'][:12].upper()}"
    serialized = json.dumps(state, ensure_ascii=False)
    assert 'Paciente' not in serialized
    assert 'Apellidos' not in serialized
    assert not any('Paciente' in path.name for path in (tmp_path / 'queue').rglob('*'))
    private_vault = (tmp_path / 'runtime/private_identities.jsonl').read_text(encoding='utf-8')
    assert 'Paciente' not in private_vault
    assert 'Apellidos' not in private_vault
    assert 'CLINICA-BILBAO-01' not in private_vault


def test_render_queue_stages_and_promotes_next_mesh_without_local_script(tmp_path: Path) -> None:
    app = build_app(tmp_path)
    first_request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'generic', 'connector_id': 'render-intake',
            'source_event_id': 'render-event-1', 'patient_name': 'Seed One',
            'clinic_reference': 'VALIDATED-SEED', 'order_reference': 'SEED-1',
        },
        'files': {'mesh': ('first.stl', TETRAHEDRON, 'model/stl')},
    }
    second_mesh = TETRAHEDRON.replace(b'vertex 1 0 0', b'vertex 2 0 0')
    second_request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'generic', 'connector_id': 'render-intake',
            'source_event_id': 'render-event-2', 'patient_name': 'Seed Two',
            'clinic_reference': 'VALIDATED-SEED', 'order_reference': 'SEED-2',
        },
        'files': {'mesh': ('second.stl', second_mesh, 'model/stl')},
    }

    with TestClient(app) as client:
        first = client.post('/api/platform-intake/mesh', **first_request)
        second = client.post('/api/platform-intake/mesh', **second_request)
        before = client.get('/api/review-queue')
        state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
        state['prepared'][0]['review_status'] = 'COMPLETED'
        (tmp_path / 'state.json').write_text(json.dumps(state), encoding='utf-8')
        advanced = client.post('/api/review-queue/next')
        after = client.get('/api/review-queue')

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()['status'] == 'STAGED_PENDING'
    assert [item['case_code'] for item in before.json()['cases']] == [first.json()['case']['case_code']]
    assert advanced.status_code == 201
    assert advanced.json()['case']['case_code'] == second.json()['case']['case_code']
    assert after.json()['cases'][-1]['case_code'] == second.json()['case']['case_code']

    persisted = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
    assert [item['queue_visibility'] for item in persisted['prepared']] == ['ACTIVE', 'ACTIVE']
    with TestClient(build_app(tmp_path)) as restarted_client:
        restarted = restarted_client.get('/api/review-queue')
    assert restarted.json()['cases'][-1]['case_code'] == second.json()['case']['case_code']


def test_new_ingest_stays_pending_while_an_earlier_pending_mesh_exists(tmp_path: Path) -> None:
    app = build_app(tmp_path)

    def ingest(client: TestClient, event_id: str, mesh: bytes):
        return client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={
                'platform': 'generic', 'connector_id': 'render-intake',
                'source_event_id': event_id, 'patient_name': event_id,
                'clinic_reference': 'VALIDATED-SEED', 'order_reference': event_id,
            },
            files={'mesh': (f'{event_id}.stl', mesh, 'model/stl')},
        )

    with TestClient(app) as client:
        first = ingest(client, 'ordered-1', TETRAHEDRON)
        second = ingest(client, 'ordered-2', TETRAHEDRON.replace(b'vertex 1 0 0', b'vertex 2 0 0'))
        state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
        state['prepared'][0]['review_status'] = 'COMPLETED'
        (tmp_path / 'state.json').write_text(json.dumps(state), encoding='utf-8')
        third = ingest(client, 'ordered-3', TETRAHEDRON.replace(b'vertex 0 1 0', b'vertex 0 2 0'))
        visible = client.get('/api/review-queue')

    assert first.json()['status'] == 'ENQUEUED'
    assert second.json()['status'] == 'STAGED_PENDING'
    assert third.json()['status'] == 'STAGED_PENDING'
    assert [item['case_code'] for item in visible.json()['cases']] == [first.json()['case']['case_code']]


def test_ingest_after_completion_waits_for_explicit_next_action(tmp_path: Path) -> None:
    app = build_app(tmp_path)

    def ingest(client: TestClient, event_id: str, mesh: bytes):
        return client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={
                'platform': 'generic', 'connector_id': 'render-intake',
                'source_event_id': event_id, 'patient_name': event_id,
                'clinic_reference': 'VALIDATED-SEED', 'order_reference': event_id,
            },
            files={'mesh': (f'{event_id}.stl', mesh, 'model/stl')},
        )

    with TestClient(app) as client:
        first = ingest(client, 'completed-first', TETRAHEDRON)
        state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
        state['prepared'][0]['review_status'] = 'COMPLETED'
        (tmp_path / 'state.json').write_text(json.dumps(state), encoding='utf-8')
        second = ingest(client, 'arrived-after-completion', TETRAHEDRON.replace(b'vertex 1 0 0', b'vertex 2 0 0'))
        before = client.get('/api/review-queue')
        advanced = client.post('/api/review-queue/next')

    assert first.json()['status'] == 'ENQUEUED'
    assert second.json()['status'] == 'STAGED_PENDING'
    assert [item['case_code'] for item in before.json()['cases']] == [first.json()['case']['case_code']]
    assert advanced.status_code == 201
    assert advanced.json()['case']['case_code'] == second.json()['case']['case_code']


def test_queue_promotion_repairs_history_first_partial_write_on_retry(tmp_path: Path) -> None:
    armed = False
    failed_once = False

    def fail_state_once(path):
        nonlocal failed_once
        if armed and Path(path).name == 'state.json' and not failed_once:
            failed_once = True
            raise OSError('injected state failure after history promotion')

    app = build_app(tmp_path, before_json_write=fail_state_once)

    def ingest(client: TestClient, event_id: str, mesh: bytes):
        return client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer test-secret-token'},
            data={
                'platform': 'generic', 'connector_id': 'render-intake',
                'source_event_id': event_id, 'patient_name': event_id,
                'clinic_reference': 'VALIDATED-SEED', 'order_reference': event_id,
            },
            files={'mesh': (f'{event_id}.stl', mesh, 'model/stl')},
        )

    with TestClient(app) as client:
        first = ingest(client, 'promotion-recovery-1', TETRAHEDRON)
        second = ingest(client, 'promotion-recovery-2', TETRAHEDRON.replace(b'vertex 1 0 0', b'vertex 2 0 0'))
        for path in (tmp_path / 'state.json', tmp_path / 'history.json'):
            payload = json.loads(path.read_text(encoding='utf-8'))
            payload['prepared'][0]['review_status'] = 'COMPLETED'
            path.write_text(json.dumps(payload), encoding='utf-8')
        armed = True
        failed = client.post('/api/review-queue/next')
        repaired = client.post('/api/review-queue/next')

    assert first.json()['status'] == 'ENQUEUED'
    assert second.json()['status'] == 'STAGED_PENDING'
    assert failed.status_code == 503
    assert repaired.status_code == 201
    state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
    history = json.loads((tmp_path / 'history.json').read_text(encoding='utf-8'))
    assert state['prepared'][1]['queue_visibility'] == 'ACTIVE'
    assert history['prepared'][1]['queue_visibility'] == 'ACTIVE'
    assert state['prepared'][1]['promoted_at'] == history['prepared'][1]['promoted_at']


def test_platform_ingest_fails_closed_without_configured_token(tmp_path: Path) -> None:
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
        daily_state_path=tmp_path / 'state.json',
        daily_outgoing_root=tmp_path / 'queue',
    )
    with TestClient(app) as client:
        response = client.post(
            '/api/platform-intake/mesh',
            headers={'Authorization': 'Bearer anything'},
            data={'platform': 'medit', 'connector_id': 'lab-medit-01'},
            files={'mesh': ('mesh.stl', TETRAHEDRON, 'model/stl')},
        )
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'PLATFORM_INGEST_NOT_CONFIGURED'


def test_idempotent_retry_repairs_partial_multiartifact_ingest(tmp_path: Path) -> None:
    failed_once = False

    def fail_history_once(path):
        nonlocal failed_once
        if Path(path).name == 'history.json' and not failed_once:
            failed_once = True
            raise OSError('injected history failure')
    request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'medit', 'connector_id': 'lab-medit-01',
            'source_event_id': 'event-recovery-1', 'patient_name': 'Paciente Sintético',
            'clinic_reference': 'CLINICA-SYNTHETIC', 'order_reference': 'ORDER-SYNTHETIC',
        },
        'files': {'mesh': ('mesh.stl', TETRAHEDRON, 'model/stl')},
    }
    with TestClient(build_app(tmp_path, before_json_write=fail_history_once), raise_server_exceptions=False) as client:
        first = client.post('/api/platform-intake/mesh', **request)
    with TestClient(build_app(tmp_path, before_json_write=fail_history_once)) as client:
        retry = client.post('/api/platform-intake/mesh', **request)

    assert first.status_code == 500
    assert retry.status_code == 200
    assert retry.json()['status'] == 'ALREADY_ENQUEUED'
    case_code = retry.json()['case']['case_code']
    history = json.loads((tmp_path / 'history.json').read_text(encoding='utf-8'))
    assert [item['case_code'] for item in history['prepared']] == [case_code]
    events = [json.loads(line) for line in (tmp_path / 'runtime/platform_intake.jsonl').read_text().splitlines()]
    assert [item['case_code'] for item in events if item['event_type'] == 'AUTHENTICATED_PLATFORM_INGEST'] == [case_code]
    assert len(list((tmp_path / 'queue').rglob('*.stl'))) == 1


def test_source_event_is_required_and_cannot_be_reused_with_other_content(tmp_path: Path) -> None:
    request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'medit', 'connector_id': 'lab-medit-01',
            'source_event_id': 'event-unique-1', 'patient_name': 'Paciente Sintético',
            'clinic_reference': 'CLINICA-SYNTHETIC', 'order_reference': 'ORDER-SYNTHETIC',
        },
        'files': {'mesh': ('mesh.stl', TETRAHEDRON, 'model/stl')},
    }
    with TestClient(build_app(tmp_path)) as client:
        first = client.post('/api/platform-intake/mesh', **request)
        conflict = client.post('/api/platform-intake/mesh', **{
            **request, 'files': {'mesh': ('mesh.stl', TETRAHEDRON + b'\n', 'model/stl')},
        })
        blank = client.post('/api/platform-intake/mesh', **{
            **request, 'data': {**request['data'], 'source_event_id': '   '},
        })
    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()['detail']['code'] == 'SOURCE_EVENT_CONFLICT'
    assert blank.status_code == 422
    assert blank.json()['detail']['code'] == 'SOURCE_EVENT_REQUIRED'


def test_retry_after_prestate_failure_reuses_prepared_case_and_artifacts(tmp_path: Path) -> None:
    failed_once = False

    def fail_state_once(path):
        nonlocal failed_once
        if Path(path).name == 'state.json' and not failed_once:
            failed_once = True
            raise OSError('injected pre-state failure')

    request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'medit', 'connector_id': 'lab-medit-01',
            'source_event_id': 'event-prestate-1', 'patient_name': 'Paciente Sintético',
            'clinic_reference': 'CLINICA-SYNTHETIC', 'order_reference': 'ORDER-SYNTHETIC',
        },
        'files': {'mesh': ('mesh.stl', TETRAHEDRON, 'model/stl')},
    }
    with TestClient(build_app(tmp_path, before_json_write=fail_state_once), raise_server_exceptions=False) as client:
        first = client.post('/api/platform-intake/mesh', **request)
    with TestClient(build_app(tmp_path, before_json_write=fail_state_once)) as client:
        retry = client.post('/api/platform-intake/mesh', **request)
    assert first.status_code == 500
    assert retry.status_code == 201
    assert len(list((tmp_path / 'queue').glob('*/mesh.*'))) == 1
    identities = [line for line in (tmp_path / 'runtime/private_identities.jsonl').read_text().splitlines() if line]
    operations = [line for line in (tmp_path / 'runtime/ingest_operations.jsonl').read_text().splitlines() if line]
    assert len(identities) == 1
    assert len(operations) == 1


def test_identity_commitment_blocks_takeover_after_vault_crash(tmp_path: Path, monkeypatch) -> None:
    request = {
        'headers': {'Authorization': 'Bearer test-secret-token'},
        'data': {
            'platform': 'medit', 'connector_id': 'lab-medit-01',
            'source_event_id': 'event-takeover-1', 'patient_name': 'Paciente Original',
            'clinic_reference': 'CLINICA-ORIGINAL', 'order_reference': 'ORDER-1',
        },
        'files': {'mesh': ('mesh.stl', TETRAHEDRON, 'model/stl')},
    }
    original_store = app_module.store_private_identity

    def crash_before_identity(**_kwargs):
        raise OSError('injected vault failure')

    monkeypatch.setattr(app_module, 'store_private_identity', crash_before_identity)
    with TestClient(build_app(tmp_path), raise_server_exceptions=False) as client:
        first = client.post('/api/platform-intake/mesh', **request)
    monkeypatch.setattr(app_module, 'store_private_identity', original_store)
    attacker = {
        **request,
        'data': {
            **request['data'], 'patient_name': 'Paciente Distinto',
            'clinic_reference': 'CLINICA-DISTINTA',
        },
    }
    with TestClient(build_app(tmp_path)) as client:
        retry = client.post('/api/platform-intake/mesh', **attacker)
    assert first.status_code == 500
    assert retry.status_code == 409
    assert retry.json()['detail']['code'] == 'SOURCE_IDENTITY_CONFLICT'
    assert not (tmp_path / 'state.json').exists()
    operations = [json.loads(line) for line in (tmp_path / 'runtime/ingest_operations.jsonl').read_text().splitlines() if line]
    assert len(operations) == 1
    assert 'patient_name' not in operations[0]
    assert 'clinic_reference' not in operations[0]
    event_id = request['data']['source_event_id']
    plain_event_sha = hashlib.sha256(event_id.encode('utf-8')).hexdigest()
    plain_key_sha = hashlib.sha256(
        f"medit|lab-medit-01|{event_id}".encode('utf-8')
    ).hexdigest()
    assert operations[0]['source_event_id_commitment'] != plain_event_sha
    assert operations[0]['event_key_commitment'] != plain_key_sha
    assert 'source_event_id_sha256' not in operations[0]
    assert 'event_key' not in operations[0]
