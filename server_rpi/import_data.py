import sqlite3
import pandas as pd

def import_edukubo_data():
   
    conn = sqlite3.connect('edukubo.db')
    cursor = conn.cursor()

    print("--- Starting Import Process ---")

    try:
        # 2. Import Stories
      
        stories_df = pd.read_csv('stories.csv')
        
        
        stories_df.to_sql('stories', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(stories_df)} stories.")

        # 3. Import Questions
 
        questions_df = pd.read_csv('questions.csv')
        
        questions_df.to_sql('questions', conn, if_exists='replace', index=False)
        print(f"Successfully imported {len(questions_df)} questions.")

        # 4. Initialize LFM/Skills table
       
        unique_difficulties = questions_df['difficulty_level'].unique()
        
        cursor.execute("CREATE TABLE IF NOT EXISTS skills (skill_id REAL PRIMARY KEY, beta_skill REAL, gamma_skill REAL)")
        
        for diff in unique_difficulties:
            cursor.execute("""
                INSERT OR IGNORE INTO skills (skill_id, beta_skill, gamma_skill) 
                VALUES (?, ?, ?)
            """, (diff, 0.0, 0.05)) 

        conn.commit()
        print("Initial difficulty parameters set for LFM.")
        print("--- Import Complete! ---")

    except Exception as e:
        print(f"Error during import: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":

    import_edukubo_data()
