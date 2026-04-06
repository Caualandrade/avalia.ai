# 🚀 GUID O DE DEPLOY - RENDER.COM

## ✅ Pré-requisitos
- Conta no GitHub com seu repositório pushado
- Conta no Render (https://render.com) - sign up com GitHub
- OpenAI API Key (se usar IA) ou deixe variável vazia

---

## 📝 PARTE 1: PREPARAR GITHUB

### 1️⃣ Fazer push do código para GitHub
```bash
git add .
git commit -m "Preparar para deploy no Render"
git push origin main
```

⚠️ **IMPORTANTE**: Certifique-se que `.env` NÃO está no git (verifique `.gitignore`)

---

## 🗄️ PARTE 2: CRIAR BANCO DE DADOS NO RENDER

### 1️⃣ Acessar Render.com
- Acesse https://render.com
- Faça login com GitHub
- Vá para Dashboard

### 2️⃣ Criar PostgreSQL Database
1. Clique em **"New +"** → **"PostgreSQL"**
2. Preencha:
   - **Name**: `avalia-ai-db` (nome do banco)
   - **Database**: `maturidade_ti` (nome da DB)
   - **User**: `postgres` (usuario padrão)
   - **Region**: Escolha próximo a você (ex: São Paulo se tiver)
   - **PostgreSQL Version**: 15
3. Clique **"Create Database"**

### 3️⃣ Copiar CONNECTION STRING
- Após criar, copie a **Internal Database URL**
- Formato: `postgresql://user:password@host:5432/database`
- **Guarde essa URL!** Você vai precisar



---

## 🐍 PARTE 3: DEPLOY BACKEND (FastAPI)

### 1️⃣ Criar novo Web Service
1. No Dashboard do Render: **"New +"** → **"Web Service"**
2. Conecte seu repositório GitHub
3. Preencha:
   ```
   Name:              avalia-ai-backend
   Root Directory:    backend/
   Runtime:           Docker
   Region:            São Paulo (ou próximo)
   Branch:            main
   Dockerfile Path:   Dockerfile
   ```

### 2️⃣ Configurar Variáveis de Ambiente
Vá em **"Environment"** e adicione:

| Variável | Valor |
|----------|-------|
| `DATABASE_URL` | _Cole a URL do PostgreSQL copiada acima_ |
| `SECRET_KEY` | `seu-secret-key-muito-grande-e-random-abc123xyz` |
| `OPENAI_API_KEY` | Sua chave do OpenAI (ou deixe vazio se não usar) |
| `PORT` | `8000` |

### 3️⃣ Configurar Health Check
- **Health Check Path**: `/docs` (FastAPI já tem docs)
- **Health Check Protocol**: HTTP

### 4️⃣ Deploy
- Clique **"Create Web Service"**
- Aguarde deployment (3-5 minutos)
- Acesse a URL gerada (ex: `https://avalia-ai-backend.onrender.com`)

**⚠️ Teste se funciona**: Acesse `https://seu-backend.onrender.com/docs`

---

## ⚛️ PARTE 4: DEPLOY FRONTEND (React)

### 1️⃣ Criar novo Web Service
1. Dashboard: **"New +"** → **"Web Service"**
2. Conecte GitHub
3. Preencha:
   ```
   Name:              avalia-ai-frontend
   Root Directory:    frontend/
   Runtime:           Docker
   Region:            São Paulo (ou próximo)
   Branch:            main
   Dockerfile Path:   Dockerfile
   ```

### 2️⃣ Configurar Variáveis de Ambiente
Vá em **"Environment"** e adicione:

| Variável | Valor |
|----------|-------|
| `VITE_API_URL` | `https://avalia-ai-backend.onrender.com` |

⚠️ **Com `https://` e SEM barra final!**

### 3️⃣ Deploy
- Clique **"Create Web Service"**
- Aguarde deployment (2-3 minutos)
- Acesse a URL gerada (ex: `https://avalia-ai-frontend.onrender.com`)

---

## 🔗 PARTE 5: TESTAR APLICAÇÃO

### 1️⃣ Abrir aplicação
```
Frontend: https://avalia-ai-frontend.onrender.com
Backend:  https://avalia-ai-backend.onrender.com/docs
Database: Criar usuário e testar login
```

### 2️⃣ Verificar Logs
Se algo der errado:
1. Vá no Web Service
2. Clique em **"Logs"**
3. Procure por erros

### 3️⃣ Testes Comuns

✅ **Frontend carrega?**
- Acesse a URL do frontend

✅ **API responde?**
- Acesse `https://seu-backend.onrender.com/docs`
- Tente fazer uma request na API

✅ **Banco de dados conecta?**
- Tente fazer login / criar conta

❌ **Erro CORS?**
- Verifique se `allow_origins=["*"]` está em `main.py`

---

## 💰 CUSTOS

| Serviço | Preço |
|---------|-------|
| Web Service (Backend) | Grátis (750h/mês) |
| Web Service (Frontend) | Grátis (750h/mês) |
| PostgreSQL Database | **$7/mês** (cheaper: $5/mês spinning disk) |
| **TOTAL** | **~$5-7/mês** |

> 💡 **Dica**: Se usar spinning disk (mais lento), cai para $5/mês

---

## 📱 ACESSO APÓS DEPLOY

```
🌐 Site:     https://avalia-ai-frontend.onrender.com
📚 API Docs: https://avalia-ai-backend.onrender.com/docs
🗄️ Database: Automático (gerenciado pelo Render)
```

---

## 🔄 COMO FAZER UPDATES

Quando mudar código:
1. Commit no GitHub
   ```bash
   git add .
   git commit -m "Minha mudança"
   git push origin main
   ```
2. Render fará **redeploy automático** (~2 minutos)

---

## ❓ TROUBLESHOOTING

| Problema | Solução |
|----------|---------|
| App não inicia | Verifique `DATABASE_URL` nas variáveis |
| Erro `pg_isready` | Espere 2-3 min após criar DB |
| Frontend não conecta backend | Verifique `VITE_API_URL` (sem / final) |
| Banco de dados vazio | Seed roda automático no `start.sh` |
| App "dormindo" | Normal no free tier - apenas acorde acessando |

---

## 🎉 PRONTO!

Sua app estará rodando 24/7 na internet por ~$5-7/mês!

Alguma dúvida sobre os passos? Me avise! 🚀
