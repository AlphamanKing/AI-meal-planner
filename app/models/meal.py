from app import db
from datetime import datetime
import json

class Meal(db.Model):
    __tablename__ = 'meals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=False)  # JSON string
    instructions = db.Column(db.Text, nullable=True)  # JSON string
    meal_type = db.Column(db.String(20), nullable=False)
    estimated_cost = db.Column(db.Float, nullable=False)
    nutritional_info = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    popularity = db.Column(db.Integer, default=0)  # Track meal popularity
    
    # Remove relationship since we're storing meals directly in MealHistory now
    
    def __repr__(self):
        return f"<Meal {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ingredients': json.loads(self.ingredients) if self.ingredients else [],
            'instructions': json.loads(self.instructions) if self.instructions else [],
            'estimated_cost': self.estimated_cost,
            'meal_type': self.meal_type,
            'nutritional_info': json.loads(self.nutritional_info) if self.nutritional_info else {},
            'popularity': self.popularity
        }


class MealHistory(db.Model):
    __tablename__ = 'meal_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=True)
    meal_type = db.Column(db.String(20), nullable=False)
    meal_name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=True)  # JSON string of ingredients
    instructions = db.Column(db.Text, nullable=True)  # JSON string of instructions
    budget = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=True)
    preferences = db.Column(db.Text, nullable=True)
    nutritional_info = db.Column(db.Text, nullable=True)  # JSON string of nutritional info
    date_selected = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='meal_history')
    meal = db.relationship('Meal', backref='history_entries')
    
    def __repr__(self):
        return f"<MealHistory {self.id}: {self.meal_name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'meal_name': self.meal_name or "Unknown",
            'meal_type': self.meal_type,
            'budget': self.budget,
            'preferences': self.preferences,
            'date_selected': self.date_selected.strftime('%Y-%m-%d %H:%M:%S'),
            'ingredients': json.loads(self.ingredients) if self.ingredients else [],
            'instructions': json.loads(self.instructions) if self.instructions else [],
            'nutritional_info': json.loads(self.nutritional_info) if self.nutritional_info else {}
        } 