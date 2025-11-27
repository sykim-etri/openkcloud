import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt

from app.schemas.login import LoginResponse, UserCreate, LoginRequest, RefreshTokenRequest, UserBase
from app.models.user import User
from app.db.dependencies import get_db 
from app.utils.auth import verify_password, create_access_token, hash_password, decode_refresh_token

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token_data = {"sub": user.email, "role": user.role}
    access_token = create_access_token(
        data=token_data,
        expires_delta=datetime.timedelta(hours=10)
    )
    
    refresh_token = create_access_token(
        data=token_data,
        expires_delta=datetime.timedelta(days=7)
    )
    
    user_info = {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "department": user.department,
    }
    
    return LoginResponse(
        success=True,
        user=UserBase(**user_info),
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=LoginResponse)
def refresh_token(request: RefreshTokenRequest):
    """
    Validates the refresh token sent by the client
    and issues a new access token.
    """
    try:
        payload = decode_refresh_token(request.refresh_token)
        email = payload.get("sub")
        role = payload.get("role")
        if email is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Issue new access token (expires in 60 minutes)
    new_access_token = create_access_token(
        data={"sub": email, "role": role},
        expires_delta=datetime.timedelta(minutes=60)
    )
    
    # Reuse user information here (may need to query DB)
    user_info = {
        "email": email,
        "name": "User Name",       # Replace with actual user information
        "role": role,
        "department": "Department" # Replace with actual user information
    }
    
    return LoginResponse(**user_info, success=True, token=new_access_token)

    
@router.post("/create_user")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if a user with the same email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Hash password
    hashed_pw = hash_password(user_data.password)
    
    user = User(
        email=user_data.email,
        hashed_password=hashed_pw,  # Store hashed password
        role=user_data.role,          # Can set default value if needed
        name=user_data.name,
        department=user_data.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"success": True, "user": user.email}