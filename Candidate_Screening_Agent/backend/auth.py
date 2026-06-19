"""Authentication utilities: JWT creation/validation."""

from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db import User, Company
from db.database import get_db

JWT_ALGORITHM = "HS256"
security = HTTPBearer()

class TokenPayload(BaseModel):
    sub: int
    company_id: int
    email: str
    role: str
    company_name: str
    company_slug: str

def create_access_token(user: User, company: Company, secret_key: str, expires_minutes: int = 1440) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "sub": str(user.id),
        "company_id": company.id,
        "email": user.email,
        "role": user.role,
        "company_name": company.name,
        "company_slug": company.slug,
        "exp": expire,
    }
    return jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str, secret_key: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except (jwt.PyJWTError, jwt.DecodeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> TokenPayload:
    from db.database import get_jwt_secret
    key = get_jwt_secret()
    return decode_access_token(credentials.credentials, key)

def require_role(*allowed_roles: str):
    async def role_checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role not in allowed_roles and user.role != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{user.role}' not authorized. Required: {', '.join(allowed_roles)}")
        return user
    return role_checker
