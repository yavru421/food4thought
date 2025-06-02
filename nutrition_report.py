from groq import Groq
import os
import json

def generate_nutrition_report(analysis_results):
    # If a single dict, wrap in list for uniformity
    if isinstance(analysis_results, dict):
        analysis_results = [analysis_results]
    if not isinstance(analysis_results, list):
        return f"Error: Unexpected analysis result format: {analysis_results}"
    # Aggregate totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    total_fiber = 0
    all_vitamins = set()
    all_minerals = set()
    meal_type = analysis_results[0].get('meal_type', 'Unknown') if analysis_results else 'Unknown'
    meal_date = analysis_results[0].get('meal_date', 'Unknown') if analysis_results else 'Unknown'
    report_lines = [f"Meal Type: {meal_type}", f"Meal Date: {meal_date}", ""]
    for idx, result in enumerate(analysis_results):
        if result.get("error"):
            report_lines.append(f"Image {result.get('image_index', idx+1)}: Error: {result['error']}")
            continue
        name = result.get("meal_name", f"Meal Image {result.get('image_index', idx+1)}")
        calories = result.get("calories", 0)
        protein = result.get("protein", 0)
        carbs = result.get("carbohydrates", 0)
        fats = result.get("fats", 0)
        fiber = result.get("fiber", 0)
        vitamins = result.get("vitamins", [])
        minerals = result.get("minerals", [])
        total_calories += calories if isinstance(calories, (int, float)) else 0
        total_protein += protein if isinstance(protein, (int, float)) else 0
        total_carbs += carbs if isinstance(carbs, (int, float)) else 0
        total_fats += fats if isinstance(fats, (int, float)) else 0
        total_fiber += fiber if isinstance(fiber, (int, float)) else 0
        all_vitamins.update(vitamins)
        all_minerals.update(minerals)
        report_lines.append(f"Image {result.get('image_index', idx+1)} - {name}:")
        report_lines.append(f"  Calories: {calories} kcal")
        report_lines.append(f"  Protein: {protein} g")
        report_lines.append(f"  Carbohydrates: {carbs} g")
        report_lines.append(f"  Fats: {fats} g")
        report_lines.append(f"  Fiber: {fiber} g")
        report_lines.append(f"  Vitamins: {', '.join(vitamins) if vitamins else 'None'}")
        report_lines.append(f"  Minerals: {', '.join(minerals) if minerals else 'None'}")
        report_lines.append("")
    # Full Plate Total
    report_lines.append("---\nFull Plate Total:")
    report_lines.append(f"Total Calories: {total_calories} kcal")
    report_lines.append(f"Total Protein: {total_protein} g")
    report_lines.append(f"Total Carbohydrates: {total_carbs} g")
    report_lines.append(f"Total Fats: {total_fats} g")
    report_lines.append(f"Total Fiber: {total_fiber} g")
    report_lines.append(f"All Vitamins: {', '.join(sorted(all_vitamins)) if all_vitamins else 'None'}")
    report_lines.append(f"All Minerals: {', '.join(sorted(all_minerals)) if all_minerals else 'None'}")
    # Compose the summary for Compound-Beta
    summary = '\n'.join(report_lines)
    # Call Compound-Beta for the final natural language report
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return summary + "\n\n[Warning: No API key found for Compound-Beta summary.]"
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Given the following meal nutrition analysis, provide a clear, concise, and insightful summary for the user.\n\n{summary}"}],
            model="compound-beta"
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return summary + f"\n\n[Compound-Beta summary failed: {e}]"

def save_report_to_file(report, filename="nutrition_report.txt"):
    with open(filename, 'w') as file:
        file.write(report)