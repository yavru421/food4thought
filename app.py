import gradio as gr
from PIL import Image
import base64
import io
import logging
from groq import Groq
import os
import time
import requests
from functools import wraps
import matplotlib.pyplot as plt
import json # For parsing structured data from AI

# Set up logging
logging.basicConfig(level=logging.INFO)

AUDIO_DIR = "audio_outputs"
os.makedirs(AUDIO_DIR, exist_ok=True)

# --- Helper Functions (Image Conversion, API Calls) ---

def convert_image_to_base64(image: Image.Image) -> str:
    """Converts the image to base64."""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_bytes = buffered.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

def retry_on_rate_limit(max_retries=5, base_delay=2.0):
    """Decorator for exponential backoff on rate limits"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check for 429 status code in different ways
                    status_code = getattr(getattr(e, 'response', None), 'status_code', None)
                    if status_code == 429 or '429' in str(e) or 'rate limit' in str(e).lower():
                        logging.warning(f"Rate limit hit. Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        raise
            raise Exception("Max retries exceeded due to rate limits or other persistent errors.")
        return wrapper
    return decorator

@retry_on_rate_limit(max_retries=5, base_delay=2.0) # Decorator defined later
def call_groq_vision_api(api_key: str, model_name: str, prompt: str, base64_image: str) -> str:
    """
    Calls the Groq API for vision analysis.

    Args:
        api_key (str): The Groq API key.
        model_name (str): The name of the vision model.
        prompt (str): The prompt for the vision analysis.
        base64_image (str): The base64-encoded image.

    Returns:
        str: The result of the vision analysis.
    """
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
            model=model_name
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        error_message = f"Error calling Groq API: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f" (Status code: {e.response.status_code})"
        logging.error(error_message)
        return error_message

@retry_on_rate_limit(max_retries=5, base_delay=2.0)
def call_groq_chat_api(api_key: str, model_name: str, messages: list) -> str:
    """Calls a Groq chat model for Q&A or other text generation."""
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name # e.g., "llama3-8b-8192", "mixtral-8x7b-32768"
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling Groq Chat API: {str(e)}")
        # Check for rate limit specifically to allow retry decorator to work if it's a direct call
        status_code = getattr(getattr(e, 'response', None), 'status_code', None)
        if status_code == 429 or '429' in str(e) or 'rate limit' in str(e).lower():
            raise # Re-raise to be caught by retry_on_rate_limit if applied
        return "Error processing your question. Please try again."


# --- New Feature Functions: Charting and Q&A ---

def parse_nutrition_data_for_chart(report_text: str) -> dict | None:
    """
    Parses the nutrition report to extract macronutrient data for charting.

    Args:
        report_text (str): The nutrition report text.

    Returns:
        dict | None: The parsed chart data or None if parsing fails.
    """
    try:
        # Look for a specific marker in the text that contains JSON
        start_marker = "### CHART_DATA ###"
        end_marker = "### END_CHART_DATA ###"
        start_index = report_text.find(start_marker)
        end_index = report_text.find(end_marker)

        if start_index == -1 or end_index == -1:
            logging.warning("Chart data markers not found in the report.")
            return None

        json_str = report_text[start_index + len(start_marker):end_index].strip()
        data = json.loads(json_str)

        # Validate expected keys for basic chart
        required_keys = ["Calories", "Protein", "Carbs", "Fat"]
        if not all(key in data for key in required_keys):
            logging.warning(f"Missing one or more required keys for chart in JSON data: {data}")
            return None

        # Ensure values are numbers
        for key in required_keys:
            if not isinstance(data[key], (int, float)):
                logging.warning(f"Chart data value for {key} is not a number: {data[key]}")
                return None

        return {key: data[key] for key in required_keys}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON for chart data: {e}")
        return None
    except Exception as e:
        logging.error(f"Error parsing nutrition data for chart: {e}")
        return None

def generate_nutrition_chart(data: dict) -> plt.Figure | None:
    """Generates a bar chart for macronutrients using Matplotlib."""
    if not data:
        return None
    try:
        labels = list(data.keys())
        values = list(data.values())

        fig, ax = plt.subplots(figsize=(6, 4)) # Smaller figure size for Gradio
        bars = ax.bar(labels, values, color=['skyblue', 'lightgreen', 'salmon', 'gold'])
        ax.set_ylabel('Amount (grams/kcal)')
        ax.set_title('Macronutrient Overview')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add values on top of bars
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05 * max(values), round(yval,1), ha='center', va='bottom')

        plt.tight_layout()
        return fig
    except Exception as e:
        logging.error(f"Error generating nutrition chart: {e}")
        return None

def handle_follow_up_question(api_key: str, question: str, context: str, chat_model: str) -> str:
    """
    Handles a follow-up question using the initial nutrition report as context.
    """
    if not question.strip():
        return "Please ask a question."
    if not context.strip():
        return "No context (initial report) available for Q&A."

    messages = [
        {"role": "system", "content": "You are a helpful nutritional assistant. The user has received the following nutrition report about their meal. Answer their follow-up questions based on this report and your general nutritional knowledge. Keep answers concise and relevant to the report provided."},
        {"role": "user", "content": f"Here is the nutrition report:\n{context}\n\nMy question is: {question}"}
    ]
    
    answer = call_groq_chat_api(api_key, chat_model, messages)
    return answer

# --- Main Analysis Function ---

def analyze_meal_and_interact(image: Image.Image, api_key: str, vision_model_name: str) -> tuple[str, plt.Figure | None, str]:
    """
    Analyzes meal image, creates a nutrition chart, and prepares for Q&A.
    Returns: (nutrition_report_text, nutrition_chart_figure, initial_report_for_qa_context)
    """
    if not api_key:
        return "Please enter your Groq API key.", None, ""
    if image is None:
        return "Please upload a meal image.", None, ""

    base64_image = convert_image_to_base64(image)
    
    # Updated prompt to request structured data for charting
    prompt = """You are an expert nutritionist. Analyze the provided image of a meal in detail.
