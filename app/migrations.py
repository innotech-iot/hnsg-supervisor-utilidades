"""Explicit, transactional revisions. Never invoked automatically at startup."""
from __future__ import annotations

import time
from sqlalchemy import inspect, select, insert, update
from .models import Meta, Controller, Asset, Audit, Base

CURRENT_SCHEMA='2'


def schema_status(db):
    with db.engine.connect() as conn:
        tables=set(inspect(conn).get_table_names())
        if not tables:
            return {'version':None,'current':CURRENT_SCHEMA,'empty':True,'mode':None}
        if not set(Base.metadata.tables)<=tables:
            raise RuntimeError('Banco incompleto/não reconhecido; restaure ou revise antes de migrar')
        metadata=dict(conn.execute(select(Meta.key,Meta.value)).all())
        if metadata.get('mode')!=db.settings.mode:
            raise RuntimeError('Banco pertence a outro modo. Nunca misture demo e live; use outro DATABASE_URL.')
        version=metadata.get('schema_version')
        if version not in {'1',CURRENT_SCHEMA}:
            raise RuntimeError('Versão de schema desconhecida; migração bloqueada')
        if version==CURRENT_SCHEMA and 'kind' not in {c['name'] for c in inspect(conn).get_columns('assets')}:
            raise RuntimeError('Schema incompatível com a versão registrada')
        return {'version':version,'current':CURRENT_SCHEMA,'empty':False,'mode':metadata['mode']}


def central_records(mode):
    return [dict(id=15,controller_id=2,name='CAG',kind='cag'),
            dict(id=16,controller_id=3,name='CAQ',kind='caq')]


def migrate_database(db):
    if db.engine.dialect.name not in {'sqlite','postgresql'}:
        raise RuntimeError('Migração suportada somente em SQLite/PostgreSQL')
    status=schema_status(db)
    if status['empty']:raise RuntimeError('Banco vazio: inicie a aplicação para criar o schema atual')
    with db.engine.begin() as conn:
        if db.engine.dialect.name=='sqlite':
            # sqlite3 legacy transaction mode does not begin for DDL by itself.
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.exec_driver_sql('LOCK TABLE meta, controllers, assets IN EXCLUSIVE MODE')
        metadata=dict(conn.execute(select(Meta.key,Meta.value)).all())
        if metadata.get('mode')!=db.settings.mode:raise RuntimeError('Banco pertence a outro modo')
        version=metadata.get('schema_version')
        if version==CURRENT_SCHEMA:
            if 'kind' not in {c['name'] for c in inspect(conn).get_columns('assets')}:
                raise RuntimeError('Schema incompatível com a versão registrada')
            return {'changed':False,'from':version,'to':CURRENT_SCHEMA}
        if version!='1':raise RuntimeError('Versão de schema desconhecida; migração bloqueada')
        if conn.scalar(select(Controller.id).where(Controller.id==3)) or conn.scalar(select(Asset.id).where(Asset.id.in_([15,16]))):
            raise RuntimeError('IDs reservados para CLP 3/CAG/CAQ ocupados; revisão manual necessária')
        if not {1,2}<=set(conn.scalars(select(Controller.id))):
            raise RuntimeError('Cadastro legado de controladores incompleto')
        if 'kind' in {c['name'] for c in inspect(conn).get_columns('assets')}:
            raise RuntimeError('Schema 1 já contém kind; não adotar alteração parcial automaticamente')
        conn.exec_driver_sql("ALTER TABLE assets ADD COLUMN kind VARCHAR(12) NOT NULL DEFAULT 'uta'")
        conn.execute(insert(Controller).values(id=3,name='CLP 3 · CAREL',host='',enabled=False,assignment_confirmed=False))
        for record in central_records(db.settings.mode):
            conn.execute(insert(Asset).values(**record,sector='Setor a cadastrar',
                profile={'validated':False,'demo_only':db.settings.mode=='demo'}))
        conn.execute(update(Meta).where(Meta.key=='schema_version').values(value=CURRENT_SCHEMA))
        conn.execute(insert(Audit).values(ts=time.time(),username='system:migration',
            action='schema_migration',target='1->2',data={'from':'1','to':CURRENT_SCHEMA,
                'added_assets':[15,16],'added_controllers':[3],'connections_enabled':False}))
    return {'changed':True,'from':'1','to':CURRENT_SCHEMA}
