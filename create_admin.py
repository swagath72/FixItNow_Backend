import mysql.connector
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="fixitnow"
        )
        cursor = conn.cursor()

        email = "admin@fixitnow.com"
        password = "admin123"
        hashed_password = pwd_context.hash(password)
        full_name = "System Admin"
        role = "admin"
        phone = "0000000000"

        # Check if user exists
        cursor.execute("SELECT id FROM app_users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            print(f"User {email} already exists. Updating role to admin...")
            cursor.execute("UPDATE app_users SET role = %s WHERE email = %s", (role, email))
        else:
            print(f"Creating admin user {email}...")
            cursor.execute(
                "INSERT INTO app_users (full_name, email, password, role, phone) VALUES (%s, %s, %s, %s, %s)",
                (full_name, email, hashed_password, role, phone)
            )
        
        conn.commit()
        print("Done!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()
