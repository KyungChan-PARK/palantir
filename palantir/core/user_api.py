from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .auth import (
    get_current_user,
    get_password_hash,
    require_role,
)
from .database import get_db
from .user import UserDB

router = APIRouter()


@router.get("/users/me")
def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "scopes": current_user.scopes,
    }


@router.post("/users/", status_code=201)
def create_user(
    user: dict,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_role("admin")),
):
    if db.query(UserDB).filter(UserDB.username == user["username"]).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자 이름입니다")
    db_user = UserDB(
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        hashed_password=get_password_hash(user["password"]),
        scopes=user.get("scopes", []),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "scopes": db_user.scopes,
    }


@router.get("/users/")
def list_users(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_role("admin")),
):
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "scopes": u.scopes,
        }
        for u in db.query(UserDB).all()
    ]


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    if current_user.id != user_id and "admin" not in (current_user.scopes or []):
        raise HTTPException(status_code=403, detail="Forbidden")
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "scopes": user.scopes,
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user: dict,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    if current_user.id != user_id and "admin" not in (current_user.scopes or []):
        raise HTTPException(status_code=403, detail="Forbidden")
    db_user = db.get(UserDB, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.full_name = user.get("full_name", db_user.full_name)
    db_user.email = user.get("email", db_user.email)
    if "password" in user:
        db_user.hashed_password = get_password_hash(user["password"])
    db.commit()
    db.refresh(db_user)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "scopes": db_user.scopes,
    }


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_role("admin")),
):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return None

