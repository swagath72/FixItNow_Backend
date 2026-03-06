from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as connection:
        print("Checking for missing columns in 'bookings' table...")
        
        # Add payment_status if it doesn't exist
        try:
            connection.execute(text("ALTER TABLE bookings ADD COLUMN payment_status VARCHAR(50) DEFAULT 'Pending'"))
            print("Added 'payment_status' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("'payment_status' already exists.")
            else:
                print(f"Error adding 'payment_status': {e}")

        # Add razorpay_order_id if it doesn't exist
        try:
            connection.execute(text("ALTER TABLE bookings ADD COLUMN razorpay_order_id VARCHAR(100)"))
            print("Added 'razorpay_order_id' column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("'razorpay_order_id' already exists.")
            else:
                print(f"Error adding 'razorpay_order_id': {e}")

        connection.commit()
        print("Migration completed.")

if __name__ == "__main__":
    migrate()
