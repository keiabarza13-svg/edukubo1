import math
from database import get_connection

# BKT (Question/Skill-Level Mastery)

def create_skill_mastery(student_id: int, skill_id: int, conn=None):
    """
    Initialize skill mastery for a student.
    Default = 0.2 (20% chance student knows skill)
    """
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_skill_mastery
        (student_id, skill_id, mastery_probability)
        VALUES (?, ?, 0.2)
    """, (student_id, skill_id))
    
    if not conn:
        db_conn.commit()
        db_conn.close()


def get_mastery(student_id: int, skill_id: int, conn=None):
    """Get current mastery probability for a skill"""
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    
    cursor.execute("""
        SELECT mastery_probability FROM student_skill_mastery
        WHERE student_id = ? AND skill_id = ?
    """, (student_id, skill_id))
    row = cursor.fetchone()
    
    if not conn:
        db_conn.close()
    return row["mastery_probability"] if row else 0.2


def bkt_update(student_id: int, skill_id: int, correct: int, 
               slip=0.1, guess=0.2, learn=0.15, conn=None):
    """
    Update skill mastery using BKT logic with a shared connection.
    """
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()

    # Get current mastery using the shared connection
    L_t = get_mastery(student_id, skill_id, conn=db_conn)

    # Bayesian update logic
    if correct:
        L_t_new = (L_t * (1 - slip)) / (L_t * (1 - slip) + (1 - L_t) * guess)
    else:
        L_t_new = (L_t * slip) / (L_t * slip + (1 - L_t) * (1 - guess))

    # Apply learning transition
    L_t_new = L_t_new + (1 - L_t_new) * learn

    # Save updated mastery
    cursor.execute("""
        INSERT INTO student_skill_mastery (student_id, skill_id, mastery_probability)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, skill_id) DO UPDATE SET
        mastery_probability = excluded.mastery_probability
    """, (student_id, skill_id, L_t_new))

    if not conn:
        db_conn.commit()
        db_conn.close()
        
    return L_t_new