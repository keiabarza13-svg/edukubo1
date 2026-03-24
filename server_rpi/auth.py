from flask import Blueprint, request, jsonify, session
from database import get_connection
from algorithm.irt import create_student_model
from algorithm.bkt import create_skill_mastery
from algorithm.lfm import initialize_student 
import bcrypt

auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/register/student', methods=['POST'])
def register_student_route():
    data = request.get_json()
    result = register_student(
        full_name=data.get('full_name'),
        username=data.get('username'),
        password=data.get('password'),
        grade_level=data.get('grade_level')
    )
    return jsonify(result)

@auth_bp.route('/register/teacher', methods=['POST'])
def register_teacher_route():
    data = request.get_json()
    result = register_teacher(
        full_name=data.get('full_name'),
        username=data.get('username'),
        password=data.get('password')
    )
    return jsonify(result)

@auth_bp.route('/login', methods=['POST'])
def login_route():
    data = request.get_json()
    result = login(data.get('username'), data.get('password'))
    
    if result["success"]:
        session['user_id'] = result['user_id']
        session['role'] = result['role']
        session['full_name'] = result['full_name']
        
    return jsonify(result)


# LOGIC FUNCTIONS

def register_student(full_name: str, username: str, password: str, grade_level: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Hash password safely
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        # Insert into users
        cursor.execute("""
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, 'student')
        """, (full_name, username, password_hash))
        user_id = cursor.lastrowid

        # Insert into students
        cursor.execute("""
            INSERT INTO students (student_id, grade_level)
            VALUES (?, ?)
        """, (user_id, grade_level))

        # Initialize Algorithms using the SHARED connection (conn=conn)
       
        create_student_model(user_id, ability=0.0, mastery=0.0, conn=conn)
        
        
        # create_skill_mastery(user_id, skill_id=1, conn=conn)

        conn.commit()
        return {"success": True, "message": "Student registered successfully."}
    
    except Exception as e:
        # Rollback ensures no partial data is saved if an algorithm fails
        conn.rollback() 
        print(f"Registration Error: {e}") # Helpful for debugging in terminal
        return {"success": False, "message": f"Database Error: {str(e)}"}
    
    finally:
        # Close 
        conn.close()

def register_teacher(full_name: str, username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

    try:
        cursor.execute("""
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, 'teacher')
        """, (full_name, username, password_hash))
        conn.commit()
        return {"success": True, "message": "Teacher registered successfully."}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

def login(username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            return {"success": False, "message": "User not found"}

        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            return {
                "success": True,
                "user_id": user["user_id"],
                "role": user["role"],
                "full_name": user["full_name"]
            }
        else:
            return {"success": False, "message": "Incorrect password"}
    finally:
        conn.close()
