from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os
from database import get_connection 
from auth import auth_bp

# Algorithm Imports
from algorithm.irt import get_ability, irt_update
from algorithm.bkt import bkt_update
from algorithm.lfm import train_lfm, increment_difficulty_attempt

app = Flask(__name__)
app.secret_key = 'edukubo_research_2026'

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# 1. TEACHER DASHBOARD
# We keep this unique so it doesn't clash with student paths
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('home'))

    conn = get_connection()
    teacher_grade = 4 

    # Pulls Student Info, IRT Ability, BKT Mastery, and their "Hardest Story"
    query = """
        SELECT 
            u.full_name, s.grade_level, sm.ability, sm.mastery,
            (SELECT st.title FROM scores sc 
             JOIN stories st ON sc.story_id = st.story_id 
             WHERE sc.student_id = u.user_id 
             ORDER BY sc.score ASC LIMIT 1) as hardest_story
        FROM users u
        JOIN students s ON u.user_id = s.student_id
        JOIN student_model sm ON u.user_id = sm.student_id
        WHERE s.grade_level = ? AND u.role = 'student'
    """
    students_data = conn.execute(query, (teacher_grade,)).fetchall()
    conn.close()
    
    return render_template('teacher_dashboard.html', 
                           students=students_data, 
                           grade=teacher_grade)

# 2. STUDENT DASHBOARD
@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    # If a teacher accidentally lands here, send them to the correct dashboard
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_dashboard'))

    user_id = session['user_id']
    conn = get_connection()
    
    # Get student level and current Ability (Theta)
    student_data = conn.execute('SELECT grade_level FROM students WHERE student_id = ?', (user_id,)).fetchone()
    student_grade = student_data['grade_level'] if student_data else 4
    student_theta = get_ability(user_id, conn)
    
    # Get Mastery for the progress bar
    mastery_row = conn.execute('SELECT mastery FROM student_model WHERE student_id = ?', (user_id,)).fetchone()
    student_mastery = mastery_row['mastery'] if mastery_row else 0.0

    # Adaptive filtering (Zone of Proximal Development)
    low_bound, high_bound = student_theta - 1.5, student_theta + 1.5

    query = """
        SELECT * FROM stories 
        WHERE grade_level = ? 
        AND CAST(difficulty_level AS REAL) BETWEEN ? AND ?
        ORDER BY difficulty_level ASC
    """
    stories_rows = conn.execute(query, (student_grade, low_bound, high_bound)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', 
                           stories=list(stories_rows), 
                           role=role,
                           full_name=session.get('full_name', 'Student'),
                           ability=round(student_theta, 2),
                           mastery=round(student_mastery, 2),
                           grade=student_grade)

# 3. CONTENT ROUTES
@app.route('/story/<int:story_id>')
def view_story(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    conn.close()
    return render_template('story.html', story=story)

@app.route('/quiz/<int:story_id>')
def take_quiz(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    conn.close()
    return render_template('quiz.html', story=story, questions=questions)

@app.route('/submit_quiz/<int:story_id>', methods=['POST'])
def submit_quiz(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    user_id = session['user_id']
    conn = get_connection()
    
    questions = conn.execute('SELECT question_id, correct_answer, difficulty_level, skill_id FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    story = conn.execute('SELECT title, difficulty_level FROM stories WHERE story_id = ?', (story_id,)).fetchone()

    responses = []
    total_correct = 0

    for q in questions:
        user_choice = request.form.get(f"question_{q['question_id']}")
        is_correct = 1 if str(user_choice).strip().lower() == str(q['correct_answer']).strip().lower() else 0
        responses.append(is_correct)
        total_correct += is_correct
        
        bkt_update(user_id, q['skill_id'], is_correct, conn=conn)
        increment_difficulty_attempt(user_id, q['difficulty_level'], conn=conn)

    # IRT Algorithm Update
    new_theta = irt_update(user_id, story['difficulty_level'], responses, conn)
    
    # Update Global Student Model
    conn.execute('''
        UPDATE student_model 
        SET ability = ?, 
            mastery = (SELECT AVG(mastery_probability) FROM student_skill_mastery WHERE student_id = ?)
        WHERE student_id = ?
    ''', (new_theta, user_id, user_id))

    conn.execute('INSERT INTO scores (student_id, story_id, score) VALUES (?, ?, ?)', (user_id, story_id, total_correct))
    
    train_lfm(conn)
    conn.commit()
    conn.close()

    return render_template('result.html', score=total_correct, total=len(responses), theta=round(new_theta, 2), story_title=story['title'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Register Blueprint
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
