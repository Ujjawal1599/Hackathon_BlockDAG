'use client'
import React from 'react';
import ConnectButton from '@/components/ConnectButton';
import { useAccount, useDisconnect } from 'wagmi';
import { ThemeToggle } from './ThemeToggle';
import { Button } from './ui/button';

const Header = () => {
  const { isConnected, address } = useAccount();
  const { disconnect } = useDisconnect();

  return (
    <div className="w-full flex items-center justify-between px-8 py-4 bg-neutral-200 dark:bg-neutral-900">
      <div className="text-xl font-bold">MetaDAG Chatbot</div>
      <div className="flex items-center gap-4">
        {isConnected && (
          <>
            <span className="text-green-800 dark:text-green-400 font-mono text-sm hidden md:inline">{address}</span>
            <Button
              onClick={() => disconnect()}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 mr-10"
            >
              Disconnect
            </Button>
          </>
        )}
        <ThemeToggle/>
        {/* <ConnectButton /> */}
      </div>
    </div>
  );
};

export default Header;