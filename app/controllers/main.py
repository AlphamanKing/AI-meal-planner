from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.meal import Meal, MealHistory
from app.utils.forms import MealPlanForm
from app.utils.groq_api import generate_meal_plans
import json
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Welcome')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent meal history for the user
    recent_meals = MealHistory.query.filter_by(user_id=current_user.id).order_by(MealHistory.date_selected.desc()).limit(5).all()
    
    # Initialize the meal plan form
    form = MealPlanForm()
    
    return render_template('main/dashboard.html', 
                          title='Dashboard', 
                          form=form, 
                          recent_meals=recent_meals)

@main_bp.route('/meal-plans', methods=['POST'])
@login_required
def get_meal_plans():
    # For JSON requests, get data from request.json
    if request.is_json:
        data = request.json
        form = MealPlanForm(meta={'csrf': False})
        form.meal_type.data = data.get('meal_type')
        try:
            form.budget.data = float(data.get('budget', 0))
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'errors': {'budget': ['Budget must be a valid number']}
            })
        form.preferences.data = data.get('preferences')
    else:
        form = MealPlanForm()
    
    if form.validate():
        meal_type = form.meal_type.data
        budget = form.budget.data
        preferences = form.preferences.data if form.preferences.data else None
        
        # Generate meal plans using Groq API
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
            })
    else:
        return jsonify({
            'status': 'error',
            'errors': {field: errors for field, errors in form.errors.items()}
        })

@main_bp.route('/save-meal', methods=['POST'])
@login_required
def save_meal():
    if not request.is_json:
        return jsonify({'status': 'error', 'message': 'Invalid request format.'}), 400
    
    data = request.json
    
    try:
        # Create a new meal history entry
        meal_history = MealHistory(
            user_id=current_user.id,
            meal_type=data.get('meal_type'),
            meal_name=data.get('name'),
            budget=data.get('budget'),
            preferences=data.get('preferences'),
            date_selected=datetime.now()
        )
        
        # Save meal details (ingredients, nutritional info, etc.)
        # Convert the ingredients list to a JSON string
        if 'ingredients' in data:
            meal_history.ingredients = json.dumps(data.get('ingredients'))
        
        # Save description
        if 'description' in data:
            meal_history.description = data.get('description')
        
        # Save instructions
        if 'instructions' in data:
            meal_history.instructions = json.dumps(data.get('instructions'))
        
        # Save nutritional info
        if 'nutritional_info' in data:
            meal_history.nutritional_info = json.dumps(data.get('nutritional_info'))
        
        # Save total cost
        if 'total_cost' in data:
            meal_history.total_cost = data.get('total_cost')
            
        db.session.add(meal_history)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Meal saved successfully!'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error saving meal: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while saving the meal.'
        }), 500

@main_bp.route('/meal-history')
@login_required
def meal_history():
    # Get all meal history for the user
    history = MealHistory.query.filter_by(user_id=current_user.id).order_by(MealHistory.date_selected.desc()).all()
    
    return render_template('main/meal_history.html',
                          title='Meal History',
                          history=history) 