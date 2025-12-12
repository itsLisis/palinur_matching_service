from fastapi import FastAPI
from db import Base, engine
from routers import matching_router
import models

app = FastAPI(title="My Dating App Service")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app.include_router(matching_router.router)

@app.get("/")
def read_root():
    return {"message": "Database tables created successfully!"}
