import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
# Secure session key for tracking log-ins
app.secret_key = "super-secret-key-change-this-later" 

# Initialize Groq client using your environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Database Setup Helper Function (Uses in-memory to prevent Render Free Tier disk errors)
def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn

# Initialize the global database connection
db_conn = init_db()

# 1. Main Chat Interface (Protected: Redirects to login if not authenticated)
@app.route('/')
def home():
    if "user" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session["user"])

# 2. Sign Up Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            db_conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists! Try a different one."
            
    return render_template('signup.html')

# 3. Log In Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session["user"] = username # Save session cookie
            return redirect(url_for('home'))
        else:
            return "Invalid username or password!"

    return render_template('login.html')

# 4. Log Out Route
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

# 5. AI Chat Message Endpoint
@app.route('/chat', methods=['POST'])
def chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get("message")
    
    # AI Query using Llama 3.3
    completion = client.chat.completions.create(
        model="llama-3.3-70b-specdec",
        messages=[
            {"role": "system", "content": "You are a helpful and intelligent AI companion."},
            {"role": "user", "content": user_message}
        ]
    )
    
    ai_response = completion.choices[0].message.content
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)