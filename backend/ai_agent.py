"""
AI Agent Service — Maturidade TI (LangChain)
----------------------------------------------
Responsável por:
  1. conduct_interview()   → Gera a próxima mensagem do agente entrevistador
  2. evaluate_response()   → Avalia resposta textual e atribui score (0-100)
  3. generate_feedback()   → Gera feedback completo pós-entrevista
  4. generate_welcome_message() → Mensagem de boas-vindas personalizada
"""

import json
import os
import logging

from database import SessionLocal
import models

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

logger = logging.getLogger(__name__)

# ─── Configuração do Modelo ─────────────────────────────────────────────────

MODEL = "gpt-5-mini"
_llm = None
OPENAI_AVAILABLE = False


def _get_llm():
    """Inicializa o LLM sob demanda."""
    global _llm, OPENAI_AVAILABLE

    if _llm is not None:
        return _llm

    db = SessionLocal()
    try:
        settings = db.query(models.AppSettings).first()
        db_api_key = settings.openai_api_key if settings else None
    finally:
        db.close()

    api_key = db_api_key or os.getenv("OPENAI_API_KEY", "")
    
    if not api_key or api_key == "sua-chave-openai-aqui":
        logger.warning("OPENAI_API_KEY não configurada — usando modo fallback sem IA.")
        OPENAI_AVAILABLE = False
        return None

    try:
        _llm = ChatOpenAI(
            model=MODEL,
            api_key=api_key,
            temperature=1.0,
            max_completion_tokens=4000,
            max_retries=3,
        )
        OPENAI_AVAILABLE = True
        logger.info(f"LangChain ChatOpenAI inicializado com modelo {MODEL}")
        return _llm
    except Exception as e:
        logger.error(f"Erro ao inicializar LangChain ChatOpenAI: {e}")
        OPENAI_AVAILABLE = False
        return None


# ─── System Prompts ───────────────────────────────────────────────────────────

INTERVIEWER_GUIDED_PROMPT = """Você é um consultor especialista em Maturidade de TI, atuando como entrevistador profissional.
Sua missão é conduzir uma entrevista estruturada com o representante de uma empresa para avaliar o nível de maturidade de TI da organização.

Regras fundamentais:
1. Conduza a entrevista SEMPRE em português do Brasil (PT-BR).
2. Faça as perguntas de forma conversacional e natural, adaptando o vocabulário ao contexto.
3. SEMPRE reaja à resposta anterior do entrevistado antes de fazer a próxima pergunta. Use expressões naturais como:
   - "Entendo, interessante que vocês já tenham isso implementado."
   - "Certo, isso mostra um bom nível de organização."
   - "Obrigado por compartilhar! Isso é um ponto relevante."
4. Se a resposta for muito curta ou vaga (ex: "sim", "existe", "temos"), NÃO passe para a próxima pergunta. Em vez disso, peça gentilmente mais detalhes. Exemplo:
   - "Poderia me contar um pouco mais sobre como isso funciona na prática?"
   - "Entendo que existe, mas como é o processo no dia a dia?"
5. Seja profissional, empático e encorajador. Não julgue negativamente a empresa.
6. Quando terminar todas as perguntas definidas, informe gentilmente que a entrevista chegou ao fim.
7. Responda APENAS como entrevistador. Não forneça avaliações parciais durante a entrevista.
8. Mantenha o contexto de todas as respostas anteriores para não repetir perguntas.
9. Introduza-se brevemente na primeira mensagem.
10. Mantenha respostas concisas (2-4 frases por vez).
11. IMPORTANTE: NÃO mencione ao usuário o seu progresso atual ou quantas perguntas faltam (ex: NÃO diga "Progresso: 2 de 5"). Apenas faça a próxima pergunta naturalmente.

Formato das suas respostas: texto simples, conversacional. Sem listas ou marcadores nas perguntas."""

