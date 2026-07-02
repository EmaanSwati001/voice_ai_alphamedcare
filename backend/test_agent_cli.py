import os
import sys
from dotenv import load_dotenv

# Add workspace folder to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal, Base, engine
from backend.app.agents.llm_agent import run_agent_turn
from backend.app.agents.prompts import SYSTEM_PROMPT
from backend.app import crud

# Load environment variables
load_dotenv()

def run_mock_demo():
    print("\n" + "="*60)
    print("WARNING: NO VALID OPENAI API KEY DETECTED")
    print("="*60)
    print("To run the REAL AI agent, please get an API key from OpenAI and place it in:")
    print("  c:\\Users\\ek139\\OneDrive\\Desktop\\voice_ai_alphamedcare\\.env")
    print("\nLine to update in .env:")
    print("  OPENAI_API_KEY=sk-proj-...")
    print("-"*60)
    print("\n[INFO] Running a SIMULATED DEMO to show how the tool-calling flow works:")
    print("  1. User: 'Hi, I need to check my claim status. I am John Doe, DOB 1985-05-15, policy POL12345.'")
    print("  2. System detects: User is requesting Claim Status and provides verification details.")
    print("  3. System triggers: verify_patient(first_name='John', last_name='Doe', ...)")
    
    db = SessionLocal()
    try:
        # Seeding database
        Base.metadata.create_all(bind=engine)
        crud.seed_database(db)
        
        # Simulating Tool Execution
        print("\n--- SIMULATION STEP 1: Verification ---")
        patient_str = crud.verify_patient(db, "John", "Doe", "1985-05-15", "POL12345")
        if patient_str:
            print(f"Database response: Patient VERIFIED. ID={patient_str.id}, Provider={patient_str.insurance_provider}")
            
            print("\n--- SIMULATION STEP 2: Lookup Claims ---")
            claims = crud.get_claims_by_patient(db, patient_str.id)
            print("Database response: Claims retrieved successfully.")
            for c in claims:
                print(f"  - Claim: {c.claim_number} | Date: {c.date_of_service} | Status: {c.status} | Total: ${c.total_amount} | Reason: {c.denial_reason}")
                
            print("\n--- SIMULATION STEP 3: Explaining Denials ---")
            denied_claim = next((c for c in claims if c.status == "Denied"), None)
            if denied_claim:
                print(f"User asks: 'Why was {denied_claim.claim_number} denied?'")
                print(f"Agent explains: 'Your claim {denied_claim.claim_number} for the amount of ${denied_claim.total_amount} was denied because: \"{denied_claim.denial_reason}\".'")
        else:
            print("Database response: Verification failed.")
            
    finally:
        db.close()
    print("="*60 + "\n")

def run_real_agent():
    print("\n" + "="*50)
    print("ALPHAMED AI VOICE AGENT CLI (REAL TIME CHAT)")
    print("="*50)
    print("Type your message and press Enter. Type 'quit' to exit.")
    print("Mock patient credentials you can verify with:")
    print("  - John Doe (DOB: 1985-05-15, Policy: POL12345)")
    print("  - Jane Smith (DOB: 1990-08-22, Policy: POL67890)")
    print("-"*50)
    
    # 1. Initialize SQLite Database
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    crud.seed_database(db)
    
    # 2. Build conversational context messages history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Send initial greeting
    greeting = "Hello! Thank you for calling AlphaMed Clinic. I am your billing assistant. How can I help you today?"
    messages.append({"role": "assistant", "content": greeting})
    print(f"\nAgent: {greeting}")
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            if not user_input or user_input.lower() in ["quit", "exit"]:
                print("Ending call. Thank you for calling AlphaMed Clinic.")
                break
                
            # Append user message
            messages.append({"role": "user", "content": user_input})
            
            # Run inference (will call DB tools recursively if needed)
            messages = run_agent_turn(messages, db)
            
            # Display final agent response (which is the last message in history)
            last_message = messages[-1]
            print(f"\nAgent: {last_message.content}")
            
            # Check if call was transferred
            # We can scan the messages history to see if the transfer tool was invoked
            for msg in reversed(messages):
                if getattr(msg, "role", None) == "assistant" and msg.tool_calls:
                    for tc in msg.tool_calls:
                        if tc.function.name == "transfer_to_human":
                            print("\n[SYSTEM] Call transferred to human billing supervisor. CLI terminated.")
                            return
    except KeyboardInterrupt:
        print("\nEnding call due to user interrupt.")
    finally:
        db.close()

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("your_openai"):
        run_mock_demo()
    else:
        run_real_agent()

if __name__ == "__main__":
    main()
