from pydantic import BaseModel
from typing import Optional

class EventCreate(BaseModel):
    source_ip: str
    service: str
    path: Optional[str] = None
    payload: Optional[str] = None
