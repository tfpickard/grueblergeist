"use client";

import { useRef, useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import Link from "next/link";

export default function Home() {
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [strictEnforcement, setStrictEnforcement] = useState(false); // NEW
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // auto-scroll
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    // fetch existing chat log
    fetchMessages();
  }, []);

  async function fetchMessages() {
    try {
      const res = await axios.get("http://127.0.0.1:5001/api/chat-log");
      setMessages(res.data);
    } catch (err) {
      console.error("Error fetching chat log:", err);
    }
  }

  async function sendMessage() {
    if (!userInput.trim()) return;

    try {
      // POST to the Flask API, including strictEnforcement as a parameter
      const res = await axios.post("http://127.0.0.1:5001/api/chat", {
        message: userInput,
        strictEnforcement: strictEnforcement, // pass boolean
      });

      // handle the response
      setMessages((prev) => [
        ...prev,
        { user: userInput },
        { assistant: res.data.reply },
      ]);
      setUserInput("");
    } catch (error) {
      console.error("Error sending message:", error);
    }
  }

  return (
    <div className="min-h-screen bg-blackBg text-white font-mono p-10 flex flex-col items-center">
      <h1 className="text-4xl text-neonPink">Grüblergeist</h1>

      <Link
        href="/persona"
        className="text-neonBlue underline hover:text-neonPink transition-all mb-5"
      >
        View AI Persona
      </Link>

      {/* Strict Enforcement Toggle */}
      <div className="mb-3 flex items-center gap-2">
        <label className="text-neonPink">Strict Enforcement?</label>
        <input
          type="checkbox"
          checked={strictEnforcement}
          onChange={(e) => setStrictEnforcement(e.target.checked)}
        />
      </div>

      <div className="border border-neonPink p-4 h-[500px] w-[800px] overflow-y-auto rounded-lg">
        {messages.length === 0 ? (
          <p className="text-gray-400">No messages yet.</p>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.user !== undefined;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`chat-bubble p-3 rounded-md max-w-xl ${
                  isUser ? "user-bubble text-black" : "ai-bubble text-black"
                }`}
              >
                <strong>{isUser ? "You" : "Grüblergeist"}:</strong>{" "}
                {msg.user || msg.assistant}
              </motion.div>
            );
          })
        )}
        <div ref={chatEndRef}></div>
      </div>

      {/* Input and Send */}
      <div className="flex mt-3 w-[800px]">
        <input
          className="flex-1 bg-black border border-neonPink text-neonPink p-2 rounded-l-lg focus:ring-2 focus:ring-neonPink"
          type="text"
          placeholder="Say something..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          className="bg-neonPink text-black px-4 py-2 rounded-r-lg hover:bg-neonBlue transition-all"
          onClick={sendMessage}
        >
          Send
        </button>
      </div>
    </div>
  );
}
