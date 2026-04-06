#!/usr/bin/env python3
"""
🔍 SCRIPT DE DIAGNÓSTICO - Verificar backend no Render
Execute isto no terminal do backend no Render para diagnosticar problemas
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*60)
print("🔍 DIAGNÓSTICO DO BACKEND - Avalia.AI")
print("="*60 + "\n")

# 1. Verificar variáveis de ambiente
print("📋 VARIÁVEIS DE AMBIENTE:")
print("-" * 60)

required_vars = ['DATABASE_URL', 'SECRET_KEY', 'PORT']
for var in required_vars:
    value = os.getenv(var)
    if var == 'DATABASE_URL':
        masked = value[:20] + '***' if value else 'NÃO DEFINIDA'
    elif var == 'SECRET_KEY':
        masked = '***' if value else 'NÃO DEFINIDA'
    else:
        masked = value or 'NÃO DEFINIDA'
    
    status = "✅" if value else "❌"
    print(f"{status} {var:<20} = {masked}")

print("\n")

# 2. Conectar ao banco de dados
print("📊 BANCO DE DADOS:")
print("-" * 60)

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    from database import SessionLocal, engine
    from sqlalchemy import text
    
    db = SessionLocal()
    result = db.execute(text("SELECT 1"))
    db.close()
    print("✅ Conexão com banco de dados: OK")
except Exception as e:
    print(f"❌ Erro ao conectar banco: {e}")

print("\n")

# 3. Verificar modelos
print("👤 USUÁRIOS NO BANCO:")
print("-" * 60)

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    from database import SessionLocal
    from models import User
    
    db = SessionLocal()
    users = db.query(User).all()
    
    if users:
        print(f"✅ {len(users)} usuário(s) encontrado(s):")
        for user in users:
            print(f"   - {user.username} ({user.email}) - Role: {user.role}")
    else:
        print("❌ NENHUM USUÁRIO ENCONTRADO!")
        print("   Execute: python check_users.py")
    
    db.close()
except Exception as e:
    print(f"❌ Erro ao verificar usuários: {e}")

print("\n")

# 4. Verificar CORS
print("🔒 SEGURANÇA (CORS):")
print("-" * 60)

try:
    with open('backend/main.py', 'r') as f:
        content = f.read()
        if 'CORSMiddleware' in content and 'allow_origins=["*"]' in content:
            print("✅ CORS habilitado para todas as origins")
        else:
            print("⚠️  Verifique configuração de CORS em main.py")
except Exception as e:
    print(f"❌ Erro ao verificar CORS: {e}")

print("\n" + "="*60)
print("📌 RESUMO:")
print("="*60)
print("""
Se vir ❌ acima:
1. Verifique variáveis de ambiente no Render Dashboard
2. Se banco está offline, reinicie no Render
3. Se não há usuários, execute: python check_users.py

Se todos estiverem ✅ mas ainda der erro:
1. Veja os logs do backend: Logs no Dashboard Render
2. Procure por status 500 ou 401
3. Verifique arquivo TROUBLESHOOTING_LOGIN.md
""")
print("="*60 + "\n")
