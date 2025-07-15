import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import sys
import os
from datetime import datetime, timezone
sys.path.append(os.path.join(os.path.dirname(__file__), 'AI_service'))
from AI_service.generate_contract import generate_contract as ai_generate_contract
from deployment_service import deployment_service
from utils.mongo import get_chat_collection
from utils.mongo import get_deployment_collection

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str

class DeployRequest(BaseModel):
    code: str
    network: str = "primordial"  # Default to BlockDAG testnet

def extract_contract_name(contract_code: str) -> str:
    # This regex matches 'contract <Name>' optionally followed by inheritance and then a '{'
    match = re.search(r'contract\s+([A-Za-z_]\w*)\s*(?:is\s*[A-Za-z_][\w, ]*)?\s*{', contract_code)
    return match.group(1) if match else "GeneratedContract"

@router.post("/generate")
async def generate_contract(req: GenerateRequest):
    # Expect prompt in the format: "<contract_type>|<features>"
    if '|' not in req.prompt:
        return {"error": "Prompt must be in the format '<contract_type>|<features>'"}
    contract_type, features = map(str.strip, req.prompt.split('|', 1))
    contract = ai_generate_contract(contract_type, features)
    return {"contract": contract}

@router.post("/deploy")
async def deploy_contract(req: DeployRequest):
    try:
        # Validate network
        if req.network.lower() not in ["primordial", "blockdag"]:
            raise HTTPException(status_code=400, detail="Only BlockDAG testnet (primordial) is supported")
        
        # Extract contract name from the code
        contract_name = extract_contract_name(req.code)
        print(f"Extracted contract name: {contract_name}")
        
        # Deploy the contract with the correct name
        deployment_result = deployment_service.deploy_contract(req.code, contract_name)
        
        if deployment_result["success"]:
            return {
                "success": True,
                "message": "Contract deployed successfully",
                "contractAddress": deployment_result["contractAddress"],
                "network": deployment_result["network"],
                "contractName": deployment_result["contractName"],
                "explorerUrl": deployment_result["explorerUrl"]
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Deployment failed: {deployment_result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment error: {str(e)}")
    finally:
        # Clean up the generated contract file
        try:
            deployment_service.cleanup_contract_file(contract_name)
        except:
            pass  # Ignore cleanup errors 

@router.post("/save_chat_history")
async def save_chat_history(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    chat_history = data.get("chat_history")  # Should be a list of messages or similar

    if not user_id or not chat_history:
        return {"success": False, "error": "user_id and chat_history are required"}

    for msg in chat_history:
        if "timestamp" not in msg:
            msg["timestamp"] = datetime.now(timezone.utc).isoformat()

    collection = get_chat_collection()
    existing = collection.find_one({"user_id": user_id})

    if existing:
        # Append to existing chat_history
        result = collection.update_one(
            {"user_id": user_id},
            {"$push": {"chat_history": {"$each": chat_history}}}
        )
        return {
            "success": True,
            "action": "appended",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    else:
        # Create new document
        result = collection.insert_one(
            {"user_id": user_id, "chat_history": chat_history}
        )
        return {
            "success": True,
            "action": "created",
            "inserted_id": str(result.inserted_id)
        }

@router.post("/save_deployment")
async def save_deployment(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    deployment = data.get("deployment")  # Should be a dict with deployment info

    if not user_id or not deployment:
        return {"success": False, "error": "user_id and deployment are required"}

    deployment["timestamp"] = deployment.get("timestamp") or datetime.now(timezone.utc).isoformat()

    collection = get_deployment_collection()
    existing = collection.find_one({"user_id": user_id})

    if existing:
        # Append to existing deployments array
        result = collection.update_one(
            {"user_id": user_id},
            {"$push": {"deployments": deployment}}
        )
        return {
            "success": True,
            "action": "appended",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    else:
        # Create new document
        result = collection.insert_one(
            {"user_id": user_id, "deployments": [deployment]}
        )
        return {
            "success": True,
            "action": "created",
            "inserted_id": str(result.inserted_id)
        }

@router.get("/get_chat_history/{user_id}")
async def get_chat_history(user_id: str):
    collection = get_chat_collection()
    doc = collection.find_one({"user_id": user_id})
    if doc:
        return {"success": True, "chat_history": doc.get("chat_history", [])}
    else:
        return {"success": False, "error": "No chat history found"} 

@router.get("/get_deployments/{user_id}")
async def get_deployments(user_id: str):
    collection = get_deployment_collection()
    doc = collection.find_one({"user_id": user_id})
    if doc and "deployments" in doc:
        return {"success": True, "deployments": doc["deployments"]}
    else:
        return {"success": True, "deployments": []} 