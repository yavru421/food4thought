# Groq API Usage Information (from streamlit_app.py)

This document outlines how Groq API calls are implemented in `streamlit_app.py`, including models and request structures, to facilitate reuse in other Python applications.

## 1. Groq Client Initialization

The Groq Python client is initialized using an API key. This is typically handled by the `initialize_groq_client` function in the Streamlit app.

**Relevant Python Code Snippet:**
```python
from groq import Groq

# Example initialization
# api_key = "YOUR_GROQ_API_KEY"
# client = Groq(api_key=api_key)

# In streamlit_app.py, it's stored in st.session_state.groq_client
# client = st.session_state.groq_client
```

## 2. Text-based Q&A / Chat Completions

Text-based interactions with the Groq API are primarily handled via the `client.chat.completions.create` method.

**Key Functions in `streamlit_app.py`**:
*   `ask_groq(question, document_text, api_key)`: Processes text Q&A. While the exact model isn't specified within this function's snippet, `handle_upload_and_qa` associates its output with the model `llama3-8b-8192`.
*   `ask_groq_with_model(question, document_text, api_key, model)`: Processes text Q&A using a specified model.

**Conceptual API Call Structure**:
The actual API call within these functions (partially shown in provided snippets) would look something like this:
```python
# Assuming 'client' is the initialized Groq client
# Assuming 'prompt' is the constructed message including document context and question

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    model="SELECTED_MODEL_NAME" # e.g., "llama3-8b-8192" or a model passed as an argument
)
response = chat_completion.choices[0].message.content
```

**Models Used for Text**:
*   **General Text Q&A (via `handle_upload_and_qa` calling `ask_groq`)**:
    *   `llama3-8b-8192`
*   **Advanced Reasoning Chatbot (user selectable, passed to `ask_groq_with_model`)**:
    *   `compound-beta`
    *   `compound-beta-mini`
    *   `deepseek-r1-distill-llama-70b`

**Note on Document Handling**:
For large documents, the `split_text_into_chunks` function is used to break down text. The `max_tokens_per_chunk` is often set around `5000`. API calls are then made per chunk, and responses are aggregated.

## 3. Vision Q&A (Image Analysis)

Vision-based Q&A also uses the `client.chat.completions.create` method but requires a specific message structure to include image data.

**Key Function in `streamlit_app.py`**: `ask_groq_vision(question, image_bytes, api_key, model)`

**API Call Structure**:
The image is base64 encoded and sent as part of the message content.
```python
import base64
# from groq import Groq # Assuming client is already initialized

# client = Groq(api_key=api_key) # Initialization
# image_bytes = ... # Your image data in bytes
# question = "Your question about the image"

base64_image = base64.b64encode(image_bytes).decode('utf-8')

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {
                        # Mime type might vary (e.g., image/png, image/jpeg)
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    model="SELECTED_VISION_MODEL_NAME" # e.g., "meta-llama/llama-4-scout-17b-16e-instruct"
)
response = chat_completion.choices[0].message.content
```

**Models Used for Vision**:
*   **Primary Vision Model (used in `ask_groq_vision`, `handle_upload_and_qa`, `vision_qa_section`)**:
    *   `meta-llama/llama-4-scout-17b-16e-instruct`
*   The docstring for `ask_groq_vision` also mentions that the model can be 'scout' or 'maverick', suggesting `meta-llama/llama-4-maverick-17b-16e-instruct` could be an alternative, though 'scout' is the one explicitly implemented and used.

## 4. Using Groq API from Client-side JavaScript/TypeScript (No Backend)

It is possible to call the Groq API directly from a client-side JavaScript or TypeScript app (such as React or plain HTML/JS) hosted on GitHub Pages or similar static hosting. The standard, safe approach is:

* **User-provided API Key:** Prompt each user to enter their own Groq API key in an input field. Do NOT hard-code your own key in the frontend code.
* **Direct API Calls:** Use `fetch` or similar browser APIs to call Groq endpoints directly from the browser, passing the user's API key in the `Authorization` header.
* **Security Note:** This is safe for demos and open tools because each user is responsible for their own key and quota. Never expose a privileged or paid key in public code.
* **Limitations:** Some advanced features (like file uploads or large payloads) may be limited by browser CORS or Groq's API policies. Always check Groq's docs for client-side compatibility.


```typescript
fetch('https://api.groq.com/openai/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${userApiKey}`,
  },
  body: JSON.stringify({
    model: 'llama3-8b-8192',
    messages: [
      { role: 'user', content: prompt }
    ]
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

This approach allows you to build 100% client-side Groq-powered apps (React, TypeScript, etc.) with no backend, as long as each user provides their own API key.


### Can you do this in Streamlit?

* **No, not fully client-side.** Streamlit is a Python framework that runs on a server (locally or in the cloud). It cannot run 100% in the browser like a static React app.
* **Streamlit always requires a Python backend** (even if hosted for free on Streamlit Community Cloud). You cannot deploy a Streamlit app to GitHub Pages or similar static hosting.
* **If you want 100% client-side, use React/TypeScript or plain HTML/JS.**

## Summary of Key API Interactions:

*   **Authentication**: Via API key passed to `Groq()` constructor.
*   **Endpoint Abstraction**: The Groq Python SDK (`groq` library) handles the specific API endpoints. Interactions are done through methods of the `client` object, primarily `client.chat.completions.create(...)`.
*   **Payloads**:
    *   Text: JSON with `messages` array (role, content).
    *   Vision: JSON with `messages` array, where content for the user role is an array containing text and image (base64 encoded with data URL).

This information should serve as a good reference for your other projects.
