from pydantic import BaseModel, EmailStr
from datetime import datetime


# =========================================================
# USER SCHEMAS
# =========================================================

class UserCreate(BaseModel):

    name: str

    email: EmailStr

    password: str


class UserResponse(BaseModel):

    id: int

    name: str

    email: EmailStr

    class Config:
        from_attributes = True


# =========================================================
# JOB SCHEMAS
# =========================================================

class JobCreate(BaseModel):

    title: str

    company: str

    location: str | None = None

    description: str | None = None

    job_url: str | None = None

    skills: str | None = None

    source: str | None = None


class JobResponse(BaseModel):

    id: int

    title: str

    company: str

    location: str | None = None

    description: str | None = None

    job_url: str | None = None

    skills: str | None = None

    source: str | None = None

    user_id: int

    class Config:
        from_attributes = True


# =========================================================
# APPLICATION SCHEMAS
# =========================================================

class ApplicationCreate(BaseModel):

    job_id: int


class ApplicationStatusUpdate(BaseModel):

    status: str


class ApplicationResponse(BaseModel):

    id: int

    user_id: int

    job_id: int

    status: str

    applied_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================
# RESUME SCHEMAS
# =========================================================

class ResumeResponse(BaseModel):

    id: int

    user_id: int

    filename: str

    file_type: str

    extracted_text: str | None = None

    uploaded_at: datetime

    class Config:
        from_attributes = True


# =========================================================
# AI JOB MATCHING SCHEMA
# =========================================================

class JobMatchResponse(BaseModel):

    job_id: int

    resume_id: int

    match_score: float

    matched_skills: list[str]

    missing_skills: list[str]

    recommendation: str