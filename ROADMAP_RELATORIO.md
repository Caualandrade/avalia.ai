# Roadmap — Geração de Relatório de Diagnóstico

Baseado nos relatórios de referência (GrupoBoom Case 3/4) e no cruzamento com o sistema atual.

**Objetivo:** Ao final de cada entrevista, o sistema gera automaticamente um relatório PDF com 6 seções estruturadas, equivalente ao `Avalia_AI_Diagnostico_GrupoBoom.pdf`.

---

## Estrutura do Relatório (referência)

| Seção | Descrição |
|-------|-----------|
| 1 | Cabeçalho: empresa, data, analista, score global, nível, qtd. categorias, achados críticos |
| 2 | Scores por Categoria (categoria → framework → barra → %) |
| 3 | Indicadores Operacionais (KPI → valor atual → benchmark → status) |
| 4 | Achados e Vulnerabilidades (badge CRÍTICO/ALTO/MÉDIO + texto) |
| 5 | Plano de Ação 90 dias (0–15 / 15–45 / 45–90 dias) |
| 6 | Diagnóstico Consolidado por Framework (framework → nível → descrição) |

---

## Etapas

### Etapa 1 — Expandir modelo `AIFeedback` e prompt de feedback
**Status:** `[x] concluída`

Campos novos a adicionar em `backend/models.py`:
- `findings` (Text/JSON): `[{severity: "CRÍTICO"|"ALTO"|"MÉDIO"|"BAIXO", description: "..."}]`
- `action_plan_90d` (Text/JSON): `{fase_0_15: [...], fase_15_45: [...], fase_45_90: [...]}`
- `framework_diagnoses` (Text/JSON): `[{framework: "COBIT 2019", level: "Nível 1 — Realizado", description: "..."}]`
- `kpi_indicators` (Text/JSON): `[{name: "...", current: "...", benchmark: "...", status: "ABAIXO"|"OK"|"ACIMA"}]`
- `critical_findings_count` (Integer): contagem dos findings CRÍTICO

Atualizar `FEEDBACK_PROMPT` em `backend/ai_agent.py` para incluir os novos campos no JSON de saída.

Atualizar `generate_feedback()` para salvar os novos campos no banco.

Executar migração (`migrate.py`).

**Entregável:** `AIFeedback` com estrutura completa para alimentar todas as 6 seções.

---

### Etapa 2 — Endpoint de dados do relatório
**Status:** `[x] concluída`  
**Depende de:** Etapa 1

Criar rota `GET /assessments/{id}/report` em `backend/main.py` que retorna:
- Dados da empresa (perfil organizacional)
- Dados do avaliador
- `AIFeedback` completo
- `category_scores` enriquecido com o framework de referência (derivado de `Question.framework_refs` via join)
- Data de geração

Permissões: COMPANY (própria), EVALUATOR (que avaliou), ADMIN (qualquer).

**Entregável:** JSON com todos os dados necessários para renderizar o relatório.

---

### Etapa 3 — Componente de relatório em HTML (frontend)
**Status:** `[x] concluída`  
**Depende de:** Etapa 2

Criar `frontend/src/components/Report.jsx` com as 6 seções:

- **Cabeçalho:** logo Avalia.AI, nome empresa, data, analista, score circular animado, nível, badges qtd. categorias + achados críticos
- **Scores por Categoria:** tabela com barra de progresso colorida e label do framework
- **Indicadores Operacionais:** tabela com status colorido (ABAIXO = vermelho, OK = verde)
- **Achados e Vulnerabilidades:** cards com badge de severidade colorido
- **Plano de Ação 90 dias:** 3 colunas lado a lado com bullets
- **Diagnóstico por Framework:** cards com framework, nível colorido e descrição

Adicionar botão "Imprimir / Exportar PDF" (usa `window.print()` + CSS `@media print`).

Integrar à tela do dashboard da empresa e do avaliador (botão "Ver Relatório" no assessment concluído).

**Entregável:** Página de relatório funcional e visualmente fiel ao modelo de referência.

---

### Etapa 4 — Geração de PDF no backend
**Status:** `[x] concluída`  
**Depende de:** Etapas 2 e 3

Adicionar `weasyprint` ou `reportlab` ao `backend/requirements.txt`.

Criar rota `GET /assessments/{id}/report/pdf` que:
1. Monta o HTML do relatório com os dados do banco
2. Converte para PDF via WeasyPrint
3. Retorna `application/pdf` com `Content-Disposition: attachment`

Criar template HTML/CSS dedicado para PDF em `backend/templates/report.html` (glassmorphism adaptado para impressão).

Adicionar botão "Baixar PDF" no frontend apontando para o endpoint.

**Entregável:** Download de PDF com layout idêntico ao modelo de referência.

---

### Etapa 5 — KPI Extraction (Indicadores Operacionais)
**Status:** `[x] concluída`  
**Depende de:** Etapa 1

Estratégia: enriquecer o `FEEDBACK_PROMPT` com instrução explícita para o LLM extrair métricas numéricas mencionadas durante a entrevista e formatá-las como KPIs.

Exemplo do que o LLM deve identificar nas respostas:
> "Nossa disponibilidade é de 96%" → `{name: "Disponibilidade do sistema", current: "96%", benchmark: "99,5%", status: "ABAIXO"}`

Se nenhuma métrica for mencionada, gerar KPIs estimados baseados no score da categoria.

**Entregável:** Seção "Indicadores Operacionais" populada automaticamente a partir do conteúdo da entrevista.

---

## Ordem de execução recomendada

```
Etapa 1 → Etapa 2 → Etapa 3 → Etapa 5 → Etapa 4
```

Etapas 1-3 cobrem ~80% do valor visual do relatório.  
Etapa 5 resolve o único item que depende da qualidade das respostas da entrevista.  
Etapa 4 é o polimento final (PDF para download).

---

## Log de entregas

| Etapa | Iniciada em | Concluída em | Observações |
|-------|------------|--------------|-------------|
| 1 | 2026-06-16 | 2026-06-16 | models.py, ai_agent.py, schemas.py, migrate.py, main.py |
| 2 | 2026-06-16 | 2026-06-16 | GET /assessments/{id}/report — ReportResponse completo, framework enrichment, RBAC |
| 3 | 2026-06-16 | 2026-06-16 | Report.jsx com 6 seções, CSS rpt-*, botão imprimir, integração Dashboard |
| 4 | 2026-06-16 | 2026-06-16 | WeasyPrint 69.0, GET /assessments/{id}/report/pdf?token=, botão "Baixar PDF" em Report.jsx |
| 5 | 2026-06-16 | 2026-06-16 | Regex extractor + FEEDBACK_PROMPT enriquecido + assessment_data com transcript/org_profile |
