from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.meal import Meal, MealHistory
from app.utils.forms import MealForm, RegistrationForm, UpdateAccountForm
import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from flask_bcrypt import Bcrypt

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
bcrypt = Bcrypt()

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
    total_users = User.query.count()
    
    # Count total meals generated
    total_meal_plans = MealHistory.query.count()
    
    # Get today's date at midnight
    today = datetime.now().date()
    
    # Count new users today
    new_users_today = User.query.filter(func.date(User.date_joined) == today).count()
    
    # Count meal plans created today
    meal_plans_today = MealHistory.query.filter(func.date(MealHistory.date_selected) == today).count()
    
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
    
    # Convert to dictionary for easier template access
    meal_type_dict = {}
    for meal_type, count in meal_type_counts:
        meal_type_dict[meal_type] = count
    
    # Define standard meal type colors for the UI 
    meal_type_colors = {
        'Breakfast': 'primary',
        'Lunch': 'success',
        'Supper': 'warning'
    }
    
    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          total_users=total_users,
                          total_meal_plans=total_meal_plans,
                          new_users_today=new_users_today,
                          meal_plans_today=meal_plans_today,
                          recent_users=recent_users,
                          recent_meals=recent_meals,
                          avg_budget=round(avg_budget, 2),
                          meal_type_counts=meal_type_dict,
                          meal_type_colors=meal_type_colors)

