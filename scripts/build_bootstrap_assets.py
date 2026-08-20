#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import trimesh
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_NAMES = (
    'faces', 'vertices', 'extent_min', 'extent_mid', 'extent_max',
    'bbox_diagonal', 'surface_area', 'faces_per_area', 'components',
    'boundary_edges', 'nonmanifold_edges', 'degenerate_faces', 'watertight',
)


def synthetic_rows() -> tuple[list[dict[str, float]], list[int]]:
    rows: list[dict[str, float]] = []
    labels: list[int] = []
    for index in range(12):
        incorrect = index >= 6
        scale = 1.0 + index * 0.03
        rows.append({
            'faces': 8000.0 + index * 500,
            'vertices': 4200.0 + index * 250,
            'extent_min': 8.0 * scale,
            'extent_mid': 22.0 * scale,
            'extent_max': 48.0 * scale,
            'bbox_diagonal': 53.4 * scale,
            'surface_area': 2100.0 * scale,
            'faces_per_area': 4.0 + index * 0.1,
            'components': 1.0 if not incorrect else 3.0 + (index % 3),
            'boundary_edges': 600.0 if not incorrect else 1800.0 + index * 100,
            'nonmanifold_edges': 0.0 if not incorrect else 20.0 + index,
            'degenerate_faces': 0.0 if not incorrect else 12.0 + index,
            'watertight': 0.0,
        })
        labels.append(int(incorrect))
    return rows, labels


def build_model(target: Path) -> None:
    rows, labels = synthetic_rows()
    model = Pipeline([
        ('vectorizer', DictVectorizer(sparse=False)),
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(class_weight='balanced', solver='liblinear', random_state=23)),
    ])
    model.fit(rows, np.asarray(labels, dtype=int))
    joblib.dump(model, target)


def build_demo_mesh(target: Path) -> None:
    crowns = []
    for index, angle in enumerate(np.linspace(-1.15, 1.15, 14)):
        radius = 24.0
        x = radius * np.sin(angle)
        y = radius * np.cos(angle) - 15.0
        crown = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        width = 2.8 + (0.8 if index in {0, 1, 12, 13} else 0.0)
        crown.apply_scale([width, 3.2, 5.0])
        crown.apply_translation([x, y, 0.0])
        crowns.append(crown)
    mesh = trimesh.util.concatenate(crowns)
    mesh.export(target, file_type='stl')


def build_knowledge_db(target: Path) -> None:
    target.unlink(missing_ok=True)
    with sqlite3.connect(target) as db:
        db.execute('CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT, confidence TEXT, sha256 TEXT UNIQUE)')
        db.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(text, ordinal UNINDEXED, document_id UNINDEXED)")
        db.commit()


def main() -> None:
    root = Path(__file__).resolve().parents[1] / 'deploy_assets'
    root.mkdir(parents=True, exist_ok=True)
    build_model(root / 'bootstrap_model.joblib')
    build_demo_mesh(root / 'synthetic_dental_arch.stl')
    build_knowledge_db(root / 'knowledge.db')
    (root / 'model_benchmark.json').write_text(json.dumps({
        'run_id': 'bootstrap-synthetic-v1',
        'model_version': 'bootstrap-synthetic-v1',
        'dataset': {'meshes': 0, 'case_groups': 0, 'labels': {'correct': 0, 'incorrect': 0}},
        'validation': 'NOT_CLINICALLY_VALIDATED',
        'models': {'random_forest': {'balanced_accuracy': 0.0, 'incorrect_recall': 0.0}},
        'decision': 'NO_PROMOTION',
        'stable_model_changed': False,
        'clinical_decision': False,
    }, indent=2) + '\n', encoding='utf-8')
    (root / 'seed_manifest.json').write_text(json.dumps({
        'schema_version': 1,
        'storage_mode': 'no_clinical_sources_in_deployment',
        'usage': 'bootstrap_only_not_for_clinical_release',
        'counts': {'total': 0, 'unique_hashes': 0, 'groups': 0},
        'records': [],
    }, indent=2) + '\n', encoding='utf-8')
    (root / 'platform_connectors.json').write_text(json.dumps({
        'schema_version': 2,
        'policy': {
            'source_mode': 'read_only',
            'supported_formats': ['stl', 'ply'],
            'stable_file_window_seconds': 30,
            'never_repeat_source_sha256': True,
            'geometric_identity_required': True,
        },
        'supported_platforms': ['medit', '3shape', 'exocad', 'itero', 'generic'],
        'connectors': [],
    }, indent=2) + '\n', encoding='utf-8')
    print(f'bootstrap_assets={root}')


if __name__ == '__main__':
    main()