INTERVIEWER_AUTONOMOUS_PROMPT = """Você é um consultor sênior de Maturidade de TI, com expertise em COBIT 2019, ITIL v4, ISO 27001, ISO 20000 e CMMI.
Sua missão é conduzir uma avaliação autônoma e completa do nível de maturidade de TI de uma empresa.

Domínios a cobrir (selecione perguntas estratégicas limitando-se ao número total configurado para a entrevista):
- Governança Corporativa de TI (responsabilidade da diretoria: comitê de TI, alinhamento com metas de negócio, gestão de risco corporativo, compliance, ROI de TI)
- Gestão de TI (responsabilidade do time operacional: processos, projetos, orçamento, contratos, fornecedores, métricas operacionais)
- Gestão de Serviços (ITSM, catálogo, SLAs, incidentes, problemas, mudanças — ITIL v4)
- Infraestrutura e Cloud (disponibilidade, escalabilidade, FinOps)
- Segurança da Informação (políticas, controle de acesso, MFA, gestão de riscos, ISO 27001)
- Gestão de Dados (qualidade, governança, analytics, LGPD)
- Inovação e Transformação Digital (automação, IA, DevOps, cultura)
- Pessoas e Capacitação (skills, certificações, retenção)

Regras de interação OBRIGATÓRIAS:
1. Conduza SEMPRE em PT-BR.
2. Comece com uma apresentação profissional e contextualização da avaliação.
3. Gere perguntas estratégicas e abertas — evite perguntas de Sim/Não.
4. Baseie as perguntas seguintes nas respostas recebidas (adaptive interviewing).
5. Explore mais profundamente áreas onde a empresa demonstra menor maturidade.
6. SEMPRE reaja à resposta anterior antes de fazer a próxima pergunta. Use expressões naturais como:
   - "Muito bem, isso demonstra um nível interessante de maturidade nessa área."
   - "Entendo. É comum empresas nesse estágio ainda estarem desenvolvendo isso."
   - "Ótimo ponto! Isso é um diferencial importante."
7. Se a resposta for muito curta ou vaga (menos de 10 palavras), NÃO avance. Peça mais detalhes:
   - "Poderia elaborar um pouco mais? Quero entender como isso funciona na prática na sua empresa."
   - "Interessante! Poderia me dar um exemplo concreto de como isso é aplicado?"
8. Monitore o progresso: ao final das perguntas programadas, conclua a entrevista agradecendo.
9. Não repita temas já cobertos adequadamente.
10. Não forneça avaliações parciais durante a entrevista.
11. Mantenha respostas concisas e naturais (2-4 frases por vez).
12. IMPORTANTE: NÃO mencione ao usuário o seu progresso atual ou quantas perguntas faltam (ex: NÃO diga "Progresso: 2 de 5"). Apenas faça a próxima pergunta naturalmente.

Formato: texto simples e conversacional. Sem markdown, listas ou marcadores."""

EVALUATOR_PROMPT = """Você é um sistema de avaliação de maturidade de TI.
Sua tarefa é analisar a resposta de um representante de empresa para uma pergunta de avaliação de maturidade de TI e atribuir um score.

Retorne APENAS um JSON válido com a seguinte estrutura:
{
  "score": <número de 0 a 100>,
  "analysis": "<análise em português de 2-3 frases explicando o score>",
  "maturity_indicators": ["<indicador 1>", "<indicador 2>"]
}

Escala de maturidade:
- 0-20: Inexistente / Caótico — processo ou prática não existe
- 21-40: Inicial / Ad-hoc — existe mas é informal e inconsistente
- 41-60: Definido — processo documentado e padronizado
- 61-80: Gerenciado — processo medido e controlado com KPIs
- 81-100: Otimizando — processo em melhoria contínua e inovação

Seja justo e criterioso. Considere especificidade, consistência e evidências na resposta."""

FEEDBACK_PROMPT = """Você é um especialista em Maturidade de TI.
Com base nos dados da entrevista fornecidos, gere um feedback executivo completo para a empresa.

Retorne APENAS um JSON válido com exatamente esta estrutura:
{
  "overall_summary": "<resumo executivo de 3-4 parágrafos em PT-BR>",
  "strengths": ["<ponto forte 1>", "<ponto forte 2>", "<ponto forte 3>"],
  "weaknesses": ["<ponto fraco 1>", "<ponto fraco 2>", "<ponto fraco 3>"],
  "recommendations": [
    {"title": "<título>", "description": "<descrição>", "priority": "alta|média|baixa"},
    {"title": "<título>", "description": "<descrição>", "priority": "alta|média|baixa"}
  ],
  "category_scores": {"<categoria>": <score 0-100>, ...}
}

Baseie-se nos dados de todas as respostas e scores fornecidos.
Seja específico, acionável e construtivo. Evite respostas genéricas.
Todo o conteúdo deve estar em PT-BR."""