1. Identify all visible food items and ingredients.
2. For each item, estimate its quantity (e.g., grams, cups, pieces).
3. Based on these estimations, provide a detailed nutritional breakdown including:
    - Total Calories (kcal)
    - Protein (grams)
    - Carbohydrates (grams)
        - Fiber (grams)
        - Sugars (grams)
    - Fats (grams)
        - Saturated Fat (grams)
        - Trans Fat (grams)
        - Unsaturated Fat (grams)
    - Key micronutrients if apparent (e.g, Sodium, Potassium, Vitamin C, Iron).
4. Provide a brief summary of the meal's likely healthiness and any notable aspects.
5. If ingredients are ambiguous, state your assumptions clearly.
Present the report in a clear, itemized format.

IMPORTANT: After the main report, include a section clearly marked with '### CHART_DATA ###' followed by a JSON object containing only these keys and their numerical values: "Calories", "Protein", "Carbs", "Fat". Example:
### CHART_DATA ###
{"Calories": 350, "Protein": 20, "Carbs": 30, "Fat": 15}
### END_CHART_DATA ###"""
    
    nutrition_report_text = call_groq_vision_api(api_key, vision_model_name, prompt, base64_image)
    
    if nutrition_report_text.startswith("Error analyzing image"):
        return nutrition_report_text, None, ""
        
    # Attempt to parse chart data from the report
    chart_data = parse_nutrition_data_for_chart(nutrition_report_text)
    nutrition_chart_figure = None
    if chart_data:
        nutrition_chart_figure = generate_nutrition_chart(chart_data)
    else:
        logging.warning("Could not generate chart data from the report.")

    # The full report text (including chart data markers if present, for context) is returned for Q&A
    return nutrition_report_text, nutrition_chart_figure, nutrition_report_text

