from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from .schemas import EventCreate
from .db import SessionLocal
from .models import Event
from sqlalchemy.orm import Session
from . import db
import requests
import os

router = APIRouter()

def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

@router.post("/events")
def receive_event(event: EventCreate, db: Session = Depends(get_db)):
    e = Event(
        source_ip=event.source_ip,
        service=event.service,
        path=event.path,
        payload=event.payload
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"status": "ok", "id": e.id}

@router.get("/events")
def list_events(db: Session = Depends(get_db)):
    rows = db.query(Event).order_by(Event.timestamp.desc()).limit(200).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "source_ip": r.source_ip,
            "service": r.service,
            "path": r.path,
            "payload": r.payload,
            "timestamp": r.timestamp.isoformat(),
            "risk_score": r.risk_score
        })
    return out
