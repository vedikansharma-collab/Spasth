from app.database.session import engine, Base
from app.models.policy import Policy, PolicyPage

def init_db():
    Base.metadata.create_all(bind=engine)
