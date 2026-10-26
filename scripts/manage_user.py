#!/usr/bin/env python3
"""Explicit local administrator maintenance. Prompts do not echo passwords."""
import argparse
import getpass
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select,delete
from app.config import Settings
from app.database import Database
from app.models import User,Session
from app.security import hash_password

def main():
    p=argparse.ArgumentParser(description='Criar usuário ou redefinir senha localmente; requer acesso ao banco.')
    p.add_argument('action',choices=['create','reset'])
    p.add_argument('username')
    p.add_argument('--role',choices=['admin','operator','viewer'],default='admin')
    p.add_argument('--name',default='Administrador HNSG')
    args=p.parse_args()
    if not 3<=len(args.username)<=80:raise SystemExit('Usuário deve ter 3 a 80 caracteres')
    password=getpass.getpass('Nova senha (mínimo 12 caracteres): ')
    confirmation=getpass.getpass('Confirme: ')
    if password!=confirmation:raise SystemExit('Senhas diferentes')
    encoded=hash_password(password)
    db=Database(Settings.from_env());db.initialize()
    try:
        with db.session() as s:
            user=s.scalar(select(User).where(User.username==args.username))
            if args.action=='create':
                if user:raise SystemExit('Usuário já existe')
                s.add(User(username=args.username,name=args.name,role=args.role,password_hash=encoded))
            else:
                if not user:raise SystemExit('Usuário não existe')
                user.password_hash=encoded;s.execute(delete(Session).where(Session.user_id==user.id))
            db.audit(s,'local-admin','user_'+args.action,args.username,{'via':'CLI local'})
        print('Operação concluída. Nenhuma senha foi escrita em arquivo.')
    finally:db.close()
if __name__=='__main__':main()
