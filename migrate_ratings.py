import mysql.connector
from database import DB_URL

# DB_URL is "mysql+mysqlconnector://root:@localhost/fixitnow_db"
# Extract parameters
# simplified for local xampp
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="fixitnow_db"
    )
    cursor = conn.cursor()
    
    # Check if columns exist in bookings table
    cursor.execute("SHOW COLUMNS FROM bookings")
    columns = [col[0] for col in cursor.fetchall()]
    
    if "rating_value" not in columns:
        print("Adding rating_value column...")
        cursor.execute("ALTER TABLE bookings ADD COLUMN rating_value INT NULL")
    
    if "rating_comment" not in columns:
        print("Adding rating_comment column...")
        cursor.execute("ALTER TABLE bookings ADD COLUMN rating_comment VARCHAR(255) NULL")
    
    conn.commit()
    print("Database schema check complete.")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error updating database: {e}")
