from pydantic import BaseModel


class GenericResponse(BaseModel):
    status: int
    details: str
