import math
import sqlite3
from database import get_connection

def get_db(conn):
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    if not original_conn and conn:
        conn.close()

def create_student_model(student_id: int, ability: float = 0.0, mastery: float = 0.0, conn=None):
    """Setup new student parameters in student_model during user registration."""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_model (student_id, ability, mastery)
        VALUES (?, ?, ?)
    """, (student_id, ability, mastery))
    
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def get_ability(student_id: int, conn=None):
    """Fetch current theta (ability level) from DB."""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("SELECT ability FROM student_model WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    close_db(db_conn, conn)
    return row[0] if row and row[0] is not None else 0.0

def update_ability(student_id: int, theta: float, conn=None):
    """Save updated theta to DB."""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("UPDATE student_model SET ability = ? WHERE student_id = ?", (theta, student_id))
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def irt_update(student_id: int, item_difficulties: list, responses: list, learning_rate: float = 0.25, conn=None):
    """
    Update student ability (theta) after a quiz using item-level 1PL IRT (Rasch Model).
    """
    theta = get_ability(student_id, conn=conn)

    for b_i, actual in zip(item_difficulties, responses):
        # 1PL IRT (Rasch Model): P(correct) = 1 / (1 + e^-(theta - b_i))
        p = 1.0 / (1.0 + math.exp(-(theta - float(b_i))))
        
        # Stochastic Gradient Ascent
        theta = theta + learning_rate * (actual - p)

    # Clamp theta between -3.0 and +3.0
    theta = max(-3.0, min(3.0, theta))

    update_ability(student_id, theta, conn=conn)
    return theta
