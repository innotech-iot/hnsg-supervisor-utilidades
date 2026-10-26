from __future__ import annotations
import time
from sqlalchemy import Boolean, Column, Float, Integer, String, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Meta(Base):
    __tablename__='meta'
    key=Column(String(80),primary_key=True)
    value=Column(Text,nullable=False)

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    username=Column(String(80),unique=True,nullable=False)
    name=Column(String(160),nullable=False)
    password_hash=Column(Text,nullable=False)
    role=Column(String(20),nullable=False)
    active=Column(Boolean,default=True,nullable=False)

class Session(Base):
    __tablename__='sessions'
    id=Column(String(64),primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True)
    csrf=Column(String(100),nullable=False)
    expires=Column(Float,nullable=False)

class Controller(Base):
    __tablename__='controllers'
    id=Column(Integer,primary_key=True)
    name=Column(String(100),nullable=False)
    host=Column(String(200),default='',nullable=False)
    port=Column(Integer,default=502,nullable=False)
    unit_id=Column(Integer,default=1,nullable=False)
    enabled=Column(Boolean,default=False,nullable=False)
    assignment_confirmed=Column(Boolean,default=False,nullable=False)
    map_revision=Column(Integer,default=0,nullable=False)
    revision=Column(Integer,default=1,nullable=False)

class Asset(Base):
    __tablename__='assets'
    id=Column(Integer,primary_key=True)
    controller_id=Column(Integer,ForeignKey('controllers.id'),nullable=False)
    name=Column(String(100),nullable=False)
    kind=Column(String(12),default='uta',server_default='uta',nullable=False)
    sector=Column(String(200),default='Setor a cadastrar',nullable=False)
    criticality=Column(String(20),default='unclassified',nullable=False)
    profile=Column(JSON,default=dict,nullable=False)
    revision=Column(Integer,default=1,nullable=False)

class Room(Base):
    __tablename__='rooms'
    id=Column(Integer,primary_key=True)
    asset_id=Column(Integer,ForeignKey('assets.id'),nullable=False)
    name=Column(String(180),nullable=False)
    purpose=Column(String(200),default='',nullable=False)
    owner=Column(String(180),default='',nullable=False)
    criticality=Column(String(30),default='unclassified',nullable=False)
    notes=Column(Text,default='',nullable=False)

class Tag(Base):
    __tablename__='tags'
    id=Column(Integer,primary_key=True)
    controller_id=Column(Integer,ForeignKey('controllers.id'),nullable=False,index=True)
    asset_id=Column(Integer,ForeignKey('assets.id'),nullable=True,index=True)
    symbol=Column(String(200),nullable=False)
    description=Column(String(500),default='',nullable=False)
    label=Column(String(200),default='',nullable=False)
    area=Column(String(20),nullable=False)
    address=Column(Integer,nullable=False)
    data_type=Column(String(20),nullable=False)
    scale=Column(Float,nullable=False)
    offset=Column(Float,default=0,nullable=False)
    unit=Column(String(40),default='',nullable=False)
    word_order=Column(String(20),default='big',nullable=False)
    byte_order=Column(String(20),default='big',nullable=False)
    access=Column(String(10),default='RO',nullable=False)
    semantic=Column(String(60),nullable=True)
    is_alarm=Column(Boolean,default=False,nullable=False)
    alarm_value=Column(Float,default=1,nullable=False)
    alarm_priority=Column(String(20),default='warning',nullable=False)
    instrument=Column(JSON,default=dict,nullable=False)
    validated=Column(Boolean,default=False,nullable=False)
    active=Column(Boolean,default=True,nullable=False)
    poll_seconds=Column(Integer,default=5,nullable=False)
    map_revision=Column(Integer,default=1,nullable=False)
    revision=Column(Integer,default=1,nullable=False)
    __table_args__=(UniqueConstraint('controller_id','symbol','map_revision',name='uq_tag_revision'),)

