import sqlite3

def hard_reset():
    conn = sqlite3.connect('edukubo.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = OFF;")

    tables = [
        'scores', 
        'quiz_results', 
        'student_difficulty_attempts', 
        'student_skill_attempts',
        'questions', 
        'stories',
        'student_model',
        'students' 
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

 
    cursor.execute("PRAGMA foreign_keys = ON;")

    conn.commit()
    conn.close()
    print("--- Database is now FRESH. You can run import_data.py now! ---")

if __name__ == "__main__":

    hard_reset()
