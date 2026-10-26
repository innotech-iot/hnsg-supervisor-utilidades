import json
import shutil
import time

import pytest
from sqlalchemy import event, inspect, select, text

from app.config import Settings
from app.database import Database
from app.models import Base, Meta, Controller, Asset, Sample, User, Audit


def legacy_database(path,mode='demo'):
    db=Database(Settings(data_dir=path,mode=mode))
    # Frozen v1 asset definition: do not derive this fixture from the new schema.
    with db.engine.begin() as conn:
        conn.exec_driver_sql('CREATE TABLE assets (id INTEGER PRIMARY KEY, controller_id INTEGER NOT NULL '
            'REFERENCES controllers(id), name VARCHAR(100) NOT NULL, sector VARCHAR(200) NOT NULL, '
            'criticality VARCHAR(20) NOT NULL, profile JSON NOT NULL, revision INTEGER NOT NULL)')
    Base.metadata.create_all(db.engine)
    with db.session() as s:
        s.add_all([Meta(key='mode',value=mode),Meta(key='schema_version',value='1'),
            Controller(id=1,name='CLP preservado',host='127.0.0.1',enabled=False),
            Controller(id=2,name='CLP 2',assignment_confirmed=False)])
        s.flush()
        for aid in range(1,15):
            s.execute(text('INSERT INTO assets VALUES (:id,:cid,:name,:sector,:criticality,:profile,:revision)'),
                {'id':aid,'cid':1 if aid in {1,2,3,9,10,12} else 2,'name':f'UTA {aid:02}',
                 'sector':'Fixture preservada','criticality':'high','profile':json.dumps({'validated':False}),'revision':7})
        s.add(User(username='fixture',name='Usuário fictício',role='viewer',password_hash='hash-ficticio'))
        s.add(Sample(asset_id=1,ts=time.time(),data={'temperature':22.7},quality='good',source=mode,versions={'1':4}))
        s.add(Audit(username='fixture',action='fixture_preserved',target='1',data={'marker':'original'}))
    return db


def assert_migrated(db):
    with db.session() as s:
        assert s.get(Meta,'schema_version').value=='2'
        assert [(a.id,a.kind,a.controller_id) for a in s.scalars(select(Asset).order_by(Asset.id))]==[
            (i,'uta',1 if i in {1,2,3,9,10,12} else 2) for i in range(1,15)]+[(15,'cag',2),(16,'caq',3)]
        original=s.get(Asset,1)
        assert (original.sector,original.criticality,original.revision,original.profile)==('Fixture preservada','high',7,{'validated':False})
        assert s.get(Controller,1).host=='127.0.0.1'
        assert s.get(Controller,2).assignment_confirmed is False
        assert not s.get(Controller,3).enabled and not s.get(Controller,3).host
        assert all(not s.get(Asset,aid).profile.get('validated') for aid in [15,16])
        assert s.scalar(select(User)).password_hash=='hash-ficticio'
        assert s.scalar(select(Sample)).data=={'temperature':22.7}
        assert s.scalar(select(Audit).where(Audit.action=='fixture_preserved')).data=={'marker':'original'}


def test_migration_preserves_existing_data_and_is_idempotent(tmp_path):
    from app.migrations import migrate_database
    db=legacy_database(tmp_path)
    try:
        assert migrate_database(db)['changed'] is True
        assert_migrated(db)
        assert migrate_database(db)['changed'] is False
        with db.session() as s:
            assert len(s.scalars(select(Audit).where(Audit.action=='schema_migration')).all())==1
        db.initialize()
    finally:db.close()


def test_startup_requires_explicit_legacy_migration(tmp_path):
    db=legacy_database(tmp_path)
    try:
        with pytest.raises(RuntimeError,match='migrate.py'):db.initialize()
        assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
    finally:db.close()


@pytest.mark.parametrize('key,value',[('mode','live'),('schema_version','999')])
def test_migration_refuses_wrong_mode_or_version_without_changes(tmp_path,key,value):
    from app.migrations import migrate_database
    db=legacy_database(tmp_path)
    try:
        with db.session() as s:s.get(Meta,key).value=value
        with pytest.raises(RuntimeError):migrate_database(db)
        assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
        with db.session() as s:assert s.get(Controller,3) is None
    finally:db.close()


def test_migration_refuses_reserved_id_without_partial_changes(tmp_path):
    from app.migrations import migrate_database
    db=legacy_database(tmp_path)
    try:
        with db.engine.begin() as conn:
            conn.exec_driver_sql("INSERT INTO assets VALUES (15,2,'Outro equipamento','Fixture','low','{}',1)")
        with pytest.raises(RuntimeError,match='reservad'):migrate_database(db)
        assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
        with db.session() as s:assert s.get(Meta,'schema_version').value=='1'
    finally:db.close()


def test_migration_rolls_back_ddl_and_data_on_failure(tmp_path):
    from app.migrations import migrate_database
    db=legacy_database(tmp_path)
    def fail_insert(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().upper().startswith('INSERT INTO ASSETS'):
            raise RuntimeError('Falha injetada após DDL')
    try:
        event.listen(db.engine,'before_cursor_execute',fail_insert)
        with pytest.raises(RuntimeError,match='injetada'):migrate_database(db)
        event.remove(db.engine,'before_cursor_execute',fail_insert)
        assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
        with db.session() as s:
            assert s.get(Meta,'schema_version').value=='1'
            assert s.get(Controller,3) is None
    finally:db.close()


def test_restore_v1_backup_to_separate_database_then_migrate(tmp_path):
    from app.migrations import migrate_database
    from app.backups import perform_backup,verify_backup
    db=legacy_database(tmp_path/'original')
    destination=tmp_path/'backup';destination.mkdir()
    try:
        report=perform_backup(db,destination,allow_same_device=True)
        assert verify_backup(report['manifest'])['integrity']=='ok'
        restored_dir=tmp_path/'restored';restored_dir.mkdir()
        shutil.copy2(report['file'],restored_dir/'demo.db')
        restored=Database(Settings(data_dir=restored_dir))
        try:
            migrate_database(restored)
            restored.initialize()
            assert_migrated(restored)
        finally:restored.close()
        with db.session() as s:assert s.get(Meta,'schema_version').value=='1'
        assert 'kind' not in {c['name'] for c in inspect(db.engine).get_columns('assets')}
    finally:db.close()


def test_startup_refuses_version_label_without_current_structure(tmp_path):
    db=legacy_database(tmp_path)
    try:
        with db.session() as s:s.get(Meta,'schema_version').value='2'
        with pytest.raises(RuntimeError,match='incompatível'):db.initialize()
    finally:db.close()


def test_migration_cli_inspects_by_default_and_obeys_application_lock(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    from filelock import FileLock
    db=legacy_database(tmp_path)
    env=os.environ.copy()
    env.update(HNSG_DATA_DIR=str(tmp_path),HNSG_MODE='demo',DATABASE_URL='',OLLAMA_ENABLED='false',REQUIRE_SSD_MOUNT='false')
    command=[sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/migrate.py')]
    try:
        result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['version']=='1'
        with FileLock(str(tmp_path/'collector.lock')):
            result=subprocess.run(command+['--apply'],env=env,capture_output=True,text=True,timeout=20)
            assert result.returncode==2
        with db.session() as s:assert s.get(Meta,'schema_version').value=='1'
        result=subprocess.run(command+['--apply'],env=env,capture_output=True,text=True,timeout=20)
        assert result.returncode==0,result.stderr
        assert_migrated(db)
    finally:db.close()
