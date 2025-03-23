from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
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

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_admin = BooleanField('Admin Privileges')
    submit = SubmitField('Update')
    
    def validate_username(self, username):
        from flask_login import current_user
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != current_user.id:
            raise ValidationError('Username is already taken. Please choose another one.')
    
    def validate_email(self, email):
        from flask_login import current_user
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != current_user.id:
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

class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    current_password = PasswordField('Current Password', validators=[])
    new_password = PasswordField('New Password', validators=[])
    confirm_new_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Profile')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken. Please choose another one.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email is already registered. Please use a different one.') 