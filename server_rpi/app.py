from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os
from database import get_connection 
from auth import auth_bp

# Algorithm Imports
from algorithm.irt import get_ability, irt_update
from algorithm.bkt import bkt_update
from algorithm.lfm import train_lfm, increment_difficulty_attempt, predict_performance

app = Flask(__name__)
app.secret_key = 'edukubo_research_2026'

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# 1. TEACHER DASHBOARD
@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('home'))

    conn = get_connection()
    teacher_grade = 4 

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

# VIEW ALL STUDENTS ROSTER
@app.route('/teacher/students_roster')
def students_roster():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('home'))

    conn = get_connection()
    query = """
        SELECT u.full_name, s.grade_level, sm.ability, sm.mastery
        FROM users u
        JOIN students s ON u.user_id = s.student_id
        JOIN student_model sm ON u.user_id = sm.student_id
        WHERE u.role = 'student'
        ORDER BY s.grade_level ASC, u.full_name ASC
    """
    students_data = conn.execute(query).fetchall()
    conn.close()

    return render_template('students_roster.html', students=students_data)

# ADD STORY AND QUESTION TO DATABASE
@app.route('/teacher/add_story', methods=['GET', 'POST'])
def add_story():
    if 'user_id' not in session or session.get('role') != 'teacher':
        return redirect(url_for('home'))

    if request.method == 'POST':
        title = request.form.get('title')
        grade_level = int(request.form.get('grade_level'))
        difficulty_level = float(request.form.get('difficulty_level'))
        content = request.form.get('content')
        is_baseline = 1 if request.form.get('is_baseline') else 0

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO stories (title, grade_level, difficulty_level, content, is_baseline)
            VALUES (?, ?, ?, ?, ?)
        """, (title, grade_level, difficulty_level, content, is_baseline))

        story_id = cursor.lastrowid

        question_text = request.form.get('question_text')
        if question_text:
            skill_id = int(request.form.get('skill_id'))
            option_a = request.form.get('option_a')
            option_b = request.form.get('option_b')
            option_c = request.form.get('option_c')
            option_d = request.form.get('option_d')
            correct_answer = request.form.get('correct_answer')
            q_difficulty = float(request.form.get('q_difficulty_level', difficulty_level))

            cursor.execute("""
                INSERT INTO questions (story_id, skill_id, question_text, option_a, option_b, option_c, option_d, correct_answer, difficulty_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (story_id, skill_id, question_text, option_a, option_b, option_c, option_d, correct_answer, q_difficulty))

        conn.commit()
        conn.close()

        return redirect(url_for('teacher_dashboard'))

    return render_template('add_story.html')

# 2. STUDENT DASHBOARD (NOW INTEGRATED WITH LFM PREDICTIONS)
@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_dashboard'))

    user_id = session['user_id']
    conn = get_connection()
    
    student_data = conn.execute('SELECT grade_level FROM students WHERE student_id = ?', (user_id,)).fetchone()
    student_grade = student_data['grade_level'] if student_data else 4
    student_theta = get_ability(user_id, conn)
    
    mastery_row = conn.execute('SELECT mastery FROM student_model WHERE student_id = ?', (user_id,)).fetchone()
    student_mastery = mastery_row['mastery'] if mastery_row else 0.0

    # Fetch candidate stories for student grade
    stories_rows = conn.execute('SELECT * FROM stories WHERE grade_level = ?', (student_grade,)).fetchall()
    
    # Predict performance for each story using LFM model
    recommended_stories = []
    for story in stories_rows:
        story_dict = dict(story)
        predicted_p = predict_performance(user_id, float(story_dict['difficulty_level']), conn=conn)
        story_dict['predicted_success'] = round(predicted_p * 100, 1)
        recommended_stories.append(story_dict)

    # Sort stories by optimal learning zone (closest to 70% success probability)
    recommended_stories.sort(key=lambda s: abs(s['predicted_success'] - 70.0))

    conn.close()
    
    return render_template('dashboard.html', 
                           stories=recommended_stories, 
                           role=role,
                           full_name=session.get('full_name', 'Student'),
                           ability=round(student_theta, 2),
                           mastery=round(student_mastery, 2),
                           grade=student_grade)

# 3. CONTENT & QUIZ SUBMISSION ROUTES
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
    if 'user_id' not in session: 
        return redirect(url_for('home'))
        
    user_id = session['user_id']
    conn = get_connection()
    
    questions = conn.execute('SELECT question_id, correct_answer, difficulty_level, skill_id FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    story = conn.execute('SELECT title, difficulty_level FROM stories WHERE story_id = ?', (story_id,)).fetchone()

    responses = []
    item_difficulties = []
    total_correct = 0

    for q in questions:
        user_choice = request.form.get(f"question_{q['question_id']}")
        is_correct = 1 if str(user_choice).strip().lower() == str(q['correct_answer']).strip().lower() else 0
        
        responses.append(is_correct)
        item_difficulties.append(float(q['difficulty_level']))
        total_correct += is_correct
        
        # BKT & LFM updates per item
        bkt_update(user_id, int(q['skill_id']), is_correct, conn=conn)
        increment_difficulty_attempt(user_id, float(q['difficulty_level']), conn=conn)

    # IRT theta update based on item difficulties
    new_theta = irt_update(user_id, item_difficulties, responses, conn=conn)
    
    # Update BKT average mastery in student_model
    conn.execute('''
        UPDATE student_model 
        SET mastery = (SELECT COALESCE(AVG(mastery_probability), 0.0) FROM student_skill_mastery WHERE student_id = ?)
        WHERE student_id = ?
    ''', (user_id, user_id))

    conn.execute('INSERT INTO scores (student_id, story_id, score) VALUES (?, ?, ?)', (user_id, story_id, total_correct))
    
    train_lfm(conn)
    conn.commit()
    conn.close()

    return render_template('result.html', score=total_correct, total=len(responses), theta=round(new_theta, 2), story_title=story['title'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
