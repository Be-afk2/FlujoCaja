from sqlmodel import SQLModel, create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

