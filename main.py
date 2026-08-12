from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

app = FastAPI(title="Bunny App Monolith")
templates = Jinja2Templates(directory="templates")

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    message = Column(String)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- UI ROUTES -----------------
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    records = db.query(Record).all()
    return templates.TemplateResponse("index.html", {"request": request, "records": records})

@app.post("/add")
def add_record(name: str = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
    db_record = Record(name=name, message=message)
    db.add(db_record)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    db.query(Record).filter(Record.id == record_id).delete()
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# ----------------- API ROUTES -----------------
@app.get("/info")
def get_info():
    return {
        "app_name": "Bunny App",
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development"),
        "database_type": "PostgreSQL" if "postgres" in DATABASE_URL else "SQLite"
    }

@app.get("/api/records")
def api_get_records(db: Session = Depends(get_db)):
    return db.query(Record).all()
