from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from database import users_collection

app = FastAPI()

class User(BaseModel):
    username: str
    email: str

@app.post("/users/", response_model=dict)
async def create_user(user: User):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    user_dict = user.dict()
    result = await users_collection.insert_one(user_dict)
    return {"id": str(result.inserted_id)}

@app.get("/users/", response_model=List[User])
async def get_users():
    users = await users_collection.find().to_list(100)
    return users

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: User):
    update_data = user.dict()
    result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no change detected")
    return await get_user(user_id)

@app.delete("/users/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
