from uuid import UUID

from pydantic import BaseModel


class ExplanationResponseSchema(BaseModel):
    explanation: str
    generated_by: str
    run_id: UUID
