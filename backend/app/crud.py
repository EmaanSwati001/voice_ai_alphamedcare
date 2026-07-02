from sqlalchemy.orm import Session
from .database import Patient, Claim, BillingInvoice, Appointment

# --- PATIENT / IDENTITY VERIFICATION ---

def verify_patient(db: Session, first_name: str, last_name: str, date_of_birth: str, policy_number: str):
    """
    Search for a patient matching all criteria.
    This acts as our identity verification guardrail (HIPAA compliance).
    """
    return db.query(Patient).filter(
        Patient.first_name.collate("NOCASE") == first_name.strip(),
        Patient.last_name.collate("NOCASE") == last_name.strip(),
        Patient.date_of_birth == date_of_birth.strip(),
        Patient.policy_number.collate("NOCASE") == policy_number.strip()
    ).first()

def get_patient_by_policy(db: Session, policy_number: str):
    return db.query(Patient).filter(Patient.policy_number.collate("NOCASE") == policy_number.strip()).first()


# --- CLAIM QUERIES ---

def get_claims_by_patient(db: Session, patient_id: int):
    """Get all insurance claims associated with a specific patient."""
    return db.query(Claim).filter(Claim.patient_id == patient_id).all()

def get_claim_by_number(db: Session, claim_number: str):
    """Get status and details of a specific claim by its claim number."""
    return db.query(Claim).filter(Claim.claim_number.collate("NOCASE") == claim_number.strip()).first()


# --- BILLING & INVOICE QUERIES ---

def get_invoices_by_patient(db: Session, patient_id: int):
    """Get all outstanding invoices or billing statements for a patient."""
    return db.query(BillingInvoice).filter(BillingInvoice.patient_id == patient_id).all()


# --- APPOINTMENT MANAGEMENT ---

def get_appointments_by_patient(db: Session, patient_id: int):
    """Get list of appointments for a patient."""
    return db.query(Appointment).filter(Appointment.patient_id == patient_id).all()

def create_appointment(db: Session, patient_id: int, appointment_date: str, provider_name: str, reason_for_visit: str):
    """Schedule a new appointment for a patient."""
    db_appointment = Appointment(
        patient_id=patient_id,
        appointment_date=appointment_date,
        provider_name=provider_name,
        reason_for_visit=reason_for_visit,
        status="Scheduled"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


# --- DATABASE SEEDING ---

def seed_database(db: Session):
    """
    Seeds the local database with realistic medical billing records for testing.
    Checks if the database is already seeded first.
    """
    if db.query(Patient).first() is not None:
        print("Database already seeded.")
        return

    # 1. Create Mock Patients
    john = Patient(
        first_name="John",
        last_name="Doe",
        date_of_birth="1985-05-15",
        policy_number="POL12345",
        insurance_provider="Blue Cross Blue Shield",
        phone_number="555-0199"
    )
    jane = Patient(
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1990-08-22",
        policy_number="POL67890",
        insurance_provider="Aetna",
        phone_number="555-0144"
    )
    db.add_all([john, jane])
    db.commit() # Commit to generate patient IDs

    # 2. Create Claims
    claims = [
        # John's claims
        Claim(
            patient_id=john.id,
            claim_number="CLM10001",
            date_of_service="2026-05-10",
            total_amount=450.00,
            amount_paid=450.00,
            status="Paid",
            denial_reason=None,
            cpt_codes="99213, 36415"  # Office visit, Blood draw
        ),
        Claim(
            patient_id=john.id,
            claim_number="CLM10002",
            date_of_service="2026-06-01",
            total_amount=1200.00,
            amount_paid=0.00,
            status="Denied",
            denial_reason="Prior Authorization Required",
            cpt_codes="72148"  # MRI Lumbar Spine
        ),
        # Jane's claims
        Claim(
            patient_id=jane.id,
            claim_number="CLM20001",
            date_of_service="2026-04-18",
            total_amount=150.00,
            amount_paid=120.00,
            status="Paid",
            denial_reason=None,
            cpt_codes="99212"  # Brief office visit
        ),
        Claim(
            patient_id=jane.id,
            claim_number="CLM20002",
            date_of_service="2026-06-15",
            total_amount=350.00,
            amount_paid=0.00,
            status="Pending",
            denial_reason=None,
            cpt_codes="99214, 94640"  # Medium office visit, Inhalation treatment
        )
    ]

    # 3. Create Billing Invoices (Unpaid patient balance)
    invoices = [
        # John's outstanding bills
        BillingInvoice(
            patient_id=john.id,
            invoice_number="INV7701",
            due_date="2026-07-20",
            outstanding_balance=45.00,  # e.g., co-pay for paid claim CLM10001
            payment_status="Unpaid"
        ),
        # Jane's outstanding bills
        BillingInvoice(
            patient_id=jane.id,
            invoice_number="INV8802",
            due_date="2026-07-15",
            outstanding_balance=30.00,  # co-pay for CLM20001
            payment_status="Unpaid"
        )
    ]

    # 4. Create Appointments
    appointments = [
        Appointment(
            patient_id=john.id,
            appointment_date="2026-07-10 10:00",
            provider_name="Dr. Sarah Johnson",
            reason_for_visit="Follow-up on MRI results",
            status="Scheduled"
        ),
        Appointment(
            patient_id=jane.id,
            appointment_date="2026-07-12 14:30",
            provider_name="Dr. Robert Lee",
            reason_for_visit="Annual physical checkup",
            status="Scheduled"
        )
    ]

    db.add_all(claims + invoices + appointments)
    db.commit()
    print("Database seeded successfully with John Doe and Jane Smith!")
