import requests
import json
import os
import time
import re
from dotenv import load_dotenv
import random

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Add fallback model if Groq is unavailable
def get_model_api_details():
    """Get API details based on available API keys"""
    if GROQ_API_KEY:
        # Only use the model that isn't decommissioned
        return {
            "api_url": GROQ_API_URL,
            "api_key": GROQ_API_KEY,
            "model": "llama3-70b-8192",  
            "headers": {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
        }
    else:
        # Using mock data instead since no API keys are available
        print("No API keys found, will use mock data")
        return None

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
        # Check API key presence and validity
        if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
            print("WARNING: GROQ_API_KEY environment variable is missing or empty")
            # Still try to get API details in case there's a fallback mechanism
        
        # Get API details
        api_details = get_model_api_details()
        
        # If no API available, use mock data
        if not api_details:
            print("No API details available, using mock data")
            return generate_mock_meal_plans(meal_type, budget, preferences)
        
        print(f"Using API model: {api_details['model']}")
        print(f"Processing request for {meal_type} with budget {budget} and preferences: {preferences}")
        
        # Make preferences more prominent in the prompt
        preferences_text = ""
        if preferences and preferences.strip():
            preferences_text = f"""
            ===== HIGHEST PRIORITY REQUIREMENT =====
            
            User preferences: "{preferences}"
            
            THESE PREFERENCES MUST BE RESPECTED IN ALL MEAL SUGGESTIONS.
            
            The inclusion of requested items (e.g., "strong tea", "tangawizi", etc.) is MORE IMPORTANT 
            than meeting the exact budget target. A meal that includes the requested preferences but
            costs slightly less than the target budget is BETTER than a meal that ignores preferences.
            
            Specific requirements:
            - If user asks for specific foods/drinks (e.g., "tea", "chapati"), INCLUDE them in at least one meal
            - For dietary preferences (vegetarian, vegan, etc.), follow them strictly for ALL meals
            - For food avoidances ("no X"), NEVER include those ingredients
            - For allergies, strictly avoid all forms of those ingredients
            - Respect cultural or religious food restrictions absolutely
            
            This is your TOP PRIORITY instruction.
            """
        
        prompt = f"""Generate EXACTLY 3 affordable meal suggestions for {meal_type} within a budget of KES {budget}.
        
        {preferences_text}

        BUDGET GUIDELINES:
        1. Aim to have each meal cost APPROXIMATELY KES {budget}.
        2. The total_cost should ideally be between 50% and 100% of the budget (KES {budget * 0.5:.0f} to KES {budget:.0f}).
        3. Meals costing LESS than the budget are ACCEPTABLE and PREFERRED over those exceeding it.
        4. NEVER generate meals that cost more than 110% of the budget (KES {budget * 1.1:.0f}).
        5. Double-check all ingredient costs and ensure they sum to the total_cost.
        
        Additional guidelines:
        1. You MUST generate EXACTLY 3 different meal options, no more and no less.
        
        2. Use REALISTIC PRICING for Kenyan ingredients. Here are some reference prices:
           - Single egg: 15 KES
           - Loaf of bread: 60 KES
           - 1 cup of rice: 35 KES
           - 1 cup of beans: 40 KES
           - 1 cup of milk: 25 KES
           - 1 large tomato: 15 KES
           - 1 large onion: 20 KES
           - 1 bunch kale (sukuma wiki): 10-15 KES
           - 1 cup flour (maize/wheat): 30 KES
           - Cooking oil (tablespoon): 10 KES
        
        3. For each meal suggestion, you MUST include:
           - A name for the meal that ACCURATELY describes its contents
           - A descriptive paragraph (minimum 30 words)
           - A detailed list of ingredients with SPECIFIC AMOUNTS and costs in KES (at least 3-5 ingredients per meal)
           - Step-by-step cooking instructions (at least 3 specific steps)
           - Total estimated cost (sum of ingredients) - MUST be within the budget range
           - Nutritional information (calories, protein, carbs, fat) WITH PERCENTAGES (0-100%)
        
        REQUIRED JSON FORMAT:
        {{
          "meals": [
            {{
              "name": "Meal Name",
              "description": "Detailed description of the meal, ingredients and nutritional benefits",
              "ingredients": [
                  {{"name": "Ingredient 1", "amount": "specific amount", "cost": numeric_cost_only}},
                  {{"name": "Ingredient 2", "amount": "specific amount", "cost": numeric_cost_only}},
                  {{"name": "Ingredient 3", "amount": "specific amount", "cost": numeric_cost_only}}
              ],
              "instructions": ["Step 1", "Step 2", "Step 3"],
              "total_cost": numeric_cost_only,
              "nutritional_info": {{
                  "calories": "value kcal",
                  "protein": percentage_value,
                  "carbs": percentage_value,
                  "fat": percentage_value
              }}
            }},
            ... 2 more meal objects ...
          ]
        }}
        
        FINAL CHECK BEFORE RESPONDING:
        1. Verify your response is a SINGLE valid JSON object with a "meals" array containing EXACTLY 3 items
        2. Verify each meal has a realistic name that matches its ingredients
        3. Verify each meal has at least 3 ingredients with specific amounts and numeric costs
        4. Verify each meal has at least 3 specific cooking instructions
        5. Verify all ingredient costs sum to the total_cost value
        6. If user specified preferences, verify each meal strictly follows ALL preferences
        
        Return ONLY the JSON object with no additional text or explanation.
        """
        
        data = {
            "model": api_details["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}
        }
        
        # Simplify the API call since we're only using one model now
        max_retries = 3
        retries = 0
        current_model = api_details["model"]
        
        while retries < max_retries:
            try:
                print(f"Attempting API call with model: {current_model}")
                response = requests.post(api_details["api_url"], headers=api_details["headers"], json=data, timeout=30)
                
                # More detailed logging for API responses
                print(f"API Status Code: {response.status_code}")
                if response.status_code != 200:
                    print(f"API Error Response: {response.text[:500]}")  # Print first 500 chars of error
                    
                    # On error, retry
                    retries += 1
                    time.sleep(2 ** retries)  # Exponential backoff
                    continue
                    
                # Process successful response
                response_json = response.json()
                content = response_json["choices"][0]["message"]["content"]
                
                # Debug log the response content
                print(f"API Response Content: {content[:200]}...")  # Print first 200 chars for debugging
                
                # Extract JSON from the content
                try:
                    # Use our robust JSON parsing helper
                    meal_plans, method = try_parse_json(content)
                    
                    if meal_plans:
                        print(f"Successfully parsed JSON response using method: {method}")
                        
                        # Ensure we have exactly 3 meal options
                        if not isinstance(meal_plans, list) or len(meal_plans) != 3:
                            print(f"API returned {len(meal_plans) if isinstance(meal_plans, list) else 'invalid'} data structure, falling back to mock data")
                            return generate_mock_meal_plans(meal_type, budget, preferences)
                        
                        # Check budget adherence
                        budget_float = float(budget)
                        min_acceptable = budget_float * 0.5  # Allow meals as low as 50% of budget
                        max_acceptable = budget_float * 1.1  # Allow meals up to 110% of budget
                        
                        # Count how many meals are outside budget constraints
                        meals_outside_budget = 0
                        for meal in meal_plans:
                            if 'total_cost' in meal:
                                try:
                                    cost = float(meal['total_cost'])
                                    if cost < min_acceptable or cost > max_acceptable:
                                        meals_outside_budget += 1
                                        print(f"Meal '{meal.get('name', 'unknown')}' with cost {cost} is outside budget range {min_acceptable:.2f}-{max_acceptable:.2f}")
                                except (ValueError, TypeError) as e:
                                    print(f"Error converting cost: {str(e)}")
                                    try:
                                        # If we can extract a number from the total_cost, try to use that
                                        if isinstance(meal['total_cost'], str):
                                            match = re.search(r'(\d+(?:\.\d+)?)', meal['total_cost'])
                                            if match:
                                                cost = float(match.group(1))
                                                print(f"Extracted cost {cost} from '{meal['total_cost']}'")
                                                if cost < min_acceptable or cost > max_acceptable:
                                                    meals_outside_budget += 1
                                                    print(f"Meal '{meal.get('name', 'unknown')}' with extracted cost {cost} is outside budget range {min_acceptable:.2f}-{max_acceptable:.2f}")
                                                continue
                                    except Exception as nested_e:
                                        print(f"Failed to extract cost: {str(nested_e)}")
                                        
                                    meals_outside_budget += 1
                                    print(f"Meal '{meal.get('name', 'unknown')}' has invalid cost format: {meal.get('total_cost')}")
                        
                        # Only fall back to mock data if ALL meals are outside budget constraints
                        if meals_outside_budget == 3:
                            print(f"All meals are outside budget constraints, falling back to mock data")
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
                        
                        # Check preference adherence
                        if preferences and preferences.strip():
                            meals_violating_preferences = 0
                            for idx, meal in enumerate(meal_plans):
                                adheres, reason = check_preferences_adherence(meal, preferences)
                                if not adheres:
                                    print(f"Meal {idx+1} '{meal.get('name', 'unknown')}' violates preferences: {reason}")
                                    meals_violating_preferences += 1
                            
                            # If more than one meal violates preferences, fall back to mock data
                            if meals_violating_preferences > 1:
                                print(f"{meals_violating_preferences} meals violate user preferences, falling back to mock data")
                                return generate_mock_meal_plans(meal_type, budget, preferences)
                        
                        return meal_plans
                    else:
                        print("JSON parsing failed completely")
                        return generate_mock_meal_plans(meal_type, budget, preferences)
                        
                except Exception as e:
                    print(f"Error processing API response: {str(e)}")
                    print(f"Problematic content: {content[:500]}")  # Show more content for debugging
                    return generate_mock_meal_plans(meal_type, budget, preferences)
                    
            except requests.exceptions.RequestException as e:
                print(f"Request error: {str(e)}")
                retries += 1
                if retries >= max_retries:
                    return generate_mock_meal_plans(meal_type, budget, preferences)
                time.sleep(2 ** retries)  # Exponential backoff
                
        # If we've exhausted all retries
        print("All API call attempts failed. Using mock data instead.")
        return generate_mock_meal_plans(meal_type, budget, preferences)
    except Exception as e:
        print(f"Error generating meal plans: {str(e)}")
        return generate_mock_meal_plans(meal_type, budget, preferences)  # Return mock data on any error

def generate_mock_meal_plans(meal_type, budget, preferences=None):
    """Generate mock meal plans as fallback"""
    print(f"Generating mock meal plans for {meal_type} with budget {budget} and preferences: {preferences}")
    return mock_meal_plans(meal_type, budget, preferences)

def check_preferences_adherence(meal, preferences):
    """
    Check if a meal adheres to user preferences
    
    Args:
        meal (dict): Meal data dictionary
        preferences (str): User preferences string
        
    Returns:
        tuple: (adheres_to_preferences, reason)
    """
    if not preferences or not preferences.strip():
        return True, ""  # No preferences specified
    
    preferences = preferences.lower()
    meal_str = json.dumps(meal).lower()  # Convert the entire meal to string for easy searching
    
    # Check if user asked for specific items to be included
    preference_items = []
    for item in ["tea", "coffee", "tangawizi", "ginger", "chapati", "ugali", "rice", "beans"]:
        if item in preferences:
            preference_items.append(item)
    
    # Check if any of the requested items are in the meal
    if preference_items:
        found_items = []
        for item in preference_items:
            if item in meal_str:
                found_items.append(item)
        
        if not found_items and len(preference_items) > 0:
            return False, f"Meal doesn't include any of the requested items: {', '.join(preference_items)}"
    
    # Common dietary preferences checking
    if "vegetarian" in preferences:
        meat_keywords = ["beef", "chicken", "pork", "mutton", "lamb", "meat", "fish", "sausage", "bacon", "ham"]
        for keyword in meat_keywords:
            if keyword in meal_str:
                return False, f"Meal contains '{keyword}' but user requested vegetarian"
    
    if "vegan" in preferences:
        animal_product_keywords = ["milk", "cheese", "butter", "ghee", "cream", "egg", "yogurt", "meat", "fish", "honey"]
        for keyword in animal_product_keywords:
            if keyword in meal_str:
                return False, f"Meal contains '{keyword}' but user requested vegan"
    
    # Check for specific food exclusions
    exclusion_phrases = ["no ", "without ", "don't want ", "exclude ", "allergy to "]
    for phrase in exclusion_phrases:
        for word in preferences.split():
            if phrase + word in preferences:
                excluded_item = word.strip()
                if excluded_item and excluded_item in meal_str:
                    return False, f"Meal contains '{excluded_item}' but user requested to exclude it"
    
    # Individual items exclusion
    for exclusion in ["no beef", "no chicken", "no pork", "no fish", "no nuts", "no wheat", "no gluten", "no dairy"]:
        if exclusion in preferences:
            excluded_item = exclusion.split("no ")[1].strip()
            if excluded_item and excluded_item in meal_str:
                return False, f"Meal contains '{excluded_item}' but user requested to exclude it"
    
    return True, "" 

def create_vegetarian_mock_meals(meal_type, budget):
    """Generate vegetarian mock meal plans"""
    budget_float = float(budget)
    
    if meal_type == "Breakfast":
        return [
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
                "name": "Vegetable Sandwich",
                "description": "A wholesome sandwich packed with fresh vegetables and a smooth avocado spread. This satisfying breakfast option provides a good balance of carbohydrates, healthy fats, and vitamins to energize your morning.",
                "ingredients": [
                    {"name": "Bread", "amount": "2 slices", "cost": 20.0},
                    {"name": "Avocado", "amount": "1/2 medium", "cost": 25.0},
                    {"name": "Tomato", "amount": "1 medium", "cost": 15.0},
                    {"name": "Lettuce", "amount": "2 leaves", "cost": 10.0},
                    {"name": "Cucumber", "amount": "4 slices", "cost": 10.0},
                    {"name": "Salt", "amount": "1 pinch", "cost": 1.0}
                ],
                "instructions": [
                    "Mash the avocado with a fork and spread on one slice of bread",
                    "Sprinkle with a pinch of salt",
                    "Layer tomato slices, lettuce, and cucumber on top",
                    "Cover with the second slice of bread",
                    "Cut in half and serve"
                ],
                "total_cost": 81.0,
                "nutritional_info": {
                    "calories": "310 kcal",
                    "protein": 10,
                    "carbs": 45,
                    "fat": 15
                }
            }
        ]
    elif meal_type == "Lunch":
        return [
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
            },
            {
                "name": "Sukuma Wiki with Ugali",
                "description": "A classic Kenyan vegetarian meal featuring sukuma wiki (kale) served with ugali. This nutritious combination provides plenty of minerals from the greens and energy from the ugali, making for a satisfying and economical lunch.",
                "ingredients": [
                    {"name": "Sukuma wiki (kale)", "amount": "1 bunch", "cost": 35.0},
                    {"name": "Onion", "amount": "1 medium", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Maize flour", "amount": "2 cups", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Chop sukuma wiki, tomatoes, and onion",
                    "Heat oil in a pan and sauté onions until translucent",
                    "Add tomatoes and cook until soft",
                    "Add sukuma wiki and cook until tender",
                    "Season with salt",
                    "In a separate pot, boil water and add maize flour gradually while stirring",
                    "Cook ugali until firm, stirring regularly",
                    "Serve sukuma wiki with ugali"
                ],
                "total_cost": 121.0,
                "nutritional_info": {
                    "calories": "420 kcal",
                    "protein": 12,
                    "carbs": 70,
                    "fat": 8
                }
            },
            {
                "name": "Bean and Vegetable Stew",
                "description": "A hearty vegetarian stew combining protein-rich beans with assorted vegetables. This nutrient-dense dish provides sustained energy and is packed with fiber, vitamins, and minerals for a healthy and filling lunch option.",
                "ingredients": [
                    {"name": "Beans", "amount": "1 cup", "cost": 40.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Potatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Spices", "amount": "to taste", "cost": 5.0}
                ],
                "instructions": [
                    "Soak beans overnight and cook until soft",
                    "Chop all vegetables into bite-sized pieces",
                    "Heat oil in a large pot and sauté onions until translucent",
                    "Add tomatoes and cook until soft",
                    "Add carrots and potatoes, cook for 5 minutes",
                    "Add cooked beans and enough water to cover",
                    "Season with salt and spices",
                    "Simmer until vegetables are tender and flavors combine"
                ],
                "total_cost": 141.0,
                "nutritional_info": {
                    "calories": "480 kcal",
                    "protein": 18,
                    "carbs": 65,
                    "fat": 12
                }
            }
        ]
    else:  # Supper
        return [
            {
                "name": "Vegetable Rice Pilau",
                "description": "A fragrant rice dish cooked with aromatic spices and mixed vegetables. This vegetarian version of the popular East African rice pilau is full of flavor and makes for a satisfying and complete evening meal.",
                "ingredients": [
                    {"name": "Rice", "amount": "2 cups", "cost": 70.0},
                    {"name": "Mixed vegetables", "amount": "2 cups", "cost": 50.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                    {"name": "Pilau masala", "amount": "1 tablespoon", "cost": 15.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Rinse rice and soak for 30 minutes, then drain",
                    "Heat oil and sauté onions until golden brown",
                    "Add garlic and pilau masala, cook for 1 minute until fragrant",
                    "Add mixed vegetables and sauté for 5 minutes",
                    "Add rice and stir to coat with spices",
                    "Add water (1:2 ratio rice to water) and salt",
                    "Bring to a boil, then reduce heat and cover",
                    "Simmer until rice is tender and water is absorbed"
                ],
                "total_cost": 176.0,
                "nutritional_info": {
                    "calories": "520 kcal",
                    "protein": 12,
                    "carbs": 85,
                    "fat": 15
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
                    {"name": "Bell pepper", "amount": "1 medium", "cost": 20.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Mixed herbs", "amount": "1 teaspoon", "cost": 5.0}
                ],
                "instructions": [
                    "Boil spaghetti in salted water until al dente",
                    "Chop all vegetables into small pieces",
                    "Heat oil in a pan and sauté onions until translucent",
                    "Add tomatoes and cook until soft",
                    "Add remaining vegetables and herbs",
                    "Simmer for 15 minutes until sauce thickens",
                    "Season with salt to taste",
                    "Drain pasta and mix with the sauce"
                ],
                "total_cost": 156.0,
                "nutritional_info": {
                    "calories": "450 kcal",
                    "protein": 12,
                    "carbs": 75,
                    "fat": 13
                }
            },
            {
                "name": "Mixed Bean Curry with Chapati",
                "description": "A hearty and protein-rich bean curry served with soft homemade chapati. This nutritious vegetarian dinner offers a perfect balance of proteins, complex carbohydrates, and essential nutrients in a flavorful and filling package.",
                "ingredients": [
                    {"name": "Mixed beans", "amount": "1.5 cups", "cost": 60.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 large", "cost": 30.0},
                    {"name": "Wheat flour", "amount": "2 cups", "cost": 50.0},
                    {"name": "Cooking oil", "amount": "3 tablespoons", "cost": 30.0},
                    {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                    {"name": "Curry spices", "amount": "2 teaspoons", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Soak beans overnight, then cook until soft",
                    "For chapati: Mix flour, water, salt to make dough; rest for 30 minutes",
                    "Roll dough into flat circles and cook on hot pan until golden spots appear",
                    "For curry: Sauté onions and garlic in oil until golden",
                    "Add tomatoes and cook until soft",
                    "Add curry spices and stir for 1 minute",
                    "Add cooked beans and simmer for 15 minutes",
                    "Serve bean curry with hot chapati"
                ],
                "total_cost": 201.0,
                "nutritional_info": {
                    "calories": "580 kcal",
                    "protein": 25,
                    "carbs": 80,
                    "fat": 18
                }
            }
        ]
        
def create_vegan_mock_meals(meal_type, budget):
    """Generate vegan mock meal plans"""
    budget_float = float(budget)
    
    if meal_type == "Breakfast":
        return [
            {
                "name": "Fruit Oatmeal Bowl",
                "description": "A hearty and energizing vegan breakfast featuring oats cooked to creamy perfection and topped with fresh seasonal fruits. This nutritious start to your day provides sustained energy from complex carbohydrates and natural fruit sugars.",
                "ingredients": [
                    {"name": "Oats", "amount": "1 cup", "cost": 25.0},
                    {"name": "Water", "amount": "2 cups", "cost": 0.0},
                    {"name": "Banana", "amount": "1 medium", "cost": 15.0},
                    {"name": "Seasonal fruits", "amount": "1/2 cup chopped", "cost": 20.0},
                    {"name": "Sugar", "amount": "1 tablespoon", "cost": 5.0}
                ],
                "instructions": [
                    "Boil water in a pot",
                    "Add oats and reduce heat to medium-low",
                    "Cook for 5-7 minutes, stirring occasionally, until creamy",
                    "Add sugar and stir",
                    "Pour into a bowl and top with sliced banana and chopped fruits"
                ],
                "total_cost": 65.0,
                "nutritional_info": {
                    "calories": "320 kcal",
                    "protein": 12,
                    "carbs": 70,
                    "fat": 5
                }
            },
            {
                "name": "Avocado Toast",
                "description": "Simple yet nutritious vegan breakfast with creamy avocado spread on toasted bread and seasoned to perfection. This popular dish provides healthy fats from avocado and wholesome carbohydrates from bread for a balanced morning meal.",
                "ingredients": [
                    {"name": "Bread", "amount": "2 slices", "cost": 20.0},
                    {"name": "Avocado", "amount": "1 medium", "cost": 50.0},
                    {"name": "Lemon juice", "amount": "1 teaspoon", "cost": 5.0},
                    {"name": "Tomato", "amount": "1 small", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Black pepper", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Toast the bread slices until golden brown",
                    "Cut avocado in half, remove the pit, and scoop out the flesh",
                    "Mash avocado with lemon juice, salt, and pepper",
                    "Spread avocado mixture on toast",
                    "Top with sliced tomatoes",
                    "Sprinkle additional salt and pepper if desired"
                ],
                "total_cost": 87.0,
                "nutritional_info": {
                    "calories": "350 kcal",
                    "protein": 8,
                    "carbs": 40,
                    "fat": 22
                }
            },
            {
                "name": "Coconut Uji (Vegan Porridge)",
                "description": "A dairy-free version of traditional Kenyan porridge made with millet flour and coconut milk. This warming breakfast option is perfect for vegans and provides a creamy consistency with tropical flavor notes from the coconut.",
                "ingredients": [
                    {"name": "Millet flour", "amount": "1/2 cup", "cost": 20.0},
                    {"name": "Water", "amount": "2 cups", "cost": 0.0},
                    {"name": "Coconut milk", "amount": "1/2 cup", "cost": 30.0},
                    {"name": "Sugar", "amount": "2 tablespoons", "cost": 10.0},
                    {"name": "Cinnamon", "amount": "1/4 teaspoon", "cost": 3.0}
                ],
                "instructions": [
                    "Mix flour with 1 cup of cold water to make a smooth paste",
                    "Boil the remaining water in a pot",
                    "Gradually add the flour mixture to the boiling water, stirring continuously",
                    "Cook on low heat for 5-7 minutes, stirring to prevent lumps",
                    "Add coconut milk, sugar, and cinnamon",
                    "Simmer for another 2 minutes and serve"
                ],
                "total_cost": 63.0,
                "nutritional_info": {
                    "calories": "250 kcal",
                    "protein": 5,
                    "carbs": 45,
                    "fat": 10
                }
            }
        ]
    elif meal_type == "Lunch":
        return [
            {
                "name": "African Peanut Stew",
                "description": "A rich and flavorful vegan stew combining sweet potatoes, vegetables, and peanut butter in a tomato-based broth. This hearty lunch option is inspired by West African cuisine and provides an excellent balance of complex carbohydrates, protein, and healthy fats.",
                "ingredients": [
                    {"name": "Sweet potatoes", "amount": "2 medium", "cost": 40.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 large", "cost": 30.0},
                    {"name": "Peanut butter", "amount": "3 tablespoons", "cost": 25.0},
                    {"name": "Spinach", "amount": "2 cups", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Spices", "amount": "to taste", "cost": 5.0}
                ],
                "instructions": [
                    "Chop sweet potatoes into cubes",
                    "Heat oil in a pot and sauté onions until translucent",
                    "Add tomatoes and cook until soft",
                    "Add sweet potatoes and enough water to cover",
                    "Simmer until sweet potatoes are almost tender",
                    "Stir in peanut butter until well integrated",
                    "Add spinach and cook until wilted",
                    "Season with salt and spices"
                ],
                "total_cost": 156.0,
                "nutritional_info": {
                    "calories": "420 kcal",
                    "protein": 15,
                    "carbs": 60,
                    "fat": 18
                }
            },
            {
                "name": "Bean and Vegetable Stew",
                "description": "A hearty vegan stew combining protein-rich beans with assorted vegetables. This nutrient-dense dish provides sustained energy and is packed with fiber, vitamins, and minerals for a healthy and filling lunch option.",
                "ingredients": [
                    {"name": "Beans", "amount": "1 cup", "cost": 40.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Potatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                    {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0},
                    {"name": "Spices", "amount": "to taste", "cost": 5.0}
                ],
                "instructions": [
                    "Soak beans overnight and cook until soft",
                    "Chop all vegetables into bite-sized pieces",
                    "Heat oil in a large pot and sauté onions until translucent",
                    "Add tomatoes and cook until soft",
                    "Add carrots and potatoes, cook for 5 minutes",
                    "Add cooked beans and enough water to cover",
                    "Season with salt and spices",
                    "Simmer until vegetables are tender and flavors combine"
                ],
                "total_cost": 141.0,
                "nutritional_info": {
                    "calories": "480 kcal",
                    "protein": 18,
                    "carbs": 65,
                    "fat": 12
                }
            },
            {
                "name": "Vegetable Chapati Wrap",
                "description": "A flavorful vegan wrap made with homemade chapati and fresh vegetables. This versatile lunch option is easy to customize, portable, and combines the softness of freshly made chapati with crunchy vegetables for a textural delight.",
                "ingredients": [
                    {"name": "Wheat flour", "amount": "1 cup", "cost": 25.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Cabbage", "amount": "1/4 head", "cost": 15.0},
                    {"name": "Onion", "amount": "1 small", "cost": 10.0},
                    {"name": "Avocado", "amount": "1/2 medium", "cost": 25.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Mix flour, salt, and water to make chapati dough",
                    "Divide into balls and roll into flat circles",
                    "Cook chapatis on a hot pan until golden brown spots appear",
                    "Grate carrots and shred cabbage finely",
                    "Slice onion thinly and mix with vegetables",
                    "Mash avocado and spread on chapati",
                    "Place vegetables on chapati, roll up and serve"
                ],
                "total_cost": 106.0,
                "nutritional_info": {
                    "calories": "380 kcal",
                    "protein": 8,
                    "carbs": 55,
                    "fat": 20
                }
            }
        ]
    else:  # Supper
        return [
            {
                "name": "Vegetable Rice Pilau",
                "description": "A fragrant rice dish cooked with aromatic spices and mixed vegetables. This vegan version of the popular East African rice pilau is full of flavor and makes for a satisfying and complete evening meal.",
                "ingredients": [
                    {"name": "Rice", "amount": "2 cups", "cost": 70.0},
                    {"name": "Mixed vegetables", "amount": "2 cups", "cost": 50.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                    {"name": "Pilau masala", "amount": "1 tablespoon", "cost": 15.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Rinse rice and soak for 30 minutes, then drain",
                    "Heat oil and sauté onions until golden brown",
                    "Add garlic and pilau masala, cook for 1 minute until fragrant",
                    "Add mixed vegetables and sauté for 5 minutes",
                    "Add rice and stir to coat with spices",
                    "Add water (1:2 ratio rice to water) and salt",
                    "Bring to a boil, then reduce heat and cover",
                    "Simmer until rice is tender and water is absorbed"
                ],
                "total_cost": 176.0,
                "nutritional_info": {
                    "calories": "520 kcal",
                    "protein": 12,
                    "carbs": 85,
                    "fat": 15
                }
            },
            {
                "name": "Coconut Bean Curry",
                "description": "A creamy and aromatic vegan curry combining protein-rich beans with coconut milk and fragrant spices. This hearty and satisfying supper option offers a perfect blend of flavors and a good source of plant-based protein.",
                "ingredients": [
                    {"name": "Mixed beans", "amount": "1.5 cups", "cost": 60.0},
                    {"name": "Coconut milk", "amount": "1 cup", "cost": 60.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Tomatoes", "amount": "2 large", "cost": 30.0},
                    {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                    {"name": "Ginger", "amount": "1 inch piece", "cost": 5.0},
                    {"name": "Curry spices", "amount": "2 teaspoons", "cost": 10.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Soak beans overnight, then cook until soft",
                    "Heat oil in a large pot and sauté onions until translucent",
                    "Add minced garlic and ginger, cook for 1 minute",
                    "Add tomatoes and cook until soft",
                    "Add curry spices and stir for 1 minute",
                    "Add cooked beans and coconut milk",
                    "Simmer for 15-20 minutes until flavors combine",
                    "Season with salt to taste and serve with rice or chapati"
                ],
                "total_cost": 206.0,
                "nutritional_info": {
                    "calories": "550 kcal",
                    "protein": 20,
                    "carbs": 65,
                    "fat": 25
                }
            },
            {
                "name": "Spaghetti with Tomato and Vegetable Sauce",
                "description": "A comforting vegan pasta dish with a rich tomato and vegetable sauce perfect for dinner. The sauce combines fresh vegetables and herbs for a nutritious and satisfying meal that's both economical and delicious.",
                "ingredients": [
                    {"name": "Spaghetti", "amount": "250g", "cost": 40.0},
                    {"name": "Tomatoes", "amount": "4 large", "cost": 60.0},
                    {"name": "Onion", "amount": "1 large", "cost": 15.0},
                    {"name": "Carrots", "amount": "1 medium", "cost": 10.0},
                    {"name": "Bell pepper", "amount": "1 medium", "cost": 20.0},
                    {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                    {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                    {"name": "Mixed herbs", "amount": "1 tablespoon", "cost": 10.0},
                    {"name": "Salt", "amount": "to taste", "cost": 1.0}
                ],
                "instructions": [
                    "Boil spaghetti in salted water until al dente",
                    "Chop all vegetables into small pieces",
                    "Heat oil in a pan and sauté onions and garlic until fragrant",
                    "Add tomatoes and cook until soft",
                    "Add remaining vegetables and herbs",
                    "Simmer for 15-20 minutes until sauce thickens",
                    "Season with salt to taste",
                    "Drain pasta and mix with the sauce"
                ],
                "total_cost": 181.0,
                "nutritional_info": {
                    "calories": "480 kcal",
                    "protein": 13,
                    "carbs": 80,
                    "fat": 14
                }
            }
        ] 

def mock_meal_plans(meal_type, budget, preferences=""):
    """Generate mock meal plans when API fails"""
    # Process preferences
    preferences = preferences.lower() if preferences else ""
    
    # Return appropriate meals based on dietary preferences
    if "vegan" in preferences:
        return create_vegan_mock_meals(meal_type, budget)
    elif "vegetarian" in preferences:
        return create_vegetarian_mock_meals(meal_type, budget)
    else:
        # Original mock meals (non-vegetarian)
        budget_float = float(budget)
        
        if meal_type == "Breakfast":
            return [
                {
                    "name": "Kenyan Breakfast Combo",
                    "description": "A hearty Kenyan breakfast featuring eggs, sausage, and toast. This classic combination provides protein and carbohydrates to fuel your morning.",
                    "ingredients": [
                        {"name": "Eggs", "amount": "2 large", "cost": 30.0},
                        {"name": "Sausage", "amount": "2 links", "cost": 50.0},
                        {"name": "Bread", "amount": "2 slices", "cost": 15.0},
                        {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                        {"name": "Salt", "amount": "to taste", "cost": 1.0}
                    ],
                    "instructions": [
                        "Heat oil in a pan",
                        "Cook sausages until browned",
                        "In the same pan, fry eggs to your liking",
                        "Toast bread slices",
                        "Serve hot with tea or coffee"
                    ],
                    "total_cost": 106.0,
                    "nutritional_info": {
                        "calories": "450 kcal",
                        "protein": 25,
                        "carbs": 30,
                        "fat": 30
                    }
                },
                {
                    "name": "Beef and Potato Hash",
                    "description": "A filling breakfast combining diced beef, potatoes, and vegetables. This protein-rich dish provides long-lasting energy and plenty of flavors to kick-start your day.",
                    "ingredients": [
                        {"name": "Ground beef", "amount": "100g", "cost": 60.0},
                        {"name": "Potatoes", "amount": "2 medium", "cost": 30.0},
                        {"name": "Onion", "amount": "1 small", "cost": 10.0},
                        {"name": "Bell pepper", "amount": "1/2 medium", "cost": 10.0},
                        {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                        {"name": "Salt and pepper", "amount": "to taste", "cost": 2.0}
                    ],
                    "instructions": [
                        "Dice potatoes into small cubes",
                        "Heat oil in a large pan",
                        "Add potatoes and cook until beginning to soften",
                        "Add ground beef and cook until browned",
                        "Add diced onions and peppers",
                        "Season with salt and pepper",
                        "Cook until vegetables are tender and meat is fully cooked"
                    ],
                    "total_cost": 132.0,
                    "nutritional_info": {
                        "calories": "520 kcal",
                        "protein": 30,
                        "carbs": 40,
                        "fat": 28
                    }
                },
                {
                    "name": "Mandazi and Tea",
                    "description": "Traditional East African doughnuts served with spiced tea. These slightly sweet, cardamom-flavored pastries are a popular breakfast item in Kenya and pair perfectly with a hot cup of chai tea.",
                    "ingredients": [
                        {"name": "All-purpose flour", "amount": "2 cups", "cost": 30.0},
                        {"name": "Sugar", "amount": "1/4 cup", "cost": 10.0},
                        {"name": "Milk", "amount": "1/2 cup", "cost": 15.0},
                        {"name": "Eggs", "amount": "1 large", "cost": 15.0},
                        {"name": "Cooking oil", "amount": "For frying", "cost": 30.0},
                        {"name": "Cardamom", "amount": "1/4 teaspoon", "cost": 5.0},
                        {"name": "Tea leaves", "amount": "2 teaspoons", "cost": 10.0}
                    ],
                    "instructions": [
                        "Mix flour, sugar, and cardamom in a bowl",
                        "Add eggs and milk to form a dough",
                        "Knead until smooth and let rest for 15 minutes",
                        "Roll out dough and cut into triangles",
                        "Deep fry until golden brown",
                        "Separately, boil water for tea and add tea leaves",
                        "Serve mandazi with hot tea"
                    ],
                    "total_cost": 115.0,
                    "nutritional_info": {
                        "calories": "380 kcal",
                        "protein": 10,
                        "carbs": 55,
                        "fat": 15
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
                    "name": "Beef Stew with Rice",
                    "description": "A hearty beef stew with tender meat and vegetables served over fluffy rice. This balanced meal provides protein, carbohydrates, and essential nutrients for a sustaining lunch option.",
                    "ingredients": [
                        {"name": "Beef cubes", "amount": "250g", "cost": 150.0},
                        {"name": "Rice", "amount": "1 cup", "cost": 35.0},
                        {"name": "Carrots", "amount": "2 medium", "cost": 20.0},
                        {"name": "Potatoes", "amount": "2 medium", "cost": 30.0},
                        {"name": "Onion", "amount": "1 large", "cost": 15.0},
                        {"name": "Tomatoes", "amount": "2 medium", "cost": 30.0},
                        {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                        {"name": "Salt", "amount": "to taste", "cost": 1.0},
                        {"name": "Spices", "amount": "to taste", "cost": 5.0}
                    ],
                    "instructions": [
                        "Heat oil and brown beef cubes",
                        "Add onions and cook until translucent",
                        "Add tomatoes and cook until soft",
                        "Add carrots, potatoes, and spices",
                        "Add water to cover and simmer until meat is tender",
                        "Separately, cook rice until fluffy",
                        "Serve beef stew over rice"
                    ],
                    "total_cost": 306.0,
                    "nutritional_info": {
                        "calories": "650 kcal",
                        "protein": 35,
                        "carbs": 60,
                        "fat": 25
                    }
                },
                {
                    "name": "Chicken and Chapati Wrap",
                    "description": "A flavorful wrap featuring tender chicken pieces with vegetables rolled in a soft chapati. This portable lunch option provides a good balance of protein and carbohydrates with the convenience of a handheld meal.",
                    "ingredients": [
                        {"name": "Chicken breast", "amount": "150g", "cost": 100.0},
                        {"name": "Wheat flour", "amount": "1 cup", "cost": 25.0},
                        {"name": "Tomato", "amount": "1 medium", "cost": 15.0},
                        {"name": "Onion", "amount": "1 small", "cost": 10.0},
                        {"name": "Lettuce", "amount": "2 leaves", "cost": 10.0},
                        {"name": "Cooking oil", "amount": "2 tablespoons", "cost": 20.0},
                        {"name": "Spices", "amount": "to taste", "cost": 5.0},
                        {"name": "Salt", "amount": "to taste", "cost": 1.0}
                    ],
                    "instructions": [
                        "Make chapati dough with flour, water, and salt",
                        "Roll out and cook chapatis on a hot pan",
                        "Season and cook chicken pieces until done",
                        "Slice chicken and vegetables",
                        "Place chicken and vegetables on chapati",
                        "Roll up and secure with toothpick if needed"
                    ],
                    "total_cost": 186.0,
                    "nutritional_info": {
                        "calories": "520 kcal",
                        "protein": 40,
                        "carbs": 45,
                        "fat": 20
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
                    "name": "Grilled Fish with Kachumbari",
                    "description": "Fresh grilled fish served with kachumbari, a traditional East African tomato and onion salad. This light yet satisfying dinner option is rich in protein and offers a refreshing contrast of flavors.",
                    "ingredients": [
                        {"name": "Tilapia fish", "amount": "1 medium", "cost": 180.0},
                        {"name": "Tomatoes", "amount": "2 large", "cost": 30.0},
                        {"name": "Onion", "amount": "1 large", "cost": 15.0},
                        {"name": "Lemon", "amount": "1 whole", "cost": 15.0},
                        {"name": "Coriander", "amount": "1 small bunch", "cost": 10.0},
                        {"name": "Cooking oil", "amount": "1 tablespoon", "cost": 10.0},
                        {"name": "Salt", "amount": "to taste", "cost": 1.0},
                        {"name": "Spices", "amount": "to taste", "cost": 5.0}
                    ],
                    "instructions": [
                        "Clean and score the fish on both sides",
                        "Season with salt, spices, and lemon juice",
                        "Grill fish until cooked through, about 5-7 minutes per side",
                        "For kachumbari, dice tomatoes and onions",
                        "Mix with chopped coriander and lemon juice",
                        "Season with salt to taste",
                        "Serve grilled fish with kachumbari on the side"
                    ],
                    "total_cost": 266.0,
                    "nutritional_info": {
                        "calories": "380 kcal",
                        "protein": 45,
                        "carbs": 15,
                        "fat": 18
                    }
                },
                {
                    "name": "Beef Pilau",
                    "description": "A fragrant one-pot rice dish cooked with beef and aromatic spices. This flavor-packed East African favorite is perfect for dinner, combining tender meat with spice-infused rice for a satisfying meal.",
                    "ingredients": [
                        {"name": "Rice", "amount": "2 cups", "cost": 70.0},
                        {"name": "Beef cubes", "amount": "200g", "cost": 120.0},
                        {"name": "Onion", "amount": "2 large", "cost": 30.0},
                        {"name": "Garlic", "amount": "3 cloves", "cost": 5.0},
                        {"name": "Pilau masala", "amount": "1 tablespoon", "cost": 15.0},
                        {"name": "Cooking oil", "amount": "3 tablespoons", "cost": 30.0},
                        {"name": "Salt", "amount": "to taste", "cost": 1.0}
                    ],
                    "instructions": [
                        "Heat oil and fry onions until golden brown",
                        "Add beef and cook until browned",
                        "Add garlic and pilau masala and cook for 1 minute",
                        "Add rice and stir to coat with spices",
                        "Add water (2 cups water to 1 cup rice) and salt",
                        "Bring to a boil, then reduce heat",
                        "Cover and simmer until rice is cooked and water is absorbed"
                    ],
                    "total_cost": 271.0,
                    "nutritional_info": {
                        "calories": "650 kcal",
                        "protein": 35,
                        "carbs": 70,
                        "fat": 25
                    }
                }
            ] 

def fix_json_formatting(json_str):
    """Apply various fixes to common JSON formatting issues in API responses"""
    # Fix KES values in JSON (replace "cost": 5 KES with "cost": 5)
    json_str = re.sub(r'"cost":\s*(\d+(?:\.\d+)?)\s*KES', r'"cost": \1', json_str)
    
    # Fix non-quoted values in amount field (e.g., amount: 1 slice)
    json_str = re.sub(r'"amount":\s*([^",\d\}]+)(?=,|\})', r'"amount": "\1"', json_str)
    
    # Fix unquoted numeric values in amount field (e.g., "amount": 2, -> "amount": "2",)
    json_str = re.sub(r'"amount":\s*(\d+(?:\.\d+)?)(?=,|\})', r'"amount": "\1"', json_str)
    
    # Convert single quotes to double quotes for JSON compatibility
    json_str = json_str.replace("'", '"')
    
    # Fix missing quotes around any property values
    json_str = re.sub(r':\s*([^",\d\{\}\[\]]+)(?=,|\})', r': "\1"', json_str)
    
    return json_str

def try_parse_json(content):
    """Try multiple approaches to parse potentially malformed JSON"""
    # First try direct parsing
    try:
        json_obj = json.loads(content)
        # Check if the result contains a "meals" array (new format)
        if isinstance(json_obj, dict) and "meals" in json_obj and isinstance(json_obj["meals"], list):
            return json_obj["meals"], "direct_with_meals"
        # Check if it's already an array (old format)
        elif isinstance(json_obj, list):
            return json_obj, "direct"
        else:
            print(f"JSON parsed but unexpected structure: {json_obj.keys() if isinstance(json_obj, dict) else type(json_obj)}")
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON object with regex
    json_match = re.search(r'\{.*"meals"\s*:\s*\[\s*\{.*\}\s*\]\s*\}', content, re.DOTALL)
    if json_match:
        json_str = fix_json_formatting(json_match.group(0))
        try:
            json_obj = json.loads(json_str)
            if "meals" in json_obj and isinstance(json_obj["meals"], list):
                return json_obj["meals"], "regex_extracted_meals"
            else:
                print(f"Extracted JSON with regex but missing meals array: {json_obj.keys()}")
        except json.JSONDecodeError:
            pass
    
    # Try to extract JSON array with regex (old format)
    json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
    if json_match:
        json_str = fix_json_formatting(json_match.group(0))
        try:
            return json.loads(json_str), "regex_extracted"
        except json.JSONDecodeError:
            pass
    
    # Try cleaning up code blocks
    cleaned_content = content.strip()
    if cleaned_content.startswith("Here is the response in the required JSON format:"):
        cleaned_content = cleaned_content.replace("Here is the response in the required JSON format:", "", 1).strip()
    if cleaned_content.startswith("```json"):
        cleaned_content = cleaned_content.replace("```json", "", 1)
    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.replace("```", "", 1)
    if cleaned_content.endswith("```"):
        cleaned_content = cleaned_content[:cleaned_content.rfind("```")]
        
    cleaned_content = fix_json_formatting(cleaned_content.strip())
    
    try:
        json_obj = json.loads(cleaned_content)
        # Check for meals array
        if isinstance(json_obj, dict) and "meals" in json_obj and isinstance(json_obj["meals"], list):
            return json_obj["meals"], "code_block_cleanup_with_meals"
        elif isinstance(json_obj, list):
            return json_obj, "code_block_cleanup"
        else:
            print(f"Cleaned JSON parsed but unexpected structure: {json_obj.keys() if isinstance(json_obj, dict) else type(json_obj)}")
    except json.JSONDecodeError:
        pass
    
    # If we still haven't successfully parsed, try reconstructing the JSON
    print("All JSON parsing attempts failed, attempting reconstruction")
    try:
        # Extreme measures - try to rebuild meal plans from extracted pieces
        meal_plans = []
        
        # Extract meal names
        meal_names = re.findall(r'"name":\s*"([^"]+)"', content)
        descriptions = re.findall(r'"description":\s*"([^"]+)"', content)
        
        # Extract ingredients sections
        ingredients_sections = re.findall(r'"ingredients":\s*\[(.*?)\]', content, re.DOTALL)
        
        # Extract instructions sections
        instructions_sections = re.findall(r'"instructions":\s*\[(.*?)\]', content, re.DOTALL)
        
        # Extract total costs
        total_costs = re.findall(r'"total_cost":\s*(\d+(?:\.\d+)?)', content)
        
        # If we have basic elements, try to construct meals
        if meal_names:
            for i in range(min(3, len(meal_names))):
                meal = {
                    "name": meal_names[i] if i < len(meal_names) else f"Meal Option {i+1}",
                    "description": descriptions[i] if i < len(descriptions) else "A delicious meal option.",
                    "total_cost": float(total_costs[i]) if i < len(total_costs) else 0,
                    "nutritional_info": {
                        "calories": "300 kcal",
                        "protein": 15,
                        "carbs": 45,
                        "fat": 10
                    }
                }
                
                # Try to extract ingredients
                if i < len(ingredients_sections):
                    try:
                        # Fix the ingredients section formatting
                        ingredients_json = "[" + fix_json_formatting(ingredients_sections[i]) + "]"
                        ingredients = json.loads(ingredients_json)
                        meal["ingredients"] = ingredients
                    except json.JSONDecodeError:
                        # Fallback to minimal ingredients
                        meal["ingredients"] = [{"name": "Various ingredients", "amount": "as needed", "cost": 0}]
                else:
                    meal["ingredients"] = [{"name": "Various ingredients", "amount": "as needed", "cost": 0}]
                
                # Try to extract instructions
                if i < len(instructions_sections):
                    try:
                        # Fix the instructions section formatting
                        instructions_json = "[" + fix_json_formatting(instructions_sections[i]) + "]"
                        instructions = json.loads(instructions_json)
                        meal["instructions"] = instructions
                    except json.JSONDecodeError:
                        # Fallback to minimal instructions
                        meal["instructions"] = ["Prepare and serve"]
                else:
                    meal["instructions"] = ["Prepare and serve"]
                
                meal_plans.append(meal)
                
            if meal_plans:
                return meal_plans, "reconstructed"
    except Exception as e:
        print(f"Error during reconstruction: {str(e)}")
    
    # All parsing approaches failed
    return None, "failed" 