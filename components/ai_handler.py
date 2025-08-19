import requests
import os
import time

# --- CONFIG ---
HF_API_KEY = os.getenv("HF_API_KEY", "API_HERE") 
CLASSIFIER_MODEL_ID = "ealvaradob/bert-finetuned-phishing"
GENERATOR_MODEL_ID = "google-t5/t5-large" 

# --- HEADERS ---
HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

# --- CLASSIFY FUNCTION ---
def classify_phishing(text):
    """
    Analyzes text using the Hugging Face classification model.
    Handles various response formats and finds the label with the highest score.
    """
    if not text:
        return "Error", 0
        
    payload = {"inputs": text}
    url = f"https://api-inference.huggingface.co/models/{CLASSIFIER_MODEL_ID}"
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=20)
        response.raise_for_status() 
        data = response.json()
        print("Raw classification response:", data)

        if isinstance(data, dict) and 'error' in data:
            print(f"API Error in classification: {data['error']}")
            return "Error", 0

        if isinstance(data, list) and data:
            results = data[0] if isinstance(data[0], list) else data
            
            if not results or not all(isinstance(item, dict) for item in results):
                 print("Unexpected result format inside list:", results)
                 return "Error", 0

            top_result = max(results, key=lambda x: x.get('score', 0))
            label = top_result.get("label", "Error")
            if label.lower() == 'benign':
                label = 'not phishing'
            return label, top_result.get("score", 0)

        print("Unexpected classification format:", data)
        return "Error", 0
    except requests.exceptions.Timeout:
        print("Error: Classification request timed out.")
        return "Error", 0
    except requests.exceptions.RequestException as e:
        print(f"Error during classification request: {e}")
        return "Error", 0


# --- GENERATOR FUNCTION (FINAL) ---
def generate_explanation(user_input, severity, reasons, ocr_text=""):
    """
    Generates a helpful explanation using the Hugging Face generator model.
    Handles API errors, model loading states, and timeouts gracefully.
    """
    reason_text = ", ".join(reasons) if reasons else "None identified"
    emotion_tag = detect_emotion(ocr_text)
    if emotion_tag:
        reason_text += f", Emotional Tone: {emotion_tag}"

    # --- FIX: Added 'Respond in English.' to the end of the task description ---
    prompt = (
        f"Context: A user is asking about a potentially malicious message.\n"
        f"Severity: {severity}\n"
        f"Detected Red Flags: {reason_text}\n"
        f"Message Text: '{ocr_text if ocr_text else 'No text provided.'}'\n"
        f"User's Question: '{user_input}'\n\n"
        f"Task: In a reassuring and professional tone, summarize the situation, "
        f"provide clear action steps, and ask if the user needs more help. Respond in English."
    )

    payload = { "inputs": prompt, "parameters": { "max_new_tokens": 150, "do_sample": True, "temperature": 0.7 } }
    url = f"https://api-inference.huggingface.co/models/{GENERATOR_MODEL_ID}"
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        print("Raw generator response:", result)

        if isinstance(result, dict) and 'error' in result:
            error_message = result['error']
            print(f"API Error in generation: {error_message}")
            if "loading" in error_message.lower():
                return "The AI assistant is starting up. Please try again in a moment. ⏳"
            return f"Error: The AI failed to generate a response. Details: {error_message}"

        # --- FIX: Check for 'translation_text' OR 'generated_text' ---
        generated_text = None
        if isinstance(result, list) and result:
            item = result[0]
            generated_text = item.get("generated_text") or item.get("translation_text")
        elif isinstance(result, dict):
            generated_text = result.get("generated_text") or result.get("translation_text")

        if generated_text:
            return generated_text.strip()
        else:
            print("Unexpected generator format:", result)
            return "Error: The AI returned an unexpected format."

    except requests.exceptions.Timeout:
        print("Generator request timed out. The model is likely still loading.")
        return "The AI assistant is taking a moment to start up. Please try your request again in a minute. ⏳"
    except requests.exceptions.RequestException as e:
        print(f"Error during generator request: {e}")
        return "Error: Could not connect to the AI assistant."


# --- EMOTION DETECTION ---
def detect_emotion(text):
    if not text:
        return None
    t = text.lower()
    if any(w in t for w in ["urgent", "immediately", "act now"]):
        return "Urgency"
    if any(w in t for w in ["congratulations", "you won", "claim"]):
        return "Excitement / Deception"
    if any(w in t for w in ["verify", "account", "security"]):
        return "Fear / Pressure"
    return None

# --- MAIN WRAPPER ---
def get_ai_response(user_input, severity, reasons, ocr_text=""):
    label, score = classify_phishing(ocr_text or user_input)

    if label.lower() == "phishing":
        verdict = f"⚠️ Phishing Detected ({score:.1%} confidence)"
    elif label.lower() == "not phishing":
         verdict = f"✅ Safe Message ({score:.1%} confidence)"
    else:
        verdict = "❌ Analysis Error"
        
    explanation = generate_explanation(user_input, severity, reasons, ocr_text)
    
    return f"{verdict}\n\n{explanation}"

# --- Example Call ---
if __name__ == "__main__":
    if not HF_API_KEY:
        print("Error: HF_API_KEY environment variable not set.")
        print("Please get a key from huggingface.co and set it in your environment.")
    else:
        print("Sending request to AI... (This may take a moment)")
        test_response = get_ai_response(
            user_input="Is this message safe?",
            severity="High",
            reasons=["Unusual link", "Spelling mistakes"],
            ocr_text="Click here immediately to verify your account and win a prize!"
        )
        print("\n--- FINAL OUTPUT ---")
        print(test_response)