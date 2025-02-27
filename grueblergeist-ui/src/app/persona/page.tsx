"use client";

import { useEffect, useState } from "react";
import axios from "axios";

export default function Persona() {
  const [persona, setPersona] = useState(null);

  useEffect(() => {
    async function fetchPersona() {
      try {
        const res = await axios.get("http://127.0.0.1:5001/api/persona");
        setPersona(res.data);
      } catch (error) {
        console.error("Error fetching persona:", error);
      }
    }

    fetchPersona();
  }, []);

  return (
    <div className="min-h-screen bg-blackBg text-white font-mono p-10">
      <h1 className="text-4xl text-neonPink">🧠 AI Persona</h1>

      {persona ? (
        <div className="border border-neonPink p-4 w-[600px] rounded-lg">
          <p>
            <strong>Avg Sentence Length:</strong> {persona.avg_sentence_length}
          </p>
          <p>
            <strong>Response Style:</strong> {persona.response_style}
          </p>
          <p>
            <strong>Most Common Words:</strong>{" "}
            {persona.most_common_words?.join(", ")}
          </p>
        </div>
      ) : (
        <p>Loading AI persona...</p>
      )}
    </div>
  );
}
