from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from database import get_connection 
from auth import auth_bp

# Import your algorithm logic
from algorithm.irt import get_ability, irt_update
from algorithm.bkt import bkt_update
from algorithm.lfm import train_lfm, increment_difficulty_attempt

app = Flask(__name__)
app.secret_key = 'edukubo_research_2026'

# --- 1. CORE ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_connection()
    
    # Fetch Student Grade Level
    student_data = conn.execute('''
        SELECT s.grade_level 
        FROM students s 
        WHERE s.student_id = ?
    ''', (user_id,)).fetchone()
    
    student_grade = student_data['grade_level'] if student_data else 4
    
    # Get IRT Ability (Theta)
    student_theta = get_ability(user_id, conn)
    
    # Get BKT Mastery
    mastery_row = conn.execute('SELECT mastery FROM student_model WHERE student_id = ?', (user_id,)).fetchone()
    student_mastery = mastery_row['mastery'] if mastery_row else 0.0

    # Range for Adaptive filtering (ZPD)
    low_bound = student_theta - 1.5  # Slightly widened for initial testing
    high_bound = student_theta + 1.5

    # Filter stories: Grade match + Difficulty Range
    # Using CAST to force "0" or "0.0" to be treated as a real number
    query = """
        SELECT * FROM stories 
        WHERE grade_level = ? 
        AND CAST(difficulty_level AS REAL) BETWEEN ? AND ?
        ORDER BY difficulty_level ASC
    """
    stories_rows = conn.execute(query, (student_grade, low_bound, high_bound)).fetchall()
    
    # --- TERMINAL DEBUGGING ---
    print(f"\n--- DASHBOARD DEBUG ---")
    print(f"User: {session.get('full_name')} | Grade: {student_grade}")
    print(f"Current Ability: {student_theta}")
    print(f"Searching for Difficulty between {low_bound} and {high_bound}")
    print(f"Stories Found: {len(stories_rows)}")
    print(f"------------------------\n")

    conn.close()
    
    return render_template('dashboard.html', 
                           stories=list(stories_rows), 
                           role=role,
                           full_name=session.get('full_name', 'Student'),
                           ability=round(student_theta, 2),
                           mastery=round(student_mastery, 2),
                           grade=student_grade)

@app.route('/story/<int:story_id>')
def view_story(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))

    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    conn.close()

    if not story: return "Story not found", 404
    return render_template('story.html', story=story, questions=questions)

@app.route('/submit_quiz/<int:story_id>', methods=['POST'])
def submit_quiz(story_id):
    if 'user_id' not in session: return redirect(url_for('home'))
    user_id = session['user_id']
    conn = get_connection()
    
    questions = conn.execute('SELECT question_id, correct_answer, difficulty_level FROM questions WHERE story_id = ?', (story_id,)).fetchall()
    story = conn.execute('SELECT difficulty_level FROM stories WHERE story_id = ?', (story_id,)).fetchone()

    responses = []
    for q in questions:
        user_choice = request.form.get(f"question_{q['question_id']}")
        is_correct = 1 if user_choice == q['correct_answer'] else 0
        responses.append(is_correct)
        
        # LFM Tracking
        increment_difficulty_attempt(user_id, q['difficulty_level'], conn=conn)

    # Run Algorithms
    new_theta = irt_update(user_id, story['difficulty_level'], responses, conn)
    avg_score = sum(responses) / len(responses) if responses else 0
    new_mastery = bkt_update(user_id, avg_score, conn)

    # Save score
    conn.execute('INSERT INTO scores (student_id, story_id, score) VALUES (?, ?, ?)', 
                 (user_id, story_id, sum(responses)))
    
    train_lfm(conn)
    conn.commit()
    conn.close()

    return render_template('result.html', 
                           score=sum(responses), 
                           total=len(responses), 
                           theta=round(new_theta, 2), 
                           mastery=round(new_mastery, 2))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- 2. REGISTER BLUEPRINTS LAST ---
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
