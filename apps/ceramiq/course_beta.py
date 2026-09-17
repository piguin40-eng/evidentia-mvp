"""Isolated course HTTP access; enforced on every request, no persistent sessions."""
import base64
import hmac
import os
import runpy
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

START = datetime.fromisoformat('2026-09-18T00:00:00+02:00').timestamp()
END = datetime.fromisoformat('2026-09-23T00:00:00+02:00').timestamp()
PASSWORD = os.environ.get('COURSE_BETA_PASSWORD', '')
if len(PASSWORD) < 8:
    raise RuntimeError('COURSE_BETA_PASSWORD must have at least eight characters')
original_parse = BaseHTTPRequestHandler.parse_request

def access_status(header, now):
    if not START <= now < END:
        return 403
    try:
        scheme, value = header.split(' ', 1)
        if scheme.lower() != 'basic':
            return 401
        user, password = base64.b64decode(value, validate=True).decode().split(':', 1)
        return 200 if hmac.compare_digest(user, 'beta') and hmac.compare_digest(password, PASSWORD) else 401
    except (ValueError, UnicodeError):
        return 401

def reply(handler, status, body, challenge=False):
    handler.send_response(status)
    handler.send_header('Content-Type', 'text/plain; charset=utf-8')
    handler.send_header('Cache-Control', 'no-store')
    if challenge:
        handler.send_header('WWW-Authenticate', 'Basic realm="Curso Vertical AI"')
    payload = body.encode()
    handler.send_header('Content-Length', str(len(payload)))
    handler.send_header('Connection', 'close')
    handler.end_headers()
    if handler.command != 'HEAD':
        handler.wfile.write(payload)
    handler.close_connection = True
    return False

def parse_request(handler):
    if not original_parse(handler):
        return False
    path = unquote(urlsplit(handler.path).path)
    if path == '/course-healthz' and handler.command in ('GET', 'HEAD'):
        return reply(handler, 200, 'ok')
    status = access_status(handler.headers.get('Authorization', ''), datetime.now(timezone.utc).timestamp())
    if status != 200:
        return reply(handler, status, 'Acceso disponible del 18 al 22 de septiembre de 2026 (Madrid).' if status == 403 else 'Introduce el usuario y la contraseña del curso.', status == 401)
    parts = PurePosixPath(path).parts
    blocked = {'data', 'deploy', '.git', 'backups', 'scripts', 'sources', 'index', 'qa'}
    if any(p.startswith('.') or p in blocked for p in parts[1:]) or path.startswith(('/api/admin/', '/api/account/', '/api/connectors/export')) or (handler.command not in ('GET','HEAD') and path.startswith(('/api/billing/', '/api/ai/client-config'))):
        return reply(handler, 403, 'Operación no disponible en el curso.')
    if not path.startswith('/api/') and path != '/':
        if PurePosixPath(path).suffix.lower() not in {'.html','.js','.css','.png','.jpg','.jpeg','.svg','.webp','.ico','.woff','.woff2','.ttf','.webmanifest','.json','.wasm','.mp4','.webm','.stl','.obj','.ply'}:
            return reply(handler, 403, 'Archivo no disponible en el curso.')
    return True

if __name__ == '__main__':
    BaseHTTPRequestHandler.parse_request = parse_request
    target, *args = sys.argv[1:]
    sys.argv = [target, *args]
    runpy.run_path(target, run_name='__main__')
