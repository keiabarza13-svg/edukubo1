from flask import Flask, render_template, abort, jsonify, request, session, redirect, url_for
from database import get_connection 
from auth import auth_bp
import random

app = Flask(__name__)
app.secret_key = 'your_research_secret_key' # Change this for production
app.register_blueprint(auth_bp)

# --- HOME ROUTE: Serving the Access Page (Login/Register) ---
@app.route('/')
def home():
    # REMOVE the 'if user_id in session' check here
    # This forces the app to ALWAYS show the Login/Register screen first
    return render_template('index.html')

# --- DASHBOARD: The Reading Library ---
@app.route('/dashboard/<role>')
def dashboard(role):
    # Security: Redirect to login if session is empty
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_connection()
    # Fetch all stories for the library
    stories_rows = conn.execute('SELECT * FROM stories').fetchall()
    conn.close()
    
    # Randomize stories for the placeholder phase
    stories = list(stories_rows)
    random.shuffle(stories)
    
    full_name = session.get('full_name', 'Student')
    
    return render_template('dashboard.html', 
                           stories=stories, 
                           role=role, 
                           full_name=full_name)

# --- STORY VIEW ---
@app.route('/story/<int:story_id>')
def view_story(story_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_connection()
    story = conn.execute('SELECT * FROM stories WHERE story_id = ?', (story_id,)).fetchone()
    conn.close()

    if story is None:
        return abort(404)

    return render_template('story.html', story=story)

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)