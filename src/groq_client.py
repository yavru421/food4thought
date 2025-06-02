class GroqClient:
    """
    Optional utility class for Groq API calls. Prefer using the Groq SDK directly in your workflow for consistency.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = self.initialize_client()

    def initialize_client(self):
        from groq import Groq
        return Groq(api_key=self.api_key)

    def analyze_meal_image(self, image_bytes: bytes) -> str:
        """Analyze meal image using Groq vision model. Returns string response."""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this meal image for nutritional insights."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.encode_image(image_bytes)}"
                                }
                            }
                        ]
                    }
                ],
                model="meta-llama/llama-4-scout-17b-16e-instruct"
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def encode_image(self, image_bytes: bytes) -> str:
        import base64
        return base64.b64encode(image_bytes).decode('utf-8')

    def get_nutritional_insights(self, meal_description: str) -> str:
        """Get nutritional insights for a meal description using Groq language model."""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Provide nutritional insights for the following meal: {meal_description}"
                    }
                ],
                model="compound-beta"  # Use compound-beta for final analysis
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error retrieving nutritional insights: {str(e)}"