class ImportBatch(Base):
    __tablename__='imports'
    id=Column(String(40),primary_key=True)
    controller_id=Column(Integer,ForeignKey('controllers.id'),nullable=False)
    filename=Column(String(200),nullable=False)
    sha256=Column(String(64),nullable=False)
    raw_text=Column(Text,nullable=False)
    parsed=Column(JSON,nullable=False)
    created=Column(Float,default=time.time,nullable=False)
    activated=Column(Boolean,default=False,nullable=False)

class Sample(Base):
    __tablename__='samples'
    id=Column(Integer,primary_key=True)
    asset_id=Column(Integer,ForeignKey('assets.id'),nullable=False)
    ts=Column(Float,nullable=False)
    data=Column(JSON,nullable=False)
    quality=Column(String(24),nullable=False)
    source=Column(String(20),nullable=False)
    versions=Column(JSON,default=dict,nullable=False)
    __table_args__=(Index('ix_samples_asset_ts','asset_id','ts'),)

class PointSnapshot(Base):
    __tablename__='point_snapshots'
    id=Column(Integer,primary_key=True)
    controller_id=Column(Integer,nullable=False)
    ts=Column(Float,nullable=False)
    data=Column(JSON,nullable=False)
    __table_args__=(Index('ix_point_snapshots_controller_ts','controller_id','ts'),)

class Aggregate(Base):
    __tablename__='hourly_aggregates'
    id=Column(Integer,primary_key=True)
    asset_id=Column(Integer,nullable=False)
    hour=Column(Float,nullable=False)
    data=Column(JSON,nullable=False)
    count=Column(Integer,nullable=False)
    valid_count=Column(Integer,nullable=False)
    __table_args__=(UniqueConstraint('asset_id','hour',name='uq_aggregate_asset_hour'),)

class Alarm(Base):
    __tablename__='alarms'
    id=Column(Integer,primary_key=True)
    key=Column(String(120),nullable=False,index=True)
    asset_id=Column(Integer,nullable=True)
    controller_id=Column(Integer,nullable=True)
    code=Column(String(80),nullable=False)
    title=Column(String(200),nullable=False)
    priority=Column(String(20),nullable=False)
    source=Column(String(30),nullable=False)
    evidence=Column(JSON,nullable=False)
    active=Column(Boolean,default=True,nullable=False)
    first_seen=Column(Float,default=time.time,nullable=False)
    last_seen=Column(Float,default=time.time,nullable=False)
    closed_at=Column(Float,nullable=True)
    ack_user=Column(String(80),nullable=True)
    ack_at=Column(Float,nullable=True)
    review=Column(String(30),default='pending',nullable=False)
    note=Column(Text,default='',nullable=False)

class Audit(Base):
    __tablename__='audit'
    id=Column(Integer,primary_key=True)
    ts=Column(Float,default=time.time,nullable=False,index=True)
    username=Column(String(80),nullable=False)
    action=Column(String(80),nullable=False)
    target=Column(String(150),nullable=False)
    data=Column(JSON,nullable=False)

class Ticket(Base):
    __tablename__='tickets'
    id=Column(Integer,primary_key=True)
    asset_id=Column(Integer,nullable=True)
    title=Column(String(200),nullable=False)
    details=Column(Text,default='',nullable=False)
    owner=Column(String(150),default='',nullable=False)
    state=Column(String(30),default='open',nullable=False)
    created=Column(Float,default=time.time,nullable=False)
    updated=Column(Float,default=time.time,nullable=False)
    username=Column(String(80),nullable=False)

class Knowledge(Base):
    __tablename__='knowledge'
    id=Column(Integer,primary_key=True)
    title=Column(String(200),nullable=False)
    body=Column(Text,nullable=False)
    revision=Column(String(100),nullable=False)
    asset_id=Column(Integer,nullable=True)
    approved=Column(Boolean,default=False,nullable=False)
    created=Column(Float,default=time.time,nullable=False)

class Command(Base):
    __tablename__='commands'
    id=Column(String(70),primary_key=True)
    user_id=Column(Integer,nullable=False)
    asset_id=Column(Integer,nullable=False)
    semantic=Column(String(60),nullable=False)
    before=Column(Float,nullable=False)
    requested=Column(Float,nullable=False)
    expires=Column(Float,nullable=False)
    state=Column(String(30),default='prepared',nullable=False)
