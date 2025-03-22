from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.meal import Meal, MealHistory
from app.utils.groq_api import generate_meal_plans
import json
from datetime import datetime

meal_api_bp = Blueprint('meal_api', __name__, url_prefix='/api')

@meal_api_bp.route('/generate-meal-plans', methods=['POST'])
@login_required
def api_generate_meal_plans():
    # Get JSON data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error', 
            'message': 'No data provided'
        }), 400
    
    # Validate required fields
    required_fields = ['meal_type', 'budget']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            'status': 'error',
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    # Get parameters
    meal_type = data.get('meal_type')
    budget = float(data.get('budget'))
    preferences = data.get('preferences')
    
    # Validate meal type
    valid_meal_types = ['Breakfast', 'Lunch', 'Supper']
    if meal_type not in valid_meal_types:
        return jsonify({
            'status': 'error',
            'message': f'Invalid meal type. Must be one of: {", ".join(valid_meal_types)}'
        }), 400
    
    # Validate budget
    if budget < 10 or budget > 1000:
        return jsonify({
            'status': 'error',
            'message': 'Budget must be between 10 and 1000 KES'
        }), 400
    
    # Generate meal plans
    meal_plans = generate_meal_plans(meal_type, budget, preferences)
    
    if meal_plans:
        return jsonify({
            'status': 'success',
            'data': meal_plans
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate meal plans. Please try again.'
        }), 500

@meal_api_bp.route('/save-meal', methods=['POST'])
@login_required
def api_save_meal():
    # Get data from request
    data = request.get_json()
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['name', 'meal_type', 'budget']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({
            'status': 'error',
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    try:
        # Create a new meal history entry
        meal_history = MealHistory(
            user_id=current_user.id,
            meal_name=data.get('name'),
            meal_description=data.get('description'),
            meal_ingredients=json.dumps(data.get('ingredients', [])),
            meal_nutritional_info=json.dumps(data.get('nutritional_info', {})),
            meal_type=data.get('meal_type'),
            budget=data.get('budget'),
            preferences=data.get('preferences'),
            date_selected=datetime.utcnow()
        )
        
        db.session.add(meal_history)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Meal saved successfully',
            'meal_id': meal_history.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error saving meal: {str(e)}'
        }), 500

@meal_api_bp.route('/meal-history', methods=['GET'])
@login_required
def api_meal_history():
    # Get all meal history for the user
    history = MealHistory.query.filter_by(user_id=current_user.id).order_by(MealHistory.date_selected.desc()).all()
    
    # Convert to list of dictionaries
    history_data = [meal.to_dict() for meal in history]
    
    return jsonify({
        'status': 'success',
        'data': history_data
    })

@meal_api_bp.route('/meal-details/<int:meal_id>', methods=['GET'])
@login_required
def get_meal_details(meal_id):
    # Get the meal history entry
    meal = MealHistory.query.filter_by(id=meal_id, user_id=current_user.id).first()
    
    if not meal:
        return jsonify({
            'status': 'error',
            'message': 'Meal not found or you do not have access to it.'
        }), 404
    
    # Parse JSON data stored in database
    try:
        # Prepare meal data
        meal_data = {
            'id': meal.id,
            'meal_type': meal.meal_type,
            'meal_name': meal.meal_name,
            'name': meal.meal_name,  # For compatibility with display functions
            'budget': meal.budget,
            'preferences': meal.preferences,
            'date_selected': meal.date_selected.strftime('%Y-%m-%d %H:%M:%S'),
            'total_cost': meal.total_cost if meal.total_cost else 0
        }
        
        # Add description if available
        if meal.description:
            meal_data['description'] = meal.description
        else:
            meal_data['description'] = "No description available."
            
        # Parse and add ingredients if available
        if meal.ingredients:
            meal_data['ingredients'] = json.loads(meal.ingredients)
        else:
            meal_data['ingredients'] = []
            
        # Parse and add instructions if available
        if meal.instructions:
            meal_data['instructions'] = json.loads(meal.instructions)
        else:
            meal_data['instructions'] = []
            
        # Parse and add nutritional info if available
        if meal.nutritional_info:
            meal_data['nutritional_info'] = json.loads(meal.nutritional_info)
        else:
            meal_data['nutritional_info'] = {
                'calories': '0 kcal',
                'protein': '0 g',
                'carbs': '0 g', 
                'fat': '0 g'
            }
            
        return jsonify({
            'status': 'success',
            'data': meal_data
        })
    except Exception as e:
        print(f"Error preparing meal details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving meal details.'
        }), 500 