# Grüblergeist: A Self-Evolving AI Assistant

**Grüblergeist** is an advanced, self-evolving chat assistant designed to mimic user behavior, improve its own code, and provide intelligent, engaging conversations. It is built with **Python 3.10+ (future-ready for 3.13)** and integrates **OpenAI's GPT models or local models like Ollama**.

This project was born from the idea of creating a **"Virtual You"**—a chatbot that not only chats but also **evolves its own personality, response style, and even refines its own code** over time.

---

## **Core Features**
✅ **Mimics Your Personality & Writing Style** (Extracted from past conversations)  
✅ **Self-Evolves via OpenAI API** (Refactors its own source code using GPT-4)  
✅ **CLI + Web UI** (Rich CLI for terminal users, Flask-based Web Interface)  
✅ **PostgreSQL for Memory** (Stores past chats, user preferences, and system evolution history)  
✅ **Dynamic Prompts** (No static lists! AI generates its own variation each time)  
✅ **Supports OpenAI & Local Models** (Choose between API-based GPT or local Ollama models)  
✅ **Configurable & Extendable** (JSON-based configuration, modular structure)

---

## **Project Structure**
```
grueblergeist/
├── assistant/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── db.py              # PostgreSQL ORM and conversation storage
│   ├── llm_client.py      # OpenAI & Ollama API interface
│   ├── chat_assistant.py  # Main chat engine, now with personality emulation
│   ├── cli.py             # Rich-based command-line interface
│   ├── web.py             # Flask-based web UI
│   ├── evolve.py          # Self-modifying AI logic
├── main.py                # Entry point for CLI/Web modes
├── config.json            # Configuration file
├── requirements.txt       # Dependencies
├── setup.sh               # Install script (virtualenv, Docker, PostgreSQL)
├── analyze_chat.py        # Extracts user language patterns from past chats
├── convert_chatgpt_export.py  # Converts exported ChatGPT data to training format
├── README.md              # (This file)
```

---

## **Making Grüblergeist Mimic You**
### **1. Extract Your Writing Style**
To make Grüblergeist sound like you, we **analyze your past conversations** for:
- **Tone** (Casual? Technical? Witty?)
- **Common Phrases** (Signature expressions)
- **Response Structure** (Concise vs. Detailed)
- **Topic Preferences** (IoT, AI, Sci-Fi, Humor, etc.)
- **Decision-Making Style** (Pragmatic? Theoretical?)

Run:
```bash
python3 analyze_chat.py --file /mnt/data/user_chat_history.md
```
This will generate a **`user_style_profile.json`** that Grüblergeist will use.

### **2. Integrate Your Style into the AI**
Grüblergeist will now **load your response style** and use it in every conversation. The `chat_assistant.py` module was updated to:
- Load your **`user_style_profile.json`**.
- Adjust responses dynamically to **mimic your phrasing, tone, and common phrases**.

---

## **How Grüblergeist Evolves Itself**
Grüblergeist can **rewrite its own source code** using **GPT-4**. This means:
- It can **refactor functions** for better performance.
- It can **add new features** based on instructions.
- It can **keep logs of all past versions** for rollback.

### **Example: Self-Evolving Command**
```bash
./main.py --mode evolve --source assistant/cli.py --output assistant/cli_v2.py   --instructions "Refactor the CLI to support interactive help commands."
```

To **let the AI evolve itself**:
```bash
./main.py --mode evolve-self --source assistant/evolve.py --output assistant/evolve_v2.py
```

---

## **Installation & Setup**
### **1. Clone the Repository**
```bash
git clone https://github.com/yourusername/grueblergeist.git
cd grueblergeist
```

### **2. Run Setup**
```bash
chmod +x setup.sh
./setup.sh
```
This will:
- Install dependencies (`pip install -r requirements.txt`)
- Start a **PostgreSQL Docker container**
- Set up your Python environment

### **3. Configure OpenAI API Key**
If using OpenAI:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### **4. Start Grüblergeist**
#### **CLI Mode**
```bash
./main.py --mode cli
```
#### **Web Mode**
```bash
./main.py --mode web
```
Visit **http://127.0.0.1:5000** to chat in the browser.

---

## **Debugging & Fixes**
### **Docker Issues**
If PostgreSQL doesn’t start, try:
```bash
sudo systemctl restart docker
```
If you see **kernel module mismatches**, check:
```bash
ls /usr/lib/modules/"$(uname -r)"
```

### **Fix OpenAI API Errors**
If you see:
```
You tried to access openai.ChatCompletion, but this is no longer supported.
```
Update your `llm_client.py`:
```python
client = openai.OpenAI()
response = client.chat.completions.create(model="gpt-4", messages=messages)
```
And upgrade OpenAI:
```bash
pip install --upgrade openai
```

---

## **Future Enhancements**
🔹 **Train a Fine-Tuned GPT Model** with user-specific data  
🔹 **Vector Memory for Context Awareness**  
🔹 **Real-time Evolution Monitoring** (Graphing improvements over time)  
🔹 **Multi-Agent Mode** (Multiple AI personalities)  

---

## **Final Thoughts**
Grüblergeist is an **AI that writes itself**, designed to become **more like you** with each conversation. It is:
- **Extensible** 🚀 – Modify prompts, train models, and add new logic.  
- **Self-Improving** 🔁 – Uses GPT to rewrite and optimize itself.  
- **Personalized** 🤖 – Mimics your writing style, humor, and decision-making.

### **Want to Make it Even More You?**
Train a **fine-tuned model** with your chat history. This will make Grüblergeist **even more precise** in its mimicry.

---

## **License**
[MIT License](https://opensource.org/licenses/MIT)  
Feel free to contribute, modify, and make Grüblergeist **your own.**

---

**Welcome to the next level of AI self-improvement. Enjoy Grüblergeist!** 🚀👻
