import json
import os
from types import SimpleNamespace
from pathlib import Path
import pytest
from app.config import Settings
from app.database import Database

def test_backup_refuses_same_disk_by_default(tmp_path):
    from app.backups import perform_backup
    db=Database(Settings(data_dir=tmp_path/'data'));db.initialize()
    dest=tmp_path/'backup';dest.mkdir()
    try:
        with pytest.raises(ValueError,match='dispositivo'):
            perform_backup(db,dest)
    finally:db.close()

def test_sqlite_backup_checksum_integrity_and_tamper(tmp_path):
    from app.backups import perform_backup,verify_backup
    db=Database(Settings(data_dir=tmp_path/'data'));db.initialize()
    dest=tmp_path/'backup';dest.mkdir()
    try:report=perform_backup(db,dest,allow_same_device=True)
    finally:db.close()
    assert verify_backup(report['manifest'])['integrity']=='ok'
    with open(report['file'],'ab') as f:f.write(b'tamper')
    with pytest.raises(ValueError,match='Checksum'):verify_backup(report['manifest'])


@pytest.mark.parametrize('source_device,destination_device,refused', [(2,2,True),(2,1,False)])
def test_backup_device_guard_uses_sqlite_file(tmp_path,monkeypatch,source_device,destination_device,refused):
    from app.backups import perform_backup,verify_backup
    source=tmp_path/'external.sqlite3'
    db=Database(Settings(data_dir=tmp_path/'data',database_url=f'sqlite:///{source}'))
    db.initialize()
    dest=tmp_path/'backup';dest.mkdir()
    original_stat=Path.stat

    def device_stat(path,*args,**kwargs):
        result=original_stat(path,*args,**kwargs)
        if path in {source,dest,db.settings.data_dir}:
            values=list(result)
            values[2]=source_device if path==source else destination_device if path==dest else 1
            return os.stat_result(values)
        return result

    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path,'stat',device_stat)
            if refused:
                with pytest.raises(ValueError,match='dispositivo'):
                    perform_backup(db,dest)
                assert not list(dest.iterdir())
            else:
                report=perform_backup(db,dest)
        if not refused:
            assert verify_backup(report['manifest'])['integrity']=='ok'
    finally:db.close()


def test_verified_sqlite_backup_releases_file(tmp_path):
    from app.backups import perform_backup,verify_backup
    db=Database(Settings(data_dir=tmp_path/'data'));db.initialize()
    dest=tmp_path/'backup';dest.mkdir()
    try:report=perform_backup(db,dest,allow_same_device=True)
    finally:db.close()
    assert verify_backup(report['manifest'])['integrity']=='ok'
    backup=Path(report['file'])
    moved=backup.with_suffix('.moved')
    backup.rename(moved)
    moved.unlink()


@pytest.mark.parametrize('password_in_query',[False,True])
def test_postgres_backup_keeps_password_out_of_process_arguments(tmp_path,monkeypatch,password_in_query):
    from sqlalchemy.engine import URL,make_url
    from app.backups import perform_backup
    import app.backups as backups
    db=Database(Settings(data_dir=tmp_path/'data'));db.initialize()
    dest=tmp_path/'backup';dest.mkdir()
    password='fixture-secret-only'
    url=URL.create('postgresql+psycopg',username='fixture',host='127.0.0.1',port=5433,
        database='fixture',password=None if password_in_query else password,
        query={'password':password,'sslmode':'require'} if password_in_query else {'sslmode':'require'})
    # Real mode/audit transaction in SQLite; only pg_dump is unavailable locally.
    proxy=SimpleNamespace(engine=SimpleNamespace(dialect=SimpleNamespace(name='postgresql'),url=url),
        settings=db.settings,session=db.session,audit=db.audit)
    observed={}
    def dump(command,**kwargs):
        observed.update(command=command,env=kwargs['env'])
        Path(command[command.index('--file')+1]).write_bytes(b'PGDMP-fixture')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(backups.shutil,'which',lambda name:'fixture-pg_dump')
    monkeypatch.setattr(backups.subprocess,'run',dump)
    try:report=perform_backup(proxy,dest,allow_same_device=True)
    finally:db.close()
    connection=make_url(observed['command'][observed['command'].index('--dbname')+1])
    assert connection.password is None
    assert 'password' not in connection.query
    assert observed['env']['PGPASSWORD']==password
    assert (connection.drivername,connection.host,connection.port,connection.database)==('postgresql','127.0.0.1',5433,'fixture')
    assert connection.query['sslmode']=='require'
    assert '--no-password' in observed['command']
    assert password not in Path(report['manifest']).read_text()
