#!/usr/bin/env python3
"""
🔑 SCRIPT DE VERIFICAÇÃO/CRIAÇÃO DE USUÁRIOS
Execute isto para verificar se há usuários no banco e criar um admin
"""

import os
import sys
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, engine
from models import Base, User, UserRole
from main import get_password_hash

def check_users():
    """Verifica usuários existentes no banco"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        if not users:
            print("\n❌ NENHUM USUÁRIO ENCONTRADO NO BANCO!")
            print("Você precisa criar pelo menos um usuário admin.\n")
            return False
        
        print(f"\n✅ {len(users)} usuário(s) encontrado(s):\n")
        for user in users:
            print(f"  👤 {user.username}")
            print(f"     Email: {user.email}")
            print(f"     Role: {user.role}")
            print(f"     Criado em: {user.created_at}\n")
        
        return True
    finally:
        db.close()

def create_admin_user(username='admin', password='admin123', email='admin@avalia.ai'):
    """Cria um usuário admin padrão"""
    db = SessionLocal()
    try:
        # Verifica se já existe
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"⚠️  Usuário '{username}' já existe!")
            return False
        
        # Cria novo usuário
        new_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN
        )
        db.add(new_user)
        db.commit()
        
        print(f"\n✅ USUÁRIO CRIADO COM SUCESSO!\n")
        print(f"  👤 Username: {username}")
        print(f"  🔑 Password: {password}")
        print(f"  📧 Email: {email}")
        print(f"  ⭐ Role: ADMIN\n")
        print("⚠️  GUARDE ESSAS CREDENCIAIS! Use-as para fazer login.\n")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    print("\n" + "="*50)
    print("🔑 GERENCIADOR DE USUÁRIOS - Avalia.AI")
    print("="*50)
    
    # Verifica conexão com banco
    try:
        print("\n📍 Testando conexão com banco de dados...")
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Banco de dados conectado!\n")
    except Exception as e:
        print(f"❌ Erro ao conectar banco: {e}")
        print("Verifique DATABASE_URL em .env\n")
        return
    
    # Verifica usuários
    has_users = check_users()
    
    if not has_users:
        print("\n" + "-"*50)
        print("Criando usuário admin padrão...")
        print("-"*50)
        create_admin_user()
        
        print("Para usar credenciais diferentes, execute:")
        print("  python check_users.py --create <username> <password> <email>\n")
    
    print("="*50)
    print("✅ Verificação concluída!")
    print("="*50 + "\n")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerenciador de usuários')
    parser.add_argument('--create', nargs=3, metavar=('USERNAME', 'PASSWORD', 'EMAIL'),
                       help='Criar novo usuário admin')
    
    args = parser.parse_args()
    
    if args.create:
        username, password, email = args.create
        print(f"\n📍 Criando usuário: {username}")
        create_admin_user(username, password, email)
    else:
        main()
