PRAGMA journal_mode=WAL;

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

CREATE TABLE IF NOT EXISTS stories (
    story_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    grade_level INTEGER NOT NULL,
    difficulty_level REAL NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL, -- This will store 'A', 'B', 'C', or 'D'
    difficulty_level REAL NOT NULL,
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
);

CREATE TABLE IF NOT EXISTS scores (
    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    story_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    date_taken DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
);

CREATE TABLE IF NOT EXISTS student_model (
    student_id INTEGER PRIMARY KEY,
    ability REAL DEFAULT 0.0,
    mastery REAL DEFAULT 0.0,
    FOREIGN KEY (student_id) REFERENCES students(student_id)

);
ALTER TABLE student_model ADD COLUMN beta_student REAL DEFAULT 0.0;
ALTER TABLE skills ADD COLUMN beta_skill REAL DEFAULT 0.0;
ALTER TABLE skills ADD COLUMN gamma_skill REAL DEFAULT 0.05;

CREATE TABLE IF NOT EXISTS student_skill_attempts (
    student_id INTEGER,
    skill_id INTEGER,
    attempts INTEGER DEFAULT 0,
    PRIMARY KEY (student_id, skill_id)
);
CREATE TABLE IF NOT EXISTS skills (
    skill_id TEXT PRIMARY KEY, -- Literal, Inferential, Critical
    beta_skill REAL DEFAULT 0.0,
    gamma_skill REAL DEFAULT 0.1
);
CREATE TABLE IF NOT EXISTS student_difficulty_attempts (
    student_id INTEGER,
    difficulty_level REAL,
    attempts INTEGER DEFAULT 0,
    PRIMARY KEY (student_id, difficulty_level)
);
-- Ensure stories table has the baseline flag
CREATE TABLE IF NOT EXISTS stories (
    story_id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    difficulty_level REAL,
    is_baseline INTEGER DEFAULT 0
);

-- Ensure questions table has choice columns
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY,
    story_id INTEGER,
    question_text TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_answer TEXT,
    difficulty_level REAL,
    FOREIGN KEY (story_id) REFERENCES stories(story_id)
);
