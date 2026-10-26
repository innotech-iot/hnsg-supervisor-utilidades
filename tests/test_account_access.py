import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.main import create_app
from app.models import User
from app.security import hash_password


@pytest.mark.parametrize('role', ['viewer', 'operator', 'admin'])
def test_own_password_and_account_visibility(tmp_path, role):
    app = create_app(Settings(data_dir=tmp_path, run_collector=False, seed_hours=0))
    with TestClient(app) as client:
        with app.state.db.session() as s:
            s.add(User(username='own_fixture', name='Fixture', role=role,
                       password_hash=hash_password('Initial-Fixture-2026!')))
            s.add(User(username='higher_fixture', name='Administrator', role='admin',
                       password_hash=hash_password('Higher-Fixture-2026!')))
        login = client.post('/api/auth/login', json={'username':'own_fixture','password':'Initial-Fixture-2026!'})
        csrf = {'X-CSRF-Token':login.json()['csrf']}
        old_cookie = client.cookies.get('hnsg_session')
        response = client.get('/api/users')
        if role != 'admin':
            assert response.status_code == 403
            assert 'higher_fixture' not in response.text
            assert client.put('/api/users/2', headers=csrf, json={'role':'viewer','active':False}).status_code == 403
        else:
            assert response.status_code == 200
            assert all('password_hash' not in user for user in response.json()['users'])
        body = {'current':'Initial-Fixture-2026!','password':'Changed-Fixture-2026!'}
        assert client.post('/api/auth/password', json=body).status_code == 403
        assert client.post('/api/auth/password', headers=csrf, json=body | {'current':'wrong'}).status_code == 403
        assert client.post('/api/auth/password', headers=csrf, json=body | {'user_id':2}).status_code == 422
        assert client.post('/api/auth/password', headers=csrf, json=body).status_code == 200
        assert client.get('/api/session', headers={'Cookie':'hnsg_session='+old_cookie}).status_code == 401
        assert client.post('/api/auth/login', json={'username':'own_fixture','password':body['current']}).status_code == 401
        assert client.post('/api/auth/login', json={'username':'own_fixture','password':body['password']}).status_code == 200
        assert client.post('/api/auth/login', json={'username':'higher_fixture','password':'Higher-Fixture-2026!'}).status_code == 200


def test_own_account_frontend_hides_restricted_accounts():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node indisponível')
    result = subprocess.run([node,'--experimental-default-type=module',str(Path(__file__).with_name('frontend_account.mjs'))],
                            capture_output=True,text=True,encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr
