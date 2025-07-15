import os
import re
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
    api_key=SecretStr(openai_api_key)
)

def preprocess_contract_code(code: str) -> str:
    try:
        # Remove SafeMath import and usage
        code = re.sub(r'import\s+[\'"]@openzeppelin/contracts/utils/math/SafeMath\.sol[\'"]\s*;?', '', code)
        code = re.sub(r'using SafeMath for uint256\s*;', '', code)
        code = re.sub(r'(\w+)\.add\(([^)]+)\)', r'\1 + \2', code)
        code = re.sub(r'(\w+)\.sub\(([^)]+)\)', r'\1 - \2', code)
        code = re.sub(r'(\w+)\.mul\(([^)]+)\)', r'\1 * \2', code)
        code = re.sub(r'(\w+)\.div\(([^)]+)\)', r'\1 / \2', code)
        
        # Fix Counters import and usage - Counters was removed in OpenZeppelin v5.x
        # Remove Counters import
        code = re.sub(r'import\s+[\'"]@openzeppelin/contracts/utils/Counters\.sol[\'"]\s*;?', '', code)
        # Remove Counters usage statement
        code = re.sub(r'using Counters for Counters\.Counter;', '', code)
        # Replace Counters.Counter with uint256
        code = re.sub(r'Counters\.Counter', 'uint256', code)
        # Replace .current() with direct variable usage
        code = re.sub(r'(\w+)\.current\(\)', r'\1', code)
        # Replace .increment() with ++
        code = re.sub(r'(\w+)\.increment\(\)', r'++\1', code)
        # Replace .decrement() with --
        code = re.sub(r'(\w+)\.decrement\(\)', r'--\1', code)
        
        # Fix _exists function - removed in OpenZeppelin v5.x
        # Replace _exists(tokenId) with ownerOf(tokenId) != address(0)
        code = re.sub(r'_exists\(([^)]+)\)', r'ownerOf(\1) != address(0)', code)
        
        # Fix Ownable constructor calls - simplified approach
        # Look for constructor patterns and add Ownable(msg.sender)
        if 'constructor(' in code and 'Ownable' in code and 'Ownable(msg.sender)' not in code:
            # Replace constructor() { with constructor() Ownable(msg.sender) {
            code = re.sub(r'constructor\([^)]*\)\s*\{', 'constructor() Ownable(msg.sender) {', code)
        
        # Fix pragma version
        code = re.sub(r'pragma solidity [^;]+;', 'pragma solidity ^0.8.0;', code)
        
        return code
    except Exception as e:
        print(f"[Preprocess] Error during regex processing: {e}")
        return code

def get_comprehensive_autofix_prompt():
    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are an expert Solidity developer. You MUST apply ALL of the following fixes to the contract below, even if it already compiles:\n"
                "1. Replace all SafeMath imports/usages with native operators (remove SafeMath).\n"
                "2. Replace all Counters imports/usages with simple uint256 variables (Counters was removed in OpenZeppelin v5.x).\n"
                "3. Replace all _exists(tokenId) calls with ownerOf(tokenId) != address(0) (_exists was removed in OpenZeppelin v5.x).\n"
                "4. If the contract inherits from Ownable, add Ownable(msg.sender) to the constructor call.\n"
                "5. Ensure pragma solidity is ^0.8.0 or higher.\n"
                "EXAMPLES:\n"
                "Before: import \"@openzeppelin/contracts/utils/Counters.sol\";\n"
                "After:  (remove this line)\n"
                "Before: using Counters for Counters.Counter;\n"
                "After:  (remove this line)\n"
                "Before: Counters.Counter private _counter;\n"
                "After:  uint256 private _counter;\n"
                "Before: _counter.current()\n"
                "After:  _counter\n"
                "Before: _counter.increment()\n"
                "After:  ++_counter\n"
                "Before: _exists(tokenId)\n"
                "After:  ownerOf(tokenId) != address(0)\n"
                "Before: constructor() ERC721(\"Name\", \"SYMBOL\") {}\n"
                "After:  constructor() ERC721(\"Name\", \"SYMBOL\") Ownable(msg.sender) {}\n"
                "Before: import \"@openzeppelin/contracts/utils/math/SafeMath.sol\";\n"
                "After:  (remove this line)\n"
                "Before: using SafeMath for uint256;\n"
                "After:  (remove this line)\n"
                "Before: a.add(b)\n"
                "After:  a + b\n"
                "Return ONLY the corrected Solidity code, no explanations."
            )
        ),
        (
            "human",
            "Here is the Solidity contract that failed to compile:\n\n{contract_code}\n\nAnd here is the compiler error message:\n\n{error_message}\n\nApply ALL the above fixes."
        )
    ])

