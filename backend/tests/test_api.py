import hashlib
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import create_app


ROOT = Path(__file__).resolve().parents[2]
TRAIN_RUN = ROOT / 'deploy_assets'
KNOWLEDGE_DB = TRAIN_RUN / 'knowledge.db'


def test_application_accepts_fourteen_character_review_password(tmp_path):
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
        app_auth_username='Miguel',
        app_auth_password='A' * 14,
    )

    assert app is not None


def test_public_contract_never_exposes_hashes_or_reviewer_identity(tmp_path):
    knowledge_db = tmp_path / 'knowledge.db'
    with sqlite3.connect(knowledge_db) as db:
        db.execute('CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT, confidence TEXT, sha256 TEXT UNIQUE)')
        db.execute('CREATE VIRTUAL TABLE chunks_fts USING fts5(text, ordinal UNINDEXED, document_id UNINDEXED)')
        db.execute('INSERT INTO documents(id, title, confidence, sha256) VALUES (1, ?, ?, ?)', ('Documento sintético', 'bootstrap', 'a' * 64))
        db.execute('INSERT INTO chunks_fts(text, ordinal, document_id) VALUES (?, 1, 1)', ('scanbody evidencia sintética',))
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=knowledge_db,
    )
    with TestClient(app) as client:
        assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'implantologia_scanbody', 'question': 'scanbody'
        })
        review = client.post('/api/reviews', json={
            'assessment_id': assessment.json()['assessment_id'],

            'human_label': 'CORRECTA',
            'judgment': 'CORRECT',
            'notes': 'Observación privada',
            'functional_class': 'implantologia_scanbody',
        })
    assert assessment.status_code == 200
    assert review.status_code == 201
    serialized_assessment = json.dumps(assessment.json(), sort_keys=True)
    serialized_review = json.dumps(review.json(), sort_keys=True)
    assert 'sha256' not in serialized_assessment.casefold()
    assert 'Identidad Privada' not in serialized_review
    assert 'Observación privada' not in serialized_review
    assert 'reviewer' not in review.json()
    assert 'change_reason' not in review.json()


def test_reviewed_hash_index_survives_application_restart(tmp_path):
    runtime = tmp_path / 'runtime'

    def app():
        return create_app(
            runtime_dir=runtime,
            demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
            model_path=TRAIN_RUN / 'bootstrap_model.joblib',
            benchmark_path=TRAIN_RUN / 'model_benchmark.json',
            manifest_path=TRAIN_RUN / 'seed_manifest.json',
            knowledge_db=KNOWLEDGE_DB,
        )

    with TestClient(app()) as client:
        first_assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'no_evaluable', 'question': 'calidad técnica'
        }).json()
        first_review = client.post('/api/reviews', json={
            'assessment_id': first_assessment['assessment_id'],

            'human_label': first_assessment['agent_output']['verdict'],
            'judgment': 'CORRECT',
            'notes': '',
            'functional_class': 'no_evaluable',
        })
    assert first_review.status_code == 201
    assert first_review.json()['new_training_sample'] is True

    with TestClient(app()) as client:
        second_assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'no_evaluable', 'question': 'calidad técnica tras reinicio'
        }).json()
        second_review = client.post('/api/reviews', json={
            'assessment_id': second_assessment['assessment_id'],

            'human_label': second_assessment['agent_output']['verdict'],
            'judgment': 'CORRECT',
            'notes': '',
            'functional_class': 'no_evaluable',
        })
    assert second_review.status_code == 201
    assert second_review.json()['new_training_sample'] is False
    assert second_review.json()['training_eligibility'] == 'REVALIDATION_EXISTING_HASH'


def test_demo_analysis_uses_synthetic_bootstrap_and_requires_human_confirmation(tmp_path):
    app = create_app(
        runtime_dir=tmp_path,
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    with TestClient(app) as client:
        response = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'implantologia_scanbody',
            'question': '¿La malla es técnicamente correcta y qué evidencia hay sobre scanbody?',
        })

    assert response.status_code == 200
    payload = response.json()
    assert payload['agent_output']['verdict'] == 'CORRECTA'
    assert 0.03 < payload['agent_output']['probability_incorrect'] < 0.04
    assert payload['technical_features']['faces'] == 4480
    assert payload['rag']['status'] == 'SIN_EVIDENCIA_RECUPERADA'
    assert payload['rag']['citations'] == []
    assert payload['requires_human_confirmation'] is True


