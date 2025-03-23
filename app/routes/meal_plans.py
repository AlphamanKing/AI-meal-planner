@meal_plans_bp.route('/generate', methods=['POST'])
def generate():
    """Generate meal plans based on user inputs"""
    try:
        data = request.get_json()
        meal_type = data.get('meal_type', 'Breakfast')
        budget = data.get('budget', '50')
        preferences = data.get('preferences', '')
        
        print(f"Generating meal plans for {meal_type} with budget {budget} and preferences: {preferences}")
        
        # Call the meal generation function from utils
        meal_plans = groq_api.generate_meal_plans(meal_type, budget, preferences)
        
        # Debug log the meals
        print(f"Generated {len(meal_plans)} meal options")
        for i, meal in enumerate(meal_plans):
            print(f"Meal {i+1}: {meal.get('name', 'Unknown')} - Cost: {meal.get('total_cost', 'Unknown')}")
            print(f"Ingredients: {len(meal.get('ingredients', []))} items")
            print(f"Instructions: {len(meal.get('instructions', []))} steps")
        
        # Return the generated meal plans
        return jsonify({
            'status': 'success',
            'meal_plans': meal_plans
        }), 200
    except Exception as e:
        print(f"Error generating meal plans: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f"Failed to generate meal plans: {str(e)}"
        }), 500 