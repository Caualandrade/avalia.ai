# 🚀 DEPLOY NO RENDER - ATUALIZAR VARIÁVEIS DE PRODUÇÃO

## ✅ Código foi enviado para GitHub!

O código com todas as correções foi feito push para o GitHub. Agora você precisa:

1. **Acessar Render Dashboard**
2. **Atualizar variáveis de ambiente** nos Web Services
3. **Triggar novo deploy** (automático ao detectar push, ou manual)

---

## 📋 **PASSO 1: Acessar seu Backend no Render**

1. Vá para: https://dashboard.render.com
2. Clique em seu **Web Service do Backend** (ex: `avalia-ai-backend`)
3. Vá em **Environment** no menu lateral

---

## 🔐 **PASSO 2: Atualizar Variáveis do Backend**

As seguintes variáveis devem estar configuradas:

| Variável | Valor | Notas |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://user:password@host:port/db` | URL do Postgres do Render |
| `SECRET_KEY` | `gere-uma-string-muito-longa-e-aleatoria` | **MUDE!** Não use a padrão |
| `OPENAI_API_KEY` | Sua chave da OpenAI | Deixe vazio se não usar IA |
| `PORT` | `8000` | Padrão (Render define automaticamente) |

### 🔑 **Como gerar uma SECRET_KEY segura:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Cole o resultado na variável `SECRET_KEY` no Render.

---

## ⚛️ **PASSO 3: Acessar seu Frontend no Render**

1. No Dashboard, clique em seu **Web Service do Frontend** (ex: `avalia-ai-frontend`)
2. Vá em **Environment**

---

## 🌐 **PASSO 4: Atualizar Variáveis do Frontend**

Configure:

| Variável | Valor |
|----------|-------|
| `VITE_API_URL` | `https://seu-backend.onrender.com` |

⚠️ **IMPORTANTE**: 
- Use `https://` (NÃO `http://`)
- URL SEM barra final (`/`)
- Exemplo: `https://avalia-ai-backend.onrender.com`

---

## 🔄 **PASSO 5: Triggar novo Deploy**

Opção A - **Automático** (recomendado):
- Render detecta push no GitHub automaticamente
- Deploy começa em ~1-2 minutos
- Verifique em **Deployments**

Opção B - **Manual**:
1. No Web Service, clique em **"Deploy latest"** ou **"Manual Deploy"**
2. Aguarde ~3-5 minutos para cada serviço

---

## ✅ **PASSO 6: Verificar Deployment**

### Backend:
1. Acesse: `https://seu-backend.onrender.com/docs`
2. Deve aparecer a documentação da API (Swagger)

### Frontend:
1. Acesse: `https://seu-frontend.onrender.com`
2. Deve aparecer a tela de login

---

## 🆘 **Se der erro:**

### ❌ 404 no Frontend
- Verifique se `VITE_API_URL` está correto
- Aguarde rebuild completar (15-20 min primeira vez)

### ❌ 500 no Backend
- Verifique se `DATABASE_URL` está correto
- Verifique se secret key está configurada
- Veja logs: **Logs** no Web Service

### ❌ Erro de CORS
- Verifique se backend tem CORSMiddleware com `allow_origins=["*"]`

---

## 📊 **Monitorar Logs**

1. Abra Web Service no Render
2. Clique em **Logs**
3. Procure por erros relevantes

---

## 💡 **Próximas etapas (opcionais):**

1. **Configurar domínio customizado** (em vez de `onrender.com`)
2. **Ativar SSL/HTTPS** (automático no Render)
3. **Configurar alertas** se algo falhar
4. **Aumentar limite de recursos** se necessário

---

## 🎯 **URLs Finais após Deploy:**

```
Frontend:  https://seu-frontend.onrender.com
Backend:   https://seu-backend.onrender.com
API Docs:  https://seu-backend.onrender.com/docs
```

---

Pronto! Suas mudanças estão no ar! 🚀

Se algo der problema, veja os logs no Render Dashboard.
