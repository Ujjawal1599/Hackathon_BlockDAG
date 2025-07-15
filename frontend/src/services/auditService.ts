import { api } from "../utils/axios";

export interface AuditRequest {
    contract_code: string;
    description?: string;
}

export interface AuditResponse {
    success: boolean;
    original_code: string;
    corrected_code: string;
    original_audit: {
        success: boolean;
        issues: string[];
        warnings: string[];
        errors: string[];
    };
    final_audit: {
        success: boolean;
        issues: string[];
        warnings: string[];
        errors: string[];
    };
    issues_fixed: number;
    remaining_issues: number;
    validation: {
        has_pragma: boolean;
        has_contract: boolean;
        has_constructor: boolean;
        has_imports: boolean;
        solidity_version: string | null;
        contract_name: string | null;
    };
    error?: string;
}

export interface ValidationResponse {
    success: boolean;
    validation: {
        has_pragma: boolean;
        has_contract: boolean;
        has_constructor: boolean;
        has_imports: boolean;
        solidity_version: string | null;
        contract_name: string | null;
    };
}

export interface SolhintResponse {
    success: boolean;
    audit_result: {
        success: boolean;
        issues: string[];
        warnings: string[];
        errors: string[];
    };
}

export async function auditContract(contractCode: string, description?: string): Promise<AuditResponse> {
    try {
        const response = await api.post("/audit", {
            contract_code: contractCode,
            description: description || ""
        });
        return response.data;
    } catch (error: any) {
        console.error("Audit failed:", error);
        throw new Error(error.response?.data?.detail || "Audit failed");
    }
}

export async function validateContract(contractCode: string, description?: string): Promise<ValidationResponse> {
    try {
        const response = await api.post("/validate", {
            contract_code: contractCode,
            description: description || ""
        });
        return response.data;
    } catch (error: any) {
        console.error("Validation failed:", error);
        throw new Error(error.response?.data?.detail || "Validation failed");
    }
}

export async function solhintAudit(contractCode: string, description?: string): Promise<SolhintResponse> {
    try {
        const response = await api.post("/solhint-only", {
            contract_code: contractCode,
            description: description || ""
        });
        return response.data;
    } catch (error: any) {
        console.error("Solhint audit failed:", error);
        throw new Error(error.response?.data?.detail || "Solhint audit failed");
    }
} 