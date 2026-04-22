import enum
import json
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EVALUATOR = "EVALUATOR"
    COMPANY = "COMPANY"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.COMPANY)
    company_name = Column(String, nullable=True)
    # M01 — perfil organizacional (apenas role=COMPANY)
    sector         = Column(String, nullable=True)
    employee_count = Column(String, nullable=True)
    it_model       = Column(String, nullable=True)
    regulations    = Column(Text,   nullable=True)  # JSON array: ["LGPD", "BACEN"]

    # Relationships
    assessments = relationship("Assessment", back_populates="company", foreign_keys="Assessment.company_id")
    evaluations_made = relationship("Assessment", back_populates="evaluator", foreign_keys="Assessment.evaluator_id")
    invites_sent = relationship("InterviewInvite", back_populates="evaluator", foreign_keys="InterviewInvite.evaluator_id")
    invites_received = relationship("InterviewInvite", back_populates="company", foreign_keys="InterviewInvite.company_id")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    weight = Column(Float, default=1.0) # Evaluator can define weight

    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")

class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    weight = Column(Float, default=1.0)

    category = relationship("Category", back_populates="subcategories")
    questions = relationship("Question", back_populates="subcategory", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"))
    framework_refs = Column(Text, nullable=True)  # M02 — JSON: ["COBIT:APO13", "ISO27001:A.8.8"]
    
    subcategory = relationship("Subcategory", back_populates="questions")
    responses = relationship("Response", back_populates="question")

class AssessmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FEEDBACK_READY = "FEEDBACK_READY"

class InterviewMode(str, enum.Enum):
    GUIDED = "GUIDED"        # Perguntas do avaliador (por categoria e IA interativa)
    AUTONOMOUS = "AUTONOMOUS" # AI gera perguntas autonomamente
    MANUAL_FORM = "MANUAL_FORM" # Formulário estático baseado nas perguntas do avaliador

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nulo no modo autônomo
    status = Column(Enum(AssessmentStatus), default=AssessmentStatus.PENDING)
    mode = Column(Enum(InterviewMode), default=InterviewMode.GUIDED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    company = relationship("User", back_populates="assessments", foreign_keys=[company_id])
    evaluator = relationship("User", back_populates="evaluations_made", foreign_keys=[evaluator_id])
    responses = relationship("Response", back_populates="assessment", cascade="all, delete-orphan")
    interview_session = relationship("InterviewSession", back_populates="assessment", uselist=False)
    feedback = relationship("AIFeedback", back_populates="assessment", uselist=False)


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)  # Nulo no modo autônomo
    score = Column(Float, nullable=True)
    comment = Column(Text, nullable=True)
    # Campos novos para entrevista AI-driven
    raw_answer = Column(Text, nullable=True)      # Resposta textual do usuário
    ai_analysis = Column(Text, nullable=True)     # Análise da IA sobre a resposta
    ai_question = Column(Text, nullable=True)     # Pergunta feita pela IA (modo autônomo)

    assessment = relationship("Assessment", back_populates="responses")
    question = relationship("Question", back_populates="responses")


# ─── NOVOS MODELOS ───────────────────────────────────────────────────────────

class InterviewInviteStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"   # Empresa aceitou / iniciou
    EXPIRED = "EXPIRED"

class InterviewInvite(Base):
    """Convite enviado pelo avaliador para a empresa iniciar uma entrevista."""
    __tablename__ = "interview_invites"

    id = Column(Integer, primary_key=True, index=True)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Categorias selecionadas pelo avaliador (JSON list de category IDs)
    category_ids = Column(Text, nullable=False)  # ex: "[1, 2, 3]"
    message = Column(Text, nullable=True)         # Mensagem personalizada do avaliador
    status = Column(Enum(InterviewInviteStatus), default=InterviewInviteStatus.PENDING)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    evaluator = relationship("User", back_populates="invites_sent", foreign_keys=[evaluator_id])
    company = relationship("User", back_populates="invites_received", foreign_keys=[company_id])
    assessment = relationship("Assessment", foreign_keys=[assessment_id])

    @property
    def category_ids_list(self):
        return json.loads(self.category_ids)


class InterviewSession(Base):
    """Sessão de chat da entrevista AI-driven."""
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), unique=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    # Progresso: quantas perguntas foram cobertas
    questions_asked = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)

    assessment = relationship("Assessment", back_populates="interview_session")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.timestamp")


class ChatMessage(Base):
    """Mensagem trocada durante a entrevista."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    role = Column(String, nullable=False)   # "agent" | "user"
    content = Column(Text, nullable=False)
    # Referência à pergunta do banco (se modo guiado)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    # Indica se esta mensagem é uma pergunta de avaliação (registra score)
    is_evaluation_question = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="messages")


class AIFeedback(Base):
    """Feedback consolidado gerado pela IA ao final da entrevista."""
    __tablename__ = "ai_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), unique=True)
    overall_summary = Column(Text)           # Resumo executivo em texto
    strengths = Column(Text)                 # JSON list de pontos fortes
    weaknesses = Column(Text)               # JSON list de pontos fracos
    recommendations = Column(Text)          # JSON list de recomendações
    category_scores = Column(Text)          # JSON dict {cat_name: score}
    score_geral = Column(Float, default=0.0)
    nivel = Column(String, default="")
    nivel_numerico = Column(Integer, default=0)   # M03 — escala 0–5
    coverage_map   = Column(Text, nullable=True)  # M02 — JSON: {"COBIT": 4, "ITIL": 2}
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="feedback")


class AppSettings(Base):
    """Configurações globais da aplicação geridas por Avaliadores/Admins"""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    openai_api_key = Column(String, nullable=True)
    autonomous_questions = Column(Integer, default=5)
