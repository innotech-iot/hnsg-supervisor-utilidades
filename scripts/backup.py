#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from app.database import Database
from app.backups import perform_backup,verify_backup
p=argparse.ArgumentParser(description='Backup consistente; não restaura nem remove dados.')
p.add_argument('destination',nargs='?');p.add_argument('--verify',metavar='MANIFEST_JSON')
p.add_argument('--allow-same-device',action='store_true',help='Somente bancada: cópia local não é backup externo')
a=p.parse_args()
try:
    if a.verify:report=verify_backup(a.verify)
    else:
        if not a.destination:p.error('Informe o diretório de destino existente')
        db=Database(Settings.from_env())
        try:report=perform_backup(db,a.destination,a.allow_same_device)
        finally:db.close()
    print(json.dumps(report,ensure_ascii=False,indent=2))
except Exception as exc:
    print('Backup/verificação falhou: '+str(exc),file=sys.stderr);raise SystemExit(1)
