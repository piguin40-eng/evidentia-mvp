"""Independent course runtime. Never restores or imports a private seed."""
import hmac
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from datetime import datetime

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('COURSE_DATA_DIR', str(ROOT / 'course-data'))).resolve()
MARKER = DATA / '.course-zero-node'
if not os.environ.get('EVIDENTIA_BASIC_AUTH_USER') or len(os.environ.get('EVIDENTIA_BASIC_AUTH_PASSWORD', '')) < 20:
    raise RuntimeError('Configure independent course credentials (password >=20 characters).')
if DATA.exists() and any(DATA.iterdir()) and not MARKER.exists():
    raise RuntimeError('Refusing existing unverified data directory. Use an empty course volume.')
DATA.mkdir(parents=True, exist_ok=True)
MARKER.touch(exist_ok=True)
os.environ['EVIDENTIA_DATA_DIR'] = str(DATA)
os.environ['EVIDENTIA_RAG_DIR'] = str(DATA / 'rag' / 'chroma')
os.environ['EVIDENTIA_RESTORE_SEED'] = 'false'
os.environ['EVIDENTIA_AUTH_MODE'] = 'basic'
os.environ['EVIDENTIA_ENABLE_OPENAI_CHAT'] = 'false'
os.environ['EVIDENTIA_PORT'] = os.environ.get('PORT', '8898')
os.environ['EVIDENTIA_HOST'] = os.environ.get('COURSE_HOST', '0.0.0.0')
import server

def exact_credentials(user, password):
    return hmac.compare_digest(user, server.BASIC_AUTH_USER) and hmac.compare_digest(password, server.BASIC_AUTH_PASSWORD)

server.valid_credentials = exact_credentials
END = datetime.fromisoformat(os.environ.get('COURSE_ACCESS_END', '2026-11-24T00:00:00+01:00'))
if END.tzinfo is None:
    raise RuntimeError('COURSE_ACCESS_END requires a timezone.')
original_parse = server.Handler.parse_request
static_files = {'/index.html','/app.js','/styles.css','/sw.js','/manifest.webmanifest','/icon.svg','/reset.html'}
def parse_request(self):
    if not original_parse(self):
        return False
    path = unquote(urlsplit(self.path).path)
    if path == '/api/healthz':
        return True
    if not self.require_auth():
        return False
    if datetime.now(END.tzinfo) >= END:
        self.send_error(403, 'Course access expired')
        return False
    if path.startswith(('/api/admin/', '/api/billing/', '/api/account/', '/api/ai/client-config')):
        self.send_error(403, 'Not available in course')
        return False
    if any(part.startswith('.') for part in path.split('/') if part):
        self.send_error(403)
        return False
    if path != '/' and not path.startswith('/api/') and path not in static_files and not path.startswith('/assets/'):
        self.send_error(403)
        return False
    return True
server.Handler.parse_request = parse_request
if __name__ == '__main__':
    server.main()
