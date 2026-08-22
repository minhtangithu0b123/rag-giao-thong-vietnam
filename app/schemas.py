from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)


class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    session_id: str = "default"
