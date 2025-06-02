import gradio as gr
import plotly.graph_objs as go
from utils import gamify_user_progress, nutrition_trend_plot, export_history_csv, get_accessibility_tips
from image_analysis import analyze_meal_image
from nutrition_report import generate_nutrition_report
import datetime
import os
import time
from dotenv import load_dotenv
import logging
from typing import List
from PIL import Image
import tempfile

# Load environment variables
load_dotenv()

# Debugging: Check if GROQ_API_KEY is accessible
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
logging.basicConfig(level=logging.INFO)
API_KEY_ENV_VAR = "GROQ_API_KEY"

# Session history
session_history = []

# --- Custom CSS for windowed look ---
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
.logo { width: 64px; height: 64px; border-radius: 12px; margin-bottom: 0.5em; display: block; margin-left: auto; margin-right: auto; }
.onboarding-modal { background: rgba(24,26,32,0.95); border-radius: 20px; padding: 2em; max-width: 500px; margin: 2em auto; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
@media (max-width: 600px) {.sidebar .gr-radio label { font-size: 1em; } .main-window {padding: 0.5em;}}
"""

def validate_api_key(api_key: str) -> bool:
    return bool(api_key and api_key.strip())

def process_images(image_paths: List[str], api_key: str, meal_type: str, meal_date: str, manual_foods: str, nutrient_goals: str):
    logging.info(f"process_images called. API key present: {bool(api_key)}. Image paths count: {len(image_paths) if image_paths else 0}")
    if not api_key or api_key.strip() == "":
        return "⚠️ API key is missing. Please check your settings.", None, None
    if not image_paths or len(image_paths) == 0:
        return "⚠️ Please upload at least one meal image.", None, None
    
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
    if not report or report.strip() == "":
        return None
    filename = f"nutrition_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    return filename

def main():
    with gr.Blocks(css=css, fill_width=True, title="Meal Nutrition Analyzer") as demo:
        # State management
        onboarding_state = gr.State({"shown": False})
        
        # --- Onboarding Modal ---
        with gr.Group(visible=True, elem_classes=["onboarding-modal"]) as onboarding_modal:
            gr.Image(value="image(14).jpg", elem_classes=["logo"], show_label=False, show_download_button=False, show_share_button=False)
            gr.Markdown("""
            # 🥗 Welcome to Meal Nutrition Analyzer
            Let's get you set up! We need your API key and preferences to provide personalized nutrition analysis.
            """)
            
            # Step 1: API Key
            api_key_input = gr.Textbox(
                label="🔑 Groq API Key", 
                type="password", 
                placeholder="Enter your Groq API key here (required)",
                info="Get your free API key at https://console.groq.com/keys"
            )
            
            # Step 2: Preferences
            user_tone = gr.Dropdown([
                "Weightwatching",
                "Diet Restrictions", 
                "Adolescent Diet Restrictions",
                "Keto",
                "Athlete/High Protein",
                "Plant-Based/Vegan"
            ], label="🎯 Set Your Nutrition Focus", value="Weightwatching")
            
            user_goal = gr.Dropdown([
                "Lose Weight",
                "Gain Muscle", 
                "More Energy",
                "Better Sleep",
                "Lower Blood Sugar"
            ], label="🏆 Main Goal", value="Lose Weight")
            
            onboarding_submit = gr.Button("🚀 Start Analyzing!", variant="primary", size="lg")
            
            # Error message for API key validation
            api_error_msg = gr.Markdown("", visible=True)

        # --- Main Application Window ---
        with gr.Group(visible=False, elem_classes=["main-window"]) as main_window:
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
                        ], value="Meal Analysis", label="Navigation", interactive=True, elem_classes=["tab-anim"])
                        gr.Markdown("""
                        **Quick Tips:**
                        - Use the calendar to select a date and view/add meals.
                        - Jump to Meal Analysis to upload and analyze new meals.
                        - Review your History for past reports.
                        - Access Settings for API key, preferences, and feedback.
                        - See Help & Outline for a full guide.
                        """)
                
                with gr.Column(scale=3, min_width=400):
                    # Tab groups
                    calendar_group = gr.Group(visible=False)
                    meal_group = gr.Group(visible=True)
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
                        Upload meal images, set meal type, and get a detailed nutrition report.
                        """)
                        with gr.Row():
                            with gr.Column(scale=2):
                                meal_type = gr.Dropdown(["Breakfast", "Lunch", "Supper"], label="Meal Type", value="Lunch")
                                manual_foods = gr.Textbox(label="Add Foods/Ingredients (optional)", placeholder="e.g. 2 eggs, 1 slice toast, 1 cup spinach")
                                nutrient_goals = gr.Textbox(label="Nutrient Goals (optional)", placeholder="e.g. 500 kcal, 30g protein")
                                images = gr.File(label="Upload Meal Images", file_count="multiple", file_types=["image"])
                                with gr.Row():
                                    submit_button = gr.Button("🔍 Analyze Meal", variant="primary", size="lg")
                                    download_btn = gr.Button("📥 Download Report", variant="secondary")
                            
                            with gr.Column(scale=1, min_width=180):
                                gr.Markdown("### Quick Actions")
                                tts_good = gr.Button("🔊 Good News", variant="secondary", interactive=False)
                                tts_bad = gr.Button("🔊 Bad News", variant="secondary", interactive=False)
                                tts_improve = gr.Button("🔊 Ways to Improve", variant="secondary", interactive=False)
                                tts_audio = gr.Audio(label="AI Voice Output", interactive=False)
                        
                        with gr.Row():
                            output = gr.Textbox(label="Nutrition Report", lines=8, interactive=False, max_lines=12)
                        
                        with gr.Accordion("Show Raw Model Output", open=False):
                            raw_output = gr.JSON(label="Raw Model Output")
                        
                        with gr.Accordion("Show Session History (last 5)", open=False):
                            history_output = gr.JSON(label="Session History (last 5)")
                    
                    # --- History Tab ---
                    with history_group:
                        gr.Markdown("## 📜 History\nView your last 5 meal analyses and reports.")
                        history_display = gr.JSON(label="Session History (last 5)")
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
                        raw_display = gr.JSON(label="Raw Model Output")
                    
                    # --- Settings & Feedback Tab ---
                    with settings_group:
                        gr.Markdown("## ⚙️ Settings & Feedback\n- Update your API key\n- Set preferences\n- Leave feedback")
                        api_key_update = gr.Textbox(label="Update API Key", type="password", placeholder="Enter new API key")
                        update_key_btn = gr.Button("Update API Key", variant="secondary")
                        feedback = gr.Textbox(label="Feedback (optional)", placeholder="How can we improve this app?", lines=3)
                        submit_feedback_btn = gr.Button("Submit Feedback", variant="secondary")
                        clear_history_btn = gr.Button("Clear History", variant="stop")
                    
                    # --- Help & Outline Tab ---
                    with help_group:
                        gr.Markdown("""
                        ## 🧭 App Outline & Help
                        
                        **Modules & Navigation:**
                        - **Calendar:** View and select dates for meal analysis.
                        - **Meal Analysis:** Upload images, set meal details, and analyze nutrition.
                        - **History:** Review your last 5 meal reports.
                        - **Raw Model Output:** See the raw AI output for transparency.
                        - **Settings & Feedback:** Manage your API key, preferences, and send feedback.
                        - **Help & Outline:** You're here! See this guide anytime.

                        **How to Use:**
                        1. Start by uploading meal images in the Meal Analysis tab.
                        2. Set your meal type and add any additional foods if needed.
                        3. Click "Analyze Meal" to get your nutrition report.
                        4. Check History for past results and trends.
                        5. Use Settings to update your info or leave feedback.
                        6. Explore Raw Model Output if you're curious about the AI's reasoning.
                        """)
                        gr.Markdown("### Accessibility Tips:")
                        gr.JSON(value=get_accessibility_tips(), label="Accessibility Best Practices")
        
        # --- Navigation logic: show only the selected group ---
        def nav_to_group(tab, onboarding_state):
            if not onboarding_state.get("shown", False):
                vis = [False, True, False, False, False, False]  # Default to meal analysis
            else:
                vis = {
                    "Calendar": [True, False, False, False, False, False],
                    "Meal Analysis": [False, True, False, False, False, False],
                    "History": [False, False, True, False, False, False],
                    "Raw Model Output": [False, False, False, True, False, False],
                    "Settings & Feedback": [False, False, False, False, True, False],
                    "Help & Outline": [False, False, False, False, False, True],
                }.get(tab, [False, True, False, False, False, False])
            
            return [gr.update(visible=vis[0]), gr.update(visible=vis[1]), gr.update(visible=vis[2]), 
                   gr.update(visible=vis[3]), gr.update(visible=vis[4]), gr.update(visible=vis[5])]
        
        # Connect navigation
        nav_tabs.change(
            fn=nav_to_group, 
            inputs=[nav_tabs, onboarding_state], 
            outputs=[calendar_group, meal_group, history_group, raw_group, settings_group, help_group]
        )
        
        # --- Event Handlers ---
        
        # Onboarding logic: store API key and hide onboarding, show main window
        def onboarding_complete(api_key, tone, goal, state):
            if not api_key or api_key.strip() == "":
                return (
                    gr.update(visible=True),   # Keep onboarding visible
                    gr.update(visible=False),  # Keep main window hidden
                    state,  # Don't update state
                    gr.update(value="⚠️ Please enter your Groq API key to continue", visible=True)  # Show error
                )
            
            print(f"Onboarding complete: tone={tone}, goal={goal}")
            return (
                gr.update(visible=False),  # Hide onboarding modal
                gr.update(visible=True),   # Show main window
                {**state, "shown": True, "tone": tone, "goal": goal, "api_key": api_key},  # Update state with API key
                gr.update(value="✅ Welcome! You're all set up.", visible=True)  # Success message
            )
        
        onboarding_submit.click(
            fn=onboarding_complete,
            inputs=[api_key_input, user_tone, user_goal, onboarding_state],
            outputs=[onboarding_modal, main_window, onboarding_state, api_error_msg]
        )
        
        # Updated meal analysis submit handler - gets API key from state
        def analyze_with_state_api_key(images, meal_type, meal_date, manual_foods, nutrient_goals, state):
            api_key = state.get("api_key", "")
            return process_images(images, api_key, meal_type, meal_date, manual_foods, nutrient_goals)
        
        submit_button.click(
            fn=analyze_with_state_api_key,
            inputs=[images, meal_type, manual_date, manual_foods, nutrient_goals, onboarding_state],
            outputs=[output, raw_output, history_output]
        )
        
        # Download report handler  
        download_btn.click(
            fn=download_report,
            inputs=[output],
            outputs=[]
        )
        
        # API key update handler
        def update_api_key(new_key, state):
            if new_key and new_key.strip():
                state["api_key"] = new_key
                return state, "✅ API key updated successfully!"
            return state, "❌ Please enter a valid API key"
        
        update_key_btn.click(
            fn=update_api_key,
            inputs=[api_key_update, onboarding_state],
            outputs=[onboarding_state, api_error_msg]
        )
        
        # Footer
        gr.HTML("""
        <div class='footer'>
            <hr style='border: none; border-top: 1px solid #444; margin: 2em 0 1em 0;'>
            <span>Made with ❤️ for better nutrition | <a href='https://console.groq.com/keys' style='color:#6A0DAD' target='_blank'>Get API Key</a> | <a href='#' style='color:#6A0DAD'>Privacy</a></span>
        </div>
        """)

    demo.launch()

if __name__ == "__main__":
    main()
