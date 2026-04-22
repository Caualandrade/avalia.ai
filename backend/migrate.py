"""Script de migração para adicionar novos campos ao banco existente."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine
from sqlalchemy import text

def run_migration():
    migrations = [
        # assessments
        ("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS mode VARCHAR(50) DEFAULT 'GUIDED'", "mode em assessments"),
        ("ALTER TABLE assessments ADD COLUMN IF NOT EXISTS ai_profile TEXT", "ai_profile em assessments"),
        ("ALTER TABLE assessments ALTER COLUMN evaluator_id DROP NOT NULL", "evaluator_id nullable"),
        ("ALTER TABLE assessments ALTER COLUMN completed_at DROP NOT NULL", "completed_at nullable"),
        # responses
        ("ALTER TABLE responses ADD COLUMN IF NOT EXISTS raw_answer TEXT", "raw_answer em responses"),
        ("ALTER TABLE responses ADD COLUMN IF NOT EXISTS ai_analysis TEXT", "ai_analysis em responses"),
        ("ALTER TABLE responses ADD COLUMN IF NOT EXISTS ai_question TEXT", "ai_question em responses"),
        ("ALTER TABLE responses ALTER COLUMN question_id DROP NOT NULL", "question_id nullable"),
        ("ALTER TABLE responses ALTER COLUMN score DROP NOT NULL", "score nullable"),
        # M01 — perfil organizacional em users
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS sector VARCHAR", "sector em users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_count VARCHAR", "employee_count em users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS it_model VARCHAR", "it_model em users"),
        ("ALTER TABLE users ADD COLUMN IF NOT EXISTS regulations TEXT", "regulations em users"),
        # M02 — rastreabilidade de frameworks
        ("ALTER TABLE questions ADD COLUMN IF NOT EXISTS framework_refs TEXT", "framework_refs em questions"),
        ("ALTER TABLE ai_feedbacks ADD COLUMN IF NOT EXISTS coverage_map TEXT", "coverage_map em ai_feedbacks"),
        # M03 — nível numérico 0–5
        ("ALTER TABLE ai_feedbacks ADD COLUMN IF NOT EXISTS nivel_numerico INTEGER DEFAULT 0", "nivel_numerico em ai_feedbacks"),
    ]

    with engine.begin() as conn:
        for sql, label in migrations:
            try:
                conn.execute(text(sql))
                print(f"✓ {label}")
            except Exception as e:
                print(f"✗ {label}: {e}")

    # Cria novas tabelas (interview_invites, interview_sessions, chat_messages, ai_feedbacks)
    import models
    models.Base.metadata.create_all(bind=engine)
    print("✓ Novas tabelas criadas/verificadas")
    print("Migration completa!")

if __name__ == "__main__":
    run_migration()
