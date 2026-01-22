from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
