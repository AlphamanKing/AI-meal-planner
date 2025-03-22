import os
import pymysql

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty string for no password
    'db': 'meal_plan_db',
    'charset': 'utf8mb4',
}

def import_schema():
    # Read the SQL file
    with open('meal_plan.sql', 'r') as file:
        sql_script = file.read()
    
    # Connect to the database
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        db=db_config['db'],
        charset=db_config['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # Split the SQL script by semicolon to execute each statement
            statements = sql_script.split(';')
            
            for statement in statements:
                # Skip empty statements
                if statement.strip():
                    cursor.execute(statement)
            
        # Commit the changes
        connection.commit()
        print("Database schema imported successfully!")
        
    except Exception as e:
        print(f"Error importing schema: {e}")
    
    finally:
        connection.close()

if __name__ == "__main__":
    import_schema() 