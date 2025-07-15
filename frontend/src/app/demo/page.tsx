"use client";

import { useAccount } from "wagmi";
import Login from "@/components/Login";
import HomeScreen from "@/components/HomeScreen";
import React from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function DemoPage() {
  const {  isConnected } = useAccount();
  // For Node.js environments
  if (typeof indexedDB === 'undefined') {
    const FDBFactory = require('fake-indexeddb/lib/FDBFactory');
    global.indexedDB = new FDBFactory();
    global.IDBKeyRange = require('fake-indexeddb/lib/FDBKeyRange');
  }
  return (
    <div className="p-0">
      <ThemeToggle />
      {isConnected ? <HomeScreen /> : <Login />}
    </div>
  );
}