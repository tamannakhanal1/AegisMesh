from fastapi import FastAPI, HTTPException
from . import db, routes

app = FastAPI(title="AegisMesh Controller", version="0.1")

db.init_db()

app.include_router(routes.router, prefix="/")
