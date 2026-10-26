from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def flag(name: str, default=False) -> bool:
    return os.getenv(name, str(default)).lower() in {'1', 'true', 'yes'}

@dataclass
class Settings:
    mode: str = 'demo'
    database_url: str = ''
    data_dir: Path = ROOT / 'runtime'
    poll_seconds: float = 2.0
    history_seconds: float = 10.0
    stale_seconds: float = 15.0
    session_hours: int = 8
    secure_cookie: bool = False
    bootstrap_password: str = ''
    run_collector: bool = True
    seed_hours: float = 3.0
    demo_full: bool = False
    demo_scenario: str = 'normal'
    ollama_enabled: bool = False
    ollama_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = ''
    ollama_timeout: float = 30.0
    history_days: int = 7
    aggregate_days: int = 365
    storage_mount: str = ''
    require_storage_mount: bool = False

    def __post_init__(self):
        self.data_dir = Path(self.data_dir).resolve()
        if self.mode not in {'demo', 'live'}:
            raise ValueError('HNSG_MODE deve ser demo ou live')
        if self.demo_scenario not in {'normal', 'faults'}:
            raise ValueError('DEMO_SCENARIO deve ser normal ou faults')
        if not 0 <= self.seed_hours <= 168:
            raise ValueError('DEMO_SEED_HOURS deve estar entre 0 e 168')
        if self.poll_seconds < 1 or self.history_seconds < self.poll_seconds:
            raise ValueError('Aquisição mínima 1 s; histórico não pode ser mais rápido que aquisição')
        if not self.database_url:
            self.database_url = f'sqlite:///{self.data_dir / (self.mode + ".db")}'
        if self.ollama_enabled and not self.ollama_model:
            raise ValueError('Defina OLLAMA_MODEL explicitamente; nenhum modelo será baixado automaticamente')

    @classmethod
    def from_env(cls):
        return cls(mode=os.getenv('HNSG_MODE','demo'),
                   data_dir=Path(os.getenv('HNSG_DATA_DIR',str(ROOT/'runtime'))),
                   database_url=os.getenv('DATABASE_URL',''),
                   poll_seconds=float(os.getenv('POLL_SECONDS','2')),
                   history_seconds=float(os.getenv('HISTORY_SECONDS','10')),
                   stale_seconds=float(os.getenv('STALE_SECONDS','15')),
                   secure_cookie=flag('COOKIE_SECURE'),
                   bootstrap_password=os.getenv('BOOTSTRAP_PASSWORD',''),
                   run_collector=not flag('DISABLE_COLLECTOR'),
                   seed_hours=float(os.getenv('DEMO_SEED_HOURS','3')),
                   demo_full=flag('DEMO_FULL'),
                   demo_scenario=os.getenv('DEMO_SCENARIO','normal'),
                   ollama_enabled=flag('OLLAMA_ENABLED'),
                   ollama_url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/'),
                   ollama_model=os.getenv('OLLAMA_MODEL',''),
                   ollama_timeout=float(os.getenv('OLLAMA_TIMEOUT','30')),
                   history_days=int(os.getenv('HISTORY_DAYS','7')),
                   aggregate_days=int(os.getenv('AGGREGATE_DAYS','365')),
                   storage_mount=os.getenv('SSD_MOUNT',''),
                   require_storage_mount=flag('REQUIRE_SSD_MOUNT'))
