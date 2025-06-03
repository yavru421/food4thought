from PIL import Image
import requests
import io
import base64
import numpy as np
from groq import Groq
import logging

def preprocess_image(image: Image.Image) -> bytes:
    """Preprocess the image for analysis."""
    # Resize image to a standard size
    image = image.resize((224, 224))
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def analyze_image(image_bytes: bytes, api_key: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> dict:
    """Send the image to the Groq API for analysis and return the response."""
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this meal image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()

def extract_nutrition_info(api_response: dict) -> dict:
    """Extract nutritional information from the API response."""
    # Assuming the response contains a 'choices' field with the analysis
    if 'choices' in api_response and len(api_response['choices']) > 0:
        return api_response['choices'][0]['message']['content']
    return {}

def analyze_meal_image(image: Image.Image, api_key: str, model: str = "meta-llama/llama-4-scout-17b-16e-instruct", prompt: str = "Analyze this meal image.") -> dict:
    import io
    import re
    buf = io.BytesIO()
    image.save(buf, format='JPEG')
    image_bytes = buf.getvalue()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    prompt = prompt.strip() + "\nReturn the result as a JSON object with keys: calories, protein, carbohydrates, fats, fiber, vitamins, minerals."
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ],
            }],
            model=model
        )
        content = chat_completion.choices[0].message.content
        logging.info(f"Raw Groq vision model output: {content}")
        if content is None:
            return {"error": "No content returned from Groq vision model."}
        # Try to extract JSON code block
        import json
        match = re.search(r'```json\s*(\{[\s\S]+?\})\s*```', content)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e:
                logging.error(f"Failed to parse extracted JSON: {e}")
        # Fallback: try to parse any JSON object in the text
        match = re.search(r'(\{[\s\S]+?\})', content)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception as e:
                logging.error(f"Failed to parse fallback JSON: {e}")
        # Fallback: return the raw output for debugging
        return {"raw": content}
    except Exception as e:
        logging.exception(f"Error in analyze_meal_image: {e}")
        return {"error": str(e)}