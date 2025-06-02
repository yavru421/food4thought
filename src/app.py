import gradio as gr
import plotly.graph_objs as go
from utils import gamify_user_progress, nutrition_trend_plot, export_history_csv, get_accessibility_tips
from image_analysis import analyze_meal_image
from nutrition_report import generate_nutrition_report
import datetime
import os
from dotenv import load_dotenv
import logging
from typing import List
from PIL import Image

# Load environment variables
load_dotenv()

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
logging.basicConfig(level=logging.INFO)
API_KEY_ENV_VAR = "GROQ_API_KEY"

# Session history
session_history = []

# --- Custom CSS for windowed look (since gradio.themes is not available) ---
css = """
.gradio-container { border: 2px solid #6A0DAD; border-radius: 12px; background: linear-gradient(135deg, #23272f 0%, #181a20 100%); color: #fff; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif; }
button:hover { transform: scale(1.05); transition: 0.3s; }
.main-window {background: rgba(24,26,32,0.98); border-radius: 22px; box-shadow: 0 6px 32px #000a, 0 1.5px 0 #4caf50; padding: 2.5em 2em 2em 2em; margin: 1.5em 0 2em 0; min-height: 600px; max-width: 900px; margin-left: auto; margin-right: auto;}
@media (max-width: 900px) {.main-window {padding: 1em; min-height: 400px;}}
.sidebar .gr-radio { background: #23272f; border-radius: 16px; box-shadow: 0 2px 8px #0004; }
.sidebar .gr-radio label { font-weight: 600; font-size: 1.1em; }
.sidebar .gr-radio input:checked + label { background: linear-gradient(90deg, #6A0DAD 60%, #4caf50 100%); color: #fff; border-radius: 12px; }
.sidebar .gr-radio input:focus + label { outline: 2px solid #4caf50; }
.sidebar .gr-radio label:hover { background: #33364a; }
.sidebar .gr-markdown { margin-bottom: 1.2em; }
.tab-anim { transition: opacity 0.4s cubic-bezier(.4,0,.2,1); opacity: 1; }
.tab-anim[hidden] { opacity: 0; pointer-events: none; }
.gamify-bar { height: 18px; border-radius: 8px; background: linear-gradient(90deg, #4caf50 60%, #6A0DAD 100%); margin: 0.5em 0; }
.gamify-badge { display: inline-block; background: #6A0DAD; color: #fff; border-radius: 8px; padding: 0.2em 0.7em; margin: 0.2em; font-weight: 600; box-shadow: 0 2px 8px #0002; }
.footer { text-align: center; color: #aaa; font-size: 0.95em; margin-top: 2em; }
.logo { width: 48px; height: 48px; border-radius: 12px; margin-bottom: 0.5em; }
@media (max-width: 600px) {.sidebar .gr-radio label { font-size: 1em; } .main-window {padding: 0.5em;}}
"""

def validate_api_key(api_key: str) -> bool:
    return True

def process_image(image: Image.Image, api_key: str) -> str:
    logging.info(f"process_image called. API key present: {bool(api_key)}. Image type: {type(image)}")
    if not api_key or api_key.strip() == "":
        logging.error("API key is empty or invalid")
        return "Error: Please enter your Groq API key."
    try:
        analysis_result = analyze_meal_image(image, api_key, model=MODEL_NAME)
        logging.debug(f"analyze_meal_image result: {analysis_result}")
        nutrition_report = generate_nutrition_report(analysis_result)
        logging.debug(f"generate_nutrition_report result: {nutrition_report}")
        return nutrition_report if nutrition_report is not None else "No nutrition report generated."
    except Exception as e:
        logging.exception(f"Error processing image: {str(e)}")
        return f"Error: {str(e)}"

