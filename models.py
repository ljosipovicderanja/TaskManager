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

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Finish FastAPI project",
                "description": "Complete CRUD operations",
                "status": "pending"
            }
        }

# Model za ažuriranje zadatka
class UpdateTaskModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[TaskStatus]

    class Config:
        schema_extra = {
            "example": {
                "title": "Update the FastAPI project",
                "description": "Fix bugs in CRUD operations",
                "status": "completed"
            }
        }

# Ako imaš druge modele, npr. korisnika:
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
