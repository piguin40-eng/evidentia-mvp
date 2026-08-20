import struct

import pytest

from backend.mesh_features import validate_mesh_resource_limits


def test_binary_stl_face_limit_is_checked_before_parser(tmp_path):
    mesh = tmp_path / 'oversized.stl'
    mesh.write_bytes(b'\0' * 80 + struct.pack('<I', 500_001))

    with pytest.raises(ValueError, match='demasiadas caras'):
        validate_mesh_resource_limits(mesh, max_bytes=100 * 1024 * 1024, max_faces=500_000)


def test_solid_header_binary_stl_cannot_bypass_face_limit(tmp_path):
    mesh = tmp_path / 'solid-header-binary.stl'
    face_count = 500_001
    header = b'solid adversarial' + b'\0' * (80 - len(b'solid adversarial'))
    with mesh.open('wb') as handle:
        handle.write(header + struct.pack('<I', face_count))
        handle.seek(84 + face_count * 50 - 1)
        handle.write(b'\0')

    with pytest.raises(ValueError, match='demasiadas caras'):
        validate_mesh_resource_limits(mesh, max_bytes=100 * 1024 * 1024, max_faces=500_000)
