import pymysql

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Empty string for no password
    'charset': 'utf8mb4',
}

def recreate_database():
    # Connect to MySQL without selecting a database
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        charset=db_config['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with connection.cursor() as cursor:
            # Drop and recreate the database
            cursor.execute("DROP DATABASE IF EXISTS meal_plan_db")
            cursor.execute("CREATE DATABASE meal_plan_db")
            
            print("Database recreated successfully!")
            
            # Use the new database
            cursor.execute("USE meal_plan_db")
            
            # Create users table
            cursor.execute("""
            CREATE TABLE `users` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `username` VARCHAR(50) NOT NULL UNIQUE,
              `email` VARCHAR(100) NOT NULL UNIQUE,
              `password` VARCHAR(255) NOT NULL,
              `is_admin` BOOLEAN DEFAULT FALSE,
              `is_active` BOOLEAN DEFAULT TRUE,
              `date_joined` DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create meals table
            cursor.execute("""
            CREATE TABLE `meals` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `name` VARCHAR(100) NOT NULL,
              `description` TEXT,
              `ingredients` TEXT NOT NULL,
              `instructions` TEXT,
              `meal_type` VARCHAR(20) NOT NULL,
              `estimated_cost` FLOAT NOT NULL,
              `nutritional_info` TEXT,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create meal history table
            cursor.execute("""
            CREATE TABLE `meal_history` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `user_id` INT NOT NULL,
              `meal_type` VARCHAR(20) NOT NULL,
              `meal_name` VARCHAR(100),
              `description` TEXT,
              `ingredients` TEXT,
              `instructions` TEXT,
              `budget` FLOAT NOT NULL,
              `total_cost` FLOAT,
              `preferences` TEXT,
              `nutritional_info` TEXT,
              `date_selected` DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            )
            """)
            
            # Create system settings table
            cursor.execute("""
            CREATE TABLE `system_settings` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `setting_key` VARCHAR(50) NOT NULL UNIQUE,
              `setting_value` TEXT NOT NULL,
              `description` TEXT,
              `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """)
            
            # Create user preferences table
            cursor.execute("""
            CREATE TABLE `user_preferences` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `user_id` INT NOT NULL,
              `preference_key` VARCHAR(50) NOT NULL,
              `preference_value` TEXT NOT NULL,
              `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              UNIQUE KEY `user_preference` (`user_id`, `preference_key`),
              FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            )
            """)
            
            # Create password resets table
            cursor.execute("""
            CREATE TABLE `password_resets` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `email` VARCHAR(100) NOT NULL,
              `token` VARCHAR(255) NOT NULL,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              `expires_at` DATETIME NOT NULL
            )
            """)
            
            # Create activity logs table
            cursor.execute("""
            CREATE TABLE `activity_logs` (
              `id` INT PRIMARY KEY AUTO_INCREMENT,
              `user_id` INT,
              `action` VARCHAR(100) NOT NULL,
              `details` TEXT,
              `ip_address` VARCHAR(45),
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
            )
            """)
            
            # Insert admin user
            cursor.execute("""
            INSERT INTO `users` (`username`, `email`, `password`, `is_admin`) 
            VALUES ('admin', 'admin@example.com', '$2b$12$X.ISmB6mSd52DAVtxpJLdeZhbpOyrx3dVWTbwTIewRfGxFEQgDyiK', TRUE)
            """)
            
            # Insert default system settings
            cursor.execute("""
            INSERT INTO `system_settings` (`setting_key`, `setting_value`, `description`) 
            VALUES 
            ('site_name', 'Comrade Meal Plan', 'Name of the website'),
            ('site_description', 'Affordable meal planning for university students', 'Short description of the website'),
            ('max_budget', '1000', 'Maximum budget allowed for meal planning'),
            ('default_meal_suggestions', '3', 'Default number of meal suggestions to generate')
            """)
            
            print("All tables created successfully!")
            
        # Commit the changes
        connection.commit()
        
    except Exception as e:
        print(f"Error recreating database: {e}")
    
    finally:
        connection.close()

if __name__ == "__main__":
    recreate_database() 