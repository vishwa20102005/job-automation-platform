from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from jose import JWTError, jwt

from database import (
    Base,
    engine,
    get_db
)

from models import (
    User,
    Job,
    Application,
    Resume
)

from schemas import (
    UserCreate,
    UserResponse,
    JobCreate,
    JobResponse,
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationResponse,
    ResumeResponse,
    JobMatchResponse
)


from auth import (
    SECRET_KEY,
    ALGORITHM,
    hash_password,
    verify_password,
    create_access_token
)

from pypdf import PdfReader
from docx import Document

from ai_matching import calculate_match
from matching import calculate_match_score
import os
import uuid

from datetime import datetime, timezone


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AI Job Application Automation Platform",
    version="1.0.0"
)


# =========================================================
# JWT AUTHENTICATION
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:

            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        return int(user_id)

    except (
        JWTError,
        ValueError
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "AI Job Application Automation API is running!"
    }


# =========================================================
# REGISTER
# =========================================================

@app.post(
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(
            User.email == user.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = hash_password(
        user.password
    )

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return new_user


# =========================================================
# LOGIN
# =========================================================

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(
            User.email == form_data.username
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        form_data.password,
        user.hashed_password
    )

    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id)
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# CURRENT USER
# =========================================================

@app.get("/me")
def get_me(
    current_user_id: int = Depends(
        get_current_user
    )
):

    return {
        "message": "JWT authentication successful!",
        "user_id": current_user_id
    }


# =========================================================
# CREATE JOB
# =========================================================

@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=201
)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    new_job = Job(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        job_url=job.job_url,
        skills=job.skills,
        source=job.source,
        user_id=current_user_id
    )

    db.add(new_job)

    db.commit()

    db.refresh(new_job)

    return new_job


# =========================================================
# GET ALL JOBS
# =========================================================