# ─── Fallbacks (sem OpenAI) ───────────────────────────────────────────────────

_FALLBACK_QUESTIONS = [
    "Como a TI da sua empresa está alinhada aos objetivos estratégicos do negócio? Existe um planejamento formal?",
    "Como são gerenciados os incidentes de TI? Existe um sistema de tickets ou service desk formalizado?",
    "Como a empresa aborda a segurança da informação? Existe uma política de segurança documentada e aplicada?",
    "Quais são os principais sistemas de TI críticos para a operação? Como a continuidade desses sistemas é garantida?",
    "Como a equipe de TI é capacitada e mantida atualizada sobre novas tecnologias e tendências?",
    "A empresa utiliza algum framework de gestão de TI (ITIL, COBIT, etc.)? Como eles são aplicados?",
    "Como são realizadas as mudanças no ambiente de TI? Existe um processo formal de gestão de mudanças?",
    "Quais métricas ou indicadores de desempenho a TI acompanha? Como esses dados são utilizados?",
    "Como a empresa trata a gestão de dados e a conformidade com a LGPD ou outras regulamentações?",
    "Quais são os principais desafios de TI enfrentados atualmente e quais investimentos estão planejados?",
]


def _get_fallback_question(session_id: str, asked: int) -> str:
    idx = asked % len(_FALLBACK_QUESTIONS)
    return _FALLBACK_QUESTIONS[idx]


# ─── Chamadas LangChain ──────────────────────────────────────────────────────

async def _invoke_llm(messages: list, json_mode: bool = False) -> str | None:
    """Chama o LLM via LangChain. Retorna None se não disponível ou erro."""
    llm = _get_llm()
    if llm is None:
        return None

    try:
        call_llm = llm

        if json_mode:
            call_llm = call_llm.bind(response_format={"type": "json_object"})

        response = await call_llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Erro na chamada LangChain: {e}")
        return None


def _build_chat_messages(system_prompt: str, history: list[dict]) -> list:
    """Converte o histórico da conversa para mensagens LangChain."""
    messages = [SystemMessage(content=system_prompt)]
    for msg in history:
        if msg["role"] == "agent":
            messages.append(AIMessage(content=msg["content"]))
        else:
            messages.append(HumanMessage(content=msg["content"]))
    return messages


# ─── Funções Principais ───────────────────────────────────────────────────────

async def conduct_interview(
    history: list[dict],
    questions_context: str,
    autonomous: bool = False,
    questions_asked: int = 0,
    total_questions: int = 0,
    session_id: str = "",
    org_profile: dict | None = None,
) -> str:
    """
    Gera a próxima mensagem do agente entrevistador.
    history: lista de dicts {"role": "agent"|"user", "content": str}
    """
    system_prompt = INTERVIEWER_AUTONOMOUS_PROMPT if autonomous else INTERVIEWER_GUIDED_PROMPT

    if org_profile:
        regs = org_profile.get("regulations") or "não informadas"
        profile_ctx = (
            f"\n\n=== CONTEXTO DA EMPRESA AVALIADA ===\n"
            f"Setor: {org_profile.get('sector') or 'não informado'}\n"
            f"Porte: {org_profile.get('employee_count') or 'não informado'}\n"
            f"Modelo de TI: {org_profile.get('it_model') or 'não informado'}\n"
            f"Regulamentações aplicáveis: {regs}\n"
            f"Adapte as perguntas e o nível de profundidade técnica a esse contexto.\n"
        )
        system_prompt += profile_ctx

    if not autonomous and questions_context:
        system_prompt += f"\n\n=== PERGUNTAS A REALIZAR ===\n{questions_context}\n\nRealize as perguntas acima em ordem, uma por vez."

    if autonomous:
        system_prompt += f"\n\n{'Atenção: ESSE É O MOMENTO DE CONCLUIR. Conclua a entrevista nesta mensagem e não faça novas perguntas.' if questions_asked >= total_questions else ''}"

    messages = _build_chat_messages(system_prompt, history)

    result = await _invoke_llm(messages)
    if result:
        return result

    # Fallback sem OpenAI
    if questions_asked >= 10:
        return (
            "Obrigado pelas suas respostas! Você compartilhou informações muito valiosas sobre o ambiente de TI da sua empresa. "
            "Com base no que foi discutido, nossa equipe preparará um relatório completo de maturidade. "
            "A entrevista está encerrada. Seu feedback estará disponível em breve."
        )
    return _get_fallback_question(session_id, questions_asked)


