PRAGMA journal_mode=WAL;

-- 1. USER MANAGEMENT
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('student','teacher')) NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY,
    grade_level INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- 2. CONTENT MANAGEMENT
CREATE TABLE IF NOT EXISTS stories (
    story_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    grade_level INTEGER NOT NULL,
    difficulty_level REAL NOT NULL, -- Used by IRT and LFM
    content TEXT NOT NULL,
    is_baseline INTEGER DEFAULT 0  -- 1 for initial assessment, 0 for adaptive
);

CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER,
    skill_id TEXT,           -- 'Literal', 'Inferential', 'Critical'
    question_text TEXT,      -- The actual sentence
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_answer TEXT,
    difficulty_level REAL    -- For IRT
);

-- 3. THE STUDENT MODEL (The "Brain" of the App)
CREATE TABLE IF NOT EXISTS student_model (
    student_id INTEGER PRIMARY KEY,
    ability REAL DEFAULT 0.0,       -- IRT Theta (Reading Ability)
    mastery REAL DEFAULT 0.0,       -- Global BKT Mastery
    beta_student REAL DEFAULT 0.0,  -- LFM Student Factor
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 4. ALGORITHM TRACKING TABLES
-- Tracks BKT progress per skill (Literal, Inferential, etc.)
CREATE TABLE IF NOT EXISTS student_skill_mastery (
    student_id INTEGER NOT NULL,
    skill_id TEXT NOT NULL,
    mastery_probability REAL DEFAULT 0.2, 
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Tracks LFM attempts per difficulty level
CREATE TABLE IF NOT EXISTS student_difficulty_attempts (
    student_id INTEGER,
    difficulty_level REAL,
    attempts INTEGER DEFAULT 0,
    PRIMARY KEY (student_id, difficulty_level),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 5. PERFORMANCE HISTORY
CREATE TABLE IF NOT EXISTS scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    date_taken DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
);