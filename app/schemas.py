from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Login(Strict):
    username:str=Field(min_length=1,max_length=80)
    password:str=Field(min_length=1,max_length=256)
class PasswordChange(Strict):
    current:str=Field(max_length=256)
    password:str=Field(min_length=12,max_length=256)
class UserCreate(Strict):
    username:str=Field(pattern=r'^[a-zA-Z0-9_.-]{3,80}$')
    name:str=Field(min_length=2,max_length=160)
    role:Literal['viewer','operator','admin']
    password:str=Field(min_length=12,max_length=256)
class UserPatch(Strict):
    active:bool
    role:Literal['viewer','operator','admin']
class ControllerPatch(Strict):
    host:str=Field(max_length=200)
    port:int=Field(ge=1,le=65535)
    unit_id:int=Field(ge=1,le=247)
    enabled:bool
    assignment_confirmed:bool
    expected_revision:int
    reason:str=Field(min_length=8,max_length=500)
class TagPatch(Strict):
    asset_id:int|None=Field(default=None,ge=1)
    semantic:str|None=Field(default=None,max_length=60)
    label:str=Field(default='',max_length=200)
    validated:bool=False
    poll_seconds:int=Field(default=5,ge=2,le=3600)
    is_alarm:bool=False
    alarm_value:float=1
    alarm_priority:Literal['info','warning','critical']='warning'
    sensor_location:str=Field(default='',max_length=200)
    sensor_model:str=Field(default='',max_length=120)
    calibration_due:str=Field(default='',max_length=40)
    expected_revision:int
    reason:str=Field(min_length=8,max_length=500)
class Profile(Strict):
    validated:bool=False
    fan_confirmation_validated:bool=False
    temperature_tolerance:float=Field(default=2,gt=0,le=30)
    humidity_tolerance:float=Field(default=8,gt=0,le=100)
    persistence_seconds:int=Field(default=300,ge=30,le=7200)
    settling_seconds:int=Field(default=120,ge=0,le=7200)
    max_gap_seconds:int=Field(default=45,ge=3,le=300)
class AssetPatch(Strict):
    name:str=Field(min_length=2,max_length=100)
    sector:str=Field(min_length=2,max_length=200)
    criticality:Literal['unclassified','low','medium','high']='unclassified'
    profile:Profile
    expected_revision:int
    reason:str=Field(min_length=8,max_length=500)
class Preview(Strict):
    controller_id:int=Field(ge=1)
    filename:str=Field(min_length=1,max_length=200)
    text:str=Field(max_length=2_000_000)
    address_base:int|None=None
    delimiter:Literal[';',',','\t','|']|None=None
class Activate(Strict):
    confirmation:str
class Review(Strict):
    review:Literal['pending','investigating','confirmed','false_positive','expected']
    note:str=Field(min_length=3,max_length=2000)
class TicketCreate(Strict):
    asset_id:int|None=Field(default=None,ge=1)
    title:str=Field(min_length=3,max_length=200)
    details:str=Field(default='',max_length=5000)
    owner:str=Field(default='',max_length=150)
class TicketPatch(Strict):
    state:Literal['open','investigating','resolved']
    details:str=Field(max_length=5000)
class RoomCreate(Strict):
    asset_id:int=Field(ge=1)
    name:str=Field(min_length=2,max_length=180)
    purpose:str=Field(default='',max_length=200)
    owner:str=Field(default='',max_length=180)
    criticality:Literal['unclassified','low','medium','high']='unclassified'
    notes:str=Field(default='',max_length=4000)
class KnowledgeCreate(Strict):
    title:str=Field(min_length=3,max_length=200)
    body:str=Field(min_length=20,max_length=60_000)
    revision:str=Field(min_length=1,max_length=100)
    asset_id:int|None=Field(default=None,ge=1)
    approved:bool=False
class Prepare(Strict):
    asset_id:int=Field(ge=1)
    semantic:Literal['temp_sp','humidity_sp','airflow_sp','mode']
    value:float
    expected:float
    reason:str=Field(min_length=8,max_length=500)
class AIHistory(Strict):
    hours:int=Field(ge=1,le=168,strict=True)
    metrics:list[str]=Field(min_length=1,max_length=6)

class AIQuestion(Strict):
    asset_id:int=Field(ge=1)
    question:str=Field(min_length=3,max_length=1000)
    history:AIHistory|None=None
