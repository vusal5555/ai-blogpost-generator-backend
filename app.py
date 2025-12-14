from typing import Union
from pydantic import BaseModel


from fastapi import FastAPI


class GenerateRequest(BaseModel):
    prd_content: str


class GenerateResponse(BaseModel):
    run_id: str
    final_post: str
    status: str


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/generate")
def generate_content():
    pass
