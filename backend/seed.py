from database import SessionLocal, engine
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed():
    db = SessionLocal()
    # Create tables
    models.Base.metadata.create_all(bind=engine)

    # 1. Admin User
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        admin = models.User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("admin123"), # In real app, use ENV
            role=models.UserRole.ADMIN
        )
        db.add(admin)
        print("Admin user created")

    # 2. Base Categories/Subcategories/Questions
    # Categorias base conforme documento
    if not db.query(models.Category).first():
        cat1 = models.Category(name="Governança de TI", weight=1.5)
        db.add(cat1)
        db.commit() # Commit to get ID

        sub1 = models.Subcategory(name="Governança Corporativa", category_id=cat1.id, weight=1.2)
        db.add(sub1)
        db.commit()

        q1 = models.Question(text="O conselho de administração possui participação ativa nas decisões de TI?", subcategory_id=sub1.id)
        q2 = models.Question(text="Existe um comitê de auditoria que supervisiona os riscos tecnológicos?", subcategory_id=sub1.id)
        db.add_all([q1, q2])

        cat2 = models.Category(name="Gestão de Serviços (ITIL)", weight=1.0)
        db.add(cat2)
        db.commit()

        sub2 = models.Subcategory(name="Catálogo de Serviços", category_id=cat2.id, weight=1.0)
        db.add(sub2)
        db.commit()

        q3 = models.Question(text="Existe um catálogo de serviços de TI formalizado?", subcategory_id=sub2.id)
        db.add(q3)
        
        print("Seed data created")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
