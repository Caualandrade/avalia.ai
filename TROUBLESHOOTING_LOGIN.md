# 🧪 GUIA DE TROUBLESHOOTING - Login não funciona

## ✅ PASSOS DE DEBUG (Na Ordem)

### **PASSO 1: Abrir Console do Navegador**

```
Pressione: F12 (ou Ctrl+Shift+I)
Clique em: Console
```

### **PASSO 2: Testar Conectividade Básica**

1. Acesse: `http://localhost:3000/debug` (ou sua URL do frontend)
2. Clique em "Testar Conexão"
3. Verifique os logs no console

**Resultados esperados:**

```
✅ BACKEND ONLINE: { message: "Bem-vindo à API de Maturidade TI" }
```

---

## 🔴 SE DER ERRO NA CONECTIVIDADE

### Erro: "NÃO CONSEGUIU CONECTAR"

**Causas possíveis:**

1. Backend não está rodando
2. URL da API incorreta
3. CORS bloqueando

**Solução:**

```bash
# 1. Verifique se backend está rodando
# Abra http://localhost:8000 (deve mostrar JSON)

# 2. Verifique VITE_API_URL
# No arquivo .env.local do frontend:
VITE_API_URL=http://localhost:8000
# (SEM barra final!)

# 3. Se ainda não funcionar, reinicie:
# Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (novo terminal)
cd frontend
npm run dev
```

---

## 🟡 SE A CONECTIVIDADE OK, MAS LOGIN FALHA

### Erro: "Usuário ou senha incorretos"

**Verificar:**

```javascript
// Copie isto no console do navegador para testar um usuário padrão:

fetch("http://localhost:8000/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: "username=admin&password=admin123",
})
  .then((r) => r.json())
  .then((data) => console.log(data));
```

**Se funcionar no console, o problema está no frontend**
**Se der erro, o problema está no backend ou dados**

---

### Erro: "CORS error"

```
Access to XMLHttpRequest at 'http://localhost:8000/token' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solução - Verificar backend `main.py`:**

```python
# Certifique-se que tem isto em main.py (linha ~25):
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite tudo em desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Se não tem, adicione! E reinicie o backend.

---

## ✅ SE CONECTAR E LOGIN FUNCIONAR

Parabéns! O backend está OK. Agora:

1. **Retire a página de debug** depois (não precisa mais)
2. **Teste no formulário de login normal**
3. **Verifique se token é salvo em localStorage**

Para ver localStorage:

```javascript
// No console:
localStorage.getItem("token"); // Deve mostrar um token JWT longo
```

---

## 📋 CHECKLIST DE VERIFICAÇÃO

Marque conforme você versa:

- [ ] Backend rodando em `http://localhost:8000`
- [ ] Frontend rodando em `http://localhost:3000` (ou outra porta)
- [ ] `.env` tem `VITE_API_URL=http://localhost:8000` (sem barra final)
- [ ] Banco de dados está online
- [ ] Usuário admin existe no banco
- [ ] CORSMiddleware está em `main.py`
- [ ] Console do navegador não mostra erros de rede
- [ ] Ao fazer login, aparece um token em `localStorage`

---

## 🆘 AINDA NÃO FUNCIONA?

1. **Cole o erro completo** que vê no console (F12)
2. **Verifique os logs do backend**:

   ```bash
   # Terminal do backend, procure por:
   # POST /token 200  ✅ Sucesso
   # POST /token 401  ❌ Credenciais inválidas
   # POST /token 500  ❌ Erro no servidor
   ```

3. **Teste a requisição direto**:
   ```bash
   curl -X POST http://localhost:8000/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   ```

---

## 🔗 ARQUIVOS RELEVANTES

- Frontend: `/frontend/src/context/AuthContext.jsx` (login logic)
- Frontend: `/frontend/src/config.js` (API_URL)
- Backend: `/backend/main.py` (endpoint /token)
- Backend: `/backend/models.py` (User model)