@app.get(
    "/jobs",
    response_model=list[JobResponse]
)
def get_jobs(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    jobs = (
        db.query(Job)
        .filter(
            Job.user_id == current_user_id
        )
        .order_by(
            Job.id.desc()
        )
        .all()
    )

    return jobs


# =========================================================
# GET SINGLE JOB
# =========================================================

@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == current_user_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job


# =========================================================
# DELETE JOB
# =========================================================

@app.delete(
    "/jobs/{job_id}"
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == current_user_id
        )
        .first()
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    db.delete(job)

    db.commit()

    return {
        "message": "Job deleted successfully",
        "job_id": job_id
    }


# =========================================================
# CREATE APPLICATION
# =========================================================

@app.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=201
)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):

    job = db.query(Job).filter(
        Job.id == application.job_id,
        Job.user_id == current_user_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_application = db.query(Application).filter(
        Application.user_id == current_user_id,
        Application.job_id == application.job_id
    ).first()

    if existing_application:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    if application.resume_id is not None:
        resume = db.query(Resume).filter(
            Resume.id == application.resume_id,
            Resume.user_id == current_user_id
        ).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

    new_application = Application(
        user_id=current_user_id,
        job_id=application.job_id,
        status=application.application_status or "READY_FOR_REVIEW",
        resume_id=application.resume_id,
        match_score=application.match_score,
        matched_skills=application.matched_skills,
        missing_skills=application.missing_skills,
        recommendation=application.recommendation,
        source=application.source,
        match_category=application.match_category,
        application_priority=application.application_priority,
        customized_resume=application.customized_resume,
        cover_letter=application.cover_letter,
        recruiter_message=application.recruiter_message,
        application_status=application.application_status or "READY_FOR_REVIEW",
        application_stage=application.application_stage or "AI_MATERIALS_GENERATED"
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    return new_application


# =========================================================
# GET APPLICATIONS
# =========================================================

@app.get("/applications", response_model=list[ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    return db.query(Application).filter(
        Application.user_id == current_user_id
    ).order_by(Application.id.desc()).all()


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

@app.put("/applications/{application_id}", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    allowed_statuses = {"READY_FOR_REVIEW", "APPLIED", "SHORTLISTED", "INTERVIEW", "REJECTED", "SELECTED"}
    new_status = status_data.status.upper().strip()
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid status. Allowed values: APPLIED, SHORTLISTED, INTERVIEW, REJECTED, SELECTED")
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = new_status
    application.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return application


# =========================================================
# DELETE APPLICATION
# =========================================================

@app.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user_id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()
    return {"message": "Application deleted successfully", "application_id": application_id}


# =========================================================
# RESUME UPLOAD + TEXT EXTRACTION
# =========================================================

@app.post(
    "/resumes/upload"
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    original_filename = file.filename

    allowed_extensions = {
        ".pdf",
        ".docx"
    }

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )

    upload_directory = os.path.join(
        os.path.dirname(__file__),
        "uploads",
        "resumes"
    )

    os.makedirs(
        upload_directory,
        exist_ok=True
    )

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    file_path = os.path.join(
        upload_directory,
        unique_filename
    )

    file_content = await file.read()

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            buffer.write(file_content)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save resume: {str(e)}"
        )

    extracted_text = ""

    try:

        if extension == ".pdf":

            reader = PdfReader(
                file_path
            )

            pages_text = []

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    pages_text.append(
                        page_text
                    )

            extracted_text = "\n".join(
                pages_text
            )

        elif extension == ".docx":

            document = Document(
                file_path
            )

            paragraphs = []

            for paragraph in document.paragraphs:

                text = paragraph.text.strip()

                if text:

                    paragraphs.append(
                        text
                    )

            extracted_text = "\n".join(
                paragraphs
            )

    except Exception as e:

        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract resume text: {str(e)}"
        )

    if not extracted_text.strip():

        if os.path.exists(file_path):

            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract text from resume. "
                "Please upload a text-based PDF or DOCX file."
            )
        )

    resume = Resume(
        user_id=current_user_id,
        filename=original_filename,
        file_path=file_path,
        file_type=extension,
        extracted_text=extracted_text,
        uploaded_at=datetime.now(
            timezone.utc
        )
    )

    db.add(resume)

    db.commit()

    db.refresh(resume)

    return {
        "message": (
            "Resume uploaded and text "
            "extracted successfully"
        ),
        "resume_id": resume.id,
        "filename": resume.filename,
        "file_type": resume.file_type,
        "text_length": len(extracted_text),
        "extracted_text": extracted_text
    }


# =========================================================
# GET RESUMES
# =========================================================

@app.get(
    "/resumes",
    response_model=list[ResumeResponse]
)
def get_resumes(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    resumes = (
        db.query(Resume)
        .filter(
            Resume.user_id == current_user_id
        )
        .order_by(
            Resume.id.desc()
        )
        .all()
    )

    return resumes


# =========================================================
# DOWNLOAD RESUME
# =========================================================

@app.get(
    "/resumes/{resume_id}/download"
)
def download_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == current_user_id
        )
        .first()
    )

    if not resume:

        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if not os.path.exists(
        resume.file_path
    ):

        raise HTTPException(
            status_code=404,
            detail="Resume file does not exist on server"
        )

    return FileResponse(
        path=resume.file_path,
        filename=resume.filename,
        media_type="application/octet-stream"
    )


# =========================================================
# DELETE RESUME
# =========================================================

@app.delete(
    "/resumes/{resume_id}"
)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(
        get_current_user
    )
):

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == resume_id,
            Resume.user_id == current_user_id
        )
        .first()
    )

    if not resume:

        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if os.path.exists(
        resume.file_path
    ):

        try:

            os.remove(
                resume.file_path
            )

        except OSError as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Could not delete resume file: {str(e)}"
                )
            )

    db.delete(resume)

    db.commit()

    return {
        "message": "Resume deleted successfully",
        "resume_id": resume_id
    }


# =========================================================
# AI JOB MATCHING
# =========================================================

@app.get("/jobs/{job_id}/match", response_model=JobMatchResponse)
def match_job_with_resume(
    job_id: int,
    resume_id: int | None = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user_id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_query = db.query(Resume).filter(Resume.user_id == current_user_id)
    if resume_id is not None:
        resume_query = resume_query.filter(Resume.id == resume_id)
    else:
        resume_query = resume_query.order_by(Resume.id.desc())
    resume = resume_query.first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.extracted_text:
        raise HTTPException(status_code=400, detail="Resume text is empty. Please upload a resume with readable text.")

    job_text = " ".join(filter(None, [job.title, job.company, job.location, job.description, job.skills]))
    result = calculate_match_score(resume.extracted_text, job_text)
    return {
        "job_id": job.id,
        "resume_id": resume.id,
        "match_score": result["score"],
        "matched_skills": result["matched_keywords"],
        "missing_skills": result["missing_keywords"],
        "recommendation": result["match_level"]
    }

