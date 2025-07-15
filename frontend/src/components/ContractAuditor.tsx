"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle, XCircle, AlertTriangle, Code, FileText } from "lucide-react";
import { toast } from "sonner";
import { auditContract, validateContract, solhintAudit, type AuditResponse } from "@/services/auditService";

interface AuditResult {
    success: boolean;
    originalCode: string;
    correctedCode: string;
    originalAudit: any;
    finalAudit: any;
    issuesFixed: number;
    remainingIssues: number;
    validation: any;
}

export default function ContractAuditor() {
    const [contractCode, setContractCode] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
    const [activeTab, setActiveTab] = useState<'original' | 'corrected'>('original');

    const handleAudit = async () => {
        if (!contractCode.trim()) {
            toast.error("Please enter contract code");
            return;
        }

        setIsLoading(true);
        try {
            const result = await auditContract(contractCode);
            setAuditResult({
                success: result.success,
                originalCode: result.original_code,
                correctedCode: result.corrected_code,
                originalAudit: result.original_audit,
                finalAudit: result.final_audit,
                issuesFixed: result.issues_fixed,
                remainingIssues: result.remaining_issues,
                validation: result.validation
            });
            toast.success(`Audit completed! Fixed ${result.issues_fixed} issues`);
        } catch (error: any) {
            toast.error(error.message || "Audit failed");
        } finally {
            setIsLoading(false);
        }
    };

    const handleValidate = async () => {
        if (!contractCode.trim()) {
            toast.error("Please enter contract code");
            return;
        }

        setIsLoading(true);
        try {
            const result = await validateContract(contractCode);
            toast.success("Validation completed");
            console.log("Validation result:", result);
        } catch (error: any) {
            toast.error(error.message || "Validation failed");
        } finally {
            setIsLoading(false);
        }
    };

    const handleSolhintOnly = async () => {
        if (!contractCode.trim()) {
            toast.error("Please enter contract code");
            return;
        }

        setIsLoading(true);
        try {
            const result = await solhintAudit(contractCode);
            toast.success("Solhint audit completed");
            console.log("Solhint result:", result);
        } catch (error: any) {
            toast.error(error.message || "Solhint audit failed");
        } finally {
            setIsLoading(false);
        }
    };

    const getValidationStatus = () => {
        if (!auditResult?.validation) return null;
        
        const { validation } = auditResult;
        const checks = [
            { label: "Pragma", status: validation.has_pragma },
            { label: "Contract", status: validation.has_contract },
            { label: "Constructor", status: validation.has_constructor },
            { label: "Imports", status: validation.has_imports }
        ];

        return checks;
    };

    const getAuditIssues = (audit: any) => {
        const issues = [];
        if (audit.errors?.length > 0) {
            issues.push(...audit.errors.map((error: string) => ({ type: 'error', message: error })));
        }
        if (audit.warnings?.length > 0) {
            issues.push(...audit.warnings.map((warning: string) => ({ type: 'warning', message: warning })));
        }
        if (audit.issues?.length > 0) {
            issues.push(...audit.issues.map((issue: string) => ({ type: 'info', message: issue })));
        }
        return issues;
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold">Smart Contract Auditor</h1>
                <p className="text-muted-foreground">
                    Upload your incomplete or incorrect smart contract and get it fixed with AI-powered analysis
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Code className="h-5 w-5" />
                        Contract Code
                    </CardTitle>
                    <CardDescription>
                        Paste your Solidity contract code here. The AI will analyze and fix any issues.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Textarea
                        placeholder="// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MyContract {
    // Your contract code here...
}"
                        value={contractCode}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setContractCode(e.target.value)}
                        className="min-h-[300px] font-mono"
                    />
                    
                    <div className="flex gap-2">
                        <Button 
                            onClick={handleAudit} 
                            disabled={isLoading}
                            className="flex-1"
                        >
                            {isLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : (
                                <CheckCircle className="h-4 w-4 mr-2" />
                            )}
                            Audit & Fix Contract
                        </Button>
                        <Button 
                            onClick={handleValidate} 
                            disabled={isLoading}
                            variant="outline"
                        >
                            <FileText className="h-4 w-4 mr-2" />
                            Validate Only
                        </Button>
                        <Button 
                            onClick={handleSolhintOnly} 
                            disabled={isLoading}
                            variant="outline"
                        >
                            <AlertTriangle className="h-4 w-4 mr-2" />
                            Solhint Only
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {auditResult && (
                <div className="space-y-6">
                    {/* Summary Card */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Audit Summary</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600">
                                        {auditResult.issuesFixed}
                                    </div>
                                    <div className="text-sm text-muted-foreground">Issues Fixed</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-orange-600">
                                        {auditResult.remainingIssues}
                                    </div>
                                    <div className="text-sm text-muted-foreground">Remaining Issues</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-600">
                                        {auditResult.validation.contract_name || "Unknown"}
                                    </div>
                                    <div className="text-sm text-muted-foreground">Contract Name</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-2xl font-bold text-purple-600">
                                        {auditResult.validation.solidity_version || "Unknown"}
                                    </div>
                                    <div className="text-sm text-muted-foreground">Solidity Version</div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Validation Status */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Contract Structure Validation</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {getValidationStatus()?.map((check, index) => (
                                    <div key={index} className="flex items-center gap-2">
                                        {check.status ? (
                                            <CheckCircle className="h-4 w-4 text-green-600" />
                                        ) : (
                                            <XCircle className="h-4 w-4 text-red-600" />
                                        )}
                                        <span className="text-sm">{check.label}</span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Code Comparison */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Code Comparison</CardTitle>
                            <CardDescription>
                                Compare the original and corrected versions of your contract
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex gap-2">
                                    <Button
                                        variant={activeTab === 'original' ? 'default' : 'outline'}
                                        onClick={() => setActiveTab('original')}
                                    >
                                        Original Code
                                    </Button>
                                    <Button
                                        variant={activeTab === 'corrected' ? 'default' : 'outline'}
                                        onClick={() => setActiveTab('corrected')}
                                    >
                                        Corrected Code
                                    </Button>
                                </div>
                                
                                <div className="bg-muted p-4 rounded-lg">
                                    <pre className="text-sm font-mono whitespace-pre-wrap">
                                        {activeTab === 'original' ? auditResult.originalCode : auditResult.correctedCode}
                                    </pre>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Audit Issues */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Original Audit */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                                    Original Audit Issues
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    {getAuditIssues(auditResult.originalAudit).map((issue, index) => (
                                        <Alert key={index}>
                                            <AlertDescription className="flex items-start gap-2">
                                                {issue.type === 'error' && <XCircle className="h-4 w-4 text-red-600 mt-0.5" />}
                                                {issue.type === 'warning' && <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />}
                                                {issue.type === 'info' && <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5" />}
                                                <span>{issue.message}</span>
                                            </AlertDescription>
                                        </Alert>
                                    ))}
                                    {getAuditIssues(auditResult.originalAudit).length === 0 && (
                                        <p className="text-muted-foreground">No issues found</p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Final Audit */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <CheckCircle className="h-5 w-5 text-green-600" />
                                    Final Audit Issues
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    {getAuditIssues(auditResult.finalAudit).map((issue, index) => (
                                        <Alert key={index}>
                                            <AlertDescription className="flex items-start gap-2">
                                                {issue.type === 'error' && <XCircle className="h-4 w-4 text-red-600 mt-0.5" />}
                                                {issue.type === 'warning' && <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5" />}
                                                {issue.type === 'info' && <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5" />}
                                                <span>{issue.message}</span>
                                            </AlertDescription>
                                        </Alert>
                                    ))}
                                    {getAuditIssues(auditResult.finalAudit).length === 0 && (
                                        <p className="text-muted-foreground">No issues found</p>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}
        </div>
    );
} 