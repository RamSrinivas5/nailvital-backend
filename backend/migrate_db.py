import mysql.connector

def migrate():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="nailvital"
        )
        cursor = conn.cursor()
        
        # Add finger column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE scans ADD COLUMN finger VARCHAR(50) AFTER image_path")
            print("Successfully added 'finger' column to 'scans' table.")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                print("Column 'finger' already exists.")
            else:
                print(f"Error: {err}")

        # Add findings_json column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE scans ADD COLUMN findings_json VARCHAR(1000) AFTER confidence")
            print("Successfully added 'findings_json' column to 'scans' table.")
        except mysql.connector.Error as err:
            if err.errno == 1060:
                print("Column 'findings_json' already exists.")
            else:
                print(f"Error: {err}")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")
        print("Please ensure XAMPP MySQL is running.")

if __name__ == "__main__":
    migrate()
