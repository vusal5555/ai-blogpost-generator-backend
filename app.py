import logging

from typing import List, Optional, Union
from pydantic import BaseModel
from agents.orchestrater import orchestrater
import sys
import os
import uuid
import sys
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException as FastAPIHTTPException

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from subapase_client import supabase


from fastapi import FastAPI, HTTPException


class GenerateRequest(BaseModel):
    prd_content: str
    original_run_id: Optional[str] = None


class GenerateResponse(BaseModel):
    run_id: str
    final_post: str
    research_notes: str
    draft: str
    fact_check_passed: bool
    retry_count: int


class LogResponse(BaseModel):
    run_id: str
    agent: str
    input: str
    output: str
    metadata: Union[dict, None] = None
    created_at: str


class PostResponse(BaseModel):
    id: str
    run_id: str
    final_post: str
    prd_content: str
    research_notes: str
    fact_check_passed: bool
    draft: str
    retry_count: int
    created_at: str


class LogsListResponse(BaseModel):
    logs: List[LogResponse]


class PostsListResponse(BaseModel):
    posts: List[PostResponse]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-blogpost-generator-frontend.vercel.app",  # ← No trailing
    ],
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

        is_regeneration = request.original_run_id is not None
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
                "original_run_id": request.original_run_id,
                "is_regeneration": is_regeneration,
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


@app.get("/api/runs/{run_id}/logs", response_model=LogsListResponse)
def get_status(run_id: str):
    try:
        response = (
            supabase.table("agent-logs").select("*").eq("run_id", run_id).execute()
        )
        data = response.data
        if not data:
            raise HTTPException(
                status_code=404, detail=f"No logs found for run_id: {run_id}"
            )

        logs = [LogResponse(**item) for item in data]

        return LogsListResponse(logs=logs)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving status: {str(e)}"
        )


@app.get("/api/posts/{run_id}", response_model=PostsListResponse)
def get_post(run_id: str):
    try:
        response = supabase.table("posts").select("*").eq("run_id", run_id).execute()
        data = response.data
        if not data:
            raise HTTPException(
                status_code=404, detail=f"No post found for run_id: {run_id}"
            )
        posts = [PostResponse(**item) for item in data]
        return PostsListResponse(posts=posts)

    except FastAPIHTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving post: {str(e)}")


@app.get("/api/posts", response_model=PostsListResponse)
def get_all_posts():
    try:
        response = supabase.table("posts").select("*").execute()
        data = response.data
        if not data:
            return PostsListResponse(posts=[])

        posts = [PostResponse(**item) for item in data]

        return PostsListResponse(posts=posts)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving posts: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
