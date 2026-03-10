import math
from database import get_connection

def create_student_model(student_id: int, ability: float = 0.0, mastery: float = 0.0, conn=None):
    """
    Accepts an optional existing connection 'conn'.
    """
    # Use existing connection if passed, otherwise open a new one
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_model (student_id, ability, mastery)
        VALUES (?, ?, ?)
    """, (student_id, ability, mastery))
    
    # Only commit and close if we opened the connection inside THIS function
    if not conn:
        db_conn.commit()
        db_conn.close()

def get_ability(student_id: int, conn=None):
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT ability FROM student_model WHERE student_id = ?
    """, (student_id,))
    row = cursor.fetchone()
    
    if not conn:
        db_conn.close()
    return row["ability"] if row else 0.0

def update_ability(student_id: int, theta: float, conn=None):
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE student_model SET ability = ? WHERE student_id = ?
    """, (theta, student_id))
    
    if not conn:
        db_conn.commit()
        db_conn.close()

def irt_update(student_id: int, story_difficulty: float, responses: list, conn=None):
    # Pass the connection down the chain
    theta = get_ability(student_id, conn=conn)
    learning_rate = 0.1

    for actual in responses:
        p = 1 / (1 + math.exp(-(theta - story_difficulty)))
        theta = theta + learning_rate * (actual - p)

    update_ability(student_id, theta, conn=conn)
    return theta