def test_uploaded_mesh_is_hashed_pseudonymized_and_analyzed(tmp_path):
    app = create_app(
        runtime_dir=tmp_path,
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    tetrahedron = b'''solid tetra
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
    with TestClient(app) as client:
        response = client.post(
            '/api/agent/analyze-upload',
            data={'functional_class': 'no_evaluable', 'question': 'calidad técnica'},
            files={'file': ('Paciente Apellido.stl', tetrahedron, 'model/stl')},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload['case_code'].startswith('AIQ-')
    assert payload['case_code'] != f"AIQ-{hashlib.sha256(tetrahedron).hexdigest()[:8].upper()}"
    assert 'source_mesh_sha256' not in payload
    assert payload['original_filename_stored'] is False
    stored = list((tmp_path / 'intake').glob('*.stl'))
    assert len(stored) == 1
    assert 'Paciente' not in stored[0].name


def test_uploaded_ascii_ply_is_pseudonymized_and_analyzed(tmp_path):
    app = create_app(
        runtime_dir=tmp_path,
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    tetrahedron = b'''ply
format ascii 1.0
element vertex 4
property float x
property float y
property float z
element face 4
property list uchar int vertex_indices
end_header
0 0 0
1 0 0
0 1 0
0 0 1
3 0 2 1
3 0 1 3
3 0 3 2
3 1 2 3
'''
    with TestClient(app) as client:
        response = client.post(
            '/api/agent/analyze-upload',
            data={'functional_class': 'no_evaluable', 'question': 'calidad técnica'},
            files={'file': ('Paciente Apellido.ply', tetrahedron, 'application/octet-stream')},
        )

    assert response.status_code == 200
    payload = response.json()
    assert 'source_mesh_sha256' not in payload
    assert payload['original_filename_stored'] is False
    stored = list((tmp_path / 'intake').glob('*.ply'))
    assert len(stored) == 1
    assert 'Paciente' not in stored[0].name


def test_repeated_mesh_review_is_revalidation_not_new_training_sample(tmp_path):
    app = create_app(
        runtime_dir=tmp_path,
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    review = {

        'human_label': 'INCORRECTA',
        'judgment': 'INCORRECT',
        'notes': 'Malla doble',
        'functional_class': 'implantologia_scanbody',
    }
    with TestClient(app) as client:
        first_assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'implantologia_scanbody', 'question': 'scanbody'
        }).json()['assessment_id']
        first = client.post('/api/reviews', json={**review, 'assessment_id': first_assessment})
        second_assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'implantologia_scanbody', 'question': 'scanbody'
        }).json()['assessment_id']
        revalidation = client.post('/api/reviews', json={**review, 'assessment_id': second_assessment})
        status = client.get('/api/training/status').json()

    assert first.status_code == 201
    assert revalidation.status_code == 201
    assert revalidation.json()['new_training_sample'] is False
    assert status['human_reviews_received'] == 2
    assert status['new_unique_training_samples'] == 1
    assert status['revalidations'] == 1


def test_multiworker_never_repeat_uses_durable_review_state(tmp_path):
    runtime = tmp_path / 'runtime'

    def build():
        return create_app(
            runtime_dir=runtime,
            demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
            model_path=TRAIN_RUN / 'bootstrap_model.joblib',
            benchmark_path=TRAIN_RUN / 'model_benchmark.json',
            manifest_path=TRAIN_RUN / 'seed_manifest.json',
            knowledge_db=KNOWLEDGE_DB,
        )

    worker_one = build()
    worker_two = build()
    with TestClient(worker_one) as first, TestClient(worker_two) as second:
        first_assessment = first.post('/api/agent/analyze-demo', json={
            'functional_class': 'no_evaluable', 'question': 'worker one',
        }).json()
        second_assessment = second.post('/api/agent/analyze-demo', json={
            'functional_class': 'no_evaluable', 'question': 'worker two',
        }).json()
        first_review = first.post('/api/reviews', json={
            'assessment_id': first_assessment['assessment_id'],
            'human_label': first_assessment['agent_output']['verdict'],
            'judgment': 'CORRECT', 'notes': '', 'functional_class': 'no_evaluable',
        })
        second_review = second.post('/api/reviews', json={
            'assessment_id': second_assessment['assessment_id'],
            'human_label': second_assessment['agent_output']['verdict'],
            'judgment': 'CORRECT', 'notes': '', 'functional_class': 'no_evaluable',
        })
    assert [first_review.status_code, second_review.status_code] == [201, 201]
    assert [first_review.json()['new_training_sample'], second_review.json()['new_training_sample']] == [True, False]


def test_assessment_created_by_one_worker_can_be_reviewed_by_another(tmp_path):
    runtime = tmp_path / 'runtime'

    def build():
        return create_app(
            runtime_dir=runtime,
            demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
            model_path=TRAIN_RUN / 'bootstrap_model.joblib',
            benchmark_path=TRAIN_RUN / 'model_benchmark.json',
            manifest_path=TRAIN_RUN / 'seed_manifest.json',
            knowledge_db=KNOWLEDGE_DB,
        )

    worker_one = build()
    worker_two = build()
    with TestClient(worker_one) as first, TestClient(worker_two) as second:
        assessment = first.post('/api/agent/analyze-demo', json={
            'functional_class': 'antagonista', 'question': 'worker handoff',
        }).json()
        review = second.post('/api/reviews', json={
            'assessment_id': assessment['assessment_id'],
            'human_label': assessment['agent_output']['verdict'],
            'judgment': 'CORRECT', 'notes': '', 'functional_class': 'antagonista',
        })
    assert review.status_code == 201


def test_review_request_rejects_client_supplied_reviewer_identity(tmp_path):
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    with TestClient(app) as client:
        assessment = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'antagonista', 'question': 'identity spoof',
        }).json()
        response = client.post('/api/reviews', json={
            'assessment_id': assessment['assessment_id'],
            'reviewer': 'Otra Persona',
            'human_label': assessment['agent_output']['verdict'],
            'judgment': 'CORRECT', 'notes': '', 'functional_class': 'antagonista',
        })
    assert response.status_code == 422


def test_training_status_excludes_append_only_reconciled_duplicate(tmp_path):
    app = create_app(
        runtime_dir=tmp_path,
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
    )
    records = [
        {'review_id': 'REV-ORIGINAL', 'case_code': 'AIQ-TEST', 'source_mesh_sha256': 'sha', 'new_training_sample': False},
        {'review_id': 'REV-DUPLICATE', 'case_code': 'AIQ-TEST', 'source_mesh_sha256': 'sha', 'new_training_sample': False},
    ]
    (tmp_path / 'reviews.jsonl').write_text('\n'.join(__import__('json').dumps(item) for item in records) + '\n')
    (tmp_path / 'review_reconciliations.jsonl').write_text(
        __import__('json').dumps({'invalid_review_id': 'REV-DUPLICATE', 'reason': 'DUPLICATE_SUBMISSION'}) + '\n'
    )

    with TestClient(app) as client:
        status = client.get('/api/training/status').json()
        latest = client.get('/api/reviews/latest', params={'case_code': 'AIQ-TEST'})

    assert status['audit_review_events'] == 2
    assert status['human_reviews_received'] == 1
    assert status['reconciled_duplicates'] == 1
    assert status['revalidations'] == 1
    assert latest.status_code == 200
    assert latest.json()['review_id'] == 'REV-ORIGINAL'


def test_daily_review_queue_case_is_visible_served_and_analyzable(tmp_path):
    import hashlib
    import json

    tetrahedron = b'''solid tetra
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
    source_sha = hashlib.sha256(tetrahedron).hexdigest()
    outgoing = tmp_path / 'outgoing'
    case_dir = outgoing / '2026-08-19_02_AIQ-TEST0001'
    case_dir.mkdir(parents=True)
    mesh = case_dir / 'AIQ-TEST0001_01.stl'
    mesh.write_bytes(tetrahedron)
    state_path = tmp_path / 'daily-state.json'
    state_path.write_text(json.dumps({'prepared': [{
        'date': '2026-08-19',
        'daily_slot': 2,
        'daily_total': 7,
        'case_code': 'AIQ-TEST0001',
        'review_status': 'AWAITING_HUMAN_REVIEW',
        'review_id': 'HR-AIQ-TEST0001-20260819-01',
        'source_mesh_sha256': source_sha,
        'delivered_stl_sha256': source_sha,
        'component_count': 1,
        'triangle_count': 4,
    }]}), encoding='utf-8')
    app = create_app(
        runtime_dir=tmp_path / 'runtime',
        demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib',
        benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json',
        knowledge_db=KNOWLEDGE_DB,
        daily_state_path=state_path,
        daily_outgoing_root=outgoing,
    )

    with TestClient(app) as client:
        queue = client.get('/api/review-queue')
        served = client.get('/api/review-queue/AIQ-TEST0001/mesh')
        analyzed = client.post('/api/agent/analyze-queue/AIQ-TEST0001', json={
            'functional_class': 'implantologia_scanbody',
            'question': '¿La malla es técnicamente correcta?',
        })

    assert queue.status_code == 200
    assert queue.json()['cases'] == [{
        'case_code': 'AIQ-TEST0001',
        'daily_slot': 2,
        'daily_total': 7,
        'review_status': 'AWAITING_HUMAN_REVIEW',
        'mesh_format': 'stl',
        'mesh_url': '/api/review-queue/AIQ-TEST0001/mesh',
        'triangle_count': 4,
    }]
    assert served.status_code == 200
    assert served.content == tetrahedron
    assert analyzed.status_code == 200
    assert analyzed.json()['case_code'] == 'AIQ-TEST0001'
    assert 'source_mesh_sha256' not in analyzed.json()
    assert 'question' not in analyzed.json()
    assert analyzed.json()['queue_source'] == 'daily_read_only'


def test_reviewing_daily_queue_case_marks_operational_queue_completed(tmp_path):
    import hashlib
    import json

    mesh_bytes = (TRAIN_RUN / 'synthetic_dental_arch.stl').read_bytes()
    source_sha = hashlib.sha256(mesh_bytes).hexdigest()
    outgoing = tmp_path / 'outgoing'
    case_dir = outgoing / '2026-08-19_03_AIQ-QUEUE002'
    case_dir.mkdir(parents=True)
    (case_dir / 'AIQ-QUEUE002_01.stl').write_bytes(mesh_bytes)
    state_path = tmp_path / 'daily-state.json'
    state_path.write_text(json.dumps({'prepared': [{
            'date': '2026-08-19', 'daily_slot': 3, 'daily_total': 7,
            'case_code': 'AIQ-QUEUE002', 'review_status': 'AWAITING_HUMAN_REVIEW',
            'review_id': 'HR-AIQ-QUEUE002-20260819-01',
            'source_mesh_sha256': source_sha, 'delivered_stl_sha256': source_sha,
            'component_count': 1, 'triangle_count': 4480,
        }]}), encoding='utf-8')
    history_path = tmp_path / 'history.json'
    history_path.write_text(json.dumps({'prepared': [{
        'date': '2026-08-19', 'daily_slot': 3, 'daily_total': 7,
        'case_code': 'AIQ-QUEUE002', 'review_status': 'AWAITING_HUMAN_REVIEW',
        'review_id': 'HR-AIQ-QUEUE002-20260819-01', 'source_sha256': source_sha,
    }]}), encoding='utf-8')
    app = create_app(
        runtime_dir=tmp_path / 'runtime', demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib', benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json', knowledge_db=KNOWLEDGE_DB,
        daily_state_path=state_path, daily_outgoing_root=outgoing,
        daily_history_path=history_path,
    )

    with TestClient(app) as client:
        assessment = client.post('/api/agent/analyze-queue/AIQ-QUEUE002', json={
            'functional_class': 'implantologia_scanbody', 'question': 'calidad técnica',
        }).json()
        second_assessment = client.post('/api/agent/analyze-queue/AIQ-QUEUE002', json={
            'functional_class': 'implantologia_scanbody', 'question': 'segunda evaluación previa',
        }).json()
        assert assessment['agent_output']['verdict'] == 'CORRECTA'
        review_payload = {
            'assessment_id': assessment['assessment_id'],
            'human_label': 'INCORRECTA', 'judgment': 'INCORRECT',
            'notes': 'Scanbody defectuoso.', 'functional_class': 'implantologia_scanbody',
        }
        wrong_function = client.post('/api/reviews', json={**review_payload, 'functional_class': 'antagonista'})
        inconsistent_judgment = client.post('/api/reviews', json={**review_payload, 'judgment': 'CORRECT'})
        review = client.post('/api/reviews', json=review_payload)
        retry = client.post('/api/reviews', json=review_payload)
        second_payload = {
            'assessment_id': second_assessment['assessment_id'],
            'human_label': second_assessment['agent_output']['verdict'],
            'judgment': 'CORRECT', 'notes': '',
            'functional_class': 'implantologia_scanbody',
        }
        rejected_second = client.post('/api/reviews', json=second_payload)
        rejected_second_retry = client.post('/api/reviews', json=second_payload)
        analyze_completed = client.post('/api/agent/analyze-queue/AIQ-QUEUE002', json={
            'functional_class': 'implantologia_scanbody', 'question': 'ya completado',
        })
        queue = client.get('/api/review-queue').json()['cases']
        training = client.get('/api/training/status').json()

    assert wrong_function.status_code == 409
    assert inconsistent_judgment.status_code == 422
    assert review.status_code == 201
    assert retry.status_code == 201
    assert retry.json()['review_id'] == review.json()['review_id']
    assert rejected_second.status_code == 409
    assert rejected_second.json()['detail']['code'] == 'CASE_ALREADY_COMPLETED'
    assert rejected_second_retry.status_code == 409
    assert analyze_completed.status_code == 409
    assert analyze_completed.json()['detail']['code'] == 'CASE_ALREADY_COMPLETED'
    assert review.json()['agent_was_correct'] is False
    assert queue[0]['review_status'] == 'COMPLETED'
    persisted_state = json.loads(state_path.read_text(encoding='utf-8'))
    assert persisted_state['prepared'][0]['app_review_id'] == review.json()['review_id']
    persisted_history = json.loads(history_path.read_text(encoding='utf-8'))
    assert persisted_history['prepared'][0]['review_status'] == 'COMPLETED'
    assert persisted_history['prepared'][0]['app_review_id'] == review.json()['review_id']
    candidates = [
        json.loads(line)
        for line in (tmp_path / 'runtime' / 'training_candidates.jsonl').read_text(encoding='utf-8').splitlines()
    ]
    assert len(candidates) == 1
    assert candidates[0]['review_id'] == review.json()['review_id']
    assert candidates[0]['source_mesh_sha256'] == source_sha
    assert candidates[0]['human_label'] == 'INCORRECTA'
    assert candidates[0]['group_assignment_status'] == 'PENDING_PROVENANCE_GROUP'
    assert candidates[0]['automatic_retraining'] is False
    assert candidates[0]['stable_model_changed'] is False
    assert training['human_reviews_received'] == 1
    assert training['candidate_records'] == 1
    assert training['pending_group_assignment'] == 1
    assert training['ready_grouped_candidates'] == 0
    assert training['next_candidate_gate']['ready'] is False


def test_platform_connector_status_hides_paths_and_scan_is_read_only(tmp_path):
    import json

    source = tmp_path / 'lab-inbox'
    source.mkdir()
    (source / 'caso.stl').write_bytes(b'''solid tetra
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
endsolid tetra''')
    config_path = tmp_path / 'connectors.json'
    config_path.write_text(json.dumps({'connectors': [{
        'connector_id': 'exocad-export', 'display_name': 'Exportación CAD',
        'source_root': str(source), 'enabled': True, 'mode': 'read_only',
    }]}), encoding='utf-8')
    app = create_app(
        runtime_dir=tmp_path / 'runtime', demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib', benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json', knowledge_db=KNOWLEDGE_DB,
        platform_connectors_path=config_path,
    )

    with TestClient(app) as client:
        status = client.get('/api/platform-connectors/status')
        scan = client.post('/api/platform-connectors/scan')

    assert status.status_code == 200
    assert status.json()['connectors'] == [{
        'connector_id': 'exocad-export', 'display_name': 'Exportación CAD',
        'enabled': True, 'mode': 'read_only', 'source_available': True,
    }]
    assert 'source_root' not in str(status.json())
    assert scan.status_code == 200
    assert scan.json()['new_source_events'] == 1
    assert scan.json()['new_unique_geometries'] == 1
    assert (source / 'caso.stl').exists()


def test_next_queue_case_requires_completion_and_is_idempotent(tmp_path: Path) -> None:
    state_path = tmp_path / 'state.json'
    outgoing = tmp_path / 'outgoing'
    first_dir = outgoing / '2026-08-20_04_AIQ-FIRST'
    first_dir.mkdir(parents=True)
    first_mesh = first_dir / 'AIQ-FIRST_01.stl'
    first_mesh.write_bytes((TRAIN_RUN / 'synthetic_dental_arch.stl').read_bytes())
    source_sha = hashlib.sha256(first_mesh.read_bytes()).hexdigest()
    state_path.write_text(json.dumps({'prepared': [{
        'date': '2026-08-20', 'daily_slot': 4, 'daily_total': 5,
        'case_code': 'AIQ-FIRST', 'review_status': 'AWAITING_HUMAN_REVIEW',
        'source_mesh_sha256': source_sha, 'triangle_count': 10,
    }]}), encoding='utf-8')
    calls = 0

    def advance() -> None:
        nonlocal calls
        calls += 1
        time.sleep(0.05)
        second_dir = outgoing / '2026-08-20_05_AIQ-SECOND'
        second_dir.mkdir(parents=True, exist_ok=True)
        second_mesh = second_dir / 'AIQ-SECOND_01.stl'
        second_mesh.write_bytes((TRAIN_RUN / 'synthetic_dental_arch.stl').read_bytes())
        state_path.write_text(json.dumps({'prepared': [{
            'date': '2026-08-20', 'daily_slot': 5, 'daily_total': 0,
            'case_code': 'AIQ-SECOND', 'review_status': 'AWAITING_HUMAN_REVIEW',
            'source_mesh_sha256': hashlib.sha256(second_mesh.read_bytes()).hexdigest(),
            'triangle_count': 20,
        }]}), encoding='utf-8')

    app = create_app(
        runtime_dir=tmp_path / 'runtime', demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
        model_path=TRAIN_RUN / 'bootstrap_model.joblib', benchmark_path=TRAIN_RUN / 'model_benchmark.json',
        manifest_path=TRAIN_RUN / 'seed_manifest.json', knowledge_db=KNOWLEDGE_DB,
        daily_state_path=state_path, daily_outgoing_root=outgoing,
        daily_advance_callback=advance,
    )
    with TestClient(app) as client:
        blocked = client.post('/api/review-queue/next')
        state = json.loads(state_path.read_text(encoding='utf-8'))
        state['prepared'][0]['review_status'] = 'COMPLETED'
        state_path.write_text(json.dumps(state), encoding='utf-8')
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: client.post('/api/review-queue/next'), range(2)))

    advanced = next(response for response in responses if response.status_code == 201)
    duplicate = next(response for response in responses if response.status_code != 201)
    assert blocked.status_code == 409
    assert blocked.json()['detail']['code'] == 'CURRENT_REVIEW_NOT_COMPLETED'
    assert advanced.status_code == 201
    assert advanced.json()['case']['case_code'] == 'AIQ-SECOND'
    assert advanced.json()['case']['daily_slot'] == 5
    assert advanced.json()['case']['daily_total'] == 0
    assert duplicate.status_code == 409
    assert duplicate.json()['detail']['code'] == 'CURRENT_REVIEW_NOT_COMPLETED'
    assert calls == 1


