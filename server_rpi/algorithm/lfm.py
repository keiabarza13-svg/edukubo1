import math
import sqlite3
from database import get_connection

def get_db(conn):
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    if not original_conn:
        conn.close()

def initialize_student(student_id: int, conn=None):
    """Setup student ability - called during signup"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_model (student_id, ability)
        VALUES (?, 0.0)
    """, (student_id,))
    
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def increment_difficulty_attempt(student_id: int, difficulty: float, conn=None):
    """Log how many times a student tries a certain difficulty"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT INTO student_difficulty_attempts (student_id, difficulty_level, attempts)
        VALUES (?, ?, 1)
        ON CONFLICT(student_id, difficulty_level)
        DO UPDATE SET attempts = attempts + 1
    """, (student_id, difficulty))
    
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def train_lfm(conn=None):
    """Placeholder for future model updates"""
    print("LFM: Parameters refreshed.")

def predict_performance(student_id: int, difficulty: float, conn=None):
    """Predict if student will pass based on ability and practice"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()

    # Get student ability (Theta)
    cursor.execute("SELECT ability FROM student_model WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    beta_s = student[0] if student else 0.0

    # Get attempt count for this level
    cursor.execute("""
        SELECT attempts FROM student_difficulty_attempts 
        WHERE student_id = ? AND difficulty_level = ?
    """, (student_id, difficulty))
    row = cursor.fetchone()
    attempts = row[0] if row else 0

    # Logit = Ability - Difficulty + Practice Effect
    logit = beta_s - difficulty + (0.05 * attempts)
    
    # Return probability (0 to 1)
    return 1 / (1 + math.exp(-logit))
