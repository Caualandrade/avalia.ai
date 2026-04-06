# 🔴 ERRO DE LOGIN NO RENDER - DIAGNÓSTICO

## 📦 O que você está vendo:

- Erro de requisição axios
- Stack trace com múltiplas chamadas de rede
- Página de login não funciona

---

## 🔍 **PASSO 1: Verificar Logs do Backend no Render**

1. Vá para: https://dashboard.render.com
2. Clique no **Web Service do Backend**
3. Clique em **Logs**
4. Procure por mensagens de erro (status 500, 404, que tal)

**Observe:**
- Há erros de conexão com banco de dados?
- Há erros de import de módulos?
- O servidor iniciou corretamente?

---

## 🌐 **PASSO 2: Verificar se Backend está respondendo**

Abra o navegador e acesse:

```
https://seu-backend.onrender.com/
```

**Esperado**: Deve ver um JSON com `{"message": "Bem-vindo à API de Maturidade TI"}`

**Se vir erro 404 ou 500**:
- Backend não está rodando corretamente
- Veja os logs no Dashboard

---

## 📡 **PASSO 3: Verificar URL da API no Frontend**

No navegador, abra o Console (F12) e execute:

```javascript
// Verificar qual URL o frontend está tentando usar
import { API_URL } from './config';
console.log('API URL:', API_URL);
```

**Deve mostrar**: `https://seu-backend.onrender.com`

Se mostrar `http://localhost:8000` → **PROBLEMA**: variável de ambiente não foi carregada!

---

## 🔧 **PASSO 4: Verificar variáveis de ambiente do Frontend**

1. Vá no Dashboard do Frontend no Render
2. Clique em **Environment**
3. Procure por `VITE_API_URL`

**Se estiver errada ou faltando:**
1. Corrija para: `https://seu-backend.onrender.com` (sem barra final)
2. Clique **Save**
3. Aguarde redeploy automático (~2 min)

---

## ⚙️ **PASSO 5: Verificar variáveis de ambiente do Backend**

No Backend, verifique:

| Variável | Status |
|----------|--------|
| `DATABASE_URL` | Deve estar configurada |
| `SECRET_KEY` | Deve estar configurada |
| `OPENAI_API_KEY` | Pode estar vazio |
| `PORT` | Deve ser `8000` |

**Se faltar algo:**
1. Configure no Render Dashboard
2. Clique **Save**
3. Aguarde redeploy

---

## 💾 **PASSO 6: Verificar Usuários no Banco**

No terminal do Render (ou localmente):

```bash
# Rodar script de diagnóstico
python diagnose_backend.py

# Ou criar usuário admin
python check_users.py
```

Se não houver usuários, o login vai falhar com **401 Unauthorized**.

---

## 🚀 **PASSO 7: Forçar novo Deploy**

Se tudo está correto, force um novo deploy:

1. Backend: Clique **"Deploy latest"** ou **"Manual Deploy"**
2. Aguarde ~3-5 minutos
3. Frontend: Clique **"Deploy latest"**
4. Aguarde rebuild (5-10 minutos)

---

## 🐛 **OBSERVAR OS LOGS DETALHADOS**

### No console do navegador (F12 → Console):
Adicione logs mais detalhados. Você vai ver:

```javascript
🔐 Tentando login em: https://seu-backend.onrender.com/token
📤 Enviando data: { username: "admin" }
❌ ERRO COMPLETO: {
  message: "...",
  status: 401 ou 500,
  statusText: "...",
  data: { detail: "..." }
}
```

**Procure pela mensagem de erro específica** acima do stack trace.

### Erros comuns:

| Erro | Solução |
|------|---------|
| `ERR_CONNECTION_REFUSED` | Backend offline ou URL errada |
| `404 Not Found` | Endpoint `/token` não existe |
| `401 Unauthorized` | Usuário/senha inválidos ou não existe |
| `500 Internal Server Error` | Erro no backend (veja logs) |
| `CORS error` | Add `allow_origins=["*"]` em main.py |

---

## 📋 **CHECKLIST Final**

Marque conforme você verifica:

- [ ] Backend está online: `https://seu-backend.onrender.com/`
- [ ] Frontend pode acessar backend (sem CORS error)
- [ ] `VITE_API_URL` está correto no Render (Frontend Environment)
- [ ] DATABASE_URL está configurada (Backend Environment)
- [ ] Há pelo menos um usuário no banco (execute `check_users.py`)
- [ ] Novos deploys foram feitos após mudanças

---

## 🆘 **Se ainda não funcionar:**

1. **Cole a mensagem de erro exata** (acima do stack trace)
2. **Digite os logs do backend** (do Render Dashboard)
3. **Verifique se `https://seu-backend.onrender.com` está online**

Isso vai ajudar a identificar o problema com precisão! 🎯
