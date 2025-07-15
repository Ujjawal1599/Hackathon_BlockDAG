# Smart Contract Audit System

This system provides AI-powered smart contract auditing and fixing capabilities using OpenAI and solhint.

## Features

### Backend Components

1. **Audit Service** (`backend/AI_service/audit_contract.py`)
   - Uses OpenAI GPT-4 to analyze and fix smart contracts
   - Integrates with solhint for static analysis
   - Provides comprehensive contract validation
   - Fixes common issues like SafeMath usage, Counters, etc.

2. **API Routes** (`backend/routes_audit.py`)
   - `/audit` - Full audit and fix functionality
   - `/validate` - Contract structure validation only
   - `/solhint-only` - Solhint static analysis only

3. **Dependencies**
   - OpenAI API for AI-powered fixes
   - Solhint for static analysis
   - LangChain for prompt management
   - FastAPI for REST API

### Frontend Components

1. **Contract Auditor** (`frontend/src/components/ContractAuditor.tsx`)
   - Modern React component with TypeScript
   - Real-time contract validation
   - Side-by-side code comparison
   - Issue tracking and reporting

2. **Audit Service** (`frontend/src/services/auditService.ts`)
   - TypeScript interfaces for type safety
   - API integration with backend
   - Error handling and response processing

3. **UI Components**
   - Card, Textarea, Badge, Alert components
   - Responsive design with Tailwind CSS
   - Loading states and error handling

## Installation

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# backend/.env
OPENAI_API_KEY=your_openai_api_key
```

3. Install solhint globally:
```bash
npm install -g solhint
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Install additional packages:
```bash
npm install sonner class-variance-authority
```

### Hardhat Setup

1. Install solhint in hardhat project:
```bash
cd contracts/hardhat
npm install solhint
```

## Usage

### API Endpoints

1. **Full Audit** (`POST /audit`)
```json
{
  "contract_code": "pragma solidity ^0.8.0; contract MyContract { ... }",
  "description": "Optional description"
}
```

2. **Validation Only** (`POST /validate`)
```json
{
  "contract_code": "contract code here",
  "description": "Optional description"
}
```

3. **Solhint Only** (`POST /solhint-only`)
```json
{
  "contract_code": "contract code here",
  "description": "Optional description"
}
```

### Frontend Usage

1. Navigate to `/audit` page
2. Paste your Solidity contract code
3. Click "Audit & Fix Contract" for full analysis
4. Use "Validate Only" for structure validation
5. Use "Solhint Only" for static analysis

## Features

### AI-Powered Fixes

The system automatically fixes common issues:

1. **SafeMath Removal** - Replaces SafeMath with native operators
2. **Counters Replacement** - Replaces Counters with uint256
3. **Ownable Constructor** - Adds proper Ownable(msg.sender) calls
4. **Pragma Updates** - Ensures ^0.8.0 or higher
5. **Security Improvements** - Adds reentrancy guards and input validation

### Solhint Integration

Static analysis checks for:

1. **Security Issues** - Reentrancy, unchecked calls, etc.
2. **Code Quality** - Line length, naming conventions, etc.
3. **Best Practices** - Function visibility, gas optimization, etc.

### Validation Features

1. **Structure Validation** - Checks for pragma, contract, constructor, imports
2. **Version Compatibility** - Ensures Solidity ^0.8.0+
3. **OpenZeppelin Compatibility** - Uses v5.x standards

## Example Response

```json
{
  "success": true,
  "original_code": "// Original contract code",
  "corrected_code": "// Fixed contract code",
  "original_audit": {
    "success": false,
    "errors": ["Error messages"],
    "warnings": ["Warning messages"]
  },
  "final_audit": {
    "success": true,
    "errors": [],
    "warnings": []
  },
  "issues_fixed": 5,
  "remaining_issues": 0,
  "validation": {
    "has_pragma": true,
    "has_contract": true,
    "has_constructor": true,
    "has_imports": true,
    "solidity_version": "^0.8.0",
    "contract_name": "MyContract"
  }
}
```

## Security Considerations

1. **Input Validation** - All contract code is validated before processing
2. **Error Handling** - Comprehensive error handling prevents crashes
3. **Rate Limiting** - Consider implementing rate limiting for production
4. **API Key Security** - Store OpenAI API key securely
5. **Code Sanitization** - Input is sanitized to prevent injection attacks

## Development

### Adding New Fixes

1. Update `preprocess_contract_code()` in `audit_contract.py`
2. Add new regex patterns for common issues
3. Update the LLM prompt with new examples
4. Test with various contract types

### Extending Validation

1. Add new checks to `validate_contract_structure()`
2. Update the validation response interface
3. Add corresponding frontend display logic

### Custom Solhint Rules

1. Modify `.solhint.json` configuration
2. Add custom rules for project-specific requirements
3. Update the audit service to handle new rule outputs

## Troubleshooting

### Common Issues

1. **Solhint not found** - Install globally: `npm install -g solhint`
2. **OpenAI API errors** - Check API key and rate limits
3. **Compilation errors** - Ensure Solidity version compatibility
4. **Frontend build errors** - Check TypeScript types and dependencies

### Debug Mode

Enable debug logging by setting environment variables:
```bash
DEBUG=1 python main.py
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure all TypeScript types are properly defined
5. Test with various contract types and edge cases 