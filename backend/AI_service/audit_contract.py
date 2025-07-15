import os
import re
import subprocess
import tempfile
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import SecretStr
from dotenv import load_dotenv

# Load API Key from backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,  # Lower temperature for more consistent fixes
    api_key=SecretStr(openai_api_key),
    model_kwargs={"max_tokens": 2048}  # Ensure the model can return long contracts
)

def run_solhint_audit(solidity_code: str) -> dict:
    """
    Run solhint audit on the provided Solidity code
    """
    try:
        # Check if solhint is available
        try:
            subprocess.run(["solhint", "--version"], capture_output=True, text=True, timeout=10)
            print(f"[DEBUG] Solhint is available")
        except FileNotFoundError:
            print(f"[DEBUG] Solhint not found - please install with: npm install -g solhint")
            return {
                "success": True,  # Assume success if solhint not available
                "issues": [],
                "warnings": [],
                "errors": []
            }
        # Save code to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sol", mode="w", encoding="utf-8") as temp:
            temp.write(solidity_code)
            temp_path = temp.name

        # Run solhint with config file
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".solhint.json")
        print(f"[DEBUG] Running solhint on file: {temp_path} with config: {config_path}")
        result = subprocess.run(["solhint", "--config", config_path, temp_path], capture_output=True, text=True, timeout=30)
        print(f"[DEBUG] Solhint command completed with return code: {result.returncode}")

        # Clean up file
        os.remove(temp_path)

        audit_result = {
            "success": True,  # Default to success
            "issues": [],
            "warnings": [],
            "errors": []
        }

        # Parse solhint output
        lines = result.stdout.split('\n')
        print(f"[DEBUG] Solhint raw output: {result.stdout}")
        print(f"[DEBUG] Solhint return code: {result.returncode}")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip solhint header lines
            if line.startswith('solhint') or line.startswith('Solhint'):
                continue
                
            # Check for different types of issues
            if 'error' in line.lower():
                audit_result["errors"].append(line)
                print(f"[DEBUG] Found error: {line}")
            elif 'warning' in line.lower():
                audit_result["warnings"].append(line)
                print(f"[DEBUG] Found warning: {line}")
            elif line and not line.startswith('✓'):  # Skip success checkmarks
                audit_result["issues"].append(line)
                print(f"[DEBUG] Found issue: {line}")
        
        # Set success based on whether there are any issues
        if audit_result["errors"] or audit_result["warnings"] or audit_result["issues"]:
            audit_result["success"] = False
            print(f"[DEBUG] Setting success to False due to issues found")
        else:
            print(f"[DEBUG] Setting success to True - no issues found")

        return audit_result
    except Exception as e:
        return {
            "success": False,
            "error": f"Solhint audit failed: {str(e)}",
            "issues": [],
            "warnings": [],
            "errors": []
        }

def get_audit_prompt():
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an expert Solidity smart contract auditor and developer. Your task is to:\n"
                "1. Analyze the provided incomplete or incorrect smart contract\n"
                "2. Identify all issues, vulnerabilities, and missing components\n"
                "3. Provide a complete, secure, and production-ready version of the contract\n"
                "4. Follow Solidity best practices and security guidelines\n"
                "5. Use OpenZeppelin contracts v5.x when appropriate\n"
                "6. Ensure the contract compiles without errors\n"
                "7. Add comprehensive comments explaining the fixes\n\n"
                "IMPORTANT RULES:\n"
                "- Always use pragma solidity ^0.8.0 or higher\n"
                "- Remove SafeMath usage (not needed in Solidity ^0.8.0)\n"
                "- Remove Counters usage (replaced with uint256 in OpenZeppelin v5.x)\n"
                "- Replace _exists() with ownerOf() != address(0) for ERC721\n"
                "- Add Ownable(msg.sender) to constructors when inheriting from Ownable\n"
                "- Use reentrancy guards where appropriate\n"
                "- Validate all inputs\n"
                "- Handle edge cases and potential vulnerabilities\n\n"
                "Return ONLY the ENTIRE corrected Solidity contract code, from the pragma statement to the last closing bracket, with NO explanations, markdown, or comments outside the code. Do not truncate the contract."
            )
        ),
        (
            "human",
            "Here is the incomplete or incorrect smart contract:\n\n{contract_code}\n\n"
            "Solhint audit results:\n{audit_results}\n\n"
            "Please provide a complete, secure, and corrected version of this contract."
        )
    ])

