from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from enum import Enum

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Enum za status zadatka
class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    in_progress = "in-progress"

# Model za zadatke
class TaskModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: str
    status: TaskStatus = TaskStatus.pending
    user_id: PyObjectId  # Dodano polje za povezivanje korisnika

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Finish FastAPI project",
                "description": "Complete CRUD operations",
                "status": "pending",
                "user_id": "60d9f1f1f4e9c9e1f8e8e8e8"  # Primjer user_id
            }
        }

# Model za ažuriranje zadatka
class UpdateTaskModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[TaskStatus]
    user_id: Optional[PyObjectId]  # Mogućnost ažuriranja korisnika koji je povezan s zadatkom

    class Config:
        schema_extra = {
            "example": {
                "title": "Update the FastAPI project",
                "description": "Fix bugs in CRUD operations",
                "status": "completed",
                "user_id": "60d9f1f1f4e9c9e1f8e8e8e8"  # Primjer user_id
            }
        }

# Model za korisnike
class UserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: str

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "johndoe@example.com"
            }
        }
