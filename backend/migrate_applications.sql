ALTER TABLE applications
    ADD COLUMN IF NOT EXISTS resume_id INTEGER REFERENCES resumes(id),
    ADD COLUMN IF NOT EXISTS match_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS matched_skills JSONB,
    ADD COLUMN IF NOT EXISTS missing_skills TEXT,
    ADD COLUMN IF NOT EXISTS recommendation TEXT,
    ADD COLUMN IF NOT EXISTS source VARCHAR(100),
    ADD COLUMN IF NOT EXISTS match_category VARCHAR(50),
    ADD COLUMN IF NOT EXISTS application_priority VARCHAR(50),
    ADD COLUMN IF NOT EXISTS customized_resume TEXT,
    ADD COLUMN IF NOT EXISTS cover_letter TEXT,
    ADD COLUMN IF NOT EXISTS recruiter_message TEXT,
    ADD COLUMN IF NOT EXISTS application_status VARCHAR(50),
    ADD COLUMN IF NOT EXISTS application_stage VARCHAR(100);

UPDATE applications
SET application_status = COALESCE(application_status, status),
    application_stage = COALESCE(application_stage, 'LEGACY_APPLICATION')
WHERE application_status IS NULL OR application_stage IS NULL;