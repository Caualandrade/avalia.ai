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
    # M04 — separar Governança Corporativa de TI de Gestão de TI
    if not db.query(models.Category).filter(models.Category.name == "Governança Corporativa de TI").first():
        cat_gov = models.Category(name="Governança Corporativa de TI", weight=1.5)
        db.add(cat_gov)
        db.commit()

        sub_gov1 = models.Subcategory(name="Estratégia e Alinhamento", category_id=cat_gov.id, weight=1.2)
        db.add(sub_gov1)
        db.commit()

        db.add_all([
            models.Question(
                text="O conselho de administração possui participação ativa nas decisões de TI?",
                subcategory_id=sub_gov1.id,
                framework_refs='["COBIT:EDM01", "COBIT:APO02"]'
            ),
            models.Question(
                text="Existe um comitê de TI com representantes da diretoria que define prioridades e investimentos?",
                subcategory_id=sub_gov1.id,
                framework_refs='["COBIT:EDM01", "COBIT:APO02"]'
            ),
            models.Question(
                text="Os investimentos em TI são vinculados formalmente às metas estratégicas de negócio (ROI, OKRs)?",
                subcategory_id=sub_gov1.id,
                framework_refs='["COBIT:APO05", "COBIT:EDM02"]'
            ),
        ])

        sub_gov2 = models.Subcategory(name="Conformidade e Risco Corporativo", category_id=cat_gov.id, weight=1.2)
        db.add(sub_gov2)
        db.commit()

        db.add_all([
            models.Question(
                text="Existe um comitê de auditoria que supervisiona os riscos tecnológicos e de segurança?",
                subcategory_id=sub_gov2.id,
                framework_refs='["COBIT:EDM03", "ISO27001:A.5.35"]'
            ),
            models.Question(
                text="A organização possui uma política formal de gestão de riscos de TI aprovada pela diretoria?",
                subcategory_id=sub_gov2.id,
                framework_refs='["COBIT:APO12", "ISO27001:6.1"]'
            ),
        ])
        print("Categoria 'Governança Corporativa de TI' criada")

    if not db.query(models.Category).filter(models.Category.name == "Gestão de TI").first():
        cat_mgmt = models.Category(name="Gestão de TI", weight=1.2)
        db.add(cat_mgmt)
        db.commit()

        sub_mgmt1 = models.Subcategory(name="Processos e Projetos", category_id=cat_mgmt.id, weight=1.0)
        db.add(sub_mgmt1)
        db.commit()

        db.add_all([
            models.Question(
                text="A TI utiliza alguma metodologia formal de gestão de projetos (PMO, Scrum, SAFe)?",
                subcategory_id=sub_mgmt1.id,
                framework_refs='["COBIT:BAI01", "COBIT:APO03"]'
            ),
            models.Question(
                text="O orçamento de TI é planejado anualmente com base em metas e riscos identificados?",
                subcategory_id=sub_mgmt1.id,
                framework_refs='["COBIT:APO06"]'
            ),
        ])

        sub_mgmt2 = models.Subcategory(name="Fornecedores e Contratos", category_id=cat_mgmt.id, weight=1.0)
        db.add(sub_mgmt2)
        db.commit()

        db.add_all([
            models.Question(
                text="Existe um processo formal de gestão de fornecedores de TI, incluindo SLAs e avaliações periódicas?",
                subcategory_id=sub_mgmt2.id,
                framework_refs='["COBIT:APO10", "ITIL:Supplier-Management"]'
            ),
            models.Question(
                text="Os contratos com fornecedores de TI incluem cláusulas de segurança, privacidade e continuidade?",
                subcategory_id=sub_mgmt2.id,
                framework_refs='["COBIT:APO10", "ISO27001:A.5.19"]'
            ),
        ])
        print("Categoria 'Gestão de TI' criada")

    if not db.query(models.Category).filter(models.Category.name == "Gestão de Serviços (ITIL)").first():
        cat2 = models.Category(name="Gestão de Serviços (ITIL)", weight=1.0)
        db.add(cat2)
        db.commit()

        sub2 = models.Subcategory(name="Catálogo de Serviços", category_id=cat2.id, weight=1.0)
        db.add(sub2)
        db.commit()

        db.add(models.Question(
            text="Existe um catálogo de serviços de TI formalizado e disponível para os usuários?",
            subcategory_id=sub2.id,
            framework_refs='["ITIL:Service-Catalogue-Management"]'
        ))
        print("Categoria 'Gestão de Serviços (ITIL)' criada")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed()
