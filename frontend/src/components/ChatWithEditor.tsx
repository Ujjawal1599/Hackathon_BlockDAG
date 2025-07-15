'use client'
import React, { useState, useEffect, useRef } from "react";
import MonacoEditor from "@monaco-editor/react";
import { CodeResponse, saveChat, sendChat } from "@/services/chatService";
import { deploySmartContract, IDeployResponse, saveDeployment, getDeployments } from "@/services/deployService";
import toast, { Toaster } from 'react-hot-toast';
import { useAccount } from "wagmi";
import { getChat } from "@/services/chatService";
import { FaHistory } from "react-icons/fa";
import DeploymentHistoryTable from "./DeploymentHistoryTable";
import { Button } from "./ui/button";
import { useTheme } from "@/context/ThemeContext";
import { Input } from "./ui/input";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogClose,
} from "./ui/dialog";

interface Message {
    sender: "user" | "ai";
    text: string;
    code?: string
}

interface Deployment {
    contractName?: string;
    contractAddress?: string;
    network?: string;
    timestamp?: string;
    explorerUrl?: string;
    [key: string]: any;
}

const initialCode = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract HelloWorld {
    string public greeting = "Hello, BlockDAG!";

    function setGreeting(string memory _greeting) public {
        greeting = _greeting;
    }
}
`;

const ChatWithEditor = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [code, setCode] = useState(initialCode);
    const [isLoading, setIsLoading] = useState(false)
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [deployInfo, setDeployInfo] = useState<IDeployResponse | null>(null);
    const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
    const [deployments, setDeployments] = useState<Deployment[]>([]);
    const { address } = useAccount();
    const { theme } = useTheme();

    const chatEndRef = useRef<HTMLDivElement | null>(null);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    useEffect(() => {
        const fetchChat = async () => {
            if (!address) return;
            try {
                const res = await getChat(address);
                if (res && res.data && res.data.chat_history) {
                    // Convert chat_history to Message[]
                    const loadedMessages = res.data.chat_history.map((msg: any) => ({
                        sender: msg.sender,
                        text: msg.message || msg.text || "",
                        code: msg.code
                    }));
                    setMessages(loadedMessages);
                    // Find last AI message with code
                    const lastAiMsg = [...loadedMessages].reverse().find(m => m.sender === 'ai' && m.code);
                    if (lastAiMsg && lastAiMsg.code) {
                        setCode(lastAiMsg.code);
                    }
                }
            } catch (e) {
                console.log(e);
            }
        };
        fetchChat();
    }, [address]);


    const handleSend = async () => {
        if (!address) {
            toast.error("Wallet not connected");
            return;
        }
        try {
            const chatPayload: Message[] = []
            setIsLoading(true)
            if (!input.trim()) return;
            let userMessage: Message = { sender: "user", text: input }
            setMessages([...messages, userMessage]);
            chatPayload.push(userMessage)

            let prompt = input
            setInput("");
            let aiResponse: CodeResponse | undefined = await sendChat(prompt)
            if (!aiResponse) return

            let aiMessage: Message = { sender: 'ai', text: aiResponse.text, code: aiResponse.code }
            setMessages(prev => [...prev, aiMessage])
            setCode(aiResponse.code)
            chatPayload.push(aiMessage)

            await saveChat(address, chatPayload)

        } catch (e: any) {
            console.log(e)
        } finally {
            setIsLoading(false)
        }
    };

    const handleDeploy = async () => {
        if (!address) {
            toast.error("Wallet not connected");
            return;
        }
        toast.loading('Deployment started...', { id: 'deploy' });
        setIsLoading(true);
        try {
            let deployResponse: IDeployResponse = await deploySmartContract(code)
            await saveDeployment(deployResponse, address)
            setDeployInfo(deployResponse);
            setIsModalOpen(true);
            toast.dismiss('deploy');
        } catch (e: any) {
            toast.dismiss('deploy');
            toast.error('Deployment failed');
            console.log(e)
        } finally {
            setIsLoading(false);
        }
    };

    const handleOpenHistory = async () => {
        if (!address) {
            toast.error("Wallet not connected");
            return;
        }
        try {
            const deployments: IDeployResponse[] = await getDeployments(address);
            setDeployments(deployments);
            setIsHistoryModalOpen(true);
        } catch (e) {
            toast.error("Failed to fetch deployment history");
            setDeployments([]);
            setIsHistoryModalOpen(true);
        }
    };

    return (
        <>
            <Toaster position="top-center" />
            {/* Modal for deployment info */}
            {isModalOpen && deployInfo && (
                <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                    <DialogContent className="max-w-lg w-full">
                        <DialogHeader>
                            <DialogTitle>Deployment Successful 🎉</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-2">
                            {deployInfo.contractAddress && (
                                <div><span className="font-semibold">Contract Address:</span> <span className="break-all">{deployInfo.contractAddress}</span></div>
                            )}
                            {deployInfo.network && (
                                <div><span className="font-semibold">Network:</span> {deployInfo.network}</div>
                            )}
                            {deployInfo.contractName && (
                                <div><span className="font-semibold">Contract Name:</span> {deployInfo.contractName}</div>
                            )}
                            {deployInfo.explorerUrl && (
                                <div className="break-all word-break break-words">
                                    <span className="font-semibold">Explorer URL:</span> <a href={deployInfo.explorerUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 underline break-all">{deployInfo.explorerUrl}</a>
                                </div>
                            )}
                            {('transactionHash' in deployInfo && (deployInfo as any).transactionHash !== undefined && (deployInfo as any).transactionHash !== 'N/A') && (
                                <div><span className="font-semibold">Transaction Hash:</span> {(deployInfo as any).transactionHash}</div>
                            )}
                        </div>
                    </DialogContent>
                </Dialog>
            )}
            {/* Modal for deployment history */}
            <DeploymentHistoryTable
                deployments={deployments}
                open={isHistoryModalOpen}
                onOpenChange={setIsHistoryModalOpen}
            />
            <div className="flex flex-col md:flex-row w-full h-[80vh] rounded-lg shadow-lg overflow-hidden bg-neutral-200 text-black dark:bg-neutral-800 dark:text-white">
                {/* Chat Section */}
                <div className="flex flex-col w-full md:w-1/2 h-full p-4 border-r border-neutral-400 dark:border-neutral-900">
                    <div className="flex-1 overflow-y-auto mb-4 space-y-2">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`p-2 flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`p-2 rounded-lg max-w-[80%] 
                                    ${msg.sender === "user"
                                        ? (theme === 'dark' ? 'bg-blue-600 text-white' : 'bg-blue-400 text-black')
                                        : (theme === 'dark' ? 'bg-gray-700 text-gray-100' : 'bg-gray-300 text-black')
                                    }
                                `}
                                >
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        <div ref={chatEndRef} />
                    </div>
                    <div className="flex gap-2">
                        <Input
                            className={`flex-1 p-2 rounded border focus:outline-none
                                ${theme === 'dark'
                                    ? 'bg-gray-800 text-white border-gray-700 placeholder-gray-400'
                                    : 'bg-white text-black border-gray-300 placeholder-gray-500'}
                            `}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            placeholder="e.g. ERC-20|burnable, mintable, capped at 1M tokens"
                            onKeyDown={e => e.key === 'Enter' && handleSend()}
                        />
                        <Button
                            className={`px-4 py-2 rounded flex items-center justify-center min-w-[64px] 
                                ${theme === 'dark'
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-blue-400 text-black hover:bg-blue-500'}
                            `}
                            onClick={handleSend}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                </svg>
                            ) : (
                                'Send'
                            )}
                        </Button>
                    </div>
                </div>
                {/* Code Editor Section */}
                <div className="w-full md:w-1/2 h-full flex flex-col">
                    <div className="flex-1">
                        <MonacoEditor
                            height="100%"
                            defaultLanguage="solidity"
                            value={code}
                            onChange={(value: any) => setCode(value || "")}
                            theme={theme === 'dark' ? 'vs-dark' : 'light'}
                            options={{ fontSize: 14, minimap: { enabled: false } }}
                        />
                    </div>
                    <div className="p-4 flex justify-end gap-2">
                        <Button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                            Compile
                        </Button>
                        <Button onClick={handleDeploy} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 flex items-center justify-center min-w-[64px]" disabled={isLoading}>
                            {isLoading ? (
                                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
                                </svg>
                            ) : (
                                'Deploy'
                            )}
                        </Button>
                        <Button
                            onClick={handleOpenHistory}
                            className="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-600 flex items-center justify-center"
                            title="View Deployment History"
                        >
                            History
                            {/* <FaHistory className="mr-2" /> */}
                            {/* <span className="hidden md:inline">History</span> */}
                        </Button>
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatWithEditor; 