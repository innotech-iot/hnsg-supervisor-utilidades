#!/usr/bin/env python3
"""Launch locally without fixed credentials; never activates a hardware connection."""
from pathlib import Path
import os
import secrets
import sys

ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
os.environ['HNSG_MODE']='demo'
os.environ.setdefault('HNSG_DATA_DIR',str(ROOT/'runtime'))
if os.getenv('DATABASE_URL'):
    print('Para iniciar a demo, remova DATABASE_URL. O inicializador usa banco SQLite separado.')
    raise SystemExit(2)
from app.config import Settings
from app.database import Database
from app.models import User
from sqlalchemy import select

settings=Settings.from_env()
db=Database(settings)
db.initialize()
with db.session() as s:
    exists=s.scalar(select(User.id).limit(1))
if not exists:
    from app.security import hash_password
    password=secrets.token_urlsafe(15)
    with db.session() as s:
        s.add(User(username='admin',name='Administrador HNSG',role='admin',password_hash=hash_password(password)))
    print('\n'+'='*66,flush=True)
    print('PRIMEIRO ACESSO — anote a senha; ela não fica salva em texto puro.',flush=True)
    print('Usuário: admin\nSenha:   '+password,flush=True)
    print('='*66+'\n',flush=True)
else:
    print('Banco demo existente. Use sua senha; para redefinir: python scripts/manage_user.py reset admin',flush=True)
db.close()
print('HNSG DEMO: http://127.0.0.1:8000 (local) ou http://<IP-DESTE-PC>:8000 (rede)\nEscutando em 0.0.0.0. Apenas dados sintéticos. Ctrl+C encerra.',flush=True)
import uvicorn
uvicorn.run('app.main:app',host='0.0.0.0',port=8000,workers=1,log_level='info')
