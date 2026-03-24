import math
from database import get_connection

def create_student_model(student_id: int, ability: float = 0.0, mastery: float = 0.0, conn=None):
    """Initializes the student's ability scores in the database."""
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO student_model (student_id, ability, mastery)
        VALUES (?, ?, ?)
    """, (student_id, ability, mastery))
    
    if not conn:
        db_conn.commit()
        db_conn.close()

def get_ability(student_id: int, conn=None):
    """Fetches the current ability (theta) for a specific student."""
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT ability FROM student_model WHERE student_id = ?
    """, (student_id,))
    row = cursor.fetchone()
    
    if not conn:
        db_conn.close()
    
    # Use index [0] to get the value from the tuple
    return row[0] if row else 0.0

def update_ability(student_id: int, theta: float, conn=None):
    """Updates the ability score after a quiz."""
    db_conn = conn if conn else get_connection()
    cursor = db_conn.cursor()
    cursor.execute("""
        UPDATE student_model SET ability = ? WHERE student_id = ?
    """, (theta, student_id))
    
    if not conn:
        db_conn.commit()
        db_conn.close()

def irt_update(student_id: int, story_difficulty: float, responses: list, conn=None):
    """Calculates new theta based on quiz responses."""
    theta = get_ability(student_id, conn=conn)
    learning_rate = 0.1

    for actual in responses:
        # IRT Probability formula
        p = 1 / (1 + math.exp(-(theta - story_difficulty)))
        theta = theta + learning_rate * (actual - p)

    update_ability(student_id, theta, conn=conn)
    return theta
