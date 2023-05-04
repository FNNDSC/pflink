from fastapi import FastAPI, status, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, HTTPBasic
from app.config import user
from fastapi.responses import RedirectResponse
from app.controllers.auth import (
    get_hashed_password,
    create_access_token,
    create_refresh_token,
    verify_password
)
from uuid import uuid4
router = APIRouter()
security = HTTPBasic()


@router.post('', summary="Create access and refresh tokens for user")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if user.user_name != form_data.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username"
        )

    if user.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    return {
        "access_token": create_access_token(user.user_name),
        "refresh_token": create_refresh_token(user.user_name),
    }
