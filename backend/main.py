from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
    db_q = models.Question(**question.dict())
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

@app.put("/questions/{question_id}", response_model=schemas.QuestionResponse)
def update_question(question_id: int, question: schemas.QuestionUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(check_evaluator)):
    db_q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not db_q:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")
    db_q.text = question.text
    db.commit()
    db.refresh(db_q)
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
            
            # Gera próxima mensagem do agente
            agent_reply = await conduct_interview(
                history=history,
                questions_context=questions_context,
                autonomous=is_autonomous,
                questions_asked=session.questions_asked,
                total_questions=session.total_questions,
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
        nivel, descricao = calculate_maturity_level(score_geral)
        
        assessment_data = {
            "company_name": assessment.company.company_name or assessment.company.username,
            "mode": assessment.mode,
            "score_geral": round(score_geral, 2),
            "responses": responses_data,
        }
        
        feedback_data = await generate_feedback(assessment_data)
        
        # Salva feedback
        feedback = models.AIFeedback(
            assessment_id=assessment_id,
            overall_summary=feedback_data.get("overall_summary", ""),
            strengths=json.dumps(feedback_data.get("strengths", []), ensure_ascii=False),
            weaknesses=json.dumps(feedback_data.get("weaknesses", []), ensure_ascii=False),
            recommendations=json.dumps(feedback_data.get("recommendations", []), ensure_ascii=False),
            category_scores=json.dumps(feedback_data.get("category_scores", {}), ensure_ascii=False),
            score_geral=round(score_geral, 2),
            nivel=nivel,
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
    nivel, descricao = calculate_maturity_level(total_score)
    
    return {
        "score_geral": round(total_score, 2),
        "nivel": nivel,
        "descricao": descricao,
        "company": assessment.company.company_name if assessment.company else "",
        "date": assessment.created_at,
        "status": assessment.status,
    }

@app.get("/assessments/{assessment_id}/report")
def get_report(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment não encontrado")
    
    responses = db.query(models.Response).filter(models.Response.assessment_id == assessment_id).all()
    if not responses:
        return {"score_geral": 0, "nivel": "N/A", "message": "Nenhuma resposta encontrada"}
    
    total_score = sum(r.score for r in responses if r.score) / max(len(responses), 1)
    nivel, descricao = calculate_maturity_level(total_score)
    
    return {
        "score_geral": round(total_score, 2),
        "nivel": nivel,
        "descricao": descricao,
        "company": assessment.company.company_name if assessment.company else "",
        "date": assessment.created_at,
        "status": assessment.status,
    }

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
