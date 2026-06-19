from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os, json

import models, schemas, database
from database import engine, get_db
from ai_agent import (
    conduct_interview, evaluate_response, generate_feedback,
    generate_welcome_message, calculate_maturity_level
)
from websocket_manager import manager

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Maturidade TI API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
_templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# ─── Auth Utilities ──────────────────────────────────────────────────────────

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def check_admin(user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas Admins podem realizar esta ação")
    return user

def check_evaluator(user: models.User = Depends(get_current_user)):
    if user.role not in [models.UserRole.EVALUATOR, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Apenas Avaliadores ou Admins podem realizar esta ação")
    return user

def check_company(user: models.User = Depends(get_current_user)):
    if user.role not in [models.UserRole.COMPANY, models.UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Apenas Empresas podem realizar esta ação")
    return user

# ─── Basic Routes ─────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Maturidade TI"}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.put("/users/me/profile", response_model=schemas.UserResponse)
def update_my_profile(
    profile: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_company),
):
    if profile.sector is not None:
        current_user.sector = profile.sector
    if profile.employee_count is not None:
        current_user.employee_count = profile.employee_count
    if profile.it_model is not None:
        current_user.it_model = profile.it_model
    if profile.regulations is not None:
        current_user.regulations = profile.regulations
    db.commit()
    db.refresh(current_user)
    return current_user

# ─── Admin ───────────────────────────────────────────────────────────────────

@app.post("/admin/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(check_admin)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(email=user.email, username=user.username, hashed_password=hashed_pwd, role=user.role, company_name=user.company_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if user.role == models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Não é permitido criar administradores via registro público")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    hashed_pwd = get_password_hash(user.password)
    new_user = models.User(email=user.email, username=user.username, hashed_password=hashed_pwd, role=user.role, company_name=user.company_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db), current_user: models.User = Depends(check_admin)):
    feedbacks = db.query(models.AIFeedback).all()
    avg_score = sum([f.score_geral for f in feedbacks]) / len(feedbacks) if feedbacks else 0.0

    return {
        "total_users": db.query(models.User).count(),
        "companies": db.query(models.User).filter(models.User.role == models.UserRole.COMPANY).count(),
        "evaluators": db.query(models.User).filter(models.User.role == models.UserRole.EVALUATOR).count(),
        "assessments": db.query(models.Assessment).count(),
        "completed_assessments": db.query(models.Assessment).filter(models.Assessment.status == models.AssessmentStatus.FEEDBACK_READY).count(),
        "avg_score": round(avg_score, 2),
    }

@app.get("/admin/users", response_model=schemas.PaginatedResponse[schemas.UserResponse])
def get_all_users(page: int = 1, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(check_admin)):
    query = db.query(models.User).order_by(models.User.id.desc())
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return {"items": users, "total": total, "page": page, "pages": pages}

# ─── Settings ────────────────────────────────────────────────────────────────

@app.get("/settings", response_model=schemas.AppSettingsResponse)
def get_settings(db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    settings = db.query(models.AppSettings).first()
    if not settings:
        settings = models.AppSettings(openai_api_key="", autonomous_questions=5)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.post("/settings/test-api-key")
def test_api_key(req: dict, current_user: models.User = Depends(check_evaluator)):
    api_key = req.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Chave não fornecida")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.models.list()
        return {"status": "ok", "message": "Conexão estabelecida com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao conectar com a API: {str(e)}")

@app.put("/settings", response_model=schemas.AppSettingsResponse)
def update_settings(updates: schemas.AppSettingsUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    settings = db.query(models.AppSettings).first()
    if not settings:
        settings = models.AppSettings(openai_api_key="", autonomous_questions=5)
        db.add(settings)
    
    if updates.openai_api_key is not None:
        settings.openai_api_key = updates.openai_api_key
    if updates.autonomous_questions is not None:
        settings.autonomous_questions = updates.autonomous_questions
        
    db.commit()
    db.refresh(settings)
    return settings

# ─── Users List (para avaliador selecionar empresa) ──────────────────────────

@app.get("/users/companies", response_model=List[schemas.UserResponse])
def list_companies(db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    return db.query(models.User).filter(models.User.role == models.UserRole.COMPANY).all()

# ─── Categorias / Subcategorias / Perguntas ───────────────────────────────────

@app.post("/categories", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    db_cat = models.Category(**category.dict())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@app.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).options(
        joinedload(models.Category.subcategories).joinedload(models.Subcategory.questions)
    ).all()

@app.post("/subcategories", response_model=schemas.SubcategoryResponse)
def create_subcategory(sub: schemas.SubcategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    db_sub = models.Subcategory(**sub.dict())
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

@app.delete("/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    cat = db.query(models.Category).filter(models.Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    db.delete(cat)
    db.commit()
    return {"detail": "Categoria excluída com sucesso."}

@app.delete("/subcategories/{sub_id}")
def delete_subcategory(sub_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    sub = db.query(models.Subcategory).filter(models.Subcategory.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcategoria não encontrada.")
    db.delete(sub)
    db.commit()
    return {"detail": "Subcategoria excluída com sucesso."}

@app.post("/questions", response_model=schemas.QuestionResponse)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    data = question.dict()
    refs = data.pop("framework_refs", None)
    db_q = models.Question(**data)
    db_q.framework_refs = json.dumps(refs, ensure_ascii=False) if refs else None
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    db_q.framework_refs = refs
    return db_q

@app.put("/questions/{question_id}", response_model=schemas.QuestionResponse)
def update_question(question_id: int, question: schemas.QuestionUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    db_q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_q:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    db_q.text = question.text
    if question.framework_refs is not None:
        db_q.framework_refs = json.dumps(question.framework_refs, ensure_ascii=False)
    db.commit()
    db.refresh(db_q)
    db_q.framework_refs = json.loads(db_q.framework_refs) if db_q.framework_refs else None
    return db_q

@app.delete("/questions/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    db_q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_q:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    db.delete(db_q)
    db.commit()
    return {"message": "Pergunta excluída com sucesso"}

# ─── Convites (Evaluator → Company) ──────────────────────────────────────────

@app.post("/invites", response_model=schemas.InviteResponse)
def create_invite(invite: schemas.InviteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    # Verifica se empresa existe
    company = db.query(models.User).filter(models.User.id == invite.company_id, models.User.role == models.UserRole.COMPANY).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Verifica se as categorias existem
    for cat_id in invite.category_ids:
        cat = db.query(models.Category).filter(models.Category.id == cat_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"Categoria {cat_id} não encontrada")
    
    db_invite = models.InterviewInvite(
        evaluator_id=current_user.id,
        company_id=invite.company_id,
        category_ids=json.dumps(invite.category_ids),
        message=invite.message,
    )
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    
    result = schemas.InviteResponse(
        id=db_invite.id,
        evaluator_id=db_invite.evaluator_id,
        company_id=db_invite.company_id,
        category_ids=json.loads(db_invite.category_ids),
        message=db_invite.message,
        status=db_invite.status,
        assessment_id=db_invite.assessment_id,
        created_at=db_invite.created_at,
        accepted_at=db_invite.accepted_at,
        evaluator=db_invite.evaluator,
        company=db_invite.company,
    )
    return result

@app.get("/invites/my", response_model=schemas.PaginatedResponse[schemas.InviteResponse])
def get_my_invites(page: int = 1, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Retorna convites paginados: empresa vê os recebidos, avaliador vê os enviados."""
    if current_user.role == models.UserRole.COMPANY:
        query = db.query(models.InterviewInvite).filter(
            models.InterviewInvite.company_id == current_user.id
        )
    else:
        query = db.query(models.InterviewInvite).filter(
            models.InterviewInvite.evaluator_id == current_user.id
        )
    
    total = query.count()
    invites = query.options(
        joinedload(models.InterviewInvite.evaluator),
        joinedload(models.InterviewInvite.company),
        joinedload(models.InterviewInvite.assessment),
    ).order_by(models.InterviewInvite.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for inv in invites:
        result.append(schemas.InviteResponse(
            id=inv.id,
            evaluator_id=inv.evaluator_id,
            company_id=inv.company_id,
            category_ids=json.loads(inv.category_ids),
            message=inv.message,
            status=inv.status,
            assessment_id=inv.assessment_id,
            created_at=inv.created_at,
            accepted_at=inv.accepted_at,
            evaluator=inv.evaluator,
            company=inv.company,
            assessment=inv.assessment,
        ))
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return {"items": result, "total": total, "page": page, "pages": pages}

# ─── Entrevistas (Interview Sessions) ─────────────────────────────────────────

@app.post("/interviews/start", response_model=schemas.InterviewSessionResponse)
async def start_interview(
    req: schemas.StartInterviewRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Empresa inicia uma entrevista.
    - Se invite_id for fornecido: modo guiado (perguntas do avaliador).
    - Se não: modo autônomo (AI gera perguntas).
    """
    if req.mode == models.InterviewMode.GUIDED:
        if not req.invite_id:
            raise HTTPException(status_code=400, detail="invite_id é obrigatório no modo guiado")
        
        invite = db.query(models.InterviewInvite).filter(
            models.InterviewInvite.id == req.invite_id,
            models.InterviewInvite.company_id == current_user.id,
            models.InterviewInvite.status == models.InterviewInviteStatus.PENDING,
        ).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Convite não encontrado ou já utilizado")
        
        # Busca categoria e perguntas
        cat_ids = json.loads(invite.category_ids)
        categories = db.query(models.Category).filter(
            models.Category.id.in_(cat_ids)
        ).options(joinedload(models.Category.subcategories).joinedload(models.Subcategory.questions)).all()
        
        all_questions = []
        for cat in categories:
            for sub in cat.subcategories:
                for q in sub.questions:
                    all_questions.append({"id": q.id, "text": q.text, "category": cat.name, "subcategory": sub.name})
        
        if not all_questions:
            raise HTTPException(status_code=400, detail="As categorias selecionadas não possuem perguntas cadastradas")
        
        # Cria Assessment
        assessment = models.Assessment(
            company_id=current_user.id,
            evaluator_id=invite.evaluator_id,
            status=models.AssessmentStatus.IN_PROGRESS,
            mode=models.InterviewMode.GUIDED,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Atualiza convite
        invite.status = models.InterviewInviteStatus.ACCEPTED
        invite.assessment_id = assessment.id
        invite.accepted_at = datetime.utcnow()
        db.commit()
        
        # Cria sessão
        session = models.InterviewSession(
            assessment_id=assessment.id,
            total_questions=len(all_questions),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Gera mensagem de boas-vindas
        cat_names = [c.name for c in categories]
        welcome_msg = await generate_welcome_message(
            company_name=current_user.company_name or current_user.username,
            categories=cat_names,
            autonomous=False,
        )
        
        # Armazena contexto das perguntas na sessão via 1ª mensagem do sistema
        questions_json = json.dumps(all_questions, ensure_ascii=False)
        system_ctx = models.ChatMessage(
            session_id=session.id,
            role="system_context",
            content=questions_json,
            is_evaluation_question=False,
        )
        db.add(system_ctx)
        
        welcome = models.ChatMessage(
            session_id=session.id,
            role="agent",
            content=welcome_msg,
            is_evaluation_question=False,
        )
        db.add(welcome)
        db.commit()
        db.refresh(session)
        
        # Filtra mensagens no retorno (remove context)
        session.messages = [m for m in session.messages if m.role != "system_context"]
        return session
    
    elif req.mode == models.InterviewMode.MANUAL_FORM:
        if not req.invite_id:
            raise HTTPException(status_code=400, detail="invite_id é obrigatório no modo formulário")
        
        invite = db.query(models.InterviewInvite).filter(
            models.InterviewInvite.id == req.invite_id,
            models.InterviewInvite.company_id == current_user.id,
            models.InterviewInvite.status == models.InterviewInviteStatus.PENDING,
        ).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Convite não encontrado ou já utilizado")
        
        # Cria Assessment
        assessment = models.Assessment(
            company_id=current_user.id,
            evaluator_id=invite.evaluator_id,
            status=models.AssessmentStatus.IN_PROGRESS,
            mode=models.InterviewMode.MANUAL_FORM,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        # Atualiza convite
        invite.status = models.InterviewInviteStatus.ACCEPTED
        invite.assessment_id = assessment.id
        invite.accepted_at = datetime.utcnow()
        db.commit()
        
        # Para o modo FORM, retornamos uma "sessão" vazia ou apenas o assessment_id
        # Vamos criar uma sessão mínima só para manter a compatibilidade se necessário,
        # mas o ideal é que o frontend entenda que mudou para modo Form.
        session = models.InterviewSession(
            assessment_id=assessment.id,
            total_questions=0, # Não usado no modo FORM da mesma maneira
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    else:
        # Modo autônomo
        assessment = models.Assessment(
            company_id=current_user.id,
            evaluator_id=None,
            status=models.AssessmentStatus.IN_PROGRESS,
            mode=models.InterviewMode.AUTONOMOUS,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        
        settings = db.query(models.AppSettings).first()
        t_questions = settings.autonomous_questions if settings else 5
        
        session = models.InterviewSession(
            assessment_id=assessment.id,
            total_questions=t_questions,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        welcome_msg = await generate_welcome_message(
            company_name=current_user.company_name or current_user.username,
            categories=[],
            autonomous=True,
        )
        
        welcome = models.ChatMessage(
            session_id=session.id,
            role="agent",
            content=welcome_msg,
            is_evaluation_question=False,
        )
        db.add(welcome)
        db.commit()
        db.refresh(session)
        return session


@app.post("/assessments/{assessment_id}/submit-form")
async def submit_manual_form(
    assessment_id: int,
    req: schemas.SubmitFormRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(check_company),
):
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id,
        models.Assessment.company_id == current_user.id
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    
    if assessment.status != models.AssessmentStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Esta avaliação não está em andamento")

    # Salva as respostas sem processar (processamento será feito em background)
    for ans in req.answers:
        response_rec = models.Response(
            assessment_id=assessment.id,
            question_id=ans.question_id,
            raw_answer=ans.raw_answer,
        )
        db.add(response_rec)
    
    assessment.status = models.AssessmentStatus.COMPLETED
    assessment.completed_at = datetime.utcnow()
    db.commit()
    
    # Processa os scores e gera feedback consolidado em background
    background_tasks.add_task(_process_manual_form_and_feedback, assessment.id)
    
    return {"message": "Respostas recebidas. Processando feedback...", "assessment_id": assessment.id}


async def _process_manual_form_and_feedback(assessment_id: int):
    """Tarefa de background: Avalia cada resposta do form e depois gera o feedback consolidado."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
        if not assessment: return

        # 1. Avalia cada resposta que ainda não tem score/análise em paralelo
        responses = db.query(models.Response).filter(
            models.Response.assessment_id == assessment_id,
            models.Response.score == None
        ).all()

        if responses:
            import asyncio
            async def score_one(r):
                if not r.question: return
                eval_result = await evaluate_response(
                    question=r.question.text,
                    answer=r.raw_answer,
                )
                r.score = eval_result["score"]
                r.ai_analysis = eval_result["analysis"]

            await asyncio.gather(*(score_one(r) for r in responses))
            db.commit()

        # 2. Gera o feedback consolidado (reutilizando a lógica existente)
        await _generate_and_save_feedback(assessment_id, db)
        
    except Exception as e:
        print(f"Erro no processamento em background (form manual): {e}")
    finally:
        db.close()




@app.get("/interviews/{session_id}", response_model=schemas.InterviewSessionResponse)
def get_interview(session_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    session = db.query(models.InterviewSession).options(
        joinedload(models.InterviewSession.messages)
    ).filter(models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    session.messages = [m for m in session.messages if m.role != "system_context"]
    return session


@app.get("/assessments/{assessment_id}/session", response_model=schemas.InterviewSessionResponse)
def get_session_by_assessment(assessment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    session = db.query(models.InterviewSession).options(
        joinedload(models.InterviewSession.messages)
    ).filter(models.InterviewSession.assessment_id == assessment_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    session.messages = [m for m in session.messages if m.role != "system_context"]
    return session


# ─── WebSocket: Chat em Tempo Real ────────────────────────────────────────────

@app.websocket("/ws/interview/{session_id}")
async def websocket_interview(session_id: int, websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(session_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_message = data.get("message", "").strip()
            
            if not user_message:
                continue
            
            # Busca sessão
            session = db.query(models.InterviewSession).options(
                joinedload(models.InterviewSession.messages)
            ).filter(models.InterviewSession.id == session_id).first()
            
            if not session or not session.is_active:
                await manager.send_error(session_id, "Sessão inválida ou encerrada.")
                break
            
            assessment = db.query(models.Assessment).filter(
                models.Assessment.id == session.assessment_id
            ).first()
            
            # Salva mensagem do usuário
            user_msg = models.ChatMessage(
                session_id=session_id,
                role="user",
                content=user_message,
                is_evaluation_question=False,
            )
            db.add(user_msg)
            db.commit()
            
            # Indica que está processando
            await manager.send_typing(session_id)
            
            # Prepara histórico para a AI (exclui system_context)
            history = [
                {"role": m.role, "content": m.content}
                for m in session.messages
                if m.role in ("agent", "user")
            ]
            history.append({"role": "user", "content": user_message})
            
            is_autonomous = assessment.mode == models.InterviewMode.AUTONOMOUS
            
            # Busca contexto de perguntas (modo guiado)
            questions_context = ""
            if not is_autonomous:
                ctx_msg = next((m for m in session.messages if m.role == "system_context"), None)
                if ctx_msg:
                    questions = json.loads(ctx_msg.content)
                    questions_context = "\n".join([
                        f"{i+1}. [{q['category']} / {q['subcategory']}] {q['text']}"
                        for i, q in enumerate(questions)
                    ])
            
            # Avalia a última resposta do usuário em background
            last_agent_eval_msg = next(
                (m for m in reversed(session.messages) if m.role == "agent" and m.is_evaluation_question),
                None
            )
            if last_agent_eval_msg:
                eval_result = await evaluate_response(
                    question=last_agent_eval_msg.content,
                    answer=user_message,
                )
                # Salva resposta avaliada
                response_rec = models.Response(
                    assessment_id=assessment.id,
                    question_id=last_agent_eval_msg.question_id,
                    score=eval_result["score"],
                    raw_answer=user_message,
                    ai_analysis=eval_result["analysis"],
                    ai_question=last_agent_eval_msg.content if is_autonomous else None,
                )
                db.add(response_rec)
                db.commit()
            
            # Verifica se deve encerrar
            should_finish = False
            if is_autonomous and session.questions_asked >= session.total_questions:
                should_finish = True
            elif not is_autonomous:
                ctx_msg = next((m for m in session.messages if m.role == "system_context"), None)
                if ctx_msg:
                    questions = json.loads(ctx_msg.content)
                    if session.questions_asked >= len(questions):
                        should_finish = True
            
            if should_finish:
                # Encerra entrevista e gera feedback
                session.is_active = False
                session.finished_at = datetime.utcnow()
                assessment.status = models.AssessmentStatus.COMPLETED
                assessment.completed_at = datetime.utcnow()
                db.commit()
                
                await manager.send_interview_complete(session_id, assessment.id)
                
                # Gera feedback em background
                await _generate_and_save_feedback(assessment.id, db)
                break
            
            # Monta perfil organizacional da empresa (M01)
            company_user = db.query(models.User).filter(
                models.User.id == assessment.company_id
            ).first()
            org_profile = None
            if company_user and any([
                company_user.sector, company_user.employee_count,
                company_user.it_model, company_user.regulations
            ]):
                org_profile = {
                    "sector": company_user.sector,
                    "employee_count": company_user.employee_count,
                    "it_model": company_user.it_model,
                    "regulations": company_user.regulations,
                }

            # Gera próxima mensagem do agente
            agent_reply = await conduct_interview(
                history=history,
                questions_context=questions_context,
                autonomous=is_autonomous,
                questions_asked=session.questions_asked,
                total_questions=session.total_questions,
                org_profile=org_profile,
            )
            
            # Determina se é uma pergunta de avaliação
            is_eval_q = True  # Cada resposta do agente é tratada como pergunta de avaliação
            session.questions_asked += 1
            
            agent_msg = models.ChatMessage(
                session_id=session_id,
                role="agent",
                content=agent_reply,
                is_evaluation_question=is_eval_q,
            )
            db.add(agent_msg)
            db.commit()
            
            # Envia para o cliente
            await manager.send_agent_message(session_id, agent_reply, {
                "questions_asked": session.questions_asked,
                "total_questions": session.total_questions,
            })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_error(session_id, f"Erro interno: {str(e)}")
        manager.disconnect(session_id)


async def _generate_and_save_feedback(assessment_id: int, db: Session):
    """Gera e salva o feedback da IA para o assessment."""
    try:
        assessment = db.query(models.Assessment).options(
            joinedload(models.Assessment.responses),
            joinedload(models.Assessment.company),
        ).filter(models.Assessment.id == assessment_id).first()
        
        if not assessment:
            return
        
        # Prepara dados para o feedback
        responses_data = []
        for r in assessment.responses:
            q_text = r.ai_question or (r.question.text if r.question else "")
            responses_data.append({
                "question": q_text,
                "answer": r.raw_answer or "",
                "score": r.score or 0,
                "analysis": r.ai_analysis or "",
            })
        
        if not responses_data:
            return
        
        score_geral = sum(r["score"] for r in responses_data) / len(responses_data)
        nivel, descricao, nivel_numerico = calculate_maturity_level(score_geral)

        # M02 — calcular coverage_map com base nos framework_refs das perguntas respondidas
        coverage_counter: dict[str, int] = {}
        for r in assessment.responses:
            if r.question and r.question.framework_refs:
                try:
                    refs = json.loads(r.question.framework_refs)
                    for ref in refs:
                        prefix = ref.split(":")[0]
                        coverage_counter[prefix] = coverage_counter.get(prefix, 0) + 1
                except Exception:
                    pass

        # Transcript legível para extração de KPIs pelo LLM
        transcript_lines = []
        for i, r in enumerate(responses_data, 1):
            if r["question"] and r["answer"]:
                transcript_lines.append(f"P{i}: {r['question']}")
                transcript_lines.append(f"R{i}: {r['answer']}")
        transcript = "\n".join(transcript_lines)

        # Scores por categoria (agrupados pela pergunta da subcategoria)
        cat_scores: dict[str, list[float]] = {}
        for r in assessment.responses:
            if r.score is None:
                continue
            if r.question and r.question.subcategory and r.question.subcategory.category:
                cat_name = r.question.subcategory.category.name
                cat_scores.setdefault(cat_name, []).append(r.score)
        category_scores_calc = {
            cat: round(sum(scores) / len(scores), 1)
            for cat, scores in cat_scores.items()
        }

        # Perfil organizacional
        comp = assessment.company
        org_profile = {
            "sector": comp.sector or "não informado",
            "employee_count": comp.employee_count or "não informado",
            "it_model": comp.it_model or "não informado",
            "regulations": json.loads(comp.regulations) if comp.regulations else [],
        }

        assessment_data = {
            "company_name": comp.company_name or comp.username,
            "mode": assessment.mode,
            "score_geral": round(score_geral, 2),
            "responses": responses_data,
            "transcript": transcript,
            "category_scores": category_scores_calc,
            "org_profile": org_profile,
        }

        feedback_data = await generate_feedback(assessment_data)

        # Salva feedback
        raw_findings = feedback_data.get("findings", [])
        critical_count = sum(1 for f in raw_findings if f.get("severity") == "CRÍTICO")

        feedback = models.AIFeedback(
            assessment_id=assessment_id,
            overall_summary=feedback_data.get("overall_summary", ""),
            strengths=json.dumps(feedback_data.get("strengths", []), ensure_ascii=False),
            weaknesses=json.dumps(feedback_data.get("weaknesses", []), ensure_ascii=False),
            recommendations=json.dumps(feedback_data.get("recommendations", []), ensure_ascii=False),
            category_scores=json.dumps(feedback_data.get("category_scores", {}), ensure_ascii=False),
            score_geral=round(score_geral, 2),
            nivel=nivel,
            nivel_numerico=nivel_numerico,
            coverage_map=json.dumps(coverage_counter, ensure_ascii=False) if coverage_counter else None,
            findings=json.dumps(raw_findings, ensure_ascii=False),
            action_plan_90d=json.dumps(feedback_data.get("action_plan_90d", {}), ensure_ascii=False),
            framework_diagnoses=json.dumps(feedback_data.get("framework_diagnoses", []), ensure_ascii=False),
            kpi_indicators=json.dumps(feedback_data.get("kpi_indicators", []), ensure_ascii=False),
            critical_findings_count=critical_count,
        )
        db.add(feedback)
        
        assessment.status = models.AssessmentStatus.FEEDBACK_READY
        db.commit()
    except Exception as e:
        print(f"Erro ao gerar feedback: {e}")


# ─── Feedback ─────────────────────────────────────────────────────────────────

@app.get("/assessments/{assessment_id}/feedback", response_model=schemas.AIFeedbackResponse)
def get_feedback(assessment_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    feedback = db.query(models.AIFeedback).filter(models.AIFeedback.assessment_id == assessment_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback ainda não disponível")
    
    return schemas.AIFeedbackResponse(
        id=feedback.id,
        assessment_id=feedback.assessment_id,
        overall_summary=feedback.overall_summary,
        strengths=json.loads(feedback.strengths),
        weaknesses=json.loads(feedback.weaknesses),
        recommendations=json.loads(feedback.recommendations),
        category_scores=json.loads(feedback.category_scores),
        score_geral=feedback.score_geral,
        nivel=feedback.nivel,
        nivel_numerico=feedback.nivel_numerico or 0,
        coverage_map=json.loads(feedback.coverage_map) if feedback.coverage_map else None,
        findings=json.loads(feedback.findings) if feedback.findings else None,
        action_plan_90d=json.loads(feedback.action_plan_90d) if feedback.action_plan_90d else None,
        framework_diagnoses=json.loads(feedback.framework_diagnoses) if feedback.framework_diagnoses else None,
        kpi_indicators=json.loads(feedback.kpi_indicators) if feedback.kpi_indicators else None,
        critical_findings_count=feedback.critical_findings_count or 0,
        generated_at=feedback.generated_at,
    )

@app.get("/assessments/my/list")
def get_my_assessments(page: int = 1, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Lista assessments paginados do usuário atual (empresa ou avaliador)."""
    if current_user.role == models.UserRole.COMPANY:
        query = db.query(models.Assessment).filter(
            models.Assessment.company_id == current_user.id
        )
    else:
        query = db.query(models.Assessment).filter(
            models.Assessment.evaluator_id == current_user.id
        )
    
    total = query.count()
    assessments = query.order_by(models.Assessment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for a in assessments:
        result.append({
            "id": a.id,
            "status": a.status,
            "mode": a.mode,
            "created_at": a.created_at,
            "completed_at": a.completed_at,
            "company_id": a.company_id,
            "evaluator_id": a.evaluator_id,
            "has_feedback": a.feedback is not None,
        })
    pages = (total + limit - 1) // limit if limit > 0 else 0
    return {"items": result, "total": total, "page": page, "pages": pages}

# ─── Legacy: Report endpoint (mantido para compatibilidade) ───────────────────

@app.get("/assessments/latest/report")
def get_latest_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    assessment = db.query(models.Assessment)\
        .filter(models.Assessment.company_id == current_user.id)\
        .order_by(models.Assessment.created_at.desc())\
        .first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Nenhuma avaliação encontrada")
    
    if assessment.feedback:
        return {
            "score_geral": assessment.feedback.score_geral,
            "nivel": assessment.feedback.nivel,
            "descricao": assessment.feedback.overall_summary[:300] + "...",
            "company": assessment.company.company_name,
            "date": assessment.created_at,
            "status": assessment.status,
            "has_ai_feedback": True,
            "assessment_id": assessment.id,
        }
    
    responses = db.query(models.Response).filter(models.Response.assessment_id == assessment.id).all()
    if not responses:
        return {"score_geral": 0, "nivel": "N/A", "message": "Nenhuma resposta encontrada"}
    
    total_score = sum(r.score for r in responses if r.score) / max(len(responses), 1)
    nivel, descricao, _ = calculate_maturity_level(total_score)
    
    return {
        "score_geral": round(total_score, 2),
        "nivel": nivel,
        "descricao": descricao,
        "company": assessment.company.company_name if assessment.company else "",
        "date": assessment.created_at,
        "status": assessment.status,
    }

_FRAMEWORK_LABELS = {
    "COBIT": "COBIT 2019",
    "ITIL": "ITIL 4",
    "ISO27001": "ISO 27001",
    "NIST": "NIST CSF",
    "CIS": "CIS Controls",
    "ISO20000": "ISO 20000",
}

def _dominant_framework_for_category(category_name: str, db: Session) -> str:
    """Retorna o label do framework mais frequente nas questões de uma categoria."""
    cat = db.query(models.Category).filter(models.Category.name == category_name).first()
    if not cat:
        return "—"
    counts: dict[str, int] = {}
    for sub in cat.subcategories:
        for q in sub.questions:
            if not q.framework_refs:
                continue
            try:
                refs = json.loads(q.framework_refs) if isinstance(q.framework_refs, str) else q.framework_refs
            except Exception:
                continue
            for ref in refs:
                prefix = ref.split(":")[0] if ":" in ref else ref
                counts[prefix] = counts.get(prefix, 0) + 1
    if not counts:
        return "—"
    dominant = max(counts, key=counts.get)
    return _FRAMEWORK_LABELS.get(dominant, dominant)


@app.get("/assessments/{assessment_id}/report", response_model=schemas.ReportResponse)
def get_report(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    assessment = (
        db.query(models.Assessment)
        .options(joinedload(models.Assessment.company), joinedload(models.Assessment.evaluator))
        .filter(models.Assessment.id == assessment_id)
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment não encontrado")

    # Permissões: COMPANY só vê o próprio, EVALUATOR só vê os que avaliou, ADMIN vê tudo
    role = current_user.role
    if role == models.UserRole.COMPANY and assessment.company_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if role == models.UserRole.EVALUATOR and assessment.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    fb = assessment.feedback
    if not fb:
        raise HTTPException(status_code=404, detail="Relatório ainda não gerado para esta avaliação")

    # Desserializar campos JSON do AIFeedback
    def _load(val, default):
        if val is None:
            return default
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return default

    category_scores: dict = _load(fb.category_scores, {})
    strengths: list = _load(fb.strengths, [])
    weaknesses: list = _load(fb.weaknesses, [])
    recommendations: list = _load(fb.recommendations, [])
    findings: list = _load(fb.findings, [])
    action_plan_90d: dict = _load(fb.action_plan_90d, {})
    framework_diagnoses: list = _load(fb.framework_diagnoses, [])
    kpi_indicators: list = _load(fb.kpi_indicators, [])
    coverage_map: dict = _load(fb.coverage_map, {})

    # Enriquecer scores por categoria com o framework dominante
    category_scores_enriched = [
        schemas.ReportCategoryScore(
            name=cat_name,
            framework=_dominant_framework_for_category(cat_name, db),
            score=round(float(score), 1),
        )
        for cat_name, score in category_scores.items()
    ]

    # Dados da empresa
    company_user = assessment.company
    regulations_raw = _load(company_user.regulations, []) if company_user else []
    company_data = schemas.ReportCompany(
        name=company_user.company_name or company_user.username if company_user else "—",
        sector=company_user.sector if company_user else None,
        employee_count=company_user.employee_count if company_user else None,
        it_model=company_user.it_model if company_user else None,
        regulations=regulations_raw if isinstance(regulations_raw, list) else None,
    )

    evaluator_data = None
    if assessment.evaluator:
        evaluator_data = schemas.ReportEvaluator(name=assessment.evaluator.username)

    nivel, nivel_descricao, nivel_numerico = calculate_maturity_level(fb.score_geral)
    critical_count = fb.critical_findings_count or sum(
        1 for f in findings if f.get("severity") == "CRÍTICO"
    )

    return schemas.ReportResponse(
        assessment_id=assessment.id,
        generated_at=fb.generated_at,
        company=company_data,
        evaluator=evaluator_data,
        score_geral=round(fb.score_geral, 1),
        nivel=fb.nivel or nivel,
        nivel_numerico=fb.nivel_numerico or nivel_numerico,
        nivel_descricao=nivel_descricao,
        overall_summary=fb.overall_summary or "",
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        category_scores_enriched=category_scores_enriched,
        findings=findings,
        critical_findings_count=critical_count,
        action_plan_90d=action_plan_90d,
        framework_diagnoses=framework_diagnoses,
        kpi_indicators=kpi_indicators,
    )


@app.get("/assessments/{assessment_id}/report/pdf")
def get_report_pdf(
    assessment_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    from weasyprint import HTML as WeasyprintHTML
    from jose import JWTError, jwt as _jwt

    try:
        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    current_user = db.query(models.User).filter(models.User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment não encontrado")

    if current_user.role == "COMPANY" and assessment.company_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if current_user.role == "EVALUATOR" and assessment.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    fb = db.query(models.AIFeedback).filter(models.AIFeedback.assessment_id == assessment_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Relatório ainda não gerado para este assessment")

    def _load(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return val
        return val or []

    nivel, nivel_descricao, nivel_numerico = calculate_maturity_level(fb.score_geral)
    score = round(fb.score_geral, 1)

    if score >= 70:
        score_color = "#22c55e"
    elif score >= 50:
        score_color = "#06b6d4"
    elif score >= 30:
        score_color = "#f59e0b"
    else:
        score_color = "#ef4444"

    company = assessment.company
    evaluator = assessment.evaluator

    category_scores_raw = _load(fb.category_scores) if hasattr(fb, "category_scores") else []
    category_scores_enriched = []
    for cs in (category_scores_raw if isinstance(category_scores_raw, list) else []):
        cat_name = cs.get("category", "")
        cat_obj = db.query(models.Category).filter(models.Category.name == cat_name).first()
        fw_label = "—"
        if cat_obj:
            fw_label = _dominant_framework_for_category(cat_obj.id, db)
        category_scores_enriched.append({**cs, "framework": fw_label})

    findings = _load(fb.findings) if fb.findings else []
    critical_count = fb.critical_findings_count or sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == "CRÍTICO")
    action_plan_90d = _load(fb.action_plan_90d) if fb.action_plan_90d else {}
    framework_diagnoses = _load(fb.framework_diagnoses) if fb.framework_diagnoses else []
    kpi_indicators = _load(fb.kpi_indicators) if fb.kpi_indicators else []
    strengths = _load(fb.strengths) if fb.strengths else []
    weaknesses = _load(fb.weaknesses) if fb.weaknesses else []
    recommendations = _load(fb.recommendations) if fb.recommendations else []

    generated_at_fmt = fb.generated_at.strftime("%d/%m/%Y %H:%M") if fb.generated_at else datetime.utcnow().strftime("%d/%m/%Y %H:%M")

    html_str = _templates.get_template("report.html").render(
        company={"name": company.company_name if company else "—", "sector": getattr(company, "sector", "—"), "employee_count": getattr(company, "employee_count", "—"), "it_model": getattr(company, "it_model", "—"), "regulations": getattr(company, "regulations", "—")},
        evaluator={"name": evaluator.username if evaluator else "—", "email": evaluator.email if evaluator else "—"} if evaluator else {"name": "Autônomo", "email": "—"},
        score_geral=score,
        nivel=fb.nivel or nivel,
        nivel_numerico=fb.nivel_numerico or nivel_numerico,
        nivel_descricao=nivel_descricao,
        score_color=score_color,
        overall_summary=fb.overall_summary or "",
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        category_scores_enriched=category_scores_enriched,
        findings=findings,
        critical_findings_count=critical_count,
        action_plan_90d=action_plan_90d,
        framework_diagnoses=framework_diagnoses,
        kpi_indicators=kpi_indicators,
        generated_at_fmt=generated_at_fmt,
        assessment_id=assessment_id,
    )

    pdf_bytes = WeasyprintHTML(string=html_str, base_url="/").write_pdf()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="relatorio-avalia-ai-{assessment_id}.pdf"'},
    )


# ─── Legacy: Sugestões de IA (mantido para o banco de questões) ───────────────

@app.post("/ai/generate-questions", response_model=schemas.AIResponse)
def generate_ai_questions(req: schemas.AIRequest, current_user: models.User = Depends(check_evaluator)):
    cat_req = req.category.lower()
    sub_req = req.subcategory.lower()
    
    suggestions_db = {
        "governança": {
            "estratégia": ["Existe um comitê de TI formalizado com participação da diretoria?","O plano diretor de TI (PDTI) está alinhado aos objetivos estratégicos do negócio?","Como os investimentos em TI são priorizados em relação ao ROI esperado?"],
            "riscos": ["Existe uma matriz de riscos de TI atualizada periodicamente?","Há um plano de continuidade de negócios (PCN) testado nos últimos 12 meses?","Como as vulnerabilidades de segurança são monitoradas e mitigadas?"]
        },
        "processos": {
            "itil": ["O catálogo de serviços está publicado e acessível aos usuários?","Existe um processo formal de gestão de incidentes com SLAs definidos?","Como o feedback do usuário é coletado para melhoria contínua dos serviços?"],
            "fluxo": ["Há um mapeamento de processos críticos de TI?","Como a gestão de mudanças é realizada para evitar impactos não planejados?","Existe automação de processos repetitivos na operação de TI?"]
        },
        "infraestrutura": {
            "segurança": ["Existem políticas de controle de acesso e MFA implementadas?","Há logs de auditoria centralizados para todos os sistemas críticos?","A empresa utiliza ferramentas de proteção contra ransomware e vazamento de dados?"],
            "cloud": ["A infraestrutura permite elasticidade automática conforme a demanda?","Existem processos de FinOps para controle de custos em nuvem?","Como a redundância e alta disponibilidade são garantidas em ambientes híbridos?"]
        }
    }
    
    final_suggestions = []
    for c_key, subs in suggestions_db.items():
        if c_key in cat_req:
            for s_key, s_list in subs.items():
                if s_key in sub_req:
                    final_suggestions = s_list
                    break
            if not final_suggestions:
                final_suggestions = list(subs.values())[0]
            break
    
    if not final_suggestions:
        final_suggestions = [
            f"Como o pilar de {req.subcategory} é monitorado atualmente?",
            f"Quais KPIs de desempenho são utilizados para {req.subcategory}?",
            f"Há investimentos planejados para melhorar a maturidade em {req.subcategory}?",
        ]
    
    return {"suggestions": final_suggestions}
