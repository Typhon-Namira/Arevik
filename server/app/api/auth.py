from fastapi import APIRouter, Depends, Header
from app.auth import Credentials, login, register, require_user, revoke

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register")
def register_route(payload: Credentials):
    return register(payload)

@router.post("/login")
def login_route(payload: Credentials):
    return login(payload)

@router.get("/me")
def me_route(user_id: int = Depends(require_user)):
    return {"user_id": user_id}

@router.post("/logout")
def logout_route(user_id: int = Depends(require_user),
                 authorization: str | None = Header(default=None)):
    revoke(authorization)
    return {"ok": True}
