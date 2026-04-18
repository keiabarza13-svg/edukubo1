import math
import sqlite3
from database import get_connection

def get_db(conn):
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    if not original_conn:
        conn.close()

def create_student_model(student_id: int, ability: float = 0.0, conn=None):
    """Setup new student score - called during signup"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    # Don't overwrite if student already exists
    cursor.execute("""
        INSERT OR IGNORE INTO student_model (student_id, ability)
        VALUES (?, ?)
    """, (student_id, ability))
    
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def get_ability(student_id: int, conn=None):
    """Get current theta (level) from DB"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("SELECT ability FROM student_model WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    close_db(db_conn, conn)
    return row[0] if row else 0.0

def update_ability(student_id: int, theta: float, conn=None):
    """Save updated score to DB"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("UPDATE student_model SET ability = ? WHERE student_id = ?", (theta, student_id))
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def irt_update(student_id: int, story_difficulty: float, responses: list, conn=None):
    """Update student level after a quiz"""
    theta = get_ability(student_id, conn=conn)
    learning_rate = 0.1

    for actual in responses:
        # Calculate success probability
        p = 1 / (1 + math.exp(-(theta - story_difficulty)))
        
        # Adjust theta based on right/wrong answer
        theta = theta + learning_rate * (actual - p)

    # Keep theta within -3 to 3 range for stability
    theta = max(-3.0, min(3.0, theta))

    update_ability(student_id, theta, conn=conn)
    return theta
