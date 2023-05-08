from fastapi import FastAPI, status, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm, HTTPBasic
from app.config import auth
from fastapi.responses import RedirectResponse
from app.controllers.auth import (
    create_access_token,
)
from uuid import uuid4
router = APIRouter()
security = HTTPBasic()


@router.post('', summary="Create access tokens for user")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if auth.user_name != form_data.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username"
        )

    if auth.password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    return {
        "access_token": create_access_token(auth.user_name),
        "token_type": "bearer",
    }
