import math
from database import get_connection

def get_db(conn):
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    if not original_conn and conn:
        conn.close()

def create_skill_mastery(student_id: int, skill_id: int, conn=None):
    """Set initial skill mastery to 20%"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_skill_mastery
        (student_id, skill_id, mastery_probability)
        VALUES (?, ?, 0.2)
    """, (student_id, int(skill_id)))
    
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def get_mastery(student_id: int, skill_id: int, conn=None):
    """Get current mastery from DB"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT mastery_probability FROM student_skill_mastery
        WHERE student_id = ? AND skill_id = ?
    """, (student_id, int(skill_id)))
    row = cursor.fetchone()
    
    close_db(db_conn, conn)
    return row[0] if row and row[0] is not None else 0.2

def bkt_update(student_id: int, skill_id: int, correct: int, 
               slip=0.1, guess=0.2, learn=0.15, conn=None):
    """Update skill mastery after an answer"""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()

    L_t = get_mastery(student_id, skill_id, conn=db_conn)

    # Bayesian posterior update
    if correct:
        L_t_new = (L_t * (1 - slip)) / ((L_t * (1 - slip)) + ((1 - L_t) * guess))
    else:
        L_t_new = (L_t * slip) / ((L_t * slip) + ((1 - L_t) * (1 - guess)))

    # Apply knowledge transition
    L_t_new = L_t_new + (1 - L_t_new) * learn

    # Clamp probability bounds [0.001, 0.999] to maintain stability
    L_t_new = max(0.001, min(0.999, L_t_new))

    cursor.execute("""
        INSERT INTO student_skill_mastery (student_id, skill_id, mastery_probability)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, skill_id) DO UPDATE SET
        mastery_probability = excluded.mastery_probability
    """, (student_id, int(skill_id), L_t_new))

    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)
        
    return L_t_new
