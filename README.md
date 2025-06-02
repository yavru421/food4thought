# Meal Nutrition Gradio App

This project is a Gradio application designed for meal image analysis and nutritional insights. It leverages the Groq API to provide advanced image analysis and generate detailed nutritional reports based on the analyzed data.

## Project Structure

```
meal-nutrition-gradio-app
├── src
│   ├── app.py                # Entry point of the Gradio application
│   ├── groq_client.py        # Handles Groq API client initialization and calls
│   ├── image_analysis.py      # Functions for processing meal images
│   ├── nutrition_report.py    # Generates nutritional reports from analysis results
│   ├── utils.py              # Utility functions for various operations
│   └── types
│       └── index.py          # Type definitions and interfaces
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Features

- **Image Analysis**: Upload a meal image to receive detailed analysis, including ingredient recognition and portion sizes.
- **Nutritional Insights**: Get a comprehensive nutritional report based on the analysis, including calorie count, macronutrient breakdown, and more.
- **User-Friendly Interface**: The application is built using Gradio, providing an intuitive interface for users to interact with.

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd meal-nutrition-gradio-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Groq API key in the environment variables or directly in the `groq_client.py` file.

## Usage

To run the application, execute the following command:

```
python src/app.py
```

This will start the Gradio interface, which you can access in your web browser.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.