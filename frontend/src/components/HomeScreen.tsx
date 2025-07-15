import React from "react";
import ChatWithEditor from "@/components/ChatWithEditor";
import Header from "./Header";

const HomeScreen = () => {

  return (
    <div className="relative min-h-screen bg-gray-100 dark:bg-[#070E1B] text-gray-900 dark:text-white">
      <Header />
      <div className="w-full mt-8 p-5 mx-auto">
        <ChatWithEditor />
      </div>
    </div>
  );
};

export default HomeScreen; 