# MealVision AI Pro 🍽️📊❓

A hackathon-ready Gradio app for meal image nutrition analysis using Groq's API. Upload a meal photo, get a detailed nutrition report, see a nutrition chart, and ask follow-up questions—all in a modern, user-friendly interface.

---

## 🚀 Features

- **Meal Image Nutrition Analysis**: Upload a meal photo and get a detailed, itemized nutrition report powered by Groq vision models.
- **Nutrition Charting**: Visualize calories, protein, carbs, and fat with a clear bar chart.
- **Interactive Q&A**: Ask follow-up questions about your meal or report (uses Groq's `compound-beta` model for chat).
- **Meal History**: (Coming soon) View and manage your past meal analyses.
- **Modern UI**: Clean, tabbed Gradio interface. Download your nutrition report as a file.
- **Dynamic Model Selection**: Vision model dropdown auto-populates from your Groq API key.
- **No TTS/Audio**: 100% text and image-based for maximum compatibility.

---

## 🛠️ Setup & Usage

1. **Clone the repo:**

   ```sh
   git clone https://github.com/yavru421/food4thought.git
   cd food4thought
   ```

2. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the app:**

   ```sh
   python app.py
   ```

4. **Open in your browser:**
   Go to [http://127.0.0.1:7860](http://127.0.0.1:7860)

5. **Enter your Groq API key** (get one at [groq.com](https://groq.com/))

6. **Upload a meal image and analyze!**

---

## 🧑‍💻 Deploy on Hugging Face Spaces

- Create a new Space (type: Gradio)
- Upload `app.py` and `requirements.txt`
- Set your Groq API key as a secret (do NOT hardcode in code)
- [Hugging Face Spaces Guide](https://huggingface.co/docs/hub/spaces)

---

## 📦 Requirements

- Python 3.9+
- gradio
- groq
- matplotlib
- Pillow

---

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss major changes.

---

## 📄 License

MIT License

---

**Powered by [Groq](https://groq.com/) & [Gradio](https://gradio.app/)**
