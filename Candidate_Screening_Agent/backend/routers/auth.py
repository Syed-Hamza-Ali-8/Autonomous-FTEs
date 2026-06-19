"""Authentication router: register, login, me, user management."""

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Company, User, Job, Candidate
from db.database import get_db, get_jwt_secret
from auth import create_access_token, TokenPayload, require_role, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- Request/Response schemas ---

class RegisterRequest(BaseModel):
    company_name: str
    email: str
    password: str
    name: str
    description: str = ""
    services: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    company_id: int
    company_name: str


class InviteUserRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "recruiter"


# --- Helpers ---

def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


def _make_unique_slug(slug: str, existing_slugs: set) -> str:
    base = slug
    counter = 1
    while slug in existing_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# --- Endpoints ---

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new company and the first user (company_admin)."""
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create company
    slug = _slugify(req.company_name)
    slug_check = await db.execute(select(Company.slug))
    existing_slugs = {r for r in slug_check.scalars().all()}
    slug = _make_unique_slug(slug, existing_slugs)

    company = Company(
        name=req.company_name,
        slug=slug,
        description=req.description,
        services=req.services,
        plan="free",
    )
    db.add(company)
    await db.flush()

    # Create first user as company_admin
    user = User(
        company_id=company.id,
        email=req.email,
        name=req.name,
        role="company_admin",
    )
    user.set_password(req.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(company)

    # Generate token
    token = create_access_token(user, company, get_jwt_secret())

    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "company_id": company.id,
            "company_name": company.name,
            "company_slug": company.slug,
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not user.check_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Fetch company
    company_result = await db.execute(select(Company).where(Company.id == user.company_id))
    company = company_result.scalar_one()

    token = create_access_token(user, company, get_jwt_secret())

    return AuthResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "company_id": company.id,
            "company_name": company.name,
            "company_slug": company.slug,
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: TokenPayload = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current authenticated user info."""
    result = await db.execute(select(User).where(User.id == user.sub))
    found = result.scalar_one_or_none()
    if not found:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=found.id,
        email=found.email,
        name=found.name,
        role=found.role,
        company_id=user.company_id,
        company_name=user.company_name,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: TokenPayload = Depends(require_role("company_admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the current company (company_admin only)."""
    result = await db.execute(
        select(User)
        .where(User.company_id == user.company_id)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    # Fetch company name
    company_result = await db.execute(select(Company).where(Company.id == user.company_id))
    company = company_result.scalar_one()

    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            company_id=u.company_id,
            company_name=company.name,
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse)
async def invite_user(
    req: InviteUserRequest,
    user: TokenPayload = Depends(require_role("company_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Add a new user to the current company (company_admin only)."""
    # Check email uniqueness globally
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ("company_admin", "hiring_manager", "recruiter"):
        raise HTTPException(status_code=400, detail="Invalid role")

    new_user = User(
        company_id=user.company_id,
        email=req.email,
        name=req.name,
        role=req.role,
    )
    new_user.set_password(req.password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        company_id=new_user.company_id,
        company_name=user.company_name,
    )


# --- Super Admin Endpoints ---

class CompanySummary(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    services: str | None = None
    plan: str
    is_active: bool
    user_count: int
    job_count: int
    candidate_count: int
    created_at: str

@router.get("/companies", response_model=list[CompanySummary])
async def list_companies(
    user: TokenPayload = Depends(require_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all registered companies (super_admin only)."""
    from sqlalchemy import func

    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()

    summaries = []
    for c in companies:
        users_count = await db.execute(select(func.count(User.id)).where(User.company_id == c.id))
        jobs_count = await db.execute(select(func.count(Job.id)).where(Job.company_id == c.id))
        candidates_count = await db.execute(select(func.count(Candidate.id)).where(Candidate.company_id == c.id))
        summaries.append(CompanySummary(
            id=c.id, name=c.name, slug=c.slug, description=c.description,
            services=c.services, plan=c.plan, is_active=c.is_active,
            user_count=users_count.scalar_one(), job_count=jobs_count.scalar_one(),
            candidate_count=candidates_count.scalar_one(),
            created_at=c.created_at.isoformat() if c.created_at else "",
        ))
    return summaries
