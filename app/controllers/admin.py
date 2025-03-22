from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.meal import Meal, MealHistory
from app.utils.forms import MealForm
import json
from datetime import datetime
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    # Count total users
    user_count = User.query.count()
    
    # Count total meals generated
    meal_count = MealHistory.query.count()
    
    # Get recent user registrations
    recent_users = User.query.order_by(User.date_joined.desc()).limit(5).all()
    
    # Get recent meal plans
    recent_meals = MealHistory.query.order_by(MealHistory.date_selected.desc()).limit(5).all()
    
    # Calculate average budget spent
    avg_budget = db.session.query(func.avg(MealHistory.budget)).scalar() or 0
    
    # Get most popular meal types
    meal_type_counts = db.session.query(
        MealHistory.meal_type, 
        func.count(MealHistory.id).label('count')
    ).group_by(MealHistory.meal_type).order_by(desc('count')).all()
    
    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          user_count=user_count,
                          meal_count=meal_count,
                          recent_users=recent_users,
                          recent_meals=recent_meals,
                          avg_budget=round(avg_budget, 2),
                          meal_type_counts=meal_type_counts)

@admin_bp.route('/users')
@admin_required
def users():
    users_list = User.query.all()
    return render_template('admin/users.html', title='Users', users=users_list)

@admin_bp.route('/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow removing admin status from own account
    if user.id == current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'You cannot remove admin privileges from your own account'
        }), 400
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'is_admin': user.is_admin
    })

@admin_bp.route('/meals')
@admin_required
def meals():
    meals_list = Meal.query.all()
    return render_template('admin/meals.html', title='Manage Meals', meals=meals_list)

@admin_bp.route('/meals/add', methods=['GET', 'POST'])
@admin_required
def add_meal():
    form = MealForm()
    
    if form.validate_on_submit():
        try:
            # Validate JSON input
            ingredients = json.loads(form.ingredients.data)
            nutritional_info = json.loads(form.nutritional_info.data)
            
            meal = Meal(
                name=form.name.data,
                description=form.description.data,
                ingredients=form.ingredients.data,  # Store as JSON string
                nutritional_info=form.nutritional_info.data,  # Store as JSON string
                estimated_cost=form.estimated_cost.data,
                meal_type=form.meal_type.data
            )
            
            db.session.add(meal)
            db.session.commit()
            
            flash('Meal added successfully!', 'success')
            return redirect(url_for('admin.meals'))
        
        except json.JSONDecodeError:
            flash('Invalid JSON format for ingredients or nutritional info', 'danger')
    
    return render_template('admin/add_meal.html', title='Add Meal', form=form)

@admin_bp.route('/meals/edit/<int:meal_id>', methods=['GET', 'POST'])
@admin_required
def edit_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    form = MealForm()
    
    if form.validate_on_submit():
        try:
            # Validate JSON input
            ingredients = json.loads(form.ingredients.data)
            nutritional_info = json.loads(form.nutritional_info.data)
            
            meal.name = form.name.data
            meal.description = form.description.data
            meal.ingredients = form.ingredients.data
            meal.nutritional_info = form.nutritional_info.data
            meal.estimated_cost = form.estimated_cost.data
            meal.meal_type = form.meal_type.data
            
            db.session.commit()
            
            flash('Meal updated successfully!', 'success')
            return redirect(url_for('admin.meals'))
        
        except json.JSONDecodeError:
            flash('Invalid JSON format for ingredients or nutritional info', 'danger')
    
    elif request.method == 'GET':
        form.name.data = meal.name
        form.description.data = meal.description
        form.ingredients.data = meal.ingredients
        form.nutritional_info.data = meal.nutritional_info
        form.estimated_cost.data = meal.estimated_cost
        form.meal_type.data = meal.meal_type
    
    return render_template('admin/edit_meal.html', title='Edit Meal', form=form, meal=meal)

@admin_bp.route('/meals/delete/<int:meal_id>', methods=['POST'])
@admin_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    
    try:
        db.session.delete(meal)
        db.session.commit()
        flash('Meal deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting meal: {str(e)}', 'danger')
    
    return redirect(url_for('admin.meals'))

@admin_bp.route('/popular-meals')
@admin_required
def popular_meals():
    # Get most popular predefined meals
    popular_meals = Meal.query.order_by(Meal.popularity.desc()).limit(10).all()
    
    # Get popular custom meals from history (count by meal_name)
    popular_custom_meals = db.session.query(
        MealHistory.meal_name,
        func.count(MealHistory.id).label('count')
    ).filter(
        MealHistory.meal_id.is_(None),  # Only custom meals (not from predefined)
        MealHistory.meal_name.isnot(None)  # Ensure name exists
    ).group_by(MealHistory.meal_name).order_by(desc('count')).limit(10).all()
    
    return render_template('admin/popular_meals.html',
                          title='Popular Meals',
                          popular_meals=popular_meals,
                          popular_custom_meals=popular_custom_meals) 