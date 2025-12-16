from typing import Union
from pydantic import BaseModel
from agents.orchestrater import orchestrater
import sys
import os
import uuid
import sys
import os
from fastapi.middleware.cors import CORSMiddleware

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from subapase_client import supabase


from fastapi import FastAPI, HTTPException


class GenerateRequest(BaseModel):
    prd_content: str


class GenerateResponse(BaseModel):
    run_id: str
    final_post: str
    research_notes: str
    draft: str
    fact_check_passed: bool
    retry_count: int


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate_content(request: GenerateRequest):

    try:

        run_id = str(uuid.uuid4())
        state = orchestrater.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.prd_content,
                    }
                ],
                "retry_count": 0,
                "run_id": run_id,
            }
        )

        supabase.table("posts").insert(
            {
                "run_id": state.get("run_id"),
                "final_post": state.get("final_post", "No final post generated"),
                "prd_content": request.prd_content,
                "research_notes": state.get("research_notes", ""),
                "fact_check_passed": state.get("fact_check_passed", False),
                "draft": state.get("draft", ""),
                "retry_count": state.get("retry_count", 0),
            }
        ).execute()

        return GenerateResponse(
            run_id=state.get("run_id"),
            final_post=state.get("final_post", "No final post generated"),
            research_notes=state.get("research_notes", ""),
            draft=state.get("draft", ""),
            fact_check_passed=state.get("fact_check_passed", False),
            retry_count=state.get("retry_count", 0),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating content: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
