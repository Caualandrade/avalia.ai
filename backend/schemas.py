from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, TypeVar, Generic, Any
from datetime import datetime
import json as _json
from models import UserRole, AssessmentStatus, InterviewMode, InterviewInviteStatus

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pages: int

# ─── User Schemas ──────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    company_name: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole
    company_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    company_name: Optional[str] = None
    sector: Optional[str] = None
    employee_count: Optional[str] = None
    it_model: Optional[str] = None
    regulations: Optional[str] = None  # JSON string
    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    sector: Optional[str] = None
    employee_count: Optional[str] = None
    it_model: Optional[str] = None
    regulations: Optional[str] = None  # JSON string: '["LGPD","BACEN"]'

# ─── Question/Category Schemas ────────────────────────────────────────────────
class QuestionBase(BaseModel):
    text: str

class QuestionCreate(QuestionBase):
    subcategory_id: int
    framework_refs: Optional[List[str]] = None

class QuestionUpdate(BaseModel):
    text: str
    framework_refs: Optional[List[str]] = None

class QuestionResponse(QuestionBase):
    id: int
    subcategory_id: int
    framework_refs: Optional[List[str]] = None

    @field_validator("framework_refs", mode="before")
    @classmethod
    def parse_framework_refs(cls, v: Any) -> Optional[List[str]]:
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except Exception:
                return None
        return v

    class Config:
        from_attributes = True

class SubcategoryBase(BaseModel):
    name: str
    weight: float = 1.0

class SubcategoryCreate(SubcategoryBase):
    category_id: int

class SubcategoryResponse(SubcategoryBase):
    id: int
    category_id: int
    questions: List[QuestionResponse] = []
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    weight: float = 1.0

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    subcategories: List[SubcategoryResponse] = []
    class Config:
        from_attributes = True

# ─── Assessment/Response Schemas ──────────────────────────────────────────────
class ResponseBase(BaseModel):
    assessment_id: int
    question_id: Optional[int] = None
    score: Optional[float] = None
    comment: Optional[str] = None

class ResponseCreate(ResponseBase):
    pass

class ResponseResponse(ResponseBase):
    id: int
    raw_answer: Optional[str] = None
    ai_analysis: Optional[str] = None
    ai_question: Optional[str] = None
    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    company_id: int
    evaluator_id: Optional[int] = None
    status: AssessmentStatus = AssessmentStatus.PENDING
    mode: InterviewMode = InterviewMode.GUIDED

class AssessmentCreate(AssessmentBase):
    pass

class AssessmentResponse(AssessmentBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    responses: List[ResponseResponse] = []
    class Config:
        from_attributes = True

# ─── Auth Schemas ─────────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ─── AI Legacy Schemas (geração de sugestões) ─────────────────────────────────
class AIRequest(BaseModel):
    category: str
    subcategory: str

class AIResponse(BaseModel):
    suggestions: List[str]

# ─── Interview Invite Schemas ─────────────────────────────────────────────────
class InviteCreate(BaseModel):
    company_id: int
    category_ids: List[int]
    message: Optional[str] = None

class InviteResponse(BaseModel):
    id: int
    evaluator_id: int
    company_id: int
    category_ids: List[int]
    message: Optional[str] = None
    status: InterviewInviteStatus
    assessment_id: Optional[int] = None
    created_at: datetime
    accepted_at: Optional[datetime] = None
    evaluator: Optional[UserResponse] = None
    company: Optional[UserResponse] = None
    assessment: Optional[AssessmentResponse] = None
    class Config:
        from_attributes = True

# ─── Interview Session Schemas ────────────────────────────────────────────────
class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    question_id: Optional[int] = None
    is_evaluation_question: bool
    timestamp: datetime
    class Config:
        from_attributes = True

class InterviewSessionResponse(BaseModel):
    id: int
    assessment_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    is_active: bool
    questions_asked: int
    total_questions: int
    messages: List[ChatMessageResponse] = []
    class Config:
        from_attributes = True

class StartInterviewRequest(BaseModel):
    invite_id: Optional[int] = None   # Modo guiado: usa convite
    mode: InterviewMode = InterviewMode.GUIDED

class SendMessageRequest(BaseModel):
    content: str

# ─── AI Feedback Schemas ──────────────────────────────────────────────────────
class AIFeedbackResponse(BaseModel):
    id: int
    assessment_id: int
    overall_summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[dict]
    category_scores: dict
    score_geral: float
    nivel: str
    nivel_numerico: int = 0
    coverage_map: Optional[dict] = None
    generated_at: datetime
    class Config:
        from_attributes = True

# ─── Manual Form Schemas ──────────────────────────────────────────────────────
class FormSubmitItem(BaseModel):
    question_id: int
    raw_answer: str

class SubmitFormRequest(BaseModel):
    answers: List[FormSubmitItem]

# ─── Users list (for evaluator) ──────────────────────────────────────────────
class UserListResponse(BaseModel):
    users: List[UserResponse]

# ─── Settings Schemas ─────────────────────────────────────────────────────────
class AppSettingsUpdate(BaseModel):
    openai_api_key: Optional[str] = None
    autonomous_questions: Optional[int] = None

class AppSettingsResponse(BaseModel):
    id: int
    openai_api_key: Optional[str] = None
    autonomous_questions: int
    class Config:
        from_attributes = True
