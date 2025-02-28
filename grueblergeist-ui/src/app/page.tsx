"use client";

import { useRef, useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

export default function Home() {
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [strictEnforcement, setStrictEnforcement] = useState(false);
  const [thresholdData, setThresholdData] = useState([]);
  const [snarkData, setSnarkData] = useState([]);
  const [topicMatch, setTopicMatch] = useState(50);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Command history for text input
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch initial chat log
  useEffect(() => {
    async function fetchMessages() {
      try {
        const res = await axios.get("http://127.0.0.1:5001/api/chat-log");
        setMessages(res.data);
      } catch (error) {
        console.error("⚠️ Error fetching chat log:", error);
      }
    }
    fetchMessages();
  }, []);

  // Fetch threshold & snark data for live graph
  useEffect(() => {
    async function fetchThresholdData() {
      try {
        const res = await axios.get(
          "http://127.0.0.1:5001/api/threshold-history",
        );
        setThresholdData(res.data.threshold);
        setSnarkData(res.data.snark);
      } catch (error) {
        console.error("⚠️ Error fetching threshold history:", error);
      }
    }

    fetchThresholdData();
    const interval = setInterval(fetchThresholdData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Fetch topic match percentage
  useEffect(() => {
    async function fetchTopicScore() {
      try {
        const res = await axios.get("http://127.0.0.1:5001/api/topic-score");
        setTopicMatch(res.data.topic_score);
      } catch (error) {
        console.error("⚠️ Error fetching topic score:", error);
      }
    }

    fetchTopicScore();
    const interval = setInterval(fetchTopicScore, 3000);
    return () => clearInterval(interval);
  }, []);

  async function sendMessage() {
    if (!userInput.trim()) return;

    try {
      const res = await axios.post("http://127.0.0.1:5001/api/chat", {
        message: userInput,
        strictEnforcement: strictEnforcement,
      });

      setMessages((prevMessages) => [
        ...prevMessages,
        { user: userInput },
        { assistant: res.data.reply },
      ]);

      // Update command history (limit to last 100 entries)
      setCommandHistory((prev) => {
        const updatedHistory = [userInput, ...prev].slice(0, 100);
        return updatedHistory;
      });
      setHistoryIndex(-1); // Reset index
      setUserInput("");
    } catch (error) {
      console.error("⚠️ Error sending message:", error);
    }
  }

  // Handle Up/Down Arrow Key for Command History
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowUp") {
      if (historyIndex + 1 < commandHistory.length) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setUserInput(commandHistory[newIndex]);
      }
    } else if (e.key === "ArrowDown") {
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setUserInput(commandHistory[newIndex]);
      } else {
        setHistoryIndex(-1);
        setUserInput("");
      }
    }
  }

  const chartData = {
    labels: thresholdData.map((_, i) => i),
    datasets: [
      {
        label: "Patience Threshold",
        data: thresholdData,
        borderColor: "blue",
        borderWidth: 2,
        fill: false,
      },
      {
        label: "Snark Level",
        data: snarkData,
        borderColor: "red",
        borderWidth: 2,
        fill: false,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    scales: {
      x: { type: "linear" },
      y: { type: "linear", min: 0, max: 1 },
    },
  };

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
        <label className="text-neonPink">Strict Mode?</label>
        <input
          type="checkbox"
          checked={strictEnforcement}
          onChange={(e) => setStrictEnforcement(e.target.checked)}
        />
      </div>

      {/* Live Graph: Patience vs. Snark */}
      <div className="w-[800px] mb-5">
        <h2 className="text-2xl text-neonBlue">Threshold & Snark Over Time</h2>
        <Line data={chartData} options={chartOptions} />
        <p className="text-white">Topic Match: {topicMatch.toFixed(1)}%</p>
      </div>

      {/* Chat Window */}
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

      {/* Chat Input & Send Button */}
      <div className="flex mt-3 w-[800px]">
        <input
          className="flex-1 bg-black border border-neonPink text-neonPink p-2 rounded-l-lg focus:ring-2 focus:ring-neonPink"
          type="text"
          placeholder="Say something..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={handleKeyDown}
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
