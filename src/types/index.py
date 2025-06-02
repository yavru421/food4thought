# This file contains type definitions and interfaces used throughout the application.

from typing import List, Dict, Any

class MealImageAnalysisResult:
    def __init__(self, ingredients: List[str], calories: float, protein: float, fat: float, carbohydrates: float):
        self.ingredients = ingredients
        self.calories = calories
        self.protein = protein
        self.fat = fat
        self.carbohydrates = carbohydrates

class NutritionReport:
    def __init__(self, meal_name: str, analysis_result: MealImageAnalysisResult):
        self.meal_name = meal_name
        self.analysis_result = analysis_result

    def generate_report(self) -> Dict[str, Any]:
        return {
            "meal_name": self.meal_name,
            "ingredients": self.analysis_result.ingredients,
            "calories": self.analysis_result.calories,
            "protein": self.analysis_result.protein,
            "fat": self.analysis_result.fat,
            "carbohydrates": self.analysis_result.carbohydrates,
        }