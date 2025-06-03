import streamlit as st
import os
from PIL import Image
import io
import base64

# Configure page
st.set_page_config(
    page_title="Meal Nutrition Analyzer",
    page_icon="🥗",
    layout="centered"
)

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
        padding: 20px;
    }
    .title-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .content-section {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="title-container">
    <h1>🥗 Meal Nutrition Analyzer</h1>
    <p>Upload meal photos and get instant nutrition analysis!</p>
</div>
""", unsafe_allow_html=True)

# Define functions for model verification
def verify_api_key(api_key):
    """Verify API key by listing available models"""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        models = client.models.list()
        
        # Extract model IDs for display
        model_list = []
        vision_models = []
        
        for model in models.data:
            # Only include vision models (Maverick and Scout)
            if any(name in model.id.lower() for name in ["maverick", "scout"]):
                model_list.append(model.id)
                vision_models.append(model.id)
                
        return True, model_list, vision_models
    except Exception as e:
        return False, [], []

# Define functions for image analysis
def analyze_image(image, api_key, nutrition_focus, model_name="meta-llama/llama-4-scout-17b-16e-instruct"):
    """Analyze the meal image with Groq API"""
    try:
        from groq import Groq
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Set up Groq client
        client = Groq(api_key=api_key)
        
        # Send the image for analysis using the vision model format
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": f"Analyze this food image. Provide detailed information about what food is in the image, ingredients, and approximate portion sizes. Focus on {nutrition_focus} nutrition aspects."},
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def generate_nutrition_report(analysis, nutrition_focus, health_goal, api_key, model_name="llama3-70b-8192"):
    """Generate nutrition report based on analysis"""
    try:
        from groq import Groq
        
        # Set up Groq client
        client = Groq(api_key=api_key)
        
        # Create a prompt for nutrition analysis
        prompt = f"""
        Based on this meal analysis:
        "{analysis}"
        
        Generate a detailed nutrition report with:
        1. Estimated calories
        2. Macronutrient breakdown (protein, carbs, fat)
        3. Key vitamins and minerals
        4. Recommendations based on "{nutrition_focus}" focus and "{health_goal}" health goal
        5. Suggestions for improvement
        
        Format your response in clear sections.
        """
        
        # Get nutrition report
        response = client.chat.completions.create(
            model=model_name,  # Use selected model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating nutrition report: {str(e)}"

# Initialize session state for model selection
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "meta-llama/llama-4-scout-17b-16e-instruct"

# Create two main columns with different widths
col1, col2 = st.columns([1, 2])

# Left sidebar - Settings
with col1:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # API Key input
    st.subheader("🔑 Setup")
    api_key = st.text_input("Groq API Key", type="password", help="Get your free API key at console.groq.com/keys")
    
    # Verify API Key
    if api_key:
        is_valid, model_list, vision_models = verify_api_key(api_key)
        
        if not is_valid:
            st.error("❌ Invalid API key. Please check your key and try again.")
        else:
            st.success("✅ API key is valid!")
            
            # Model selection
            st.subheader("🤖 Model Selection")
            if model_list:
                # Find the index of the currently selected model
                try:
                    default_index = model_list.index(st.session_state.selected_model)
                except ValueError:
                    default_index = 0
                
                selected_model = st.selectbox(
                    "Select Model",
                    options=model_list,
                    index=default_index,
                    help="Choose the model for image analysis",
                    key="model_selector"
                )
                # Update the session state with user selection
                st.session_state.selected_model = selected_model
            else:
                st.warning("No models available with this API key")
    
    # Get the model name from session state
    model_name = st.session_state.selected_model
    
    # Nutrition preferences
    st.subheader("🎯 Preferences")
    nutrition_focus = st.radio(
        "Nutrition Focus",
        options=[
            "Weightwatching",
            "Diet Restrictions",
            "Adolescent Diet",
            "Keto",
            "Athlete/High Protein",
            "Plant-Based/Vegan"
        ]
    )
    
    health_goal = st.radio(
        "Health Goal",
        options=[
            "Lose Weight",
            "Gain Muscle",
            "More Energy",
            "Better Sleep", 
            "Lower Blood Sugar"
        ]
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Right side - Image upload and results
with col2:
    # Image upload section
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    st.subheader("📸 Upload Your Meal")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    
    # Display uploaded image
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded meal image", use_column_width=True)
    
    analyze_button = st.button("🔍 Analyze Meal")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Results section
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    st.subheader("📊 Analysis Results")
    
    # Process image when button is clicked
    if analyze_button:
        if not api_key:
            st.error("❌ Please enter your Groq API key to analyze meals.")
        elif uploaded_file is None:
            st.error("❌ Please upload an image of your meal.")
        else:
            image = Image.open(uploaded_file)  # Ensure image is always defined here
            with st.spinner("Analyzing meal..."):
                # Analyze image
                analysis_result = analyze_image(image, api_key, nutrition_focus, model_name)
                
                if analysis_result is not None and isinstance(analysis_result, str) and "error" in analysis_result.lower():
                    st.error(analysis_result)
                elif analysis_result is None:
                    st.error("An unknown error occurred during analysis.")
                else:
                    # Generate nutrition report
                    with st.spinner("Generating nutrition report..."):
                        nutrition_report = generate_nutrition_report(analysis_result, nutrition_focus, health_goal, api_key, model_name)
                    
                    # Display results
                    st.markdown("### 📸 Image Analysis")
                    st.write(analysis_result)
                    
                    st.markdown("---")
                    
                    st.markdown("### 📊 Nutrition Report")
                    st.write(nutrition_report)
                    
                    st.markdown("---")
                    
                    st.info(f"*Analysis completed with {nutrition_focus} focus for {health_goal} goal.*")
    else:
        st.info("Upload a meal photo and click 'Analyze Meal' to get started!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 10px; color: #666;">
    <p>Made with ❤️ using Groq AI</p>
</div>
""", unsafe_allow_html=True)