def clean_llm_code_output(code: str) -> str:
    code = code.strip()
    code = re.sub(r'^```solidity\s*', '', code, flags=re.IGNORECASE)
    code = re.sub(r'^```', '', code)
    code = re.sub(r'```$', '', code)
    lines = code.split('\n')
    cleaned_lines = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith('//') or line.strip().startswith('/*'):
            continue
        if '```' in line:
            in_code_block = not in_code_block
            continue
        if not in_code_block and line.strip():
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).strip()

def llm_autofix_solidity(contract_code: str, error_message: str) -> str:
    """
    Hybrid autofix: regex for known patterns, LLM for complex fixes.
    """
    print(f"[LLM Autofix] Starting autofix process...")
    try:
        # Preprocess known patterns
        print(f"[LLM Autofix] Applying regex preprocessing...")
        preprocessed_code = preprocess_contract_code(contract_code)
        print(f"[LLM Autofix] Regex preprocessing completed")
        
        # Now call the LLM for any remaining issues
        print(f"[LLM Autofix] Calling LLM for additional fixes...")
        autofix_prompt = get_comprehensive_autofix_prompt()
        
        # Create the prompt manually to avoid string formatting issues
        system_message = (
            "You are an expert Solidity developer. You MUST apply ALL of the following fixes to the contract below, even if it already compiles:\n"
            "1. Replace all SafeMath imports/usages with native operators (remove SafeMath).\n"
            "2. Replace all Counters imports/usages with simple uint256 variables (Counters was removed in OpenZeppelin v5.x).\n"
            "3. Replace all _exists(tokenId) calls with ownerOf(tokenId) != address(0) (_exists was removed in OpenZeppelin v5.x).\n"
            "4. If the contract inherits from Ownable, add Ownable(msg.sender) to the constructor call.\n"
            "5. Ensure pragma solidity is ^0.8.0 or higher.\n"
            "EXAMPLES:\n"
            "Before: import \"@openzeppelin/contracts/utils/Counters.sol\";\n"
            "After:  (remove this line)\n"
            "Before: using Counters for Counters.Counter;\n"
            "After:  (remove this line)\n"
            "Before: Counters.Counter private _counter;\n"
            "After:  uint256 private _counter;\n"
            "Before: _counter.current()\n"
            "After:  _counter\n"
            "Before: _counter.increment()\n"
            "After:  ++_counter\n"
            "Before: _exists(tokenId)\n"
            "After:  ownerOf(tokenId) != address(0)\n"
            "Before: constructor() ERC721(\"Name\", \"SYMBOL\") {}\n"
            "After:  constructor() ERC721(\"Name\", \"SYMBOL\") Ownable(msg.sender) {}\n"
            "Before: import \"@openzeppelin/contracts/utils/math/SafeMath.sol\";\n"
            "After:  (remove this line)\n"
            "Before: using SafeMath for uint256;\n"
            "After:  (remove this line)\n"
            "Before: a.add(b)\n"
            "After:  a + b\n"
            "Return ONLY the corrected Solidity code, no explanations."
        )
        
        human_message = f"Here is the Solidity contract that failed to compile:\n\n{preprocessed_code}\n\nAnd here is the compiler error message:\n\n{error_message}\n\nApply ALL the above fixes."
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system_message), HumanMessage(content=human_message)]
        
        response = llm(messages)
        code = str(response.content) if hasattr(response, 'content') else str(response)
        code = clean_llm_code_output(code)
        print(f"[LLM Autofix] LLM processing completed")
        return code
    except Exception as e:
        print(f"[LLM Autofix] Error during fix: {e}")
        import traceback
        traceback.print_exc()
        return contract_code

def validate_fixes(original_code: str, fixed_code: str) -> dict:
    """
    Validate that common fixes were applied correctly
    """
    fixes = {
        "ownable_constructor": False,
        "counters_import": False,
        "counters_usage": False,
        "safemath_removed": False,
        "exists_fixed": False,
        "solidity_version": False
    }
    
    # Check Ownable constructor fix
    if "Ownable(msg.sender)" in fixed_code:
        fixes["ownable_constructor"] = True
    
    # Check Counters import fix (should be removed)
    if "import \"@openzeppelin/contracts/utils/Counters.sol\";" not in fixed_code and "import \"@openzeppelin/contracts/utils/Counters.sol\";" in original_code:
        fixes["counters_import"] = True
    
    # Check Counters usage fix (should be replaced with uint256)
    if "Counters.Counter" not in fixed_code and "Counters.Counter" in original_code:
        fixes["counters_usage"] = True
    
    # Check SafeMath removal
    if "SafeMath" not in fixed_code and "SafeMath" in original_code:
        fixes["safemath_removed"] = True
    
    # Check _exists fix (should be replaced with ownerOf check)
    if "_exists(" not in fixed_code and "_exists(" in original_code:
        fixes["exists_fixed"] = True
    
    # Check Solidity version
    if "pragma solidity ^0.8" in fixed_code:
        fixes["solidity_version"] = True
    
    return fixes 