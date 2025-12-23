import re

def mask_sensitive_data(text):
    """
    Detects and masks sensitive user information
    before sending data to AI systems.
    """

    masked_text = text
    detected_items = []

    # Phone numbers (10-digit)
    phone_pattern = r'\b\d{10}\b'
    phones = re.findall(phone_pattern, masked_text)
    if phones:
        detected_items.append("Phone Number")
        masked_text = re.sub(phone_pattern, "[MASKED_PHONE]", masked_text)

    # Email IDs
    email_pattern = r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
    emails = re.findall(email_pattern, masked_text)
    if emails:
        detected_items.append("Email ID")
        masked_text = re.sub(email_pattern, "[MASKED_EMAIL]", masked_text)

    # UPI IDs
    upi_pattern = r'\b[\w\.-]+@[\w]+\b'
    upis = re.findall(upi_pattern, masked_text)
    if upis:
        detected_items.append("UPI ID")
        masked_text = re.sub(upi_pattern, "[MASKED_UPI]", masked_text)

    return {
        "original_text": text,
        "masked_text": masked_text,
        "detected_items": list(set(detected_items))
    }
    
if __name__ == "__main__":
    sample_text = "You won ₹50,000! Call 9876543210 or pay via test@upi"
    result = mask_sensitive_data(sample_text)
    print(result)


