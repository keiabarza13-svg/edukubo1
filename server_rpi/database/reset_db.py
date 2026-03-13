import sqlite3

def hard_reset():
    conn = sqlite3.connect('edukubo.db')
    cursor = conn.cursor()

    # 1. TEMPORARILY DISABLE FOREIGN KEYS
    # This allows us to delete "Parent" tables like stories without error
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # 2. LIST ALL TABLES TO CLEAR
    # Order doesn't matter now because constraints are OFF
    tables = [
        'scores', 
        'quiz_results', 
        'student_difficulty_attempts', 
        'student_skill_attempts',
        'questions', 
        'stories',
        'student_model',
        'students' # Include this if you want to wipe test students too
    ]

    print("--- Hard Resetting Database ---")
    for table in tables:
        try:
            # Delete all data
            cursor.execute(f"DELETE FROM {table};")
            # Reset ID counters back to 1
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
            print(f"✅ Cleared and Reset: {table}")
        except sqlite3.OperationalError:
            print(f"⚠️ Table {table} not found, skipping...")

    # 3. RE-ENABLE FOREIGN KEYS
    cursor.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    conn.close()
    print("--- Database is now FRESH. You can run import_data.py now! ---")

if __name__ == "__main__":
    hard_reset()