async def evaluate_response(question: str, answer: str) -> dict:
    """
    Avalia a resposta textual de uma empresa para uma pergunta de maturidade.
    Retorna: {"score": float, "analysis": str, "maturity_indicators": list}
    """
    messages = [
        SystemMessage(content=EVALUATOR_PROMPT),
        HumanMessage(content=f"Pergunta: {question}\n\nResposta da empresa: {answer}"),
    ]

    result = await _invoke_llm(messages, json_mode=True)
    if result:
        try:
            parsed = json.loads(result)
            return {
                "score": float(parsed.get("score", 50)),
                "analysis": parsed.get("analysis", ""),
                "maturity_indicators": parsed.get("maturity_indicators", []),
            }
        except Exception:
            pass

    # Fallback — score médio baseado no tamanho e qualidade da resposta
    words = len(answer.split())
    if words < 10:
        score = 30.0
        analysis = "Resposta muito breve. Considere detalhar mais as práticas e processos da empresa."
    elif words < 30:
        score = 50.0
        analysis = "Resposta moderada. Demonstra algum conhecimento, mas poderia ser mais específica."
    else:
        score = 65.0
        analysis = "Resposta detalhada. Demonstra bom conhecimento do assunto."

    return {"score": score, "analysis": analysis, "maturity_indicators": []}


async def generate_feedback(assessment_data: dict) -> dict:
    """Gera feedback completo pós-entrevista."""
    data_str = json.dumps(assessment_data, ensure_ascii=False, indent=2)

    messages = [
        SystemMessage(content=FEEDBACK_PROMPT),
        HumanMessage(content=f"Dados da entrevista:\n{data_str}"),
    ]

    result = await _invoke_llm(messages, json_mode=True)
    if result:
        try:
            return json.loads(result)
        except Exception:
            pass

    # Fallback — feedback estático baseado no score
    score = assessment_data.get("score_geral", 50)
    company = assessment_data.get("company_name", "a empresa")
    nivel, _, _lvl = calculate_maturity_level(score)

    return {
        "overall_summary": (
            f"A avaliação de maturidade de TI de {company} foi concluída com sucesso. "
            f"O score geral obtido foi de {score:.0f}%, indicando um nível de maturidade '{nivel}'. "
            "A empresa demonstrou pontos positivos em algumas práticas, mas há oportunidades claras de melhoria. "
            "As recomendações abaixo foram elaboradas com base nas respostas fornecidas durante a entrevista."
        ),
        "strengths": [
            "Disposição para avaliar e medir a maturidade de TI",
            "Engajamento da equipe no processo de avaliação",
            "Abertura para identificar oportunidades de melhoria",
        ],
        "weaknesses": [
            "Formalização de processos e documentação ainda em desenvolvimento",
            "Adoção de frameworks de referência pode ser aprimorada",
            "Gestão baseada em indicadores precisa de maior estruturação",
        ],
        "recommendations": [
            {
                "title": "Implementar Gestão de Serviços de TI",
                "description": "Adotar ITIL v4 para padronizar processos de incidentes, mudanças e problemas.",
                "priority": "alta"
            },
            {
                "title": "Fortalecer a Segurança da Informação",
                "description": "Implementar política formal de segurança, controle de acesso e MFA em sistemas críticos.",
                "priority": "alta"
            },
            {
                "title": "Estabelecer Governança de TI",
                "description": "Criar comitê de TI com participação da diretoria e alinhar TI aos objetivos estratégicos.",
                "priority": "média"
            },
        ],
        "category_scores": {
            "Governança": score * 0.9,
            "Segurança": score * 0.85,
            "Infraestrutura": score * 1.05,
            "Processos": score * 0.95,
            "Pessoas": score * 1.0,
        },
    }


