import gradio as gr
import os
import logging
from PIL import Image
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Image analysis functions (originally in image_analysis.py)
def analyze_meal_image(image, api_key, nutrition_focus="Weightwatching"):
    """Analyze a meal image using Groq Vision API."""
    logging.info(f"Analyzing image with {nutrition_focus} focus")
    try:
        # For a self-contained version, we'll implement a simple version
        # that sends the image to Groq API
        from groq import Groq
        import base64
        import io
        
        # Convert PIL Image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Set up Groq client
        client = Groq(api_key=api_key)
        
        # Create prompt for food analysis
        prompt = f"""
        Analyze this food image and provide a detailed description of:
        1. What foods are visible
        2. Approximate portion sizes
        3. Main ingredients
        4. Cooking methods used (if apparent)
        
        Focus on {nutrition_focus} aspects.
        Be concise but thorough in your analysis.
        """
        
        # Call Groq API with multimodal capabilities
        response = client.chat.completions.create(
            model="llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                    ]
                }
            ],
            max_tokens=500
        )
        
        analysis = response.choices[0].message.content
        return analysis
        
    except Exception as e:
        logging.error(f"Error analyzing image: {str(e)}")
        return f"Error analyzing image: {str(e)}"

# Nutrition report generation (originally in nutrition_report.py)
def generate_nutrition_report(analysis_result, nutrition_focus, health_goal, api_key):
    """Generate a nutrition report based on the image analysis."""
    logging.info(f"Generating report with focus: {nutrition_focus}, goal: {health_goal}")
    try:
        from groq import Groq
        
        # Set up Groq client
        client = Groq(api_key=api_key)
        
        # Create prompt for nutrition report
        prompt = f"""
        Based on this meal analysis:
        "{analysis_result}"
        
        Generate a detailed nutrition report with:
        1. Estimated calories
        2. Macronutrient breakdown (protein, carbs, fat)
        3. Key vitamins and minerals
        4. Recommendations based on "{nutrition_focus}" focus and "{health_goal}" health goal
        5. Potential improvements for better nutrition
        
        Format your response clearly with sections and bullet points.
        Be realistic and evidence-based in your analysis.
        """
        
        # Call Groq API for text generation
        response = client.chat.completions.create(
            model="llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )
        
        report = response.choices[0].message.content
        return report
        
    except Exception as e:
        logging.error(f"Error generating nutrition report: {str(e)}")
        return f"Error generating nutrition report: {str(e)}"

# Simple CSS for a clean single page
css = """
.gradio-container {
    font-family: 'Segoe UI', Arial, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}
.header {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.section {
    background: white;
    padding: 25px;
    border-radius: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}
.result-box {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    margin-top: 15px;
}
button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
}
"""

def analyze_meal(image, api_key, nutrition_focus, health_goal):
    """Simple meal analysis function"""
    if not api_key or api_key.strip() == "":
        return "❌ Please enter your Groq API key to analyze meals."
    
    if image is None:
        return "❌ Please upload an image of your meal."
    
    try:
        # Analyze the image
        logging.info(f"Analyzing meal with focus: {nutrition_focus}, goal: {health_goal}")
        
        # Get the image analysis
        analysis_result = analyze_meal_image(image, api_key, nutrition_focus)
        
        if isinstance(analysis_result, str) and "error" in analysis_result.lower():
            return f"❌ Analysis Error: {analysis_result}"
        
        # Generate nutrition report
        nutrition_report = generate_nutrition_report(
            analysis_result, 
            nutrition_focus, 
            health_goal, 
            api_key
        )
        
        if isinstance(nutrition_report, str) and "error" in nutrition_report.lower():
            return f"❌ Report Error: {nutrition_report}"
        
        # Format the complete result
        result = f"""
## 🥗 Meal Analysis Complete!

### 📸 Image Analysis
{analysis_result}

---

### 📊 Nutrition Report
{nutrition_report}

---

*Analysis completed with {nutrition_focus} focus for {health_goal} goal.*
        """
        
        return result
        
    except Exception as e:
        logging.error(f"Error in analyze_meal: {str(e)}")
        return f"❌ Unexpected error: {str(e)}"

# Create the Gradio interface
with gr.Blocks(css=css, title="🥗 Meal Nutrition Analyzer") as demo:
    gr.HTML("""
    <div class="header">
        <h1>🥗 Meal Nutrition Analyzer</h1>
        <p>Upload your meal photos and get instant AI-powered nutrition analysis!</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML('<div class="section">')
            gr.Markdown("## 🔑 Setup")
            api_key = gr.Textbox(
                label="Groq API Key",
                placeholder="Enter your Groq API key here...",
                type="password",
                info="Get your free API key at console.groq.com/keys"
            )
            
            gr.Markdown("## 🎯 Preferences")
            nutrition_focus = gr.Radio(
                choices=[
                    "Weightwatching",
                    "Diet Restrictions", 
                    "Adolescent Diet",
                    "Keto",
                    "Athlete/High Protein",
                    "Plant-Based/Vegan"
                ],
                label="Nutrition Focus",
                value="Weightwatching"
            )
            
            health_goal = gr.Radio(
                choices=[
                    "Lose Weight",
                    "Gain Muscle", 
                    "More Energy",
                    "Better Sleep",
                    "Lower Blood Sugar"
                ],
                label="Health Goal",
                value="Lose Weight"
            )
            gr.HTML('</div>')
        
        with gr.Column(scale=2):
            gr.HTML('<div class="section">')
            gr.Markdown("## 📸 Upload Your Meal")
            image_input = gr.Image(
                label="Meal Photo",
                type="pil",
                sources=["upload", "webcam"],
                height=300
            )
            
            analyze_btn = gr.Button(
                "🔍 Analyze Meal", 
                variant="primary",
                size="lg"
            )
            gr.HTML('</div>')
    
    # Results section
    gr.HTML('<div class="section">')
    gr.Markdown("## 📊 Analysis Results")
    result_output = gr.Markdown(
        value="Upload a meal photo and click 'Analyze Meal' to get started!",
        elem_classes=["result-box"]
    )
    gr.HTML('</div>')
    
    # Connect the analyze button
    analyze_btn.click(
        fn=analyze_meal,
        inputs=[image_input, api_key, nutrition_focus, health_goal],
        outputs=[result_output]
    )
    
    # Footer
    gr.HTML("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #666;">
        <p>Made with ❤️ using Groq AI • <a href="https://github.com/yavru421/food4thought" target="_blank">GitHub</a></p>
    </div>
    """)

if __name__ == "__main__":
    # Launch configuration for both local and Hugging Face Spaces
    demo.launch(
        share=False,
        server_name="0.0.0.0" if "SPACE_ID" in os.environ else "127.0.0.1",
        server_port=7860,
        show_error=True
    )
