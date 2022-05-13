from fastapi import APIRouter, HTTPException
from models import User
from routers import db

router = APIRouter()


@router.post("/add/{user_id}")
async def get_users(user_id: str, user: User):
    try:
        user.postsCreated = []
        db.collection(u"users").document(user_id).set(dict(user))

        return {"message": "User added successfully"}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
