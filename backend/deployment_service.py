import os
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import re

from AI_service.llm_autofix import llm_autofix_solidity

class ContractDeploymentService:
    def __init__(self):
        self.hardhat_dir = Path(__file__).parent.parent / "contracts" / "hardhat"
        
        # Load environment variables from backend directory
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        print(f"Loading .env from: {env_path}")
        load_dotenv(dotenv_path=env_path)
        
        self.deployer_private_key = os.getenv("DEPLOYER_PRIVATE_KEY")
        print(f"DEPLOYER_PRIVATE_KEY loaded: {'Yes' if self.deployer_private_key else 'No'}")
        
        if not self.deployer_private_key:
            print("DEPLOYER_PRIVATE_KEY not found in .env")
            print("Available environment variables:")
            for key, value in os.environ.items():
                if 'KEY' in key or 'PRIVATE' in key:
                    print(f"  {key}: {value[:10]}..." if value else f"  {key}: None")
            sys.exit(1)
        
        # Find npx executable
        self.npx_path = shutil.which("npx")
        if not self.npx_path:
            print("npx not found in PATH")
            sys.exit(1)
        print(f"npx found at: {self.npx_path}")
        
        # Verify Hardhat directory exists
        if not self.hardhat_dir.exists():
            raise ValueError(f"Hardhat directory not found: {self.hardhat_dir}")
        
        print(f"Hardhat directory: {self.hardhat_dir}")
        print(f"Hardhat directory exists: {self.hardhat_dir.exists()}")
    
    def save_contract_to_file(self, contract_code: str, contract_name: str = "GeneratedContract") -> str:
        """Save the contract code to a temporary file in the Hardhat contracts directory"""
        contract_name = extract_contract_name(contract_code)
        contract_file = self.hardhat_dir / "contracts" / f"{contract_name}.sol"
        
        # Ensure the contracts directory exists
        contract_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Saving contract to: {contract_file}")
        print(f"Contract file parent exists: {contract_file.parent.exists()}")
        
        # Write the contract code
        try:
            with open(contract_file, 'w', encoding='utf-8') as f:
                f.write(contract_code)
            print(f"Contract saved successfully to {contract_file}")
        except Exception as e:
            print(f"Error saving contract: {e}")
            raise
        
        return str(contract_file)
    
    def compile_contract(self, contract_name: str = "GeneratedContract") -> Dict[str, Any]:
        """Compile the contract using Hardhat"""
        original_dir = os.getcwd()  # Initialize at the beginning
        try:
            print(f"Changing to Hardhat directory: {self.hardhat_dir}")
            os.chdir(self.hardhat_dir)
            print(f"Current directory after change: {os.getcwd()}")
            
            # Check if hardhat is available using the full npx path
            try:
                result = subprocess.run([str(self.npx_path), "hardhat", "--version"], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"hardhat is available: {result.stdout.strip()}")
                else:
                    print(f"hardhat not available: {result.stderr}")
                    return {"success": False, "error": f"hardhat not available: {result.stderr}"}
            except Exception as e:
                print(f"Error checking hardhat: {e}")
                return {"success": False, "error": f"Error checking hardhat: {e}"}
            
            # Run Hardhat compile using the full npx path
            print("Running hardhat compile...")
            result = subprocess.run(
                [str(self.npx_path), "hardhat", "compile"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(f"Compile stdout: {result.stdout}")
            print(f"Compile stderr: {result.stderr}")
            print(f"Compile return code: {result.returncode}")
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Compilation failed: {result.stderr}"
                }
            
            # Read the compiled artifact
            artifact_path = self.hardhat_dir / "artifacts" / "contracts" / f"{contract_name}.sol" / f"{contract_name}.json"
            print(f"Looking for artifact at: {artifact_path}")
            print(f"Artifact exists: {artifact_path.exists()}")
            
            if not artifact_path.exists():
                return {
                    "success": False,
                    "error": "Compiled artifact not found"
                }
            
            with open(artifact_path, 'r') as f:
                artifact = json.load(f)
            
            return {
                "success": True,
                "artifact": artifact,
                "bytecode": artifact.get("bytecode", ""),
                "abi": artifact.get("abi", [])
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compilation timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Compilation error: {str(e)}"
            }
        finally:
            # Always restore the original directory
            try:
                os.chdir(original_dir)
            except:
                pass  # Ignore errors when changing back to original directory
    
    def deploy_contract(self, contract_code: str, contract_name: str = "GeneratedContract") -> Dict[str, Any]:
        """Deploy the contract to BlockDAG testnet"""
        original_dir = os.getcwd()  # Initialize at the beginning
        constructor_args = get_default_constructor_args(contract_code)
        try:
            # Save contract to file
            contract_file = self.save_contract_to_file(contract_code, contract_name)
            
            # Compile the contract using the same contract_name
            compile_result = self.compile_contract(contract_name)
            # If compilation failed, try to autofix with LLM and recompile
            if not compile_result["success"]:
                # Attempt to autofix using LLM
                fixed_code = llm_autofix_solidity(contract_code, compile_result.get("error", ""))
                if fixed_code and fixed_code != contract_code:
                    # Save the fixed contract to file
                    contract_file = self.save_contract_to_file(fixed_code, contract_name)
                    # Try to recompile with the fixed code
                    compile_result = self.compile_contract(contract_name)
                    if not compile_result["success"]:
                        return compile_result["error"]
                    contract_code = fixed_code  # Use the fixed code for deployment
                
            
            # Change to Hardhat directory
            os.chdir(self.hardhat_dir)
            
            # Create deployment script
            args_str = ", ".join(repr(arg) for arg in (constructor_args or []))
            deploy_script = f"""
const hre = require("hardhat");

async function main() {{
    const {contract_name} = await hre.ethers.getContractFactory("{contract_name}");
    const contract = await {contract_name}.deploy({args_str});
    await contract.waitForDeployment();
    
    const address = await contract.getAddress();
    console.log("{contract_name} deployed to:", address);
    
    // Return deployment info as JSON
    console.log(JSON.stringify({{
        success: true,
        contractAddress: address,
        network: "primordial",
        contractName: "{contract_name}"
    }}));
}}

main()
    .then(() => process.exit(0))
    .catch((error) => {{
        console.error(error);
        console.log(JSON.stringify({{
            success: false,
            error: error.message
        }}));
        process.exit(1);
    }});
"""
            
            # Save deployment script
            script_file = self.hardhat_dir / "scripts" / "deploy_generated.js"
            with open(script_file, 'w') as f:
                f.write(deploy_script)
            
            result = subprocess.run(
                [str(self.npx_path), "hardhat", "run", "scripts/deploy_generated.js", "--network", "primordial"],
                capture_output=True,
                text=True,
                timeout=120
            )
            print(f"Deployment result: {result.stdout}")
            # Parse the JSON output from the script
            try:
                # Find the JSON output in the stdout
                lines = result.stdout.strip().split('\n')
                json_output = None
                for line in lines:
                    if line.startswith('{') and line.endswith('}'):
                        json_output = json.loads(line)
                        break
                
                if json_output and json_output.get("success"):
                    return {
                        "success": True,
                        "contractAddress": json_output["contractAddress"],
                        "network": json_output["network"],
                        "contractName": json_output["contractName"],
                        "transactionHash": "N/A",  # Could be extracted from deployment logs
                        "explorerUrl": f"https://primordial.bdagscan.com/address/{json_output['contractAddress']}"
                    }
                else:
                    return {
                        "success": False,
                        "error": json_output.get("error", "Deployment failed") if json_output else result.stderr
                    }
                    
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Failed to parse deployment result: {result.stdout}"
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Deployment timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Deployment error: {str(e)}"
            }
        finally:
            # Always restore the original directory
            try:
                os.chdir(original_dir)
            except:
                pass  # Ignore errors when changing back to original directory
    
    def cleanup_contract_file(self, contract_name: str = "GeneratedContract"):
        """Clean up the generated contract file"""
        contract_file = self.hardhat_dir / "contracts" / f"{contract_name}.sol"
        if contract_file.exists():
            contract_file.unlink()

def extract_contract_name(contract_code: str) -> str:
    match = re.search(r'contract\s+(\w+)', contract_code)
    return match.group(1) if match else "GeneratedContract"

def get_default_constructor_args(contract_code: str):
    """
    Extracts constructor parameters from Solidity code and returns default values.
    """
    # Find the constructor definition
    match = re.search(r'constructor\s*\(([^)]*)\)', contract_code)
    if not match:
        return []  # No constructor or default constructor

    params = match.group(1).strip()
    if not params:
        return []

    args = []
    # Split parameters by comma, handle multiple spaces
    for param in params.split(','):
        param = param.strip()
        if not param:
            continue
        # Extract type and name
        parts = param.split()
        if len(parts) < 2:
            continue
        param_type = parts[0]
        # Assign default values based on type
        if 'uint' in param_type or 'int' in param_type:
            args.append(0)
        elif 'string' in param_type:
            args.append("default")
        elif 'address' in param_type:
            args.append("0x0000000000000000000000000000000000000000")
        elif 'bool' in param_type:
            args.append(False)
        elif param_type.endswith('[]'):
            args.append([])
        else:
            args.append(None)  # Unknown type, use None

    return args

# Create a global instance
deployment_service = ContractDeploymentService() 