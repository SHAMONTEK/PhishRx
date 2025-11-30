# components/privacy_detector.py
import re

# // ==== [TYPES] Privacy Finding Patterns =====================================
# // Responsibility: Define the regex patterns for different types of PII/sensitive data.
# // Connections:   Used by the analyze_text_privacy function.
# // Notes:         Patterns are ordered from more specific (like email) to more general.
# //                This is not a foolproof validator, but a "detector" for risky text.
# // ============================================================================
PRIVACY_PATTERNS = {
    # Matches common email formats.
    'PII_EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    
    # Matches various phone formats (e.g., (123) 456-7890, 123-456-7890, +1...)
    'PII_PHONE': r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}',
    
    # Matches 13-16 digit numbers, potentially with spaces/dashes.
    # This is a broad net and may have false positives (e.g., order numbers).
    'PII_CREDIT_CARD': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b|\b\d{13,16}\b',
    
    # Matches common sensitive keywords.
    # Uses re.IGNORECASE flag in the function.
    'SENSITIVE_KEYWORD': r'\b(password|ssn|social security|account number|username|login|verify your account)\b'
}


# // ==== [E1] analyze_text_privacy ============================================
# // Responsibility: Scan raw text using regex to find and tag potential PII.
# // Connections:   Called by PhishRxApp.__init__ to analyze OCR text.
# // Notes:         Returns a list of dictionaries, one for each finding.
# //                Does not remove duplicates; finding "password" 3 times is 3 findings.
# // ============================================================================
def analyze_text_privacy(ocr_text: str) -> list[dict]:
    """
    Analyzes raw OCR text for potential privacy-sensitive information
    using a predefined set of regex patterns.

    Args:
        ocr_text: The string content from the OCR scan.

    Returns:
        A list of dictionaries, where each dict represents a single finding.
        Example: [{'type': 'PII_EMAIL', 'text': 'user@example.com'}]
    """
    if not ocr_text:
        return []

    findings = []
    
    # Use a set to avoid adding the exact same text match for the same type
    # (e.g., if a complex regex matches "123-456-7890" and "456-7890")
    found_matches = set()

    for finding_type, pattern in PRIVACY_PATTERNS.items():
        
        # Set case-insensitivity only for keywords
        flags = re.IGNORECASE if finding_type == 'SENSITIVE_KEYWORD' else 0
        
        try:
            matches = re.finditer(pattern, ocr_text, flags=flags)
            
            for match in matches:
                match_text = match.group(0).strip()
                
                # Create a unique key for this finding
                match_key = (finding_type, match_text)
                
                if match_text and match_key not in found_matches:
                    findings.append({
                        'type': finding_type,
                        'text': match_text
                    })
                    found_matches.add(match_key)
                    
        except Exception as e:
            print(f"⚠️ Error during regex for {finding_type}: {e}")

    return findings


# // ==== [UTIL] Standalone Test Block =========================================
# // Responsibility: Test the detector function if this file is run directly.
# // Connections:   None (only runs for __main__).
# // Notes:         Provides a simple way to validate new regex patterns.
# // ============================================================================
if __name__ == "__main__":
    print("--- Running Privacy Detector Standalone Test ---")
    
    test_text = """
    Hello,
    
    Your account is at risk! Please reset your password at http://fake-link.com
    To verify your account, reply with your username and full password.
    
    Also, confirm your phone is (123) 456-7890 and your email is test_user@phishing.net.
    
    We may need your SSN later.
    - Support Team (contact: support@real.com)
    
    Card: 4111-2222-3333-4444
    """
    
    detected_findings = analyze_text_privacy(test_text)
    
    if detected_findings:
        print(f"\n✅ Found {len(detected_findings)} potential PII/Sensitive items:")
        for i, item in enumerate(detected_findings):
            print(f"  {i+1}. Type: {item['type']}, Text: \"{item['text']}\"")
    else:
        print("\nℹ️ No items found.")

    print("\n--- Test Complete ---")