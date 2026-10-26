"""Server-side sessions, password hashing and safe exports. No browser-side authorization."""
from __future__ import annotations
import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

ITERATIONS = 600_000

def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 256:
        raise ValueError('A senha deve ter entre 12 e 256 caracteres')
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${derived.hex()}'

def verify_password(password: str, encoded: str) -> bool:
    try:
        name, iterations, salt, expected = encoded.split('$')
        if name != 'pbkdf2_sha256' or len(password) > 256:
            return False
        got = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(got.hex(), expected)
    except (ValueError, TypeError):
        return False

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def new_token() -> str:
    return secrets.token_urlsafe(32)

def csv_safe(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + value
    return value

class LoginLimiter:
    """Local single-process limiter. Deployment intentionally permits ONE worker."""
    def __init__(self):
        self.attempts = defaultdict(deque)
    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.attempts[key]
        while q and q[0] < now - 300:
            q.popleft()
        if len(q) >= 8:
            return False
        q.append(now)
        if len(self.attempts) > 5000:
            self.attempts.clear()
            self.attempts[key].append(now)
        return True
    def clear(self, key: str):
        self.attempts.pop(key, None)
