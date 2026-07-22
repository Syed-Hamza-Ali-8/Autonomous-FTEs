from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timedelta
import bcrypt

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    services = Column(String(300), nullable=True)  # e.g., "Software Development, AI, Consulting"
    plan = Column(String(20), nullable=False, default="free")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="company", cascade="all, delete-orphan")
    pending_approvals = relationship("PendingApproval", back_populates="company", cascade="all, delete-orphan")
    interview_slots = relationship("InterviewSlot", back_populates="company", cascade="all, delete-orphan")
    scheduling_conversations = relationship("SchedulingConversation", back_populates="company", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="company")

    # Constraints
    __table_args__ = (
        CheckConstraint("plan IN ('free', 'pro', 'enterprise')", name="check_plan"),
        Index("idx_companies_slug", "slug"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(30), nullable=False, default="recruiter")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="users")

    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('super_admin', 'company_admin', 'hiring_manager', 'recruiter')", name="check_user_role"),
        Index("idx_users_company", "company_id"),
        Index("idx_users_email", "email"),
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=False, index=True)
    rubric_path = Column(String(300), nullable=False)
    hiring_manager_email = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")
    pending_approvals = relationship("PendingApproval", back_populates="job", cascade="all, delete-orphan")
    interview_slots = relationship("InterviewSlot", back_populates="job", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed', 'paused')", name="check_job_status"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_company", "company_id"),
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(200), nullable=False, index=True)
    name = Column(String(200))
    timezone = Column(String(50), nullable=True)  # Candidate's timezone (e.g., "Asia/Kolkata")
    cv_text = Column(Text)
    status = Column(String(50), nullable=False, default="queued")
    total_score = Column(Float)
    must_haves_met = Column(Boolean)
    score_breakdown = Column(JSONB)
    strengths = Column(JSONB)
    weaknesses = Column(JSONB)
    red_flags = Column(JSONB)
    recommendation = Column(String(20))
    confidence = Column(String(20))
    score_summary = Column(Text)
    screening_questions = Column(JSONB)
    candidate_reply = Column(Text)
    reply_analysis = Column(JSONB)
    gmail_message_id = Column(String(200))
    rejection_message_id = Column(String(200))
    rejection_reply_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="candidates")
    job = relationship("Job", back_populates="candidates")
    pending_approvals = relationship("PendingApproval", back_populates="candidate", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="candidate")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'scoring', 'scored', 'questions_sent', 'awaiting_reply', "
            "'replied', 'shortlisted', 'rejected', 'hired', 'manual_review')",
            name="check_candidate_status"
        ),
        CheckConstraint("recommendation IN ('advance', 'reject', 'review')", name="check_recommendation"),
        CheckConstraint("confidence IN ('high', 'medium', 'low')", name="check_confidence"),
        Index("idx_candidates_status", "status"),
        Index("idx_candidates_job_id", "job_id"),
        Index("idx_candidates_email", "email"),
        Index("idx_candidates_company", "company_id"),
        Index("idx_candidates_created_at", "created_at"),
    )


class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(20), nullable=False)
    score = Column(Float)
    recommendation = Column(Text)
    brief_summary = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
    approved_by = Column(String(200))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=48))

    # Relationships
    company = relationship("Company", back_populates="pending_approvals")
    candidate = relationship("Candidate", back_populates="pending_approvals")
    job = relationship("Job", back_populates="pending_approvals")

    # Constraints
    __table_args__ = (
        CheckConstraint("action IN ('advance', 'reject')", name="check_action"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'expired')", name="check_approval_status"),
        Index("idx_approvals_status", "status"),
        Index("idx_approvals_candidate_id", "candidate_id"),
        Index("idx_approvals_company", "company_id"),
        Index("idx_approvals_expires_at", "expires_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="SET NULL"))
    action_type = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    input_summary = Column(Text)
    output_summary = Column(Text)
    approval_status = Column(String(20))
    approved_by = Column(String(200))
    result = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="audit_logs")
    candidate = relationship("Candidate", back_populates="audit_logs")

    # Constraints
    __table_args__ = (
        CheckConstraint("result IN ('success', 'failure', 'manual_review')", name="check_result"),
        Index("idx_audit_company", "company_id"),
        Index("idx_audit_candidate", "candidate_id"),
        Index("idx_audit_action_type", "action_type"),
        Index("idx_audit_created_at", "created_at"),
    )


class InterviewSlot(Base):
    __tablename__ = "interview_slots"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="available")
    timezone = Column(String(50), nullable=False, default="UTC")
    meeting_link = Column(String(500))
    interviewer_name = Column(String(200))
    interviewer_email = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="interview_slots")
    candidate = relationship("Candidate")
    job = relationship("Job", back_populates="interview_slots")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('available', 'proposed', 'booked', 'completed', 'cancelled')", name="check_slot_status"),
        Index("idx_slots_status", "status"),
        Index("idx_slots_start_time", "start_time"),
        Index("idx_slots_candidate_id", "candidate_id"),
        Index("idx_slots_job_id", "job_id"),
        Index("idx_slots_company", "company_id"),
    )


class SchedulingConversation(Base):
    __tablename__ = "scheduling_conversations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    conversation_state = Column(String(30), nullable=False, default="initiated")
    last_message_id = Column(String(200))
    proposed_slots = Column(JSONB)
    confirmed_slot_id = Column(Integer, ForeignKey("interview_slots.id", ondelete="SET NULL"))
    conversation_history = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="scheduling_conversations")
    candidate = relationship("Candidate")
    job = relationship("Job")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "conversation_state IN ('initiated', 'proposing_times', 'awaiting_confirmation', "
            "'awaiting_questions_reply', 'awaiting_timezone', 'confirmed', 'rescheduling', 'cancelled')",
            name="check_conversation_state"
        ),
        Index("idx_scheduling_company", "company_id"),
        Index("idx_scheduling_candidate", "candidate_id"),
        Index("idx_scheduling_state", "conversation_state"),
        Index("idx_scheduling_updated_at", "updated_at"),
    )
