import sqlite3
import os

# Get the absolute path of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Path to your SQLite database file
db_path = os.path.join(script_dir, 'instance', 'app.db')

print(f"Attempting to connect to database at: {db_path}")

# Check if the file exists
if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
    print("Current working directory:", os.getcwd())
    print("Contents of the current directory:", os.listdir(os.getcwd()))
    print("Contents of the 'instance' directory (if it exists):", 
          os.listdir(os.path.join(script_dir, 'instance')) if os.path.exists(os.path.join(script_dir, 'instance')) else "instance directory not found")
    exit(1)

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the maximum ROWID you want to keep
    max_rowid_to_keep = 190  # Adjust this value as needed

    # Execute DELETE command
    delete_query = """
    DELETE FROM survey_data
    WHERE ROWID <= (SELECT MAX(ROWID) - ? FROM survey_data)
    """

    cursor.execute(delete_query, (max_rowid_to_keep,))

    # Commit the changes
    conn.commit()

    print(f"Deleted {cursor.rowcount} rows.")

    # Optionally, vacuum the database
    cursor.execute("VACUUM")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
finally:
    if conn:
        conn.close()