from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# Load environment variables early so ElevenLabs service can see them
from dotenv import load_dotenv
load_dotenv()

# Import database engine, session, Base, and CRUD operations
from .database import engine, Base, get_db
from . import crud
# Import ElevenLabs router AFTER env is loaded
from .elevenlabs.router import router as elevenlabs_router

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Seed the database on application startup
db_session = next(get_db())
crud.seed_database(db_session)

# Initialize FastAPI App
app = FastAPI(
    title="AlphaMed Voice AI Backend",
    description="Backend API endpoints for patient verification, claims, billing, and scheduling.",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing) so our frontend dashboard can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(elevenlabs_router, prefix="/elevenlabs")


# --- PYDANTIC MODEL SCHEMAS ---
# Used for input validation and output documentation

class PatientVerificationInput(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    policy_number: str

class PatientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: str
    policy_number: str
    insurance_provider: str
    phone_number: str

    class Config:
        from_attributes = True

class ClaimResponse(BaseModel):
    id: int
    patient_id: int
    claim_number: str
    date_of_service: str
    total_amount: float
    amount_paid: float
    status: str
    denial_reason: Optional[str]
    cpt_codes: str

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    patient_id: int
    invoice_number: str
    due_date: str
    outstanding_balance: float
    payment_status: str

    class Config:
        from_attributes = True

class AppointmentCreateInput(BaseModel):
    policy_number: str
    appointment_date: str
    provider_name: str
    reason_for_visit: str

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    appointment_date: str
    provider_name: str
    reason_for_visit: str
    status: str

    class Config:
        from_attributes = True


# --- API ENDPOINTS ---



@app.post("/api/verify-patient", response_model=PatientResponse)
def verify_patient_endpoint(data: PatientVerificationInput, db: Session = Depends(get_db)):
    """
    Verifies a patient's identity.
    Returns patient profile if successful, otherwise raises a 401 Unauthorized.
    """
    patient = crud.verify_patient(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        policy_number=data.policy_number
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification failed. Patient details do not match our records."
        )
    return patient


@app.get("/api/patients/{policy_number}/claims", response_model=List[ClaimResponse])
def get_patient_claims(policy_number: str, db: Session = Depends(get_db)):
    """Retrieve all claims for a verified patient by policy number."""
    patient = crud.get_patient_by_policy(db, policy_number)
    if not patient:
        raise HTTPException(status_code=444, detail="Patient policy number not found.")
    return crud.get_claims_by_patient(db, patient_id=patient.id)


@app.get("/api/claims/{claim_number}", response_model=ClaimResponse)
def get_claim_details(claim_number: str, db: Session = Depends(get_db)):
    """Retrieve details of a single claim using its unique claim number."""
    claim = crud.get_claim_by_number(db, claim_number)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_number} not found.")
    return claim


@app.get("/api/patients/{policy_number}/invoices", response_model=List[InvoiceResponse])
def get_patient_invoices(policy_number: str, db: Session = Depends(get_db)):
    """Retrieve outstanding invoices for a verified patient by policy number."""
    patient = crud.get_patient_by_policy(db, policy_number)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient policy number not found.")
    return crud.get_invoices_by_patient(db, patient_id=patient.id)


@app.get("/api/patients/{policy_number}/appointments", response_model=List[AppointmentResponse])
def get_patient_appointments(policy_number: str, db: Session = Depends(get_db)):
    """Retrieve scheduled appointments for a patient by policy number."""
    patient = crud.get_patient_by_policy(db, policy_number)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient policy number not found.")
    return crud.get_appointments_by_patient(db, patient_id=patient.id)


@app.post("/api/appointments", response_model=AppointmentResponse)
def schedule_appointment(data: AppointmentCreateInput, db: Session = Depends(get_db)):
    """Schedules a new doctor appointment for a patient."""
    patient = crud.get_patient_by_policy(db, data.policy_number)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient policy number not found.")
    
    appointment = crud.create_appointment(
        db,
        patient_id=patient.id,
        appointment_date=data.appointment_date,
        provider_name=data.provider_name,
        reason_for_visit=data.reason_for_visit
    )
    return appointment


# Serve static frontend dashboard files
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

