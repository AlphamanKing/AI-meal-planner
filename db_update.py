from app import db, create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Add is_active column if it doesn't exist
    db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
    
    # Add last_login column if it doesn't exist
    db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login DATETIME NULL"))
    
    # Commit the changes
    db.session.commit()
    
    print("Database updated successfully!") 