from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


def _fernet_key(secret: str) -> bytes:
    try:
        raw = secret.encode('ascii')
    except UnicodeEncodeError as exc:
        raise ValueError('El secreto de identidad debe ser ASCII') from exc
    try:
        Fernet(raw)
        return raw
    except (ValueError, TypeError):
        if len(raw) < 48 or len(set(raw)) < 8:
            raise ValueError('El secreto de identidad debe tener al menos 48 caracteres aleatorios diversos')
        return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())


def validate_identity_key(key: str) -> None:
    _fernet_key(key)


def store_private_identity(
    *,
    path: Path | str,
    encryption_key: str,
    case_code: str,
    patient_name: str,
    clinic_reference: str,
    order_reference: str,
    created_at: str,
    source_event_id: str = '',
) -> bool:
    payload = {
        'schema_version': 1,
        'case_code': case_code,
        'patient_name': patient_name.strip(),
        'clinic_reference': clinic_reference.strip(),
        'order_reference': order_reference.strip(),
        'source_event_id': source_event_id.strip(),
        'created_at': created_at,
    }
    cipher = Fernet(_fernet_key(encryption_key))
    ciphertext = cipher.encrypt(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')
    ).decode('ascii')
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a+', encoding='utf-8') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        for line in handle:
            if line.strip() and json.loads(line).get('case_code') == case_code:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                return False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps({
            'schema_version': 1,
            'case_code': case_code,
            'ciphertext': ciphertext,
        }, sort_keys=True) + '\n')
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return True


def load_private_identity(
    *,
    path: Path | str,
    encryption_key: str,
    case_code: str,
) -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return None
    cipher = Fernet(_fernet_key(encryption_key))
    with target.open('r', encoding='utf-8') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            record = next(
                (json.loads(line) for line in handle if line.strip() and json.loads(line).get('case_code') == case_code),
                None,
            )
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    if record is None:
        return None
    try:
        cleartext = cipher.decrypt(str(record['ciphertext']).encode('ascii'))
    except (InvalidToken, KeyError, ValueError) as exc:
        raise ValueError('PRIVATE_IDENTITY_DECRYPTION_FAILED') from exc
    payload = json.loads(cleartext.decode('utf-8'))
    if payload.get('case_code') != case_code:
        raise ValueError('PRIVATE_IDENTITY_CASE_MISMATCH')
    return payload
