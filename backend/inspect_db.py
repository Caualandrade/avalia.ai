import sys, os, asyncio
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('OPENAI_API_KEY', 'sk-test-placeholder')

async def test():
    from database import get_db
    import models
    
    db = next(get_db())
    
    # Simula usuário empresa
    user = db.query(models.User).filter(models.User.username == 'empresa').first()
    print(f"Usuário: {user.username} id={user.id} role={user.role}")
    
    try:
        assessment = models.Assessment(
            company_id=user.id,
            evaluator_id=None,
            status=models.AssessmentStatus.IN_PROGRESS,
            mode=models.InterviewMode.AUTONOMOUS,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        print(f"Assessment criado: id={assessment.id}, status={assessment.status}, mode={assessment.mode}")
        
        session = models.InterviewSession(
            assessment_id=assessment.id,
            total_questions=10,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        print(f"Session criada: id={session.id}")
        
        # Limpa
        db.delete(session)
        db.delete(assessment)
        db.commit()
        print("Limpeza OK")
        print("\n✓ Endpoint /interviews/start DEVE funcionar agora!")
        
    except Exception as e:
        db.rollback()
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
