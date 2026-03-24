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

@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_connection()
    
    # 1. Get Student Info
    student_data = conn.execute('SELECT grade_level FROM students WHERE student_id = ?', (user_id,)).fetchone()
    student_grade = student_data['grade_level'] if student_data else 4
    
    # 2. Get IRT Ability (Theta) from student_model
    student_theta = get_ability(user_id, conn)
    
    # 3. Get BKT Mastery Summary from student_model
    mastery_row = conn.execute('SELECT mastery FROM student_model WHERE student_id = ?', (user_id,)).fetchone()
    student_mastery = mastery_row['mastery'] if mastery_row else 0.0

    # 4. Adaptive filtering (Zone of Proximal Development)
    low_bound, high_bound = student_theta - 1.5, student_theta + 1.5

    # Filter stories based on Grade and IRT Ability
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

@app.route('/quiz/<int:story_id>')
def take_quiz(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    conn.close()
    
    if not story: return "Story not found", 404
    return render_template('quiz.html', story=story, questions=questions)

@app.route('/story/<int:story_id>')
def view_story(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    conn.close()
    if not story: return "Story not found", 404
    return render_template('story.html', story=story)

@app.route('/submit_quiz/<int:story_id>', methods=['POST'])
def submit_quiz(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    user_id = session['user_id']
    conn = get_connection()
    
    # 1. Fetch questions and story data
    questions = conn.execute('''
        SELECT question_id, correct_answer, difficulty_level, skill_id 
        FROM questions WHERE story_id = ?
    ''', (story_id,)).fetchall()
    
    story = conn.execute('SELECT title, difficulty_level FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    
    if not questions or not story:
        conn.close()
        return "Quiz data missing", 404

    responses = []
    total_correct = 0

    # 2. Process each question
    for q in questions:
        user_choice = request.form.get(f"question_{q['question_id']}")
        is_correct = 1 if str(user_choice).strip().lower() == str(q['correct_answer']).strip().lower() else 0
        
        responses.append(is_correct)
        total_correct += is_correct
        
        # BKT Update per Skill
        bkt_update(user_id, q['skill_id'], is_correct, conn=conn)
        
        # LFM Tracking
        increment_difficulty_attempt(user_id, q['difficulty_level'], conn=conn)

    # 3. Algorithm Calculations
    new_theta = irt_update(user_id, story['difficulty_level'], responses, conn)
    
    # 4. Sync Database (Update student_model)
    conn.execute('''
        UPDATE student_model 
        SET ability = ?, 
            mastery = (SELECT AVG(mastery_probability) FROM student_skill_mastery WHERE student_id = ?)
        WHERE student_id = ?
    ''', (new_theta, user_id, user_id))

    conn.execute('INSERT INTO scores (student_id, story_id, score) VALUES (?, ?, ?)', 
                 (user_id, story_id, total_correct))
    
    # 5. Get the final mastery value to pass to the template (Fixes UndefinedError)
    mastery_row = conn.execute('SELECT mastery FROM student_model WHERE student_id = ?', (user_id,)).fetchone()
    current_mastery = mastery_row['mastery'] if mastery_row else 0.0
    
    train_lfm(conn)
    
    conn.commit()
    conn.close()

    # 6. Render results with all necessary variables
    return render_template('result.html', 
                           score=total_correct, 
                           total=len(responses), 
                           theta=round(new_theta, 2),
                           mastery=current_mastery,  # Sent to fix the Jinja2 error
                           story_title=story['title'])
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Register Authentication Blueprint
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
