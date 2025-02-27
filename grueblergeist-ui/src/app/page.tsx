"use client";

import { useRef, useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import Link from "next/link";

export default function Home() {
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [, forceRender] = useState(0); // Force a re-render if needed
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to the bottom whenever messages change
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Fetch existing chat messages on page load
  useEffect(() => {
    async function fetchMessages() {
      try {
        const res = await axios.get("http://127.0.0.1:5001/api/chat-log");
        console.log("📩 Initial Chat Log:", res.data);
        setMessages(res.data);
      } catch (error) {
        console.error("⚠️ Error fetching chat log:", error);
      }
    }

    fetchMessages();
  }, []);

  // Send a message to Flask API and update the chat log
  async function sendMessage() {
    if (!userInput.trim()) return;

    console.log("📨 Sending message:", userInput);

    try {
      const res = await axios.post("http://127.0.0.1:5001/api/chat", {
        message: userInput,
      });

      console.log("📩 Flask Response:", res.data);

      if (res.status !== 200 || !res.data || !res.data.reply) {
        console.error("🚨 Flask API Error:", res);
        return;
      }

      // Add two entries:
      // 1) A user message object
      // 2) An assistant message object
      setMessages((prev) => {
        const updated = [
          ...prev,
          { user: userInput },
          { assistant: res.data.reply },
        ];
        console.log("📜 Updated Messages in State Setter:", updated);
        return updated;
      });

      // Force a re-render just in case
      forceRender((prev) => prev + 1);

      // Clear the input
      setUserInput("");
    } catch (error) {
      console.error("⚠️ Error sending message:", error);
    }
  }

  return (
    <div className="min-h-screen bg-blackBg text-white font-mono p-10 flex flex-col items-center">
      <h1 className="text-4xl text-neonPink">Grüblergeist</h1>

      {/* Link to AI Persona Page */}
      <Link
        href="/persona"
        className="text-neonBlue underline hover:text-neonPink transition-all mb-5"
      >
        View AI Persona
      </Link>

      {/* Chat Window */}
      <div className="border border-neonPink p-4 h-[500px] w-[800px] overflow-y-auto rounded-lg">
        {messages.length === 0 ? (
          <p className="text-gray-400">No messages yet.</p>
        ) : (
          messages.map((msg, index) => {
            // We decide if this is a user or AI message based on property presence
            const isUserMsg = msg.user !== undefined;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`chat-bubble p-3 rounded-md max-w-xl ${
                  isUserMsg ? "user-bubble text-black" : "ai-bubble text-black"
                }`}
              >
                <strong>{isUserMsg ? "You" : "Grüblergeist"}:</strong>{" "}
                {isUserMsg ? msg.user : msg.assistant}
              </motion.div>
            );
          })
        )}
        {/* Always keep this anchor div at the bottom */}
        <div ref={chatEndRef}></div>
      </div>

      {/* Chat Input */}
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
