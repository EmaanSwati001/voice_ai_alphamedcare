import os
import sys

# Add the current directory to Python pathway so it can find backend.app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, Base, engine
from backend.app import crud

def test_database_locally():
    print("--- Starting Local Database Test ---")
    
    # 1. Initialize DB and recreate tables
    print("Recreating database tables...")
    Base.metadata.drop_all(bind=engine) # Clear any previous runs
    Base.metadata.create_all(bind=engine)
    
    # 2. Get a database session
    db = SessionLocal()
    
    try:
        # 3. Seed database
        print("Seeding database with mock data...")
        crud.seed_database(db)
        
        # 4. Verify Identity Verification (HIPAA Guardrail)
        print("\nTesting Identity Verification:")
        # Test success case
        verified_patient = crud.verify_patient(
            db,
            first_name="John",
            last_name="Doe",
            date_of_birth="1985-05-15",
            policy_number="POL12345"
        )
        assert verified_patient is not None, "Verification failed for valid patient John Doe!"
        print(f"  [SUCCESS] Verified John Doe. Patient ID: {verified_patient.id}, Provider: {verified_patient.insurance_provider}")
        
        # Test failure case
        failed_verification = crud.verify_patient(
            db,
            first_name="John",
            last_name="Doe",
            date_of_birth="1985-05-15",
            policy_number="WRONG_POLICY"
        )
        assert failed_verification is None, "Verification should have failed for invalid policy!"
        print("  [SUCCESS] Correctly blocked invalid policy verification request.")
        
        # 5. Verify Claim Status Lookup
        print("\nTesting Claim Lookup:")
        claim = crud.get_claim_by_number(db, "CLM10002")
        assert claim is not None, "Could not find claim CLM10002!"
        assert claim.status == "Denied", "Claim status should be Denied!"
        print(f"  [SUCCESS] Claim CLM10002 found. Status: {claim.status}, Reason: {claim.denial_reason}")
        
        # 6. Verify Appointments Scheduling
        print("\nTesting Appointment Creation:")
        initial_appts = crud.get_appointments_by_patient(db, verified_patient.id)
        print(f"  Initial appointments count for John: {len(initial_appts)}")
        
        new_appt = crud.create_appointment(
            db,
            patient_id=verified_patient.id,
            appointment_date="2026-08-01 09:00",
            provider_name="Dr. Sarah Johnson",
            reason_for_visit="Routine cleaning and exam"
        )
        assert new_appt.id is not None, "Failed to insert appointment into database!"
        
        updated_appts = crud.get_appointments_by_patient(db, verified_patient.id)
        print(f"  Updated appointments count for John: {len(updated_appts)}")
        assert len(updated_appts) == len(initial_appts) + 1, "Appointment list didn't increase!"
        print(f"  [SUCCESS] New appointment scheduled at {new_appt.appointment_date}")
        
        print("\n--- All DB Tests Passed Successfully! ---")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_database_locally()