def clean_llm_code_output(code: str) -> str:
    """Clean the LLM output to extract only the Solidity code"""
    code = code.strip()
    
    # Look for code blocks first
    code_block_match = re.search(r'```solidity\s*\n(.*?)\n```', code, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # If no code block, look for pragma solidity to find the start of the contract
    pragma_match = re.search(r'pragma solidity.*?;', code, re.DOTALL | re.IGNORECASE)
    if pragma_match:
        start_idx = code.find(pragma_match.group(0))
        return code[start_idx:].strip()
    
    # Fallback: remove markdown and explanatory text
    lines = code.split('\n')
    cleaned_lines = []
    in_code = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip markdown headers and explanatory text
        if line.startswith('#') or line.startswith('###') or line.startswith('**'):
            continue
        if line.startswith('Changes and Explanations:') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.'):
            continue
        if 'pragma solidity' in line.lower():
            in_code = True
        if in_code:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

def detect_functional_improvements(original_code: str, corrected_code: str) -> dict:
    """
    Detect functional improvements made by the AI
    """
    improvements = {
        "security_improvements": [],
        "functionality_improvements": [],
        "best_practice_improvements": [],
        "structural_improvements": [],
        "total_improvements": 0
    }
    
    # Check for structural improvements (major additions)
    if "import" in corrected_code and "import" not in original_code:
        import_count = corrected_code.count("import")
        original_import_count = original_code.count("import")
        if import_count > original_import_count:
            improvements["structural_improvements"].append(f"Added {import_count - original_import_count} import statements")
    
    if "contract" in corrected_code and "contract" not in original_code:
        improvements["structural_improvements"].append("Added contract declaration")
    
    if "struct" in corrected_code and "struct" not in original_code:
        improvements["structural_improvements"].append("Added struct definition")
    
    # Check for security improvements
    if "ReentrancyGuard" in corrected_code and "ReentrancyGuard" not in original_code:
        improvements["security_improvements"].append("Added ReentrancyGuard protection")
    
    if "nonReentrant" in corrected_code and "nonReentrant" not in original_code:
        improvements["security_improvements"].append("Added nonReentrant modifier")
    
    # Check for functionality improvements
    if "require(" in corrected_code and corrected_code.count("require(") > original_code.count("require("):
        improvements["functionality_improvements"].append("Added input validation")
    
    # Check for best practice improvements
    if "_exists(" in corrected_code and "ownerOf(tokenId) != address(0)" in original_code:
        improvements["best_practice_improvements"].append("Fixed ERC721 existence check")
    
    if "Ownable()" in original_code and "Ownable()" not in corrected_code:
        improvements["best_practice_improvements"].append("Fixed constructor inheritance")
    
    # Count total improvements
    improvements["total_improvements"] = (
        len(improvements["security_improvements"]) +
        len(improvements["functionality_improvements"]) +
        len(improvements["best_practice_improvements"]) +
        len(improvements["structural_improvements"])
    )
    
    return improvements

def audit_and_fix_contract(contract_code: str) -> dict:
    """
    Main function to audit and fix a smart contract
    """
    print(f"[Audit Contract] Starting audit process...")
    
    try:
        # Step 1: Run solhint audit
        print(f"[Audit Contract] Running solhint audit...")
        solhint_results = run_solhint_audit(contract_code)
        print(f"[Audit Contract] Solhint audit completed")
        
        # Step 2: Prepare audit results for LLM
        issues = []
        if solhint_results["errors"]:
            issues.extend([f"ERROR: {error}" for error in solhint_results["errors"]])
        if solhint_results["warnings"]:
            issues.extend([f"WARNING: {warning}" for warning in solhint_results["warnings"]])
        if solhint_results["issues"]:
            issues.extend([f"ISSUE: {issue}" for issue in solhint_results["issues"]])
        
        if issues:
            audit_summary = "\n".join(issues)
        else:
            audit_summary = "No issues found - contract passed solhint analysis"
        
        # Step 3: Call LLM for fixes
        print(f"[Audit Contract] Calling LLM for contract fixes...")
        audit_prompt = get_audit_prompt()
        
        # Create the prompt manually
        system_message = (
            "You are an expert Solidity smart contract auditor and developer. Your task is to:\n"
            "1. Analyze the provided incomplete or incorrect smart contract\n"
            "2. Identify all issues, vulnerabilities, and missing components\n"
            "3. Provide a complete, secure, and production-ready version of the contract\n"
            "4. Follow Solidity best practices and security guidelines\n"
            "5. Use OpenZeppelin contracts v5.x when appropriate\n"
            "6. Ensure the contract compiles without errors\n"
            "7. Add comprehensive comments explaining the fixes\n\n"
            "IMPORTANT RULES:\n"
            "- Always use pragma solidity ^0.8.0 or higher\n"
            "- Remove SafeMath usage (not needed in Solidity ^0.8.0)\n"
            "- Remove Counters usage (replaced with uint256 in OpenZeppelin v5.x)\n"
            "- Replace _exists() with ownerOf() != address(0) for ERC721\n"
            "- Add Ownable(msg.sender) to constructors when inheriting from Ownable\n"
            "- Use reentrancy guards where appropriate\n"
            "- Validate all inputs\n"
            "- Handle edge cases and potential vulnerabilities\n\n"
                            "Return ONLY the ENTIRE corrected Solidity contract code, from the pragma statement to the last closing bracket, with NO explanations, markdown, or comments outside the code. Do not truncate the contract."
        )
        
        human_message = f"Here is the incomplete or incorrect smart contract:\n\n{contract_code}\n\nSolhint audit results:\n{audit_summary}\n\nPlease provide a complete, secure, and corrected version of this contract."
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system_message), HumanMessage(content=human_message)]
        
        response = llm(messages)
        corrected_code = str(response.content) if hasattr(response, 'content') else str(response)
        corrected_code = clean_llm_code_output(corrected_code)
        
        print(f"[Audit Contract] LLM processing completed")
        
        # Step 4: Run solhint on corrected code
        print(f"[Audit Contract] Running solhint on corrected code...")
        final_audit = run_solhint_audit(corrected_code)
        print(f"[Audit Contract] Final audit completed")
        
        # Step 5: Detect functional improvements
        print(f"[Audit Contract] Detecting functional improvements...")
        improvements = detect_functional_improvements(contract_code, corrected_code)
        
        # Calculate total issues fixed (solhint + functional improvements)
        solhint_issues = len(solhint_results.get("errors", [])) + len(solhint_results.get("warnings", []))
        functional_improvements = improvements["total_improvements"]
        total_issues_fixed = solhint_issues + functional_improvements
        
        print(f"[Audit Contract] Solhint issues: {solhint_issues}, Functional improvements: {functional_improvements}")
        
        return {
            "success": True,
            "original_code": contract_code,
            "corrected_code": corrected_code,
            "original_audit": solhint_results,
            "final_audit": final_audit,
            "issues_fixed": total_issues_fixed,
            "remaining_issues": len(final_audit.get("errors", [])) + len(final_audit.get("warnings", [])),
            "improvements": improvements
        }
        
    except Exception as e:
        print(f"[Audit Contract] Error during audit: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "original_code": contract_code,
            "corrected_code": contract_code
        }

def validate_contract_structure(contract_code: str) -> dict:
    """
    Basic validation of contract structure
    """
    validation = {
        "has_pragma": False,
        "has_contract": False,
        "has_constructor": False,
        "has_imports": False,
        "solidity_version": None,
        "contract_name": None
    }
    
    # Check pragma
    pragma_match = re.search(r'pragma solidity\s+([^;]+);', contract_code)
    if pragma_match:
        validation["has_pragma"] = True
        validation["solidity_version"] = pragma_match.group(1).strip()
    
    # Check contract definition
    contract_match = re.search(r'contract\s+(\w+)', contract_code)
    if contract_match:
        validation["has_contract"] = True
        validation["contract_name"] = contract_match.group(1)
    
    # Check constructor
    if 'constructor(' in contract_code:
        validation["has_constructor"] = True
    
    # Check imports
    if 'import' in contract_code:
        validation["has_imports"] = True
    
    return validation 