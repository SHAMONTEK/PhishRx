# PhishRx  

PhishRx is a real-time phishing detection tool that scans screenshots, extracts text with OCR, and uses AI models to detect scams, suspicious links, and phishing attempts.  

---

## 🚀 Features
- 📸 One-click **screenshot scan**
- 🧠 AI-powered classification of safe / suspicious / scam
- 🔎 OCR text extraction
- ⚡ Real-time severity verdicts (Safe, Suspicious, Scam)
- 📂 Scan history with confidence scores
- 🤖 “Learn Why” assistant to explain threats
- 💾 Save & Report options

---

## 🛠️ Setup

### 1. Clone the Repository
```bash
git clone https://github.com/SHAMONTEK/PhishRx.git
cd PhishRx
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# On Windows: .venv\\Scripts\\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration

Environment variables are required for API access.  

1. Copy `.env.example` → `.env`  
2. Edit `.env` with your keys:  

```env
HF_API_KEY=your_huggingface_key_here
OPENAI_API_KEY=your_openai_key_here
```

*(Tip: never commit your `.env` file — keep it local.)*

---

## ▶️ Run the App
```bash
python phisher_lite.py
```

This will launch the PhishRx app with the tray icon and scanning features.  

---

## 📖 Usage
1. Click the tray icon → **Scan Screen**  
2. Wait for OCR + AI analysis  
3. See the result window: ✅ Safe / ⚠️ Suspicious / ❌ Scam  
4. Use **Learn Why**, **Save**, or **Report** buttons as needed.  

---

## 🧩 Project Structure
```
components/        # Core logic modules
utils.py           # Helper functions
phisher_lite.py    # Main launcher script
phisher_ai_gui.py  # GUI logic
scan_history.csv   # Saved scan results
```

---

## 📜 License
MIT License – Free to use and modify.  

---

## ✨ Author
Created by **ShaMonte Knight**  
