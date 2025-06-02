def load_image(image_path: str):
    """Load an image from a file path using PIL."""
    from PIL import Image
    try:
        image = Image.open(image_path)
        return image
    except Exception as e:
        raise ValueError(f"Error loading image: {e}")

def format_nutrition_data(nutrition_data: dict) -> dict:
    """Format nutrition data keys for display."""
    formatted_data = {}
    for key, value in nutrition_data.items():
        formatted_data[key.capitalize()] = value
    return formatted_data

def handle_api_error(error: Exception) -> dict:
    """Return a standardized error dict for API errors."""
    return {"error": str(error), "message": "An error occurred while processing your request."}

# --- Advanced Gradio Hackathon Features: Utility Functions ---
import json
import plotly.graph_objs as go

def gamify_user_progress(history):
    """Return a dict with gamification stats (streaks, badges, etc.) from session history."""
    streak = 0
    badges = []
    if history:
        # Simple streak: consecutive days with entries
        dates = sorted({h['meal_date'] for h in history if 'meal_date' in h})
        if dates:
            from datetime import datetime, timedelta
            streak = 1
            for i in range(1, len(dates)):
                d0 = datetime.strptime(dates[i-1], '%Y-%m-%d')
                d1 = datetime.strptime(dates[i], '%Y-%m-%d')
                if (d1 - d0).days == 1:
                    streak += 1
                else:
                    streak = 1
            if streak >= 7:
                badges.append('7-Day Streak')
            if len(dates) >= 30:
                badges.append('Consistency Pro')
    return {"streak": streak, "badges": badges}

def nutrition_trend_plot(history):
    """Return a Plotly figure showing nutrition trends over time from session history."""
    if not history:
        return go.Figure()
    dates = []
    calories = []
    protein = []
    for h in history:
        dates.append(h.get('meal_date', ''))
        report = h.get('report', {})
        if isinstance(report, str):
            try:
                report = json.loads(report)
            except Exception:
                report = {}
        calories.append(report.get('Calories', 0))
        protein.append(report.get('Protein', 0))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=calories, mode='lines+markers', name='Calories'))
    fig.add_trace(go.Scatter(x=dates, y=protein, mode='lines+markers', name='Protein'))
    fig.update_layout(title='Nutrition Trends', xaxis_title='Date', yaxis_title='Amount')
    return fig

def export_history_csv(history):
    """Export session history to CSV format string."""
    import csv
    import io
    if not history:
        return ''
    output = io.StringIO()
    fieldnames = list(history[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in history:
        writer.writerow(row)
    return output.getvalue()

def anonymize_report(report):
    """Remove any user-identifiable info from a report dict for sharing."""
    if isinstance(report, dict):
        report = dict(report)
        report.pop('user_id', None)
        report.pop('user_name', None)
    return report

def get_accessibility_tips():
    """Return a list of accessibility best practices for Gradio apps."""
    return [
        "Use clear labels and alt text for all images and buttons.",
        "Ensure keyboard navigation is possible for all interactive elements.",
        "Use sufficient color contrast and readable font sizes.",
        "Test with screen readers and mobile devices.",
        "Provide text alternatives for audio/voice features."
    ]

if __name__ == "__main__":
    # Sample session history for testing
    sample_history = [
        {"meal_date": "2025-06-01", "report": {"Calories": 500, "Protein": 30}},
        {"meal_date": "2025-06-02", "report": {"Calories": 600, "Protein": 35}},
        {"meal_date": "2025-06-03", "report": {"Calories": 550, "Protein": 32}},
        {"meal_date": "2025-06-04", "report": {"Calories": 700, "Protein": 40}},
        {"meal_date": "2025-06-05", "report": {"Calories": 650, "Protein": 38}},
        {"meal_date": "2025-06-06", "report": {"Calories": 620, "Protein": 36}},
        {"meal_date": "2025-06-07", "report": {"Calories": 610, "Protein": 34}},
    ]
    print("Testing gamify_user_progress:", gamify_user_progress(sample_history))
    print("Testing nutrition_trend_plot (should be a Plotly Figure):", nutrition_trend_plot(sample_history))
    print("Testing export_history_csv:")
    print(export_history_csv(sample_history))
    print("Testing anonymize_report:", anonymize_report({"user_id": 123, "user_name": "Test", "Calories": 500}))
    print("Testing get_accessibility_tips:", get_accessibility_tips())