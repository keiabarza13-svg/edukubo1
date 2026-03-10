import math
from database import get_connection

def get_db(conn):
    """Helper to handle the connection logic."""
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    """Helper to close only if we opened it here."""
    if not original_conn:
        conn.close()

def initialize_student(student_id: int, conn=None):
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE student_model
        SET beta_student = COALESCE(beta_student, 0.0)
        WHERE student_id = ?
    """, (student_id,))
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def increment_attempt(student_id: int, skill_id: int, conn=None):
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("""
        INSERT INTO student_skill_attempts (student_id, skill_id, attempts)
        VALUES (?, ?, 1)
        ON CONFLICT(student_id, skill_id)
        DO UPDATE SET attempts = attempts + 1
    """, (student_id, skill_id))
    if not conn:
        db_conn.commit()
    close_db(db_conn, conn)

def get_attempts(student_id: int, skill_id: int, conn=None):
    db_conn = get_db(conn)
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT attempts FROM student_skill_attempts
        WHERE student_id = ? AND skill_id = ?
    """, (student_id, skill_id))
    row = cursor.fetchone()
    close_db(db_conn, conn)
    return row["attempts"] if row else 0

def predict(student_id: int, skill_id: int, conn=None):
    db_conn = get_db(conn)
    cursor = db_conn.cursor()

    # Get parameters in one go if possible to save time
    cursor.execute("SELECT beta_student FROM student_model WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    beta_s = student["beta_student"] if student else 0.0

    cursor.execute("SELECT beta_skill, gamma_skill FROM skills WHERE skill_id = ?", (skill_id,))
    skill = cursor.fetchone()

    if not skill:
        close_db(db_conn, conn)
        return 0.5

    beta_k, gamma_k = skill["beta_skill"], skill["gamma_skill"]
    attempts = get_attempts(student_id, skill_id, conn=db_conn)

    close_db(db_conn, conn)

    logit = beta_s + beta_k + gamma_k * attempts
    return 1 / (1 + math.exp(-logit))