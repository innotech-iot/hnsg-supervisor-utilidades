"""Consistent local backup with manifest. Never restores or deletes application data."""
from __future__ import annotations
import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from .models import Meta
from .postgres import client_connection

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def perform_backup(db,destination: str|Path,allow_same_device: bool=False) -> dict:
    destination=Path(destination).resolve()
    if not destination.is_dir():raise ValueError('Destino precisa existir e estar montado antes do backup')
    engine=db.engine.dialect.name
    if engine not in {'sqlite','postgresql'}:raise ValueError('Banco não suportado')
    source_device_path=db.settings.data_dir
    if engine=='sqlite':
        source=Path(db.engine.url.database).resolve()
        if not source.is_file():raise ValueError('Banco SQLite de origem ausente')
        source_device_path=source
    # SQLite may reside outside data_dir via DATABASE_URL. For PostgreSQL,
    # data_dir remains a local check; independence requires deployment validation.
    if destination.stat().st_dev==source_device_path.stat().st_dev and not allow_same_device:
        raise ValueError('Backup no mesmo dispositivo: selecione armazenamento independente; exceção apenas para testes')
    with db.session() as s:
        mode=s.get(Meta,'mode')
        if not mode or mode.value!=db.settings.mode:raise ValueError('Banco não inicializado ou modo incorreto')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name=f'hnsg-{db.settings.mode}-{stamp}-{secrets.token_hex(3)}'
    final=destination/(name+('.sqlite3' if engine=='sqlite' else '.pgdump'))
    temp=final.with_suffix(final.suffix+'.partial')
    fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    try:
        if engine=='sqlite':
            # Connection context managers commit/rollback but do not close handles.
            with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src:
                with closing(sqlite3.connect(temp)) as dst:src.backup(dst)
        else:
            binary=shutil.which('pg_dump')
            if not binary:raise ValueError('Instale pg_dump compatível com o servidor PostgreSQL')
            connection,env=client_connection(db.engine.url)
            proc=subprocess.run([binary,'--format=custom','--no-owner','--no-acl','--no-password',
                '--file',str(temp),'--dbname',connection],env=env,
                capture_output=True,text=True,timeout=600)
            if proc.returncode:raise RuntimeError('pg_dump falhou; verifique conectividade, permissões e versão do cliente')
        os.replace(temp,final)
        report={'file':str(final),'filename':final.name,'sha256':digest(final),'bytes':final.stat().st_size,
                'timestamp':time.time(),'mode':db.settings.mode,'engine':engine,
                'same_device_exception':allow_same_device,'restore_tested':False}
        manifest=final.with_suffix(final.suffix+'.json')
        report['manifest']=str(manifest)
        with os.fdopen(os.open(manifest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
        with db.session() as s:
            s.merge(Meta(key='last_backup',value=json.dumps(report)))
            db.audit(s,'system:backup','backup_created',final.name,report)
        return report
    finally:
        if temp.exists():temp.unlink()

def verify_backup(manifest_path: str|Path) -> dict:
    manifest=Path(manifest_path).resolve();report=json.loads(manifest.read_text())
    path=(manifest.parent/report['filename']).resolve()
    if path.parent!=manifest.parent:raise ValueError('Caminho inválido no manifesto')
    if digest(path)!=report['sha256']:raise ValueError('Checksum SHA-256 divergente')
    if report['engine']=='sqlite':
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as s:
            integrity=s.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity!='ok':raise ValueError('Integridade SQLite inválida')
    elif report['engine']=='postgresql':
        binary=shutil.which('pg_restore')
        if not binary:raise ValueError('pg_restore necessário para examinar o arquivo')
        p=subprocess.run([binary,'--list',str(path)],capture_output=True,timeout=60)
        if p.returncode:raise ValueError('Arquivo PostgreSQL não pôde ser listado')
        integrity='archive_listed_only'
    else:raise ValueError('Tipo de backup não reconhecido')
    return {'file':str(path),'sha256':report['sha256'],'integrity':integrity,
            'restored_to_separate_database':False,
            'notice':'Checksum/estrutura não substituem restauração integral e teste funcional.'}
