import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app, default_app
from backend.identity_vault import load_private_identity, store_private_identity, validate_identity_key


def test_render_generated_secret_derives_a_stable_fernet_key(tmp_path: Path) -> None:
    secret = 'Ab3!xyZ9' * 8
    target = tmp_path / 'identities.jsonl'
    validate_identity_key(secret)
    assert store_private_identity(
        path=target,
        encryption_key=secret,
        case_code='AIQ-OPAQUE',
        patient_name='Paciente Sintético',
        clinic_reference='CLINICA-SYNTHETIC',
        order_reference='ORDER-SYNTHETIC',
        created_at='2026-08-20T00:00:00Z',
    )
    restored = load_private_identity(path=target, encryption_key=secret, case_code='AIQ-OPAQUE')
    assert restored is not None
    assert restored['patient_name'] == 'Paciente Sintético'
    with pytest.raises(ValueError, match='48 caracteres'):
        validate_identity_key('short-secret')
    with pytest.raises(ValueError, match='aleatorios diversos'):
        validate_identity_key('r' * 64)


ROOT = Path(__file__).resolve().parents[2]
TRAIN_RUN = ROOT / 'deploy_assets'
KNOWLEDGE_DB = TRAIN_RUN / 'knowledge.db'


def basic(username: str, password: str) -> dict[str, str]:
    value = base64.b64encode(f'{username}:{password}'.encode()).decode()
    return {'Authorization': f'Basic {value}'}


def test_production_ui_requires_basic_auth_and_same_origin_for_writes(tmp_path: Path) -> None:
    static = tmp_path / 'dist'
    static.mkdir()
    (static / 'index.html').write_text('<html>ABUTMENTIQ_STATIC_OK</html>', encoding='utf-8')
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
        daily_state_path=tmp_path / 'state.json',
        daily_outgoing_root=tmp_path / 'queue',
        static_dir=static,
        app_auth_username='miguel',
        app_auth_password='a-strong-test-password',
        allowed_origins=('https://abutmentiq.example',),
    )

    with TestClient(app) as client:
        health = client.get('/healthz')
        anonymous_ui = client.get('/')
        authorized_ui = client.get('/', headers=basic('miguel', 'a-strong-test-password'))
        anonymous_api = client.get('/api/status')
        authorized_api = client.get('/api/status', headers=basic('miguel', 'a-strong-test-password'))
        csrf_blocked = client.post(
            '/api/agent/analyze-upload',
            headers=basic('miguel', 'a-strong-test-password'),
            data={'functional_class': 'Antagonista'},
            files={'file': ('mesh.stl', b'solid empty\nendsolid empty', 'model/stl')},
        )
        wrong_scheme = client.post(
            '/api/agent/analyze-upload',
            headers={**basic('miguel', 'a-strong-test-password'), 'Origin': 'http://abutmentiq.example', 'Host': 'abutmentiq.example'},
            data={'functional_class': 'Antagonista'},
            files={'file': ('mesh.stl', b'solid empty\nendsolid empty', 'model/stl')},
        )

    assert health.status_code == 200
    assert health.json() == {'status': 'ok'}
    assert anonymous_ui.status_code == 401
    assert anonymous_ui.headers['www-authenticate'] == 'Basic realm="AbutmentIQ"'
    assert authorized_ui.status_code == 200
    assert 'ABUTMENTIQ_STATIC_OK' in authorized_ui.text
    assert anonymous_api.status_code == 401
    assert authorized_api.status_code == 200
    assert csrf_blocked.status_code == 403
    assert csrf_blocked.json()['detail']['code'] == 'INVALID_REQUEST_ORIGIN'
    assert wrong_scheme.status_code == 403
    assert wrong_scheme.json()['detail']['code'] == 'INVALID_REQUEST_ORIGIN'


def test_default_app_fails_closed_without_auth_or_explicit_local_demo(monkeypatch) -> None:
    for name in (
        'ABUTMENTIQ_APP_USERNAME',
        'ABUTMENTIQ_APP_PASSWORD',
        'ABUTMENTIQ_REQUIRE_APP_AUTH',
        'ABUTMENTIQ_LOCAL_DEMO',
        'ABUTMENTIQ_ALLOWED_ORIGIN',
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match='autenticación'):
        default_app()

    monkeypatch.setenv('ABUTMENTIQ_APP_USERNAME', 'reviewer')
    monkeypatch.setenv('ABUTMENTIQ_APP_PASSWORD', 'a-strong-test-password')
    with pytest.raises(RuntimeError, match='ALLOWED_ORIGIN'):
        default_app()
    monkeypatch.delenv('ABUTMENTIQ_APP_USERNAME')
    monkeypatch.delenv('ABUTMENTIQ_APP_PASSWORD')

    monkeypatch.setenv('ABUTMENTIQ_LOCAL_DEMO', 'true')
    app = default_app()
    with TestClient(app) as client:
        assert client.get('/healthz').status_code == 200