async def generate_welcome_message(company_name: str, categories: list[str], autonomous: bool = False) -> str:
    """Gera mensagem de boas-vindas personalizada para iniciar a entrevista."""
    if autonomous:
        prompt = f"""Gere uma mensagem de boas-vindas profissional e acolhedora para iniciar uma entrevista autônoma de maturidade de TI com a empresa "{company_name}".

Mencione que você irá cobrir diversas áreas como Governança, Segurança, Infraestrutura, Gestão de Serviços, Inovação e Pessoas.
Explique brevemente o processo e peça para começar. Seja caloroso e profissional. Máximo 4 frases."""
    else:
        cats_str = ", ".join(categories)
        prompt = f"""Gere uma mensagem de boas-vindas profissional e acolhedora para iniciar uma entrevista de maturidade de TI com a empresa "{company_name}".

A entrevista cobrirá as seguintes áreas: {cats_str}.
Explique brevemente o processo e que as respostas devem ser em texto livre. Peça para começar. Seja caloroso e profissional. Máximo 4 frases."""

    messages = [
        SystemMessage(content="Você é um consultor de Maturidade de TI. Responda sempre em PT-BR."),
        HumanMessage(content=prompt),
    ]

    result = await _invoke_llm(messages)
    if result:
        return result

    # Fallback sem OpenAI
    if autonomous:
        return (
            f"Olá e bem-vindo(a) à avaliação de maturidade de TI, {company_name}! "
            "Sou seu consultor de maturidade e conduzirei uma avaliação abrangente cobrindo áreas como "
            "Governança, Segurança da Informação, Infraestrutura, Gestão de Serviços, Inovação e Pessoas. "
            "Por favor, responda às perguntas de forma completa e detalhada — não há respostas certas ou erradas. "
            "Vamos começar? Pode me contar brevemente como a TI está estruturada na sua empresa?"
        )
    else:
        cats_str = ", ".join(categories) if categories else "diversas áreas de TI"
        return (
            f"Olá e bem-vindo(a), {company_name}! "
            f"Sou seu consultor de maturidade de TI e conduzirei esta entrevista cobrindo as seguintes áreas: {cats_str}. "
            "Responda às perguntas em texto livre, de forma clara e detalhada — isso ajudará a obter uma avaliação mais precisa. "
            "Vamos começar! Pode me falar um pouco sobre o contexto atual de TI da sua empresa?"
        )


def calculate_maturity_level(score: float) -> tuple[str, str, int]:
    """Retorna (nível, descrição, nível_0_a_5) baseado no score geral."""
    if score <= 20:
        return ("Caótico / Inexistente", "A TI opera sem processos formais. As iniciativas são completamente ad-hoc e dependem de esforços individuais sem padronização.", 0)
    elif score <= 40:
        return ("Inicial / Reativo", "A TI opera como um centro de custos isolado. Processos são ad-hoc e as soluções dependem fortemente do esforço individual.", 1)
    elif score <= 55:
        return ("Definido / Padronizado", "Processos começam a ser padronizados e documentados. Existe foco em disponibilidade e prevenção de problemas rotineiros.", 2)
    elif score <= 70:
        return ("Gerenciado / Proativo", "A TI está alinhada aos processos de negócio. Gestão baseada em indicadores e foco em entregar valor real à empresa.", 3)
    elif score <= 85:
        return ("Otimizando / Estratégico", "A TI é parceira do negócio e motor de inovação. Tecnologia é usada para criar vantagens competitivas e novos modelos de receita.", 4)
    else:
        return ("Excelência / Referência", "A TI é referência no setor. Inovação contínua, benchmarks externos positivos e cultura de melhoria permanente.", 5)
