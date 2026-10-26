from __future__ import annotations
import os
import json
import time
import threading
from contextlib import contextmanager
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from .models import Base, Meta, User, Controller, Asset, Audit, Knowledge
from .security import hash_password

PLC1 = {1,2,3,9,10,12}

class Database:
    def __init__(self, settings):
        self.settings=settings
        settings.data_dir.mkdir(parents=True,exist_ok=True)
        if settings.require_storage_mount:
            if not settings.storage_mount or not os.path.ismount(settings.storage_mount):
                raise RuntimeError('SSD ausente/não montado: inicialização bloqueada')
        args={'check_same_thread':False,'timeout':10} if settings.database_url.startswith('sqlite') else {}
        kwargs={} if settings.database_url.startswith('sqlite') else {'pool_size':3,'max_overflow':2,'pool_pre_ping':True}
        self.engine=create_engine(settings.database_url,connect_args=args,**kwargs)
        if settings.database_url.startswith('sqlite'):
            @event.listens_for(self.engine,'connect')
            def pragmas(dbapi_conn,_):
                dbapi_conn.execute('PRAGMA journal_mode=WAL')
                dbapi_conn.execute('PRAGMA synchronous=FULL')
                dbapi_conn.execute('PRAGMA foreign_keys=ON')
                dbapi_conn.execute('PRAGMA busy_timeout=10000')
        self.factory=sessionmaker(bind=self.engine,expire_on_commit=False)
        self.lock=threading.RLock()

    @contextmanager
    def session(self):
        with self.lock:
            with self.factory() as s:
                try:
                    yield s
                    s.commit()
                except Exception:
                    s.rollback()
                    raise

    def initialize(self):
        from .migrations import schema_status, CURRENT_SCHEMA, central_records
        status=schema_status(self)
        if not status['empty'] and status['version']!=CURRENT_SCHEMA:
            raise RuntimeError('Schema antigo: faça backup, pare a aplicação e execute scripts/migrate.py --apply explicitamente')
        Base.metadata.create_all(self.engine)
        with self.session() as s:
            mode=s.get(Meta,'mode')
            if mode and mode.value!=self.settings.mode:
                raise RuntimeError('Banco pertence a outro modo. Nunca misture demo e live; use outro DATABASE_URL.')
            schema=s.get(Meta,'schema_version')
            if schema and schema.value!=CURRENT_SCHEMA:
                raise RuntimeError('Versão de schema incompatível; faça migração explícita')
            if not mode:
                s.add(Meta(key='mode',value=self.settings.mode))
                s.add(Meta(key='schema_version',value=CURRENT_SCHEMA))
            if not s.get(Controller,1):
                s.add_all([Controller(id=1,name='CLP 1 · CAREL',assignment_confirmed=True),
                           Controller(id=2,name='CLP 2 · CAREL',assignment_confirmed=False),
                           Controller(id=3,name='CLP 3 · CAREL',assignment_confirmed=False)])
                s.flush()
                for i in range(1,15):
                    s.add(Asset(id=i,controller_id=1 if i in PLC1 else 2,name=f'UTA {i:02}',
                                kind='uta',
                                sector='Ambiente demonstrativo' if self.settings.mode=='demo' else 'Setor a cadastrar',
                                profile={'validated':self.settings.mode=='demo','demo_only':self.settings.mode=='demo',
                                         'temperature_tolerance':2.0,'humidity_tolerance':8.0,
                                         'persistence_seconds':300,'settling_seconds':120,'max_gap_seconds':45}))
                for record in central_records(self.settings.mode):
                    s.add(Asset(**record,profile={'validated':False,'demo_only':self.settings.mode=='demo'}))
            if not s.scalar(select(User.id).limit(1)) and self.settings.bootstrap_password:
                s.add(User(username='admin',name='Administrador HNSG',role='admin',
                           password_hash=hash_password(self.settings.bootstrap_password)))
            if not s.scalar(select(Knowledge.id).limit(1)):
                s.add(Knowledge(title='Limites do diagnóstico — base de desenvolvimento',revision='dev-1',
                    approved=True,body='Esta base não contém a sequência aprovada das UTAs do hospital. '
                    'Dados de demonstração não são medições do HNSG. Comando não comprova retorno físico. '
                    'Resfriamento e reaquecimento podem fazer parte de desumidificação legítima. '
                    'A análise não libera salas nem substitui inspeção técnica. Não alterar PID apenas por hipótese.'))

    def audit(self,s,username,action,target,data=None):
        s.add(Audit(username=username,action=action,target=str(target),data=data or {}))

    def close(self):
        self.engine.dispose()


def asdict(row):
    return {c.name:getattr(row,c.name) for c in row.__table__.columns}
