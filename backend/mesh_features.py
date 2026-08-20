from __future__ import annotations

from pathlib import Path


DEFAULT_MAX_MESH_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_FACES = 500_000
DEFAULT_MAX_VERTICES = 1_000_000


def validate_mesh_resource_limits(
    path: Path | str,
    *,
    max_bytes: int = DEFAULT_MAX_MESH_BYTES,
    max_faces: int = DEFAULT_MAX_FACES,
    max_vertices: int = DEFAULT_MAX_VERTICES,
) -> None:
    mesh_path = Path(path)
    size = mesh_path.stat().st_size
    if size > max_bytes:
        raise ValueError('malla demasiado grande')
    suffix = mesh_path.suffix.casefold()
    if suffix == '.stl':
        with mesh_path.open('rb') as handle:
            header = handle.read(84)
            if len(header) >= 84:
                face_count = int.from_bytes(header[80:84], 'little')
                expected_binary_size = 84 + face_count * 50
                looks_binary = expected_binary_size == size or b'\0' in header[:80]
                if looks_binary:
                    if face_count > max_faces:
                        raise ValueError('malla con demasiadas caras')
                    if expected_binary_size != size:
                        raise ValueError('STL binario truncado o inconsistente')
                    return
            handle.seek(0)
            face_count = 0
            for line in handle:
                if line.lstrip().lower().startswith(b'facet normal'):
                    face_count += 1
                    if face_count > max_faces:
                        raise ValueError('malla con demasiadas caras')
    elif suffix == '.ply':
        faces = vertices = None
        with mesh_path.open('rb') as handle:
            for index, raw_line in enumerate(handle):
                if index > 10_000:
                    raise ValueError('cabecera PLY demasiado grande')
                line = raw_line.decode('ascii', errors='strict').strip().casefold()
                if line.startswith('element face '):
                    faces = int(line.split()[-1])
                elif line.startswith('element vertex '):
                    vertices = int(line.split()[-1])
                elif line == 'end_header':
                    break
        if faces is not None and faces > max_faces:
            raise ValueError('malla con demasiadas caras')
        if vertices is not None and vertices > max_vertices:
            raise ValueError('malla con demasiados vértices')


def mesh_features(path: Path | str) -> dict[str, float | int]:
    """Extrae rasgos geométricos reproducibles sin usar nombres ni metadatos."""
    import numpy as np
    import trimesh

    validate_mesh_resource_limits(path)
    loaded = trimesh.load_mesh(Path(path), process=False)
    if isinstance(loaded, trimesh.Scene):
        if not loaded.geometry:
            raise ValueError('empty mesh scene')
        mesh = trimesh.util.concatenate(tuple(loaded.geometry.values()))
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError('mesh has no faces')
    if len(mesh.faces) > DEFAULT_MAX_FACES:
        raise ValueError('malla con demasiadas caras tras parseo')
    if len(mesh.vertices) > DEFAULT_MAX_VERTICES:
        raise ValueError('malla con demasiados vértices tras parseo')

    mesh = mesh.copy()
    mesh.merge_vertices()
    vertices = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces, dtype=np.int64)
    if not np.isfinite(vertices).all():
        raise ValueError('mesh has non-finite coordinates')

    tri_edges = np.sort(
        np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]])),
        axis=1,
    )
    _, edge_counts = np.unique(tri_edges, axis=0, return_counts=True)
    extents = np.sort(np.asarray(mesh.extents, dtype=float))
    area = float(mesh.area)
    face_components = trimesh.graph.connected_components(
        mesh.face_adjacency,
        nodes=np.arange(len(faces)),
        min_len=1,
    )
    area_faces = np.asarray(mesh.area_faces, dtype=float)

    return {
        'faces': int(len(faces)),
        'vertices': int(len(vertices)),
        'extent_min': float(extents[0]),
        'extent_mid': float(extents[1]),
        'extent_max': float(extents[2]),
        'bbox_diagonal': float(np.linalg.norm(extents)),
        'surface_area': area,
        'faces_per_area': float(len(faces) / area) if area > 0 else 0.0,
        'components': int(len(face_components)),
        'boundary_edges': int(np.sum(edge_counts == 1)),
        'nonmanifold_edges': int(np.sum(edge_counts > 2)),
        'degenerate_faces': int(np.sum(area_faces <= 1e-12)),
        'watertight': int(bool(mesh.is_watertight)),
    }
