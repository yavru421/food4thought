# 🥗 Meal Nutrition Analyzer

An AI-powered nutrition analysis tool that analyzes meal images and provides detailed nutritional information using Groq's vision models.

![Meal Nutrition Analyzer](image(14).jpg)

## ✨ Features

- 📸 **Image Analysis**: Upload meal photos for instant nutrition analysis
- 🔍 **Detailed Reports**: Get comprehensive nutritional breakdowns
- 🎯 **Personalized Goals**: Set nutrition focus and health goals
- 📊 **Progress Tracking**: Track your nutrition history and trends
- 🔊 **Audio Feedback**: Text-to-speech nutrition summaries
- 🎨 **Modern UI**: Beautiful, responsive interface

## 🚀 Live Demo

- **Hugging Face Spaces**: [Coming Soon]
- **GitHub Repository**: [https://github.com/YourUsername/meal-nutrition-analyzer](https://github.com/YourUsername/meal-nutrition-analyzer)

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- Groq API Key ([Get one free here](https://console.groq.com/keys))

### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YourUsername/meal-nutrition-analyzer.git
   cd meal-nutrition-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create a .env file with your Groq API key
   echo "GROQ_API_KEY=your_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser** to `http://localhost:7860`

## 🔧 Configuration

### Nutrition Focus Options
- **Weightwatching**: Calorie-focused analysis
- **Diet Restrictions**: Allergen and restriction awareness
- **Adolescent Diet**: Teen-specific nutrition needs
- **Keto**: Low-carb, high-fat focus
- **Athlete/High Protein**: Performance nutrition
- **Plant-Based/Vegan**: Plant-based nutrition analysis

### Health Goals
- Lose Weight
- Gain Muscle
- More Energy
- Better Sleep
- Lower Blood Sugar

## 📱 Usage

1. **Setup**: Enter your Groq API key and select your nutrition preferences
2. **Upload**: Take or upload photos of your meals
3. **Analyze**: Get detailed nutritional analysis powered by AI
4. **Track**: Review your nutrition history and progress
5. **Improve**: Get personalized recommendations

## 🏗️ Architecture

- **Frontend**: Gradio web interface
- **AI Vision**: Groq LLaMA-Vision models
- **Text Generation**: Groq Compound-Beta
- **Audio**: Groq TTS (Text-to-Speech)
- **Data**: Local session storage

## 📂 Project Structure

```
meal-nutrition-analyzer/
├── app.py                 # Main Gradio application
├── image_analysis.py      # Image processing and AI analysis
├── nutrition_report.py    # Report generation
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── image(14).jpg        # App logo
└── .env                 # Environment variables (create this)
```

## 🔑 API Keys

This app requires a Groq API key for AI functionality:

1. Visit [console.groq.com/keys](https://console.groq.com/keys)
2. Create a free account
3. Generate an API key
4. Enter it in the app's welcome screen

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing powerful AI models
- [Gradio](https://gradio.app/) for the amazing web interface framework
- [Hugging Face](https://huggingface.co/) for hosting and deployment

## 🐛 Issues & Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/YourUsername/meal-nutrition-analyzer/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide as much detail as possible including error messages and screenshots

## 🚀 Deployment

### Hugging Face Spaces
The app is configured to work on Hugging Face Spaces with zero configuration needed.

### Local Development
```bash
python app.py
```

---

Made with ❤️ for better nutrition tracking
