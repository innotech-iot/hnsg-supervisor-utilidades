#!/usr/bin/env python3
"""Run on ANOTHER host. Exit status integrates with hospital monitoring; no notifications configured."""
import argparse,json,sys,urllib.request
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('base_url');a=p.parse_args()
try:
    with urllib.request.urlopen(a.base_url.rstrip('/')+'/health/ready',timeout=5) as r:
        ready=json.load(r).get('ready') is True
except Exception:ready=False
print(json.dumps({'ready':ready,'checked_at':datetime.now(timezone.utc).isoformat()}))
sys.exit(0 if ready else 2)
