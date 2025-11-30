# // ==== [ENGINE] Gemini AI Handler ===========================================
# // Responsibility: Connect to the Gemini API to get AI responses.
# // Connections:   Called by phisher_ai_gui.py. Replaces old Hugging Face logic.
# // Notes:         Uses the user-provided API key.
# // ============================================================================

import requests
import json
import time

# // ==== [STATE] API Configuration ============================================
# // Responsibility: Store the API key and endpoint.
# // ============================================================================

# --- User-provided API Key ---
API_KEY = "AIzaSyCAgjvnB0lF0K7iON4PUwV8Jjdyo4YLPCc" 

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"

# // ==== [E2] get_ai_response =================================================
# // Responsibility: Get a contextual AI response from the Gemini API.
# // Connections:   Called by the main GUI thread.
# // ============================================================================
# In ai_handler.py - FIX THE PROMPT:

def get_ai_response(user_input, reasons, severity, ocr_text):
    """
    Gets a contextual AI response focused on the ACTUAL SCREENSHOT ANALYSIS
    """
    
    # FIXED SYSTEM PROMPT:
    system_prompt = (
        "You are GUARDIAN AI, a screenshot analysis assistant. "
        "You ONLY analyze the OCR text from screenshots that users provide. "
        "You NEVER claim to see previous interactions, network data, or files. "
        "You ONLY discuss the specific screenshot content. "
        "Be helpful and specific about the visual/text content. "
        "If the user asks 'what do you see', refer ONLY to the OCR text from their screenshot. "
        "Never give generic security advice - only advice specific to the analyzed content."
    )
    
    # FIXED USER PROMPT:
    if "what do you see" in user_input.lower() or "what do you see" in user_input:
        prompt = (
            f"I am analyzing OCR text from your screenshot. Here's what I see:\n"
            f"SCREENSHOT TEXT: \"{ocr_text[:500]}...\"\n\n"
            f"Based on this text, I identified: {severity} risk level with these findings: {reasons}\n\n"
            f"What specific aspects of this text would you like me to explain?"
        )
    else:
        # Regular analysis prompt
        prompt = (
            f"Screenshot Analysis Results:\n"
            f"- Risk Level: {severity}\n" 
            f"- Findings: {reasons}\n"
            f"- OCR Text: \"{ocr_text[:300]}...\"\n\n"
            f"User Question: {user_input}\n\n"
            f"Answer based ONLY on the screenshot content above."
        )

    # ... rest of your existing code ...

    # --- 3. Construct the Payload ---
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.5, # Lowered for more direct, less "creative" responses
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 8192, # --- [FIX] Increased from 256 ---
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    # --- 4. Make the Request with Retry ---
    max_retries = 3
    delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=20)
            
            if response.status_code == 200:
                response_json = response.json()
                
                # --- [FIX] Safer response parsing ---
                if not response_json.get('candidates'):
                    # This can happen if the prompt is blocked
                    if response_json.get('promptFeedback'):
                        print(f"Gemini Error: Prompt blocked. Feedback: {response_json['promptFeedback']}")
                        return "Error: The analysis request was blocked for safety reasons."
                    return "Error: AI response was empty."

                candidate = response_json['candidates'][0]
                
                # Check for MAX_TOKENS or other non-ideal finish reasons
                finish_reason = candidate.get('finishReason')
                if finish_reason and finish_reason not in ["STOP", "MAX_TOKENS"]:
                    print(f"Gemini Warning: Non-stop finish reason: {finish_reason}")
                    # If it's a safety block, say so.
                    if finish_reason == "SAFETY":
                        return "Error: The AI's response was blocked for safety reasons."

                # Check for the actual text
                if (candidate.get('content') and
                    candidate['content'].get('parts') and
                    candidate['content']['parts'][0].get('text')):
                    
                    text = candidate['content']['parts'][0]['text']
                    return text.strip()
                else:
                    # This is the error you saw: "Unexpected response structure"
                    # It means the candidate is there, but 'parts' is missing,
                    # which can happen with MAX_TOKENS or other errors.
                    print(f"Gemini Error: Unexpected response structure: {response_json}")
                    return "Error: I received an incomplete response from the AI."

            else:
                print(f"Gemini Error: Status Code {response.status_code}, Response: {response.text}")
                if 400 <= response.status_code < 500:
                    return f"Error: API key or request issue ({response.status_code})."
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
        
        except requests.exceptions.RequestException as e:
            print(f"Gemini Error: Request failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                return f"Error: Could not connect to the AI service ({e})."
    
    return "Error: The AI service is currently unavailable after multiple attempts."

# // ==== [UTIL] Standalone Test ===============================================
# // Responsibility: Allow testing this file directly.
# // ============================================================================
if __name__ == "__main__":
    print("--- Testing Gemini AI Handler (Security Guard Persona) ---")
    
    # Test 1: Initial Analysis
    print("\n--- Test 1: Initial Analysis ---")
    test_reasons = ["Urgency", "Suspicious URL"]
    test_severity = "High"
    test_ocr = "URGENT! Your account is locked. Click http://bit.ly/fake to fix."
    response1 = get_ai_response("Initial analysis", test_reasons, test_severity, test_ocr)
    print(f"Response:\n{response1}")
    
    # Test 2: Follow-up
    print("\n--- Test 2: Follow-up Question ---")
    response2 = get_ai_response("What should I do now?", test_reasons, test_severity, test_ocr)
    print(f"Response:\n{response2}")
    
    print("\n--- Test Complete ---")