import sqlite3
import pandas as pd

def import_edukubo_data():
    # 1. Connect to your database
    # Make sure this filename matches your actual database file
    conn = sqlite3.connect('edukubo.db')
    cursor = conn.cursor()

    print("--- Starting Import Process ---")

    try:
        # 2. Import Stories
        # Load the CSV you saved from the 'stories' sheet
        stories_df = pd.read_csv('stories.csv')
        
        # We use 'if_exists=replace' for the first time to ensure 
        # the table structure matches our CSV perfectly.
        stories_df.to_sql('stories', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(stories_df)} stories.")

        # 3. Import Questions
        # Load the CSV you saved from the 'questions' sheet
        questions_df = pd.read_csv('questions.csv')
        
        questions_df.to_sql('questions', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(questions_df)} questions.")

        # 4. Initialize LFM/Skills table
        # Since we are using difficulty levels (0.0, 1.0, 1.5), 
        # let's pre-insert them into a 'skills' or 'difficulty' metadata table
        unique_difficulties = questions_df['difficulty_level'].unique()
        
        cursor.execute("CREATE TABLE IF NOT EXISTS skills (skill_id REAL PRIMARY KEY, beta_skill REAL, gamma_skill REAL)")
        
        for diff in unique_difficulties:
            cursor.execute("""
                INSERT OR IGNORE INTO skills (skill_id, beta_skill, gamma_skill) 
                VALUES (?, ?, ?)
            """, (diff, 0.0, 0.05)) # 0.05 is your 'learning gain' factor

        conn.commit()
        print("Initial difficulty parameters set for LFM.")
        print("--- Import Complete! ---")

    except Exception as e:
        print(f"Error during import: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    import_edukubo_data()