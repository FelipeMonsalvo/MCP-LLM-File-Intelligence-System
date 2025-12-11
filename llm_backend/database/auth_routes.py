"""
Authentication Routes: register, login, logout, and user info
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import timedelta
from .database import get_db, User
from .auth import (get_password_hash, authenticate_user, create_access_token, verify_token, get_user_by_id, ACCESS_TOKEN_EXPIRE_MINUTES)

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    token = request.cookies.get(AUTH_COOKIE_NAME)

    if not token:
        raise credentials_exception
    
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")

    if user_id is None:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "username": user.username}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=AUTH_COOKIE_NAME, httponly=True, samesite="lax", path="/")
    return {"message": "Successfully logged out"}


AUTH_COOKIE_NAME = "access_token"