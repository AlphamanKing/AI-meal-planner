import pymysql

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty string for no password
    'db': 'meal_plan_db',
    'charset': 'utf8mb4',
}

def create_users_table():
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
            # Drop the existing users table if it exists
            cursor.execute("DROP TABLE IF EXISTS users")
            
            # Create the users table to match our model
            create_table_sql = """
            CREATE TABLE `users` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `username` VARCHAR(50) NOT NULL UNIQUE,
              `email` VARCHAR(100) NOT NULL UNIQUE,
              `password` VARCHAR(255) NOT NULL,
              `is_admin` BOOLEAN DEFAULT FALSE,
              `date_joined` DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_sql)
            
            # Insert a default admin user
            insert_admin_sql = """
            INSERT INTO `users` (`username`, `email`, `password`, `is_admin`) 
            VALUES ('admin', 'admin@example.com', '$2b$12$X.ISmB6mSd52DAVtxpJLdeZhbpOyrx3dVWTbwTIewRfGxFEQgDyiK', TRUE)
            """
            cursor.execute(insert_admin_sql)
            
        # Commit the changes
        connection.commit()
        print("Users table created successfully!")
        
    except Exception as e:
        print(f"Error creating users table: {e}")
    
    finally:
        connection.close()

if __name__ == "__main__":
    create_users_table() 