def process_images(image_paths: List[str], api_key: str, meal_type: str, meal_date: str, manual_foods: str, nutrient_goals: str):
    logging.info(f"process_images called. API key present: {bool(api_key)}. Image paths count: {len(image_paths) if image_paths else 0}")
    if not api_key or api_key.strip() == "":
        return "Please enter your Groq API key.", None, None
    if not image_paths or len(image_paths) == 0:
        return "Please upload at least one meal image.", None, None
    all_results = []
    for idx, image_path in enumerate(image_paths):
        try:
            img = Image.open(image_path)
            prompt = f"Analyze this meal image. Meal type: {meal_type}. Date: {meal_date}. Provide a detailed breakdown of all visible foods, ingredients, and nutritional values."
            if manual_foods.strip():
                prompt += f"\nThe user also reports these foods/ingredients: {manual_foods}. Include them in the analysis."
            analysis_result = analyze_meal_image(img, api_key, model=MODEL_NAME, prompt=prompt)
            if isinstance(analysis_result, dict):
                analysis_result['meal_type'] = meal_type
                analysis_result['meal_date'] = str(meal_date)
                analysis_result['image_index'] = idx + 1
            all_results.append(analysis_result)
        except Exception as e:
            all_results.append({"error": str(e), "image_index": idx + 1})
    try:
        nutrition_report = generate_nutrition_report(all_results)
        # Save to session history
        session_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "meal_type": meal_type,
            "meal_date": meal_date,
            "manual_foods": manual_foods,
            "nutrient_goals": nutrient_goals,
            "report": nutrition_report
        })
        return nutrition_report, all_results, session_history[-5:]
    except Exception as e:
        return f"Error: {str(e)}", all_results, session_history[-5:]

