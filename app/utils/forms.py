from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models.user import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose another one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class MealPlanForm(FlaskForm):
    meal_type = SelectField('Meal Type', 
                            choices=[('Breakfast', 'Breakfast'), 
                                    ('Lunch', 'Lunch'), 
                                    ('Supper', 'Supper')],
                            validators=[DataRequired()])
    budget = FloatField('Budget (KES)', 
                       validators=[DataRequired(), 
                                  NumberRange(min=10, max=1000, 
                                              message='Budget must be between 10 and 1000 KES')])
    preferences = TextAreaField('Preferences (Optional)', 
                               validators=[Length(max=500)],
                               render_kw={"placeholder": "E.g., I prefer vegetarian meals, or I like spicy food..."})
    submit = SubmitField('Generate Meal Plans')

class MealForm(FlaskForm):
    name = StringField('Meal Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    ingredients = TextAreaField('Ingredients (JSON format)', validators=[DataRequired()])
    nutritional_info = TextAreaField('Nutritional Info (JSON format)', validators=[DataRequired()])
    estimated_cost = FloatField('Estimated Cost (KES)', validators=[DataRequired(), NumberRange(min=1)])
    meal_type = SelectField('Meal Type', 
                            choices=[('Breakfast', 'Breakfast'), 
                                    ('Lunch', 'Lunch'), 
                                    ('Supper', 'Supper')],
                            validators=[DataRequired()])
    submit = SubmitField('Save Meal') 