@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of users per page
    
    # Apply filters if provided
    username_filter = request.args.get('username', '')
    email_filter = request.args.get('email', '')
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    
    # Start with base query
    query = User.query
    
    # Apply filters
    if username_filter:
        query = query.filter(User.username.contains(username_filter))
    if email_filter:
        query = query.filter(User.email.contains(email_filter))
    if status_filter:
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
    if role_filter:
        if role_filter == 'admin':
            query = query.filter(User.is_admin == True)
        elif role_filter == 'user':
            query = query.filter(User.is_admin == False)
    
    # Execute paginated query
    paginated_users = query.order_by(User.date_joined.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', 
                          title='Users', 
                          users=paginated_users.items,
                          pagination=paginated_users,
                          current_page=page,
                          total_pages=paginated_users.pages,
                          prev_page=paginated_users.prev_num if paginated_users.has_prev else None,
                          next_page=paginated_users.next_num if paginated_users.has_next else None)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            is_admin='is_admin' in request.form  # Check if admin checkbox is checked
        )
        
        # Add and commit to database
        db.session.add(user)
        db.session.commit()
        
        flash(f'User account created for {form.username.data}!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/add_user.html', title='Add User', form=form)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateAccountForm()
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        
        # Check if we're updating the password
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Update admin status if not the current user
        if user.id != current_user.id:
            user.is_admin = 'is_admin' in request.form
        
        db.session.commit()
        flash('User account has been updated!', 'success')
        return redirect(url_for('admin.user_details', user_id=user.id))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    
    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # Delete all related meal history
        MealHistory.query.filter_by(user_id=user.id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {user.username} has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's meal history
    user_meals = MealHistory.query.filter_by(user_id=user_id).order_by(MealHistory.date_selected.desc()).all()
    
    # Calculate user statistics
    user_stats = {
        'meal_count': len(user_meals),
        'avg_budget': sum(meal.budget for meal in user_meals) / len(user_meals) if user_meals else 0
    }
    
    # Calculate meal type distribution
    meal_type_stats = {}
    for meal in user_meals:
        meal_type_stats[meal.meal_type.lower()] = meal_type_stats.get(meal.meal_type.lower(), 0) + 1
    
    # Get monthly activity data
    monthly_activity = {
        'labels': [],
        'data': []
    }
    
    # Get budget over time data
    budget_time = {
        'labels': [],
        'data': []
    }
    
    for meal in user_meals:
        date_str = meal.date_selected.strftime('%Y-%m')
        if date_str not in monthly_activity['labels']:
            monthly_activity['labels'].append(date_str)
            monthly_activity['data'].append(1)
        else:
            idx = monthly_activity['labels'].index(date_str)
            monthly_activity['data'][idx] += 1
            
        budget_time['labels'].append(meal.date_selected.strftime('%Y-%m-%d'))
        budget_time['data'].append(meal.budget)
    
    # Define standard meal type colors for the UI 
    meal_type_colors = {
        'Breakfast': 'primary',
        'Lunch': 'success',
        'Supper': 'warning'
    }
    
    return render_template('admin/user_details.html',
                          title=f'User Details - {user.username}',
                          user=user,
                          user_meals=user_meals,
                          user_stats=user_stats,
                          meal_type_stats=meal_type_stats,
                          monthly_activity=monthly_activity,
                          budget_time=budget_time,
                          meal_type_colors=meal_type_colors)

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
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of meals per page
    
    # Apply filters if provided
    meal_type_filter = request.args.get('meal_type', '')
    date_range = request.args.get('date_range', '')
    
    # Start with base query
    query = MealHistory.query
    
    # Apply filters
    if meal_type_filter:
        query = query.filter(MealHistory.meal_type == meal_type_filter)
    
    if date_range:
        today = datetime.now().date()
        if date_range == 'today':
            query = query.filter(func.date(MealHistory.date_selected) == today)
        elif date_range == 'week':
            # Calculate start of the week (last Sunday)
            start_of_week = today - timedelta(days=today.weekday() + 1)
            query = query.filter(MealHistory.date_selected >= start_of_week)
        elif date_range == 'month':
            # Calculate start of the month
            start_of_month = today.replace(day=1)
            query = query.filter(MealHistory.date_selected >= start_of_month)
    
    # Get meal type counts for statistics
    meal_type_counts_query = db.session.query(
        MealHistory.meal_type, 
        func.count(MealHistory.id).label('count')
    ).group_by(MealHistory.meal_type).all()
    
    meal_type_counts = {}
    for meal_type, count in meal_type_counts_query:
        meal_type_counts[meal_type] = count
    
    # Execute paginated query
    paginated_meals = query.order_by(MealHistory.date_selected.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Define standard meal type colors for the UI 
    meal_type_colors = {
        'Breakfast': 'primary',
        'Lunch': 'success',
        'Supper': 'warning'
    }
    
    # Calculate budget ranges for chart
    budget_ranges = {
        'range1': 0,  # 0-100
        'range2': 0,  # 101-200
        'range3': 0,  # 201-300
        'range4': 0,  # 301-400
        'range5': 0   # 401+
    }
    
    # Query all budgets to calculate ranges
    all_budgets = db.session.query(MealHistory.budget).all()
    for (budget,) in all_budgets:
        if budget <= 100:
            budget_ranges['range1'] += 1
        elif budget <= 200:
            budget_ranges['range2'] += 1
        elif budget <= 300:
            budget_ranges['range3'] += 1
        elif budget <= 400:
            budget_ranges['range4'] += 1
        else:
            budget_ranges['range5'] += 1
    
    return render_template('admin/meals.html', 
                          title='Manage Meals', 
                          meals=paginated_meals.items,
                          pagination=paginated_meals,
                          current_page=page,
                          total_pages=paginated_meals.pages,
                          prev_page=paginated_meals.prev_num if paginated_meals.has_prev else None,
                          next_page=paginated_meals.next_num if paginated_meals.has_next else None,
                          meal_type_counts=meal_type_counts,
                          meal_type_colors=meal_type_colors,
                          budget_ranges=budget_ranges)

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
    meal = MealHistory.query.get_or_404(meal_id)
    
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
    # Use MealHistory to find popular meals instead of using Meal.popularity
    popular_meals_query = db.session.query(
        MealHistory.meal_name,
        func.count(MealHistory.id).label('count')
    ).filter(
        MealHistory.meal_name.isnot(None)  # Ensure name exists
    ).group_by(MealHistory.meal_name).order_by(desc('count')).limit(10).all()
    
    # Format the results as a list of dictionaries
    popular_meals = [
        {'name': meal_name, 'popularity': count} 
        for meal_name, count in popular_meals_query
    ]
    
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

@admin_bp.route('/meals/<int:meal_id>')
@admin_required
def meal_details(meal_id):
    meal = MealHistory.query.get_or_404(meal_id)
    
    # Calculate nutritional info if available
    nutritional_data = {}
    if meal.nutritional_info:
        try:
            nutritional_data = json.loads(meal.nutritional_info)
        except json.JSONDecodeError:
            nutritional_data = {}
    
    # Parse ingredients if available
    ingredients = []
    if meal.ingredients:
        try:
            ingredients = json.loads(meal.ingredients)
        except json.JSONDecodeError:
            ingredients = []
    
    # Parse instructions if available
    instructions = []
    if meal.instructions:
        try:
            instructions = json.loads(meal.instructions)
        except json.JSONDecodeError:
            instructions = []
    
    return render_template('admin/meal_details.html',
                          title=f'Meal Details - {meal.meal_name}',
                          meal=meal,
                          nutritional_data=nutritional_data,
                          ingredients=ingredients,
                          instructions=instructions) 