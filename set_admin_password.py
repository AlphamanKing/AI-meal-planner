from flask_bcrypt import Bcrypt
import pymysql
from getpass import getpass

def update_admin_password():
    bcrypt = Bcrypt()
    
    # Get new password securely
    new_password = getpass("Enter new admin password: ")
    confirm_password = getpass("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords don't match!")
        return
    
    # Generate hash using bcrypt
    password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    # Update database
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='meal_plan_db',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = 'admin'",
                (password_hash,)
            )
        connection.commit()
        print("Admin password updated successfully!")
    except Exception as e:
        print(f"Error updating password: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    update_admin_password()