def download_report(report):
    with open("nutrition_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    return "nutrition_report.txt"

def tts_groq(text, api_key, voice="good-news"):
    """Call Groq TTS API for a given text and voice style, summarizing if needed to fit the TTS length limit."""
    from groq import Groq
    import tempfile
    import re
    tts_limit = 400  # Groq TTS character limit (safe value)
    # Use only valid Groq voices
    voice_map = {
        "good-news": "Fritz-PlayAI",
        "bad-news": "Thunder-PlayAI",
        "improve": "Celeste-PlayAI"
    }
    groq_voice = voice_map.get(voice, "Fritz-PlayAI")
    tts_model = "playai-tts"
    response_format = "wav"
    # If text is too long, summarize it using Compound-Beta
    if len(text) > tts_limit:
        try:
            client = Groq(api_key=api_key)
            # Prompt for a summary suitable for TTS
            summary_prompt = f"Summarize the following for a {voice.replace('-', ' ')} voice announcement, max {tts_limit} characters, clear and engaging:\n{text}"
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": summary_prompt}],
                model="compound-beta"
            )
            summary = chat_completion.choices[0].message.content
            if summary:
                text = summary.strip()[:tts_limit]
            else:
                text = text[:tts_limit]
        except Exception as e:
            text = text[:tts_limit]
    try:
        client = Groq(api_key=api_key)
        response = client.audio.speech.create(
            model=tts_model,
            voice=groq_voice,
            input=text,
            response_format=response_format
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            response.write_to_file(tmp.name)
            return tmp.name
    except Exception as e:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as tmp:
            tmp.write(f"TTS Error: {e}")
            return tmp.name

def main():
    onboarding_state = gr.State({"shown": False})
    with gr.Blocks(css=css, fill_width=True) as demo:
        # --- Onboarding Modal ---
        onboarding_modal = gr.Group(visible=True, elem_classes=["onboarding-modal"])
        main_window = gr.Group(visible=False, elem_classes=["main-window"])
        with onboarding_modal:
            gr.Image(value="https://cdn-icons-png.flaticon.com/512/3075/3075977.png", elem_classes=["logo"], show_label=False, show_download_button=False, show_share_button=False)
            gr.Markdown("""
            # 👋 Welcome to Meal Nutrition Analyzer
            Let's personalize your experience! Please set your preferred tone and main goal for your nutrition journey.
            """)
            user_tone = gr.Dropdown([
                "Weightwatching",
                "Diet Restrictions",
                "Adolescent Diet Restrictions",
                "Keto",
                "Athlete/High Protein",
                "Plant-Based/Vegan"
            ], label="Set the Tone", value="Weightwatching")
            user_goal = gr.Dropdown([
                "Lose Weight",
                "Gain Muscle",
                "More Energy",
                "Better Sleep",
                "Lower Blood Sugar"
            ], label="Main Goal", value="Lose Weight")
            onboarding_submit = gr.Button("Get Started!", variant="primary")

        with main_window:
            # --- Main Layout: Sidebar + Tabs ---
            with gr.Row():
                with gr.Column(scale=1, min_width=260):
                    with gr.Group(elem_classes=["sidebar"]):
                        gr.Markdown("""
                        # 🥗 Meal Nutrition Analyzer
                        <span style='font-size:1.1em;'>Navigation</span>
                        """)
                        nav_tabs = gr.Radio([
                            "Calendar",
                            "Meal Analysis",
                            "History",
                            "Raw Model Output",
                            "Settings & Feedback",
                            "Help & Outline"
                        ], value="Calendar", label="Navigation", interactive=True, elem_classes=["tab-anim"])
                        gr.Markdown("""
                        **Quick Tips:**
                        - Use the calendar to select a date and view/add meals.
                        - Jump to Meal Analysis to upload and analyze new meals.
                        - Review your History for past reports.
                        - Access Settings for API key, preferences, and feedback.
                        - See Help & Outline for a full guide.
                        """)
                with gr.Column(scale=3, min_width=400):
                    with gr.Group(elem_classes=["main-window"]):
                        calendar_group = gr.Group(visible=True)
                        meal_group = gr.Group(visible=False)
                        history_group = gr.Group(visible=False)
                        raw_group = gr.Group(visible=False)
                        settings_group = gr.Group(visible=False)
                        help_group = gr.Group(visible=False)
                        # --- Calendar Tab ---
                        with calendar_group:
                            today = datetime.date.today()
                            recent_dates = [(today - datetime.timedelta(days=i)).isoformat() for i in range(7)]
                            gr.Markdown("""
                            ## 📅 Meal Calendar
                            Select a date to view or add meal analyses. Use the zoom controls to switch between month, week, or day view.
                            """)
                            with gr.Row():
                                calendar_date = gr.Dropdown(choices=recent_dates, value=today.isoformat(), label="Pick a Recent Date", interactive=True)
                                today_btn = gr.Button("Today", variant="secondary")
                                manual_date = gr.Textbox(label="Or Enter Date (YYYY-MM-DD)", value=today.isoformat(), interactive=True)
                            def set_today():
                                return gr.update(value=today.isoformat()), gr.update(value=today.isoformat())
                            today_btn.click(fn=set_today, inputs=None, outputs=[calendar_date, manual_date])
                            zoom = gr.Radio(["Month", "Week", "Day"], value="Month", label="Zoom View")
                            gr.Markdown("<span style='font-size:0.95em;'>[Prev] [Today] [Next]</span>")
                        # --- Meal Analysis Tab ---
                        with meal_group:
                            gr.Markdown("""
                            ## 🍽️ Meal Analysis
                            Upload meal images, set meal type, and get a nutrition report.
                            """)
                            with gr.Row():
                                with gr.Column(scale=2):
                                    api_key_box = gr.Textbox(label="Groq API Key", type="password", placeholder="Paste your Groq API key here")
                                    meal_type = gr.Dropdown(["Breakfast", "Lunch", "Supper"], label="Meal Type", value="Lunch")
                                    manual_foods = gr.Textbox(label="Add Foods/Ingredients (optional)", placeholder="e.g. 2 eggs, 1 slice toast, 1 cup spinach")
                                    nutrient_goals = gr.Textbox(label="Nutrient Goals (optional)", placeholder="e.g. 500 kcal, 30g protein")
                                    images = gr.File(label="Upload Meal Images", file_count="multiple", file_types=["image"])
                                    with gr.Row():
                                        submit_button = gr.Button("Analyze Meal", variant="primary")
                                        download_btn = gr.Button("Download Report", variant="secondary")
                                with gr.Column(scale=1, min_width=180):
                                    gr.Markdown("### Quick Actions")
                                    tts_good = gr.Button("🔊 Good News", variant="secondary", interactive=False)
                                    tts_bad = gr.Button("🔊 Bad News", variant="secondary", interactive=False)
                                    tts_improve = gr.Button("🔊 Ways to Improve", variant="secondary", interactive=False)
                                    tts_audio = gr.Audio(label="AI Voice Output", interactive=False)
                            with gr.Row():
                                output = gr.Textbox(label="Nutrition Report", lines=6, interactive=False, max_lines=8)
                            with gr.Accordion("Show Raw Model Output", open=False):
                                raw_output = gr.JSON(label="Raw Model Output")
                            with gr.Accordion("Show Session History (last 5)", open=False):
                                history_output = gr.JSON(label="Session History (last 5)")
                        # --- History Tab ---
                        with history_group:
                            gr.Markdown("## 📜 History\nView your last 5 meal analyses and reports.")
                            history_output = gr.JSON(label="Session History (last 5)")
                            gamify_stats = gr.JSON(label="Gamification Stats (Streaks, Badges)")
                            gr.Markdown("### Progress Toward Weekly Goal")
                            gr.HTML('<div class="gamify-bar" style="width:70%"></div>')
                            gr.Markdown("**Badges:** <span class='gamify-badge'>🥇 Streak 5</span> <span class='gamify-badge'>🥗 Healthy Choice</span>", elem_id="badges")
                            trend_plot = gr.Plot(label="Nutrition Trends")
                            export_btn = gr.Button("Export History as CSV", variant="secondary")
                            csv_file = gr.File(label="Download CSV")
                        # --- Raw Model Output Tab ---
                        with raw_group:
                            gr.Markdown("## 🛠️ Raw Model Output\nInspect the raw output from the Groq vision and Compound-Beta models for debugging or curiosity.")
                            raw_output = gr.JSON(label="Raw Model Output")
                        # --- Settings & Feedback Tab ---
                        with settings_group:
                            gr.Markdown("## ⚙️ Settings & Feedback\n- Update your API key\n- Set preferences\n- Leave feedback")
                            feedback = gr.Textbox(label="Feedback (optional)", placeholder="How can we improve this app?")
                            clear_history_btn = gr.Button("Clear History", variant="stop")
                        # --- Help & Outline Tab ---
                        with help_group:
                            gr.Markdown("## 🧭 App Outline & Help\n**Modules & Navigation:**\n- **Calendar:** View and select dates for meal analysis.\n- **Meal Analysis:** Upload images, set meal details, and analyze nutrition.\n- **History:** Review your last 5 meal reports.\n- **Raw Model Output:** See the raw AI output for transparency.\n- **Settings & Feedback:** Manage your API key, preferences, and send feedback.\n- **Help & Outline:** You're here! See this guide anytime.\n\n**How to Use:**\n1. Start in the Calendar to pick a date.\n2. Go to Meal Analysis to upload and analyze your meal.\n3. Check History for past results.\n4. Use Settings to update your info or leave feedback.\n5. Explore Raw Model Output if you're curious about the AI's reasoning.")
                            gr.Markdown("### Accessibility Tips:")
                            gr.JSON(value=get_accessibility_tips(), label="Accessibility Best Practices")
        # --- Navigation logic: show only the selected group ---
        def nav_to_group(tab, onboarding_state):
            if not onboarding_state.get("shown", False):
                vis = [True, False, False, False, False, False]
            else:
                vis = {
                    "Calendar": [True, False, False, False, False, False],
                    "Meal Analysis": [False, True, False, False, False, False],
                    "History": [False, False, True, False, False, False],
                    "Raw Model Output": [False, False, False, True, False, False],
                    "Settings & Feedback": [False, False, False, False, True, False],
                    "Help & Outline": [False, False, False, False, False, True],
                }.get(tab, [True, False, False, False, False, False])
            # Animate tab transitions by toggling tab-anim class
            import time
            time.sleep(0.15)
            return [gr.update(visible=vis[0]), gr.update(visible=vis[1]), gr.update(visible=vis[2]), gr.update(visible=vis[3]), gr.update(visible=vis[4]), gr.update(visible=vis[5])]
        # Always connect nav_tabs.change inside the Blocks context
        nav_tabs.change(fn=nav_to_group, inputs=[nav_tabs, onboarding_state], outputs=[calendar_group, meal_group, history_group, raw_group, settings_group, help_group])
        # Onboarding logic: hide onboarding, show main window
        onboarding_submit.click(
            fn=lambda tone, goal, state: (gr.update(visible=False), gr.update(visible=True), {**state, "shown": True, "tone": tone, "goal": goal}),
            inputs=[user_tone, user_goal, onboarding_state],
            outputs=[onboarding_modal, main_window, onboarding_state],
            queue=False
        )

    demo.launch()
    gr.HTML("""
    <div class='footer'>
        <hr style='border: none; border-top: 1px solid #444; margin: 2em 0 1em 0;'>
        <span>Made with ❤️ for Hackathons | <a href='https://github.com/your-repo' style='color:#6A0DAD'>GitHub</a> | <a href='#' style='color:#6A0DAD'>Privacy</a></span>
    </div>
    """)

# --- Hugging Face Spaces compatibility ---
# If running on Spaces, use gradio's launch arguments for public sharing
import sys
if __name__ == "__main__":
    if any("spaces" in arg for arg in sys.argv) or "SPACE_ID" in os.environ:
        main()
    else:
        main()