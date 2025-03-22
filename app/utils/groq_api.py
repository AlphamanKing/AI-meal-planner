import requests
import json
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_meal_plans(meal_type, budget, preferences=None):
    """
    Generate meal plans based on user inputs using Groq API (LLaMA 3)
    
    Args:
        meal_type (str): Breakfast, Lunch, or Supper
        budget (float): Budget in KES
        preferences (str, optional): User's meal preferences
        
    Returns:
        list: List of 3 meal plan options in dict format
    """
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Generate 3 affordable meal suggestions for {meal_type} within a budget of KES {budget}.
        
        {f'Consider these preferences: {preferences}' if preferences else ''}

        IMPORTANT GUIDELINES:
        1. Use REALISTIC PRICING for Kenyan ingredients. Here are some reference prices:
           - Single egg: 15 KES
           - Loaf of bread: 60 KES
           - 1 cup of rice: 35 KES
           - 1 cup of beans: 40 KES
           - 1 cup of milk: 25 KES
           - 1 large tomato: 15 KES
           - 1 large onion: 20 KES
           - 1 bunch kale (sukuma wiki): 30-40 KES
           - 1 cup flour (maize/wheat): 30 KES
           - Cooking oil (tablespoon): 10 KES
        
        2. USE THE FULL BUDGET effectively. The total cost should be between 70% and 95% of the budget (KES {budget}).
        
        3. For each meal suggestion, include:
           - A name for the meal
           - A descriptive paragraph (minimum 30 words)
           - A list of ingredients with SPECIFIC AMOUNTS and costs in KES
           - Step-by-step cooking instructions
           - Total estimated cost (sum of ingredients)
           - Nutritional information (calories, protein, carbs, fat) WITH UNITS
        
        Format as valid JSON with this structure:
        [
          {{
            "name": "Meal Name",
            "description": "Detailed description of the meal, ingredients and nutritional benefits",
            "ingredients": [
                {{"name": "Ingredient", "amount": "specific amount", "cost": cost_in_kes}}
            ],
            "instructions": ["Step 1", "Step 2", "Step 3"],
            "total_cost": total_cost_in_kes,
            "nutritional_info": {{
                "calories": "value kcal",
                "protein": "value g",
                "carbs": "value g",
                "fat": "value g"
            }}
          }}
        ]
        
        Return ONLY a valid JSON array with no additional text.
        """
        
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        # Retry mechanism
        max_retries = 3
        retries = 0
        
        while retries < max_retries:
            try:
                response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    response_json = response.json()
                    content = response_json["choices"][0]["message"]["content"]
                    
                    # Extract JSON from the content
                    try:
                        # Try to find JSON array in the content using regex
                        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                        
                        if json_match:
                            json_str = json_match.group(0)
                            # Clean up any potential string format issues
                            json_str = json_str.replace("'", '"')
                            
                            # Parse the JSON
                            meal_plans = json.loads(json_str)
                            
                            # Ensure nutritional info values have units and create numeric versions
                            for meal in meal_plans:
                                if 'nutritional_info' in meal:
                                    # Create a clean version for numeric operations but preserve the display values
                                    numeric_info = {}
                                    for key, value in meal['nutritional_info'].items():
                                        if isinstance(value, str):
                                            # Extract numeric part if value has units (like "5g")
                                            numeric_value = re.match(r'(\d+(?:\.\d+)?)', value)
                                            if numeric_value:
                                                numeric_info[key] = float(numeric_value.group(1))
                                        elif isinstance(value, (int, float)):
                                            # If it's already a number, use default units
                                            if key == 'calories':
                                                meal['nutritional_info'][key] = f"{value} kcal"
                                            else:
                                                meal['nutritional_info'][key] = f"{value} g"
                                            numeric_info[key] = value
                                    
                                    # Add numeric values for calculations if needed
                                    meal['numeric_nutritional_info'] = numeric_info
                            
                            return meal_plans
                        else:
                            # If no JSON array found, try to find any JSON-like structure
                            print(f"Failed to extract JSON array, attempting to parse full content")
                            # Remove any text before and after JSON
                            content = content.strip()
                            if content.startswith("```json"):
                                content = content.replace("```json", "", 1)
                            if content.startswith("```"):
                                content = content.replace("```", "", 1)
                            if content.endswith("```"):
                                content = content[:content.rfind("```")]
                                
                            content = content.strip()
                            meal_plans = json.loads(content)
                            
                            # Ensure nutritional info values have units
                            if isinstance(meal_plans, list):
                                for meal in meal_plans:
                                    if 'nutritional_info' in meal:
                                        # Create a clean version for numeric operations but preserve the display values
                                        numeric_info = {}
                                        for key, value in meal['nutritional_info'].items():
                                            if isinstance(value, str):
                                                # Extract numeric part if value has units (like "5g")
                                                numeric_value = re.match(r'(\d+(?:\.\d+)?)', value)
                                                if numeric_value:
                                                    numeric_info[key] = float(numeric_value.group(1))
                                            elif isinstance(value, (int, float)):
                                                # If it's already a number, use default units
                                                if key == 'calories':
                                                    meal['nutritional_info'][key] = f"{value} kcal"
                                                else:
                                                    meal['nutritional_info'][key] = f"{value} g"
                                                numeric_info[key] = value
                                        
                                        # Add numeric values for calculations if needed
                                        meal['numeric_nutritional_info'] = numeric_info
                            
                            return meal_plans
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {content}")
                        # Return mock data as fallback
                        return generate_mock_meal_plans(meal_type, budget)
                elif response.status_code == 429:  # Rate limit error
                    retries += 1
                    time.sleep(2 ** retries)  # Exponential backoff
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    return generate_mock_meal_plans(meal_type, budget)
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff
        
        return generate_mock_meal_plans(meal_type, budget)  # Return mock data if all retries fail
    except Exception as e:
        print(f"Error generating meal plans: {str(e)}")
        return generate_mock_meal_plans(meal_type, budget)  # Return mock data on any error

def generate_mock_meal_plans(meal_type, budget):
    """Generate mock meal plans when API fails"""
    budget_float = float(budget)
    target_cost = budget_float * 0.8  # Target 80% of the budget
    
    if meal_type == "Breakfast":
        return [
            {
                "name": "Simple Toast and Eggs",
                "description": "A classic breakfast of toast with fried eggs, providing a perfect balance of carbohydrates and protein to start your day energized. This simple yet satisfying meal is quick to prepare and uses affordable ingredients.",
                "ingredients": [
                    {"name": "Bread", "amount": "2 slices", "cost": 20.0},
                    {"name": "Eggs", "amount": "2 large", "cost": 30.0},
                    {"name": "Butter", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "1 pinch", "cost": 1.0}
                ],
                "instructions": [
                    "Toast the bread until golden brown",
                    "Heat the butter in a pan over medium heat",
                    "Crack the eggs into the pan and fry to your preference",
                    "Add salt to taste",
                    "Serve eggs on top of the buttered toast"
                ],
                "total_cost": 61.0,
                "nutritional_info": {
                    "calories": "320 kcal",
                    "protein": "16 g",
                    "carbs": "28 g",
                    "fat": "18 g"
                },
                "numeric_nutritional_info": {
                    "calories": 320,
                    "protein": 16,
                    "carbs": 28,
                    "fat": 18
                }
            },
            {
                "name": "Kenyan Uji (Porridge)",
                "description": "Traditional Kenyan porridge made with millet flour, perfect for a warming breakfast. This nutritious staple provides sustained energy throughout the morning and can be sweetened to taste with honey or sugar.",
                "ingredients": [
                    {"name": "Millet flour", "amount": "1/2 cup", "cost": 20.0},
                    {"name": "Water", "amount": "2 cups", "cost": 0.0},
                    {"name": "Milk", "amount": "1/2 cup", "cost": 15.0},
                    {"name": "Sugar", "amount": "2 tablespoons", "cost": 10.0}
                ],
                "instructions": [
                    "Mix flour with 1 cup of cold water to make a smooth paste",
                    "Boil the remaining water in a pot",
                    "Gradually add the flour mixture to the boiling water, stirring continuously",
                    "Cook on low heat for 5-7 minutes, stirring to prevent lumps",
                    "Add milk and sugar to taste"
                ],
                "total_cost": 45.0,
                "nutritional_info": {
                    "calories": "220 kcal",
                    "protein": "5 g",
                    "carbs": "45 g",
                    "fat": "2 g"
                },
                "numeric_nutritional_info": {
                    "calories": 220,
                    "protein": 5,
                    "carbs": 45,
                    "fat": 2
                }
            }
        ]
    elif meal_type == "Lunch":
        return [
            {
                "name": "Ugali with Sukuma Wiki",
                "description": "Traditional Kenyan meal with maize meal and kale, a staple combination that's both nutritious and filling. Sukuma wiki (kale) is rich in vitamins while ugali provides the energy-giving carbohydrates needed for an active day.",
                "ingredients": [
                    {"name": "Maize flour", "amount": "2 cups", "cost": 30.0},
                    {"name": "Sukuma wiki (kale)", "amount": "1 bunch", "cost": 35.0},
                    {"name": "Onion", "amount": "1 medium", "cost": 15.0},
                    {"name": "Tomato", "amount": "1 large", "cost": 15.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Boil 4 cups of water in a pot",
                    "Add maize flour gradually while stirring to avoid lumps", 
                    "Cook ugali until firm, stirring regularly",
                    "In a separate pan, heat oil and fry onions until translucent",
                    "Add chopped tomatoes and cook until soft",
                    "Add chopped sukuma wiki and cook until tender",
                    "Season with salt to taste and serve with ugali"
                ],
                "total_cost": 106.0,
                "nutritional_info": {
                    "calories": "480 kcal",
                    "protein": "12 g",
                    "carbs": "80 g",
                    "fat": "8 g"
                },
                "numeric_nutritional_info": {
                    "calories": 480,
                    "protein": 12,
                    "carbs": 80,
                    "fat": 8
                }
            }
        ]
    else:  # Supper
        return [
            {
                "name": "Rice and Beans Dinner",
                "description": "A wholesome and filling combination of rice and beans that delivers complete proteins. This economical and satisfying meal is enhanced with aromatic onions and spices for a flavorful dinner option.",
                "ingredients": [
                    {"name": "Rice", "amount": "1 cup", "cost": 35.0},
                    {"name": "Beans", "amount": "1/2 cup (dry)", "cost": 25.0},
                    {"name": "Onion", "amount": "1 medium", "cost": 15.0},
                    {"name": "Tomato", "amount": "1 large", "cost": 15.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Spices", "amount": "1 teaspoon", "cost": 5.0}
                ],
                "instructions": [
                    "Soak beans for at least 4 hours or overnight",
                    "Cook beans until soft (about 1 hour)",
                    "In a separate pot, cook rice until fluffy",
                    "In a pan, fry onions until golden brown",
                    "Add tomatoes and spices and cook for 3-5 minutes",
                    "Add the cooked beans to the onion-tomato mixture",
                    "Mix well and simmer for 5 minutes",
                    "Serve the beans over rice"
                ],
                "total_cost": 106.0,
                "nutritional_info": {
                    "calories": "520 kcal",
                    "protein": "18 g",
                    "carbs": "90 g",
                    "fat": "7 g"
                },
                "numeric_nutritional_info": {
                    "calories": 520,
                    "protein": 18,
                    "carbs": 90,
                    "fat": 7
                }
            }
        ] 