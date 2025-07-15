"use client";

import React from "react";
import { Button } from "@/components/button";
import { Card, CardContent } from "@/components/card";
import { Feature } from "@/components/feature";
import {Step} from "@/components/step";
  import { CheckCircle, MessageSquare, Pencil, Upload, PersonStanding, Speech, PackageOpen, GraduationCap, ArrowRight } from "lucide-react";
  import { useRouter } from 'next/navigation';
  import { ThemeToggle } from "@/components/ThemeToggle";
import { Step2 } from "@/components/step2";

  export default function HomePage() {
    const router = useRouter();
    const gotochatpage = () => {
      router.push('/demo'); 
    };
    return (
      <main className="bg-white dark:bg-[#0c0e12] text-gray-900 dark:text-white min-h-screen p-6 space-y-16">
        <ThemeToggle />
        <header className="flex flex-col items-center space-y-4 text-center">
          <h1 className="text-3xl md:text-5xl font-bold">
            Build & Deploy Smart Contracts with AI —<br /> Powered by BlockDAG
          </h1>
        <p className="text-gray-500 dark:text-gray-400 max-w-xl">
          Generate, audit, and deploy contracts using natural language. No code needed.
        </p>
        <div className="flex gap-4">
          <Button variant="default" onClick={gotochatpage}>Try the Demo</Button>
          <Button variant="outline" onClick={() => router.push('/audit')}>Contract Auditor</Button>
          <Button variant="outline" onClick={() => window.open('https://github.com/Ujjawal1599/Hackathon_BlockDAG', '_blank')}>View on GitHub</Button>
        </div>
      </header>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <Feature icon={<MessageSquare />} text="Natural Language Code Generation" />
        <Feature icon={<CheckCircle />} text="Real-time AI Feedback" />
        <Feature icon={<Pencil />} text="Integrated Monaco Editor" />
        <Feature icon={<Upload />} text="Automated Security Audits" />
      </section>

      <section className="text-center space-y-6">
        <h2 className="text-2xl font-semibold">How it Works</h2>
        <div className="flex flex-col md:flex-row items-center justify-center gap-6">
          <Step icon={<MessageSquare />} label="Chat with AI" bold />
          <ArrowRight className="hidden md:inline-block w-5 h-5 text-gray-400 dark:text-gray-600" />
          <Step icon={<Pencil />} label="Edit and audit code live" bold/>
          <ArrowRight className="hidden md:inline-block w-5 h-5 text-gray-400 dark:text-gray-600" />
          <div className="mt-6 md:mt-5">
            <Step icon={<Upload />} label="Deploy to BlockDAG testnet" bold />
          </div>
        </div>
      </section>



      <section className="text-center space-y-6">
        <h2 className="text-2xl font-semibold">Use Cases</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <Card><CardContent className="p-4"><Step2 icon={<PersonStanding />}label=" Startups" /><span className="text-xs">Total UX/99</span></CardContent></Card>
          <Card><CardContent className="p-4"><Step2 icon={<Speech />}label="Auditors"/><span className="text-xs">AI-enhanced audits</span></CardContent></Card>
          <Card><CardContent className="p-4"><Step2 icon={<PackageOpen />}label="Web3 Builders"/><span className="text-xs">Decentralize smart contracts</span></CardContent></Card>
          <Card><CardContent className="p-4"><Step2 icon={<GraduationCap />}label="Educators"/><span className="text-xs">Teach blockchain effortlessly</span></CardContent></Card>
        </div>
      </section>

      <footer className="text-center text-sm text-gray-400 dark:text-gray-600 mt-10">
        Developed by Aniket,Amritesh, Navneet, Rithika and Ujjawal
      </footer>
    </main>
  );
}