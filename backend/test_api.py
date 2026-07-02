import time
import httpx

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    print("Waiting for FastAPI server to start...")
    for _ in range(20):
        try:
            response = httpx.get(BASE_URL)
            if response.status_code == 200:
                print("Server is active!")
                return True
        except httpx.RequestError:
            time.sleep(0.5)
    print("Server failed to start in time.")
    return False

def test_http_api():
    if not wait_for_server():
        return
    
    print("\n--- Starting HTTP API Tests ---")
    
    # 1. Test Root Endpoint
    resp = httpx.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    print("  [SUCCESS] Root endpoint returned status 200.")
    
    # 2. Test Verification Endpoint (Success)
    verify_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1985-05-15",
        "policy_number": "POL12345"
    }
    resp = httpx.post(f"{BASE_URL}/api/verify-patient", json=verify_payload)
    assert resp.status_code == 200
    patient_data = resp.json()
    assert patient_data["first_name"] == "John"
    print(f"  [SUCCESS] Verified patient via API: {patient_data['first_name']} {patient_data['last_name']}")
    
    # 3. Test Verification Endpoint (Failure)
    failed_payload = verify_payload.copy()
    failed_payload["policy_number"] = "WRONG_POLICY"
    resp = httpx.post(f"{BASE_URL}/api/verify-patient", json=failed_payload)
    assert resp.status_code == 401
    print("  [SUCCESS] Correctly rejected invalid patient verification via API (401 Unauthorized).")
    
    # 4. Test Claims Endpoint
    resp = httpx.get(f"{BASE_URL}/api/patients/POL12345/claims")
    assert resp.status_code == 200
    claims = resp.json()
    assert len(claims) >= 2
    print(f"  [SUCCESS] Retrieved {len(claims)} claims for policy POL12345 via API.")
    
    # 5. Test Single Claim Details
    resp = httpx.get(f"{BASE_URL}/api/claims/CLM10002")
    assert resp.status_code == 200
    claim_details = resp.json()
    assert claim_details["status"] == "Denied"
    print(f"  [SUCCESS] Retrieved claim CLM10002 details: Status is {claim_details['status']}, denial reason: {claim_details['denial_reason']}")
    
    # 6. Test Scheduling Appointment
    sched_payload = {
        "policy_number": "POL12345",
        "appointment_date": "2026-08-15 11:30",
        "provider_name": "Dr. Sarah Johnson",
        "reason_for_visit": "Follow up MRI"
    }
    resp = httpx.post(f"{BASE_URL}/api/appointments", json=sched_payload)
    assert resp.status_code == 200
    appt = resp.json()
    assert appt["appointment_date"] == "2026-08-15 11:30"
    print(f"  [SUCCESS] Scheduled appointment via API for {appt['appointment_date']} with {appt['provider_name']}")
    
    print("\n--- All HTTP API Tests Passed! ---")

if __name__ == "__main__":
    test_http_api()
