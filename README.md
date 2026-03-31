# 📊 Avalia.AI - Plataforma de Avaliação de Maturidade de TI

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

Esta plataforma permite que empresas avaliem o seu nível de maturidade em TI através de entrevistas inteligentes, gerando relatórios automáticos e diagnósticos precisos por categoria.

## 🌟 Funcionalidades Principais
- **Entrevistas Inteligentes (IA):** Agente de IA capaz de conduzir entrevistas dinâmicas e contextuais.
- **Modos de Coleta:** Escolha entre preenchimento manual de formulários ou o modo assistido por IA.
- **Dashboards em Tempo Real:** Visualização de progresso e scores de maturidade.
- **Relatórios Detalhados:** Feedback automatizado com base no desempenho organizacional.
- **Gestão de Categorias:** Criação e personalização de trilhas de avaliação (Questionários).

---

## 🛠 Stack Tecnológica

### Backend (API & IA)
- **Framework:** FastAPI (Python 3.11)
- **IA/LLM:** OpenAI API + LangChain
- **Persistência:** SQLAlchemy + PostgreSQL
- **Segurança:** Auth JWT + Passlib (Bcrypt)
- **Comunicação:** WebSockets para entrevistas em tempo real

### Frontend (User Interface)
- **Framework:** React + Vite
- **Styling:** Vanilla CSS (Design Moderno & Glassmorphism)
- **Ícones:** SVG nativo / Lucide

### Infraestrutura
- **Orquestração:** Docker & Docker Compose
- **Servidor:** Uvicorn

---

## 🚀 Como Iniciar com Docker (Recomendado)

O Docker orquestra todos os serviços automaticamente, incluindo o banco de dados e as variáveis de ambiente.

1. **Configurar Variáveis de Ambiente:**
   - No diretório `backend/`, duplique o arquivo `.env.example` (ou crie um novo `.env`) e adicione sua chave da OpenAI:
     ```env
     DATABASE_URL=postgresql://user:pass@db/maturidade_ti
     SECRET_KEY=sua_chave_secreta_jwt
     OPENAI_API_KEY=sua_chave_aqui
     ```

2. **Subir os Contêineres:**
   ```bash
   docker-compose up --build
   ```

3. **Popular o Banco (Seed Inicial):**
   Execute o script de seed para criar os usuários administradores e as categorias iniciais:
   ```bash
   docker exec -it maturidade_backend python migrate.py
   docker exec -it maturidade_backend python seed.py
   ```

---

## 💻 Desenvolvimento Local (Sem Docker)

### 1. Requisitos
- **PostgreSQL 15+** rodando localmente.
- **Python 3.11+**
- **Node.js 18+**

### 2. Configurar o Banco
Crie um banco de dados vazio chamado `maturidade_ti` no seu PostgreSQL local.

### 3. Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/MacOS:
source venv/bin/activate

pip install -r requirements.txt
python migrate.py
python seed.py
uvicorn main:app --reload
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 👤 Acesso Inicial
Após rodar o script de **seed**, utilize as seguintes credenciais para acessar o painel:

- **Usuário:** `admin`
- **Senha:** `admin123`

---

## 📈 Níveis de Maturidade
O diagnóstico é baseado nos seguintes intervalos de maturidade:

1.  🔴 **Artesanal / Reativo (0 - 40%)**: TI sem processos definidos, focada em resolver incêndios.
2.  🟡 **Eficiente / Proativo (40 - 80%)**: Processos definidos e monitoramento básico.
3.  🟢 **Eficaz / Otimizado (80 - 90%)**: TI alinhada aos processos de negócio.
4.  💎 **Estratégico (90 - 100%)**: TI como diferencial competitivo e inovação contínua.

---

© 2026 Avalia.AI - Maturidade de TI
