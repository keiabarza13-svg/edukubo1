import math
from database import get_connection

def get_db(conn):
    return conn if conn else get_connection()

def close_db(conn, original_conn):
    if not original_conn:
        conn.close()

def increment_difficulty_attempt(student_id: int, difficulty: float, conn=None):
    """Tracks how many times a student has attempted questions of a certain difficulty."""
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
    """Placeholder for global model retraining logic."""
    print("LFM: Difficulty-based interaction parameters refreshed.")

def predict_performance(student_id: int, difficulty: float, conn=None):
    """Predicts probability of success based on current ability and practice (attempts)."""
    db_conn = get_db(conn)
    cursor = db_conn.cursor()

    # Get student ability (IRT Theta)
    cursor.execute("SELECT ability FROM student_model WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    beta_s = student["ability"] if student else 0.0

    # LFM Math: logit = Student Ability + Practice Effect
    # We'll assume a standard growth factor (gamma) of 0.05 per attempt
    cursor.execute("SELECT attempts FROM student_difficulty_attempts WHERE student_id = ? AND difficulty_level = ?", 
                   (student_id, difficulty))
    row = cursor.fetchone()
    attempts = row["attempts"] if row else 0

    # Logistic Function
    logit = beta_s - difficulty + (0.05 * attempts)
    return 1 / (1 + math.exp(-logit))