def test_assessment_can_be_reviewed_after_application_restart(tmp_path: Path) -> None:
    def build():
        return create_app(
            runtime_dir=tmp_path / 'runtime',
            demo_mesh=TRAIN_RUN / 'synthetic_dental_arch.stl',
            model_path=TRAIN_RUN / 'bootstrap_model.joblib',
            benchmark_path=TRAIN_RUN / 'model_benchmark.json',
            manifest_path=TRAIN_RUN / 'seed_manifest.json',
            knowledge_db=KNOWLEDGE_DB,
        )

    with TestClient(build()) as client:
        analyzed = client.post('/api/agent/analyze-demo', json={
            'functional_class': 'antagonista',
            'question': 'Control técnico sintético',
        })
    assert analyzed.status_code == 200
    assert 'source_mesh_sha256' not in analyzed.json()

    with TestClient(build()) as restarted:
        reviewed = restarted.post('/api/reviews', json={
            'assessment_id': analyzed.json()['assessment_id'],

            'human_label': analyzed.json()['agent_output']['verdict'],
            'judgment': 'CORRECT',
            'notes': '',
            'functional_class': 'antagonista',
        })
        latest = restarted.get('/api/reviews/latest', params={'case_code': analyzed.json()['case_code']})

    assert reviewed.status_code == 201
    assert latest.status_code == 200
    assert 'source_mesh_sha256' not in reviewed.json()
    assert 'source_mesh_sha256' not in latest.json()
