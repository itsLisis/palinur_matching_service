from fastapi import FastAPI
from db import Base, engine
import models

app = FastAPI(title="My Dating App Service")

# THIS LINE CREATES YOUR TABLES!
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Database tables created successfully!"}
