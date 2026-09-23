import sqlite3
import os

def initialize_database():
    db_name = 'edukubo.db'
    schema_name = 'schema.sql' # Ensure your schema file is named this

    # 1. Delete the old database if it exists to start fresh
    if os.path.exists(db_name):
        os.remove(db_name)
        print(f"🗑️ Existing {db_name} deleted.")

    try:
        # 2. Connect to SQLite (this automatically creates the .db file)
        conn = sqlite3.connect(db_name)
        print(f"📁 Created new {db_name} file.")

        # 3. Read and execute the schema.sql script
        with open(schema_name, 'r') as f:
            conn.executescript(f.read())
        
        conn.commit()
        print("✅ Schema applied successfully! All tables created.")

    except sqlite3.Error as e:
        print(f"❌ SQLite Error: {e}")
    except FileNotFoundError:
        print(f"❌ Error: {schema_name} not found. Make sure the file exists!")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()
    