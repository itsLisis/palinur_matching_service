from fastapi import FastAPI
from db import Base, engine, SessionLocal
from routers import matching_router
import models

app = FastAPI(title="Matching Service")

Base.metadata.create_all(bind=engine)

app.include_router(matching_router.router)


@app.get("/")
def read_root():
    return {"message": "Matching Service is running!"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "matching"}
