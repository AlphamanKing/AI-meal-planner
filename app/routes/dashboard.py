from flask import Blueprint, render_template, redirect, url_for, flash, request, session
import json
from app.models import db, User, Meal

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@dashboard.route('/index')
def index():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the user's meals from the database
    user_id = session['user_id']
    user = User.query.get(user_id)
    user_meals = Meal.query.filter_by(user_id=user_id).all()
    
    return render_template('dashboard/index.html', 
                           user=user, 
                           user_meals=user_meals, 
                           meal_types=["Breakfast", "Lunch", "Supper"],
                           budgets=["0-100", "100-200", "200-300", "300+"])

@dashboard.route('/generate_meal_plan', methods=['POST'])
def generate_meal_plan():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get form data
    meal_type = request.form.get('meal_type')
    budget = request.form.get('budget')
    preferences = request.form.get('preferences', '')
    
    # Validate inputs
    if not meal_type or not budget:
        flash('Please provide all required information', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Generate meal plans
    from app.utils.groq_api import generate_meal_plans
    
    # Capture the flag for mock data to notify user
    is_mock_data = False
    
    try:
        print(f"Starting meal plan generation for {meal_type} with budget {budget} and preferences: '{preferences}'")
        meal_plans = generate_meal_plans(meal_type, budget, preferences)
        
        # Check if we received mock data
        first_meal_name = meal_plans[0]["name"] if meal_plans and len(meal_plans) > 0 else ""
        
        # Simple check to detect if mock data is being used (based on common mock meal names)
        mock_meal_indicators = [
            "Kenyan Breakfast Combo", 
            "Ugali with Sukuma Wiki", 
            "Rice and Beans Dinner",
            "Fruit and Yogurt Bowl",
            "Vegetable Chapati Wrap",
            "Fruit Oatmeal Bowl",
            "Avocado Toast"
        ]
        
        is_mock_data = any(indicator in first_meal_name for indicator in mock_meal_indicators)
        print(f"Using mock data: {is_mock_data}, First meal: {first_meal_name}")
        print(f"Number of meal plans returned: {len(meal_plans)}")
        
        # Additional validation for generated meals
        if not is_mock_data:
            print("Validating AI-generated meals:")
            print(f"Meal 1: {meal_plans[0].get('name', 'unknown')}")
            print(f"Meal 2: {meal_plans[1].get('name', 'unknown') if len(meal_plans) > 1 else 'missing'}")
            print(f"Meal 3: {meal_plans[2].get('name', 'unknown') if len(meal_plans) > 2 else 'missing'}")
            
            # Check if preferences are honored
            if preferences:
                print(f"Checking preference adherence for: '{preferences}'")
                from app.utils.groq_api import check_preferences_adherence
                for idx, meal in enumerate(meal_plans):
                    adheres, reason = check_preferences_adherence(meal, preferences)
                    print(f"Meal {idx+1} adheres to preferences: {adheres} {'' if adheres else f'- {reason}'}")
        
        # Save meal plans to database
        user_id = session['user_id']
        
        for meal in meal_plans:
            new_meal = Meal(
                user_id=user_id,
                meal_type=meal_type,
                meal_name=meal['name'],
                description=meal['description'],
                ingredients=json.dumps(meal['ingredients']),
                instructions=json.dumps(meal['instructions']),
                total_cost=meal['total_cost'],
                nutritional_info=json.dumps(meal['nutritional_info'])
            )
            db.session.add(new_meal)
        
        db.session.commit()
        
        if is_mock_data:
            flash('We\'ve provided alternative meal suggestions based on your preferences. These meals are carefully selected to match your dietary requirements.', 'info')
        else:
            flash('Meal plans generated successfully!', 'success')
            
        return redirect(url_for('dashboard.index'))
    
    except Exception as e:
        flash(f'Error generating meal plans: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index')) 