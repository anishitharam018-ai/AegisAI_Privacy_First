import os
import json
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from google import genai

from masking import mask_sensitive_data

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

print("API KEY LOADED:", API_KEY[:6], "*****")

app = Flask(__name__)

# Initialize Gemini client
client = genai.Client(
    api_key=API_KEY,
    http_options={"api_version": "v1"}
)

def analyze_with_gemini(masked_text, primary_model="models/gemini-2.5-pro", fallback_model="models/gemini-2.5-flash", max_retries=2):
    prompt = f"""
You are an AI safety assistant.

Analyze the following message ONLY for scam-related signals:
- urgency or pressure tactics
- unrealistic rewards
- payment requests
- threatening language

STRICT RULES:
- Do NOT infer masked data
- Do NOT reconstruct personal information
- Focus only on language patterns

Respond ONLY in this JSON format:
{{
  "risk_level": "Low | Medium | High",
  "reasons": ["reason 1", "reason 2"],
  "user_advice": "short advice"
}}

Message:
{masked_text}
"""

    def _call_model(model_name):
        return client.models.generate_content(model=model_name, contents=prompt)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = _call_model(primary_model)
            break
        except Exception as e:
            last_error = e
            # If quota/exhausted or rate limit, try once after a short backoff
            msg = str(e).lower()
            if "resource_exhausted" in msg or "quota" in msg or "429" in msg or "rate" in msg:
                import time
                backoff = 1 + attempt * 2
                time.sleep(backoff)
                continue
            # For other errors, stop retrying
            break
    else:
        # attempts exhausted
        response = None

    # If primary failed with quota or rate-limit, try fallback model once
    if response is None and last_error is not None:
        try:
            response = _call_model(fallback_model)
        except Exception as e2:
            # return combined error messages for debugging
            return f"Primary error: {last_error}\nFallback error: {e2}"

    if response is None:
        return str(last_error) if last_error is not None else "No response from GenAI client"

    # Response parsing: prefer `.text`, then `.content`, then string conversion
    raw = None
    if hasattr(response, "text") and response.text:
        raw = response.text
    elif hasattr(response, "content") and response.content:
        raw = response.content
    else:
        raw = str(response)

    # Clean common code-fence wrappers (```json ... ``` or ``` ... ```) and decode bytes
    if isinstance(raw, bytes):
        raw = raw.decode(errors="ignore")
    raw = raw.strip()
    # Remove triple-backtick fences and optional language tag
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    # Try to load JSON directly
    try:
        parsed = json.loads(raw)
        return parsed
    except Exception:
        # Attempt to extract the first {...} JSON object in the text
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                parsed = json.loads(m.group(0))
                return parsed
            except Exception:
                pass

    # If parsing fails, return the cleaned raw text for debugging
    return raw

def analyze_message(original_text):
    mask_result = mask_sensitive_data(original_text)
    masked_text = mask_result["masked_text"]
    detected_items = mask_result["detected_items"]
    ai_result = analyze_with_gemini(masked_text)
    return {
        "user_view": original_text,
        "ai_view": masked_text,
        "detected_sensitive_data": detected_items,
        "analysis": ai_result
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request"}), 400
    result = analyze_message(data['message'])
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
