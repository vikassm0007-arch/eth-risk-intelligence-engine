"""
Enterprise Authentication & Role-Based Access Control (RBAC) Router
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import time
import secrets
import hashlib
import jwt
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Cookie
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eth_account.messages import encode_defunct
from web3 import Web3

from backend.db import get_db_session, UserModel, AuditLogModel

SECRET_KEY = "SUPER_SECRET_ENTERPRISE_JWT_KEY_EVM_RISK_INTELLIGENCE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 86400  # 24 Hours

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & RBAC"])

# Helper: Password Hashing
def hash_password(password: str) -> str:
    salt = "EVM_RISK_SALT_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Helper: JWT Generation
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# In-Memory SIWE Nonce Store
SIWE_NONCES: Dict[str, str] = {}

# Pydantic Schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "Junior Analyst"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SIWEVerifyRequest(BaseModel):
    wallet_address: str
    signature: str
    message: str

class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    wallet_address: Optional[str] = None
    role: str
    status: str


# Authentication Dependency
async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session)
) -> UserModel:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer authentication token"
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed or expired")

    result = await session.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User account not found")
    return user


def require_roles(allowed_roles: List[str]):
    """Decorator / Dependency factory for enforcing RBAC permissions."""
    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {allowed_roles}"
            )
        return current_user
    return role_checker


# Auth Endpoints

@auth_router.post("/signup", response_model=UserResponse)
async def signup(req: SignupRequest, session: AsyncSession = Depends(get_db_session)):
    # Check if user already exists
    result = await session.execute(select(UserModel).where(UserModel.email == req.email.lower()))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = UserModel(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role=req.role if req.role in ("Admin", "Senior Analyst", "Junior Analyst", "Viewer") else "Junior Analyst",
        status="ACTIVE"
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@auth_router.post("/login")
async def login(req: LoginRequest, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(UserModel).where(UserModel.email == req.email.lower()))
    user = result.scalars().first()

    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email credentials")

    token = create_access_token({"user_id": user.id, "email": user.email, "role": user.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }


@auth_router.get("/siwe/nonce")
async def get_siwe_nonce(address: str):
    address_clean = address.lower().strip()
    nonce = secrets.token_hex(16)
    SIWE_NONCES[address_clean] = nonce
    return {"nonce": nonce, "message": f"Sign-in to EVM Risk Platform with nonce: {nonce}"}


@auth_router.post("/siwe/verify")
async def verify_siwe(req: SIWEVerifyRequest, session: AsyncSession = Depends(get_db_session)):
    wallet_clean = req.wallet_address.lower().strip()

    try:
        # Recover ECDSA signer address from SIWE message
        w3 = Web3()
        message_hash = encode_defunct(text=req.message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=req.signature).lower()

        if recovered_address != wallet_clean:
            raise HTTPException(status_code=401, detail="Cryptographic signature verification failed")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SIWE verification error: {str(e)}")

    # Check if wallet user exists, else auto-register
    result = await session.execute(select(UserModel).where(UserModel.wallet_address == wallet_clean))
    user = result.scalars().first()

    if not user:
        user = UserModel(
            wallet_address=wallet_clean,
            email=f"{wallet_clean[:6]}...{wallet_clean[-4:]}@web3.eth",
            role="Senior Analyst",
            status="ACTIVE"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = create_access_token({"user_id": user.id, "wallet_address": user.wallet_address, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "wallet_address": user.wallet_address,
            "email": user.email,
            "role": user.role
        }
    }


@auth_router.get("/me")
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "wallet_address": current_user.wallet_address,
        "role": current_user.role,
        "status": current_user.status
    }


@auth_router.get("/users")
async def list_analysts(
    current_user: UserModel = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    result = await session.execute(select(UserModel))
    users = result.scalars().all()
    return [{
        "id": u.id,
        "email": u.email,
        "wallet_address": u.wallet_address,
        "role": u.role
    } for u in users]
