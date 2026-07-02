from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# SQLite database file path. It will create a 'medical_billing.db' file in the root backend directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./medical_billing.db"

# The engine connects SQLAlchemy to our SQLite database.
# 'check_same_thread': False is required only for SQLite because FastAPI can handle requests on multiple threads,
# and SQLite by default restricts access to a single thread.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We inherit from this class to create our database models (tables).
Base = declarative_base()


class Patient(Base):
    """
    Represents a patient in the clinic database.
    Used for verifying identity before revealing sensitive health/claim information.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    policy_number = Column(String, unique=True, index=True, nullable=False)
    insurance_provider = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)

    # Relationships to access related tables easily
    claims = relationship("Claim", back_populates="patient")
    invoices = relationship("BillingInvoice", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")


class Claim(Base):
    """
    Represents an insurance claim filed for medical services.
    Enables checking claim status, paid/unpaid amounts, and denial reasons.
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    claim_number = Column(String, unique=True, index=True, nullable=False)
    date_of_service = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    status = Column(String, nullable=False)  # E.g., 'Paid', 'Pending', 'Denied'
    denial_reason = Column(String, nullable=True)  # E.g., 'Prior Authorization Required'
    cpt_codes = Column(String, nullable=False)  # Comma-separated list of CPT codes (e.g., '99213, 36415')

    patient = relationship("Patient", back_populates="claims")


class BillingInvoice(Base):
    """
    Represents outstanding bills/invoices sent to the patient for their co-pay/deductible portions.
    """
    __tablename__ = "billing_invoices"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    due_date = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    outstanding_balance = Column(Float, nullable=False)
    payment_status = Column(String, nullable=False)  # E.g., 'Unpaid', 'Paid', 'Partially Paid'

    patient = relationship("Patient", back_populates="invoices")


class Appointment(Base):
    """
    Represents medical doctor appointments.
    Enables the voice agent to look up schedules or schedule new ones.
    """
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_date = Column(String, nullable=False)  # YYYY-MM-DD HH:MM
    provider_name = Column(String, nullable=False)  # Dr. Name
    reason_for_visit = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Scheduled")  # E.g., 'Scheduled', 'Cancelled', 'Completed'

    patient = relationship("Patient", back_populates="appointments")


# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
