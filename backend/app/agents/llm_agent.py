import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import crud
from .prompts import SYSTEM_PROMPT

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client. It automatically looks for the OPENAI_API_KEY environment variable.
openai_client = OpenAI()

# --- DEFINE TOOLS FOR THE LLM ---
# These schemas tell the LLM what functions exist, their descriptions, and what parameters they require.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "verify_patient",
            "description": "Verifies a patient's identity using first name, last name, date of birth (YYYY-MM-DD), and policy number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string", "description": "Patient's first name"},
                    "last_name": {"type": "string", "description": "Patient's last name"},
                    "date_of_birth": {"type": "string", "description": "Date of birth in YYYY-MM-DD format"},
                    "policy_number": {"type": "string", "description": "Insurance policy number, e.g. POL12345"}
                },
                "required": ["first_name", "last_name", "date_of_birth", "policy_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_claims",
            "description": "Retrieves all claims associated with a verified patient's policy number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "Insurance policy number"}
                },
                "required": ["policy_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_claim_details",
            "description": "Retrieves specific details (status, amount, denial reasons) of a claim by its claim number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_number": {"type": "string", "description": "Claim number, e.g. CLM10001"}
                },
                "required": ["claim_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_invoices",
            "description": "Retrieves outstanding billing invoices and co-pays for a patient using their policy number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "Insurance policy number"}
                },
                "required": ["policy_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": "Retrieves all future medical appointments for a patient using their policy number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "Insurance policy number"}
                },
                "required": ["policy_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_new_appointment",
            "description": "Schedules a new doctor appointment for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "Insurance policy number"},
                    "appointment_date": {"type": "string", "description": "Date and time of appointment in format YYYY-MM-DD HH:MM"},
                    "provider_name": {"type": "string", "description": "Name of the doctor (e.g. Dr. Sarah Johnson)"},
                    "reason_for_visit": {"type": "string", "description": "Brief reason for scheduling the visit"}
                },
                "required": ["policy_number", "appointment_date", "provider_name", "reason_for_visit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "Transfers the phone call to a human billing supervisor or representative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Reason for call transfer"}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Searches the clinic knowledge base (policies, FAQs, CPT code reference guides) for answers to patient questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query containing keywords or natural language questions."}
                },
                "required": ["query"]
            }
        }
    }
]


# --- EXECUTE TOOLS ---
# This helper executes the python database function that corresponds to the tool OpenAI wanted to run.

def execute_tool_call(name: str, arguments: dict, db: Session) -> str:
    """Executes DB queries based on the function name and arguments provided by the LLM."""
    print(f"\n[SYSTEM] Executing Tool: {name} with args: {arguments}")
    
    try:
        if name == "verify_patient":
            patient = crud.verify_patient(
                db,
                first_name=arguments.get("first_name"),
                last_name=arguments.get("last_name"),
                date_of_birth=arguments.get("date_of_birth"),
                policy_number=arguments.get("policy_number")
            )
            if patient:
                return json.dumps({
                    "verified": True,
                    "patient_id": patient.id,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "insurance_provider": patient.insurance_provider
                })
            else:
                return json.dumps({"verified": False, "message": "Patient records not found."})
                
        elif name == "get_patient_claims":
            patient = crud.get_patient_by_policy(db, arguments.get("policy_number"))
            if not patient:
                return json.dumps({"error": "Invalid policy number."})
            claims = crud.get_claims_by_patient(db, patient.id)
            return json.dumps([
                {
                    "claim_number": c.claim_number,
                    "date_of_service": c.date_of_service,
                    "status": c.status,
                    "total_amount": c.total_amount,
                    "amount_paid": c.amount_paid
                } for c in claims
            ])
            
        elif name == "get_claim_details":
            claim = crud.get_claim_by_number(db, arguments.get("claim_number"))
            if not claim:
                return json.dumps({"error": "Claim not found."})
            return json.dumps({
                "claim_number": claim.claim_number,
                "date_of_service": claim.date_of_service,
                "total_amount": claim.total_amount,
                "amount_paid": claim.amount_paid,
                "status": claim.status,
                "denial_reason": claim.denial_reason,
                "cpt_codes": claim.cpt_codes
            })
            
        elif name == "get_patient_invoices":
            patient = crud.get_patient_by_policy(db, arguments.get("policy_number"))
            if not patient:
                return json.dumps({"error": "Invalid policy number."})
            invoices = crud.get_invoices_by_patient(db, patient.id)
            return json.dumps([
                {
                    "invoice_number": i.invoice_number,
                    "due_date": i.due_date,
                    "outstanding_balance": i.outstanding_balance,
                    "payment_status": i.payment_status
                } for i in invoices
            ])
            
        elif name == "get_patient_appointments":
            patient = crud.get_patient_by_policy(db, arguments.get("policy_number"))
            if not patient:
                return json.dumps({"error": "Invalid policy number."})
            appointments = crud.get_appointments_by_patient(db, patient.id)
            return json.dumps([
                {
                    "appointment_date": a.appointment_date,
                    "provider_name": a.provider_name,
                    "reason_for_visit": a.reason_for_visit,
                    "status": a.status
                } for a in appointments
            ])
            
        elif name == "schedule_new_appointment":
            patient = crud.get_patient_by_policy(db, arguments.get("policy_number"))
            if not patient:
                return json.dumps({"error": "Invalid policy number."})
            appt = crud.create_appointment(
                db,
                patient_id=patient.id,
                appointment_date=arguments.get("appointment_date"),
                provider_name=arguments.get("provider_name"),
                reason_for_visit=arguments.get("reason_for_visit")
            )
            return json.dumps({
                "status": "Scheduled",
                "appointment_id": appt.id,
                "appointment_date": appt.appointment_date,
                "provider_name": appt.provider_name
            })
            
        elif name == "transfer_to_human":
            return json.dumps({
                "status": "Transferring call to human agent...",
                "reason": arguments.get("reason")
            })
            
        elif name == "search_knowledge_base":
            from ..services.rag_service import rag_service
            results = rag_service.search(arguments.get("query"), top_k=2)
            return json.dumps(results)
            
        else:
            return json.dumps({"error": f"Tool '{name}' is not supported."})
            
    except Exception as e:
        return json.dumps({"error": f"Internal database execution error: {str(e)}"})


# --- RUN CONVERSATION INFERENCE ---

def run_agent_turn(messages: list, db: Session) -> list:
    """
    Submits messages to OpenAI, processes tool calls recursively if requested,
    and appends the results back to the conversation message history list.
    """
    # 1. Call OpenAI completions API
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # 2. Append LLM response message to conversation history
    messages.append(response_message)
    
    # 3. Check if LLM requested any tool calls
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            # Parse function details
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute database query
            tool_result = execute_tool_call(function_name, function_args, db)
            
            # Append tool result back to history (so the LLM knows the database response)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_result
            })
            
        # Call the LLM again with the tool results so it can formulate its response
        return run_agent_turn(messages, db)
        
    return messages