# --- Gradio UI ---
def main():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        with gr.Tabs():
            with gr.TabItem("Analyze Meal"):
                gr.Markdown("""# 🥗 MealVision AI Pro 📊❓\nUpload a meal photo, get a detailed nutrition report, see a chart, and ask follow-up questions!""")
                qa_context_state = gr.State("") 
                api_key_state = gr.State("")
                with gr.Row():
                    with gr.Column(scale=1):
                        api_key_input = gr.Textbox(label="Groq API Key", type="password", placeholder="Enter your Groq API key here...", elem_id="api_key_input")
                        model_dropdown = gr.Dropdown(choices=[], label="Vision Model", interactive=True)
                        image_input = gr.Image(type="pil", label="Upload Meal Image")
                        analyze_btn = gr.Button("Analyze Meal & Get Insights ✨", variant="primary")
                        download_btn = gr.Button("Download Nutrition Report", variant="secondary")
                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 Nutritional Insights")
                        output_text_report = gr.Textbox(label="Full Nutrition Report", lines=10, interactive=False)
                        output_nutrition_chart = gr.Plot(label="Macronutrient Chart")
                        output_table = gr.Dataframe(headers=["Nutrient", "Amount"], label="Nutrition Table", interactive=False)
                        gr.Markdown("### ❓ Ask Follow-up Questions")
                        qa_question_input = gr.Textbox(label="Your Question", placeholder="e.g., How can I make this healthier?", lines=2)
                        qa_answer_output = gr.Textbox(label="Answer", lines=3, interactive=False)
                        ask_qa_btn = gr.Button("Ask Question 🗣️")
                        gr.Markdown("---")
                        gr.Markdown("**Tip:** You can download your report, ask follow-up questions, or view your meal history in the next tab.")

                def fetch_and_populate_models(api_key):
                    try:
                        client = Groq(api_key=api_key)
                        models = client.models.list()
                        # List all model IDs (no filtering)
                        model_ids = [m.id for m in models.data]
                        if not model_ids:
                            logging.warning("No models found for this API key.")
                            model_dropdown.choices = []
                            model_dropdown.value = None
                            return gr.update(choices=[], value=None)
                        # Update dropdown
                        model_dropdown.choices = model_ids
                        model_dropdown.value = model_ids[0]
                        return gr.update(choices=model_ids, value=model_ids[0])
                    except Exception as e:
                        logging.error(f"Error fetching models: {e}")
                        model_dropdown.choices = []
                        model_dropdown.value = None
                        return gr.update(choices=[], value=None)

                api_key_input.change(
                    fetch_and_populate_models,
                    inputs=api_key_input,
                    outputs=[model_dropdown]
                )

                def on_analyze_click(img, key, vision_model):
                    report, chart, context = analyze_meal_and_interact(img, key, vision_model)
                    chart_data = parse_nutrition_data_for_chart(report)
                    table_data = [[k, v] for k, v in chart_data.items()] if chart_data is not None else []
                    return report, chart, table_data, context, key

                analyze_btn.click(
                    on_analyze_click,
                    inputs=[image_input, api_key_input, model_dropdown],
                    outputs=[output_text_report, output_nutrition_chart, output_table, qa_context_state, api_key_state],
                    api_name="analyze_meal_and_interact"
                )

                def on_ask_question_click(question, context, key):
                    if not question.strip():
                        return "Please enter a question.", ""
                    answer = handle_follow_up_question(key, question, context, "compound-beta")
                    return answer, ""

                ask_qa_btn.click(
                    on_ask_question_click,
                    inputs=[qa_question_input, qa_context_state, api_key_state],
                    outputs=[qa_answer_output, qa_context_state],
                    api_name="handle_follow_up_question"
                )

                def on_download_click(report_text):
                    # Create a temporary file to store the report
                    try:
                        temp_file_path = "temp_nutrition_report.txt"
                        with open(temp_file_path, "w") as temp_file:
                            temp_file.write(report_text)
                        return gr.File.update(value=temp_file_path, file_name="nutrition_report.txt")
                    except Exception as e:
                        logging.error(f"Error creating download file: {e}")
                        return None

                download_btn.click(
                    on_download_click,
                    inputs=[output_text_report],
                    outputs=[gr.File(label="Download Nutrition Report")]
                )

            with gr.TabItem("Meal History"):
                gr.Markdown("""# 📜 Meal History\nComing soon: View and manage your past meal analyses and reports here.""")
                # Placeholder for future meal history feature
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Your Past Analyses")
                        # This could be a DataTable or similar component to list past meals
                        past_meals_table = gr.Dataframe(headers=["Date", "Meal Image", "Calories", "Protein", "Carbs", "Fat"], interactive=False)
                    with gr.Column():
                        gr.Markdown("### Analysis Details")
                        # Details of the selected past analysis
                        past_meal_details = gr.Textbox(label="Details", lines=10, interactive=False)
                        past_meal_chart = gr.Plot(label="Macronutrient Chart")
                        gr.Markdown("### Actions")
                        reanalyze_btn = gr.Button("Re-analyze Meal", variant="primary")
                        download_history_btn = gr.Button("Download History Report", variant="secondary")

                gr.Markdown("**Note:** Your meal history is private and secure. Only you have access to this data.")

                # Placeholder functions for future implementation
                def fetch_past_meals(key):
                    return [], "" # Return empty for now

                def download_history_report(key):
                    return None # Placeholder

                # On tab open, load past meals for the user
                demo.load(
                    fetch_past_meals,
                    inputs=[api_key_state],
                    outputs=[past_meals_table, past_meal_details]
                )

                # Add interactivity for the past meals table and buttons
                def on_past_meal_select(selected_row):
                    if not selected_row:
                        return "", None
                    # Extract data from the selected row
                    date, image_b64, calories, protein, carbs, fat = selected_row[0]
                    details = f"Date: {date}\nCalories: {calories}\nProtein: {protein}\nCarbs: {carbs}\nFat: {fat}"
                    return details, None # No chart for now

                past_meals_table.select(
                    on_past_meal_select,
                    inputs=[past_meals_table],
                    outputs=[past_meal_details, past_meal_chart]
                )

                reanalyze_btn.click(
                    on_analyze_click,
                    inputs=[past_meals_table, api_key_state, model_dropdown],
                    outputs=[output_text_report, output_nutrition_chart, output_table, qa_context_state, api_key_state],
                    api_name="analyze_meal_and_interact"
                )

                download_history_btn.click(
                    download_history_report,
                    inputs=[api_key_state],
                    outputs=[gr.File(label="Download History Report")]
                )

        gr.Markdown("<small>Powered by Groq AI | <a href='https://github.com/your-repo'>View Source</a></small>", elem_id="footer")
    demo.launch()

if __name__ == "__main__":
    main()
