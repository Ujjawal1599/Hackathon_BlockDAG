from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys
import os
from datetime import datetime, timezone
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI_service'))
from AI_service.audit_contract import audit_and_fix_contract, validate_contract_structure, run_solhint_audit

router = APIRouter()

class ContractAuditRequest(BaseModel):
    contract_code: str
    description: str = ""

@router.get("/test")
async def test_endpoint():
    """
    Simple test endpoint to check if the API is working
    """
    return {"message": "Audit API is working!", "status": "ok"}

@router.post("/test-audit")
async def test_audit_endpoint(req: ContractAuditRequest):
    """
    Test endpoint to see what's being received
    """
    return {
        "message": "Request received successfully",
        "contract_code_length": len(req.contract_code),
        "description": req.description,
        "contract_code_preview": req.contract_code[:100] + "..." if len(req.contract_code) > 100 else req.contract_code
    }

class AuditResponse(BaseModel):
    success: bool
    original_code: str
    corrected_code: str
    original_audit: dict
    final_audit: dict
    issues_fixed: int
    remaining_issues: int
    validation: dict
    improvements: dict | None = None
    error: str | None = None

@router.post("/audit")
async def audit_contract(req: ContractAuditRequest):
    """
    Audit and fix a smart contract using OpenAI and solhint
    """
    try:
        print('req', req)
        print('herehererere')
        print(f"[DEBUG] Received request with contract_code length: {len(req.contract_code)}")
        print(f"[DEBUG] Description: {req.description}")
        
        # Validate contract structure
        validation = validate_contract_structure(req.contract_code)
        print(f"[DEBUG] Validation result: {validation}")
        
        # Perform audit and fix
        audit_result = audit_and_fix_contract(req.contract_code)
        print(f"[DEBUG] Audit result keys: {audit_result.keys()}")
        
        # Add validation to the response
        audit_result["validation"] = validation
        
        # Check if all required fields are present
        required_fields = ["success", "original_code", "corrected_code", "original_audit", "final_audit", "issues_fixed", "remaining_issues", "validation"]
        missing_fields = [field for field in required_fields if field not in audit_result]
        if missing_fields:
            print(f"[DEBUG] Missing fields: {missing_fields}")
            raise HTTPException(status_code=500, detail=f"Missing required fields: {missing_fields}")
        
        return AuditResponse(**audit_result)
        
    except Exception as e:
        print(f"[DEBUG] Error in audit_contract: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

@router.post("/validate")
async def validate_contract(req: ContractAuditRequest):
    """
    Validate contract structure without fixing
    """
    try:
        validation = validate_contract_structure(req.contract_code)
        return {
            "success": True,
            "validation": validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/solhint-only")
async def solhint_audit(req: ContractAuditRequest):
    """
    Run only solhint audit without LLM fixes
    """
    try:
        audit_result = run_solhint_audit(req.contract_code)
        return {
            "success": True,
            "audit_result": audit_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solhint audit failed: {str(e)}") 