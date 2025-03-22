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
        
        # Make preferences more prominent in the prompt
        preferences_text = ""
        if preferences and preferences.strip():
            preferences_text = f"""
            CRITICAL: The user has specified these preferences: "{preferences}"
            You MUST honor these preferences in ALL meal suggestions.
            Do not suggest meals that conflict with these preferences.
            """
        
        prompt = f"""Generate EXACTLY 3 affordable meal suggestions for {meal_type} within a budget of KES {budget}.
        
        {preferences_text}

        IMPORTANT GUIDELINES:
        1. You MUST generate EXACTLY 3 different meal options, no more and no less.
        
        2. Use REALISTIC PRICING for Kenyan ingredients. Here are some reference prices:
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
        
        3. USE THE FULL BUDGET effectively. The total cost should be between 70% and 95% of the budget (KES {budget}).
        
        4. For each meal suggestion, include:
           - A name for the meal
           - A descriptive paragraph (minimum 30 words)
           - A list of ingredients with SPECIFIC AMOUNTS and costs in KES
           - Step-by-step cooking instructions
           - Total estimated cost (sum of ingredients)
           - Nutritional information (calories, protein, carbs, fat) WITH PERCENTAGES (0-100%)
        
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
                "protein": percentage_value,
                "carbs": percentage_value,
                "fat": percentage_value
            }}
          }}
        ]
        
        The JSON MUST contain EXACTLY 3 meal options - if you return fewer or more than 3, your response will be rejected.
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
                            
                            # Ensure we have exactly 3 meal options
                            if len(meal_plans) != 3:
                                print(f"API returned {len(meal_plans)} meal options instead of 3, falling back to mock data")
                                return generate_mock_meal_plans(meal_type, budget, preferences)
                            
                            # Ensure nutritional info values are proper percentages
                            for meal in meal_plans:
                                if 'nutritional_info' in meal:
                                    nutrition = meal['nutritional_info']
                                    
                                    # Make sure protein, carbs and fat are percentages (0-100)
                                    for key in ['protein', 'carbs', 'fat']:
                                        if key in nutrition:
                                            value = nutrition[key]
                                            
                                            # Convert to number if it's a string
                                            if isinstance(value, str):
                                                # Extract numeric part
                                                numeric_value = re.match(r'(\d+(?:\.\d+)?)', value)
                                                if numeric_value:
                                                    value = float(numeric_value.group(1))
                                                else:
                                                    # Default percentage if parsing fails
                                                    value = 25  # Set a reasonable default
                                            
                                            # Ensure it's a percentage (0-100)
                                            if isinstance(value, (int, float)):
                                                # If value is too large to be a percentage (e.g., in grams), convert it
                                                if value > 100:
                                                    value = min(100, value / 3)  # Simple conversion
                                                
                                                # Store as number for the progress bar to work properly
                                                nutrition[key] = value
                            
                            return meal_plans
                        else:
                            # Try to parse the full content as JSON
                            content = content.strip()
                            if content.startswith("```json"):
                                content = content.replace("```json", "", 1)
                            if content.startswith("```"):
                                content = content.replace("```", "", 1)
                            if content.endswith("```"):
                                content = content[:content.rfind("```")]
                                
                            content = content.strip()
                            meal_plans = json.loads(content)
                            
                            # Ensure we have exactly 3 meal options
                            if not isinstance(meal_plans, list) or len(meal_plans) != 3:
                                print(f"API returned {len(meal_plans) if isinstance(meal_plans, list) else 'invalid'} data, falling back to mock data")
                                return generate_mock_meal_plans(meal_type, budget, preferences)
                            
                            # Process nutritional info
                            for meal in meal_plans:
                                if 'nutritional_info' in meal:
                                    nutrition = meal['nutritional_info']
                                    
                                    # Make sure protein, carbs and fat are percentages (0-100)
                                    for key in ['protein', 'carbs', 'fat']:
                                        if key in nutrition:
                                            value = nutrition[key]
                                            
                                            # Convert to number if it's a string
                                            if isinstance(value, str):
                                                # Extract numeric part
                                                numeric_value = re.match(r'(\d+(?:\.\d+)?)', value)
                                                if numeric_value:
                                                    value = float(numeric_value.group(1))
                                                else:
                                                    # Default percentage if parsing fails
                                                    value = 25  # Set a reasonable default
                                            
                                            # Ensure it's a percentage (0-100)
                                            if isinstance(value, (int, float)):
                                                # If value is too large to be a percentage (e.g., in grams), convert it
                                                if value > 100:
                                                    value = min(100, value / 3)  # Simple conversion
                                                
                                                # Store as number for the progress bar to work properly
                                                nutrition[key] = value
                            
                            return meal_plans
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {content}")
                        # Return mock data as fallback
                        return generate_mock_meal_plans(meal_type, budget, preferences)
                elif response.status_code == 429:  # Rate limit error
                    retries += 1
                    time.sleep(2 ** retries)  # Exponential backoff
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    return generate_mock_meal_plans(meal_type, budget, preferences)
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff
        
        return generate_mock_meal_plans(meal_type, budget, preferences)  # Return mock data if all retries fail
    except Exception as e:
        print(f"Error generating meal plans: {str(e)}")
        return generate_mock_meal_plans(meal_type, budget, preferences)  # Return mock data on any error

def generate_mock_meal_plans(meal_type, budget, preferences=None):
    """Generate mock meal plans when API fails"""
    budget_float = float(budget)
    target_cost = budget_float * 0.8  # Target 80% of the budget
    
    # Create an array of 3 meal plans for all meal types
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
                    "protein": 40,
                    "carbs": 35,
                    "fat": 25
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
                    "protein": 15,
                    "carbs": 80,
                    "fat": 5
                }
            },
            {
                "name": "Fruit and Yogurt Bowl",
                "description": "A refreshing and nutritious breakfast bowl with yogurt and seasonal fruits. This light yet satisfying option provides probiotics from yogurt and essential vitamins from fruits, giving you a healthy start to your day.",
                "ingredients": [
                    {"name": "Plain yogurt", "amount": "1 cup", "cost": 40.0},
                    {"name": "Banana", "amount": "1 medium", "cost": 15.0},
                    {"name": "Seasonal fruits", "amount": "1/2 cup chopped", "cost": 20.0},
                    {"name": "Honey", "amount": "1 tablespoon", "cost": 10.0}
                ],
                "instructions": [
                    "Pour yogurt into a bowl",
                    "Slice banana and add to the bowl",
                    "Add chopped seasonal fruits",
                    "Drizzle with honey and serve immediately"
                ],
                "total_cost": 85.0,
                "nutritional_info": {
                    "calories": "280 kcal",
                    "protein": 20,
                    "carbs": 60,
                    "fat": 10
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
                    "protein": 15,
                    "carbs": 75,
                    "fat": 10
                }
            },
            {
                "name": "Rice and Bean Stew",
                "description": "A hearty combination of fluffy rice and protein-rich bean stew that makes for a satisfying lunch. The beans provide plant-based protein while the aromatic rice creates a complete meal that will keep you full throughout the afternoon.",
                "ingredients": [
                    {"name": "Rice", "amount": "1 cup", "cost": 35.0},
                    {"name": "Beans", "amount": "1/2 cup", "cost": 20.0},
                    {"name": "Onion", "amount": "1 medium", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Spices", "amount": "to taste", "cost": 5.0}
                ],
                "instructions": [
                    "Boil beans until soft (or use pre-cooked beans)",
                    "In a separate pot, cook rice until fluffy",
                    "In a pan, heat oil and sauté onions until translucent",
                    "Add chopped tomatoes and spices and cook until soft",
                    "Add beans and simmer for 10 minutes",
                    "Serve bean stew over rice"
                ],
                "total_cost": 116.0,
                "nutritional_info": {
                    "calories": "450 kcal",
                    "protein": 20,
                    "carbs": 70,
                    "fat": 10
                }
            },
            {
                "name": "Vegetable Chapati Wrap",
                "description": "A flavorful wrap made with homemade chapati and fresh vegetables. This versatile lunch option is easy to customize, portable, and combines the softness of freshly made chapati with crunchy vegetables for a textural delight.",
                "ingredients": [
                    {"name": "Wheat flour", "amount": "1 cup", "cost": 25.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Cabbage", "amount": "1/4 head", "cost": 15.0},
                    {"name": "Onion", "amount": "1 small", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Mix flour, salt, and water to make chapati dough",
                    "Divide into balls and roll into flat circles",
                    "Cook chapatis on a hot pan until golden brown spots appear",
                    "Grate carrots and shred cabbage finely",
                    "Slice onion thinly and mix with vegetables",
                    "Place vegetables on chapati, roll up and serve"
                ],
                "total_cost": 81.0,
                "nutritional_info": {
                    "calories": "350 kcal",
                    "protein": 10,
                    "carbs": 55,
                    "fat": 35
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
                    "protein": 22,
                    "carbs": 68,
                    "fat": 10
                }
            },
            {
                "name": "Spaghetti with Vegetable Sauce",
                "description": "A comforting pasta dish with a rich vegetable sauce perfect for dinner. The sauce combines fresh vegetables and herbs for a nutritious and satisfying meal that's both economical and delicious.",
                "ingredients": [
                    {"name": "Spaghetti", "amount": "250g", "cost": 40.0},
                    {"name": "Tomatoes", "amount": "3 large", "cost": 45.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Boil spaghetti in salted water until al dente",
                    "Chop tomatoes, onion, and grate carrots",
                    "Heat oil in a pan and sauté onions until translucent",
                    "Add tomatoes and carrots and cook until soft",
                    "Season the sauce with salt",
                    "Drain pasta and mix with the sauce",
                    "Serve hot"
                ],
                "total_cost": 131.0,
                "nutritional_info": {
                    "calories": "450 kcal",
                    "protein": 12,
                    "carbs": 75,
                    "fat": 13
                }
            },
            {
                "name": "Chapati and Beef Stew",
                "description": "A hearty dinner combining soft chapati with rich beef stew. This classic Kenyan combination offers tender pieces of beef slow-cooked with vegetables in a flavorful broth, paired with freshly made chapati.",
                "ingredients": [
                    {"name": "Wheat flour", "amount": "2 cups", "cost": 50.0},
                    {"name": "Beef", "amount": "250g", "cost": 150.0},
                    {"name": "Potatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "3 tablespoons", "cost": 30.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Mix flour, salt, and water to make chapati dough and set aside",
                    "Cut beef into small pieces and boil until tender",
                    "In a pan, heat oil and sauté onions until golden",
                    "Add tomatoes and cook until soft",
                    "Add carrots, potatoes, and beef with some of the broth",
                    "Simmer until vegetables are tender and sauce thickens",
                    "Roll chapati dough into circles and cook on a hot pan",
                    "Serve chapati with beef stew"
                ],
                "total_cost": 316.0,
                "nutritional_info": {
                    "calories": "680 kcal",
                    "protein": 35,
                    "carbs": 50,
                    "fat": 15
                }
            }
        ] 