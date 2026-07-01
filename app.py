import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this-later" # Keeps logins secure

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Database Setup Helper Function
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Run database creation
init_db()

# Main Chat Interface (Protected)
@app.route('/')
def home():
    if "user" not in session:
        return redirect(url_for('login')) # Send to login if not signed in
    return render_template('index.html', username=session["user"])

# Sign Up Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists! Try a different one."
            
    return render_template('signup.html')

# Log In Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username # Save user session data
            return redirect(url_for('home'))
        else:
            return "Invalid username or password!"

    return render_template('login.html')

# Log Out Route
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

# AI Message Processing Endpoint
@app.route('/chat', methods=['POST'])
def chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get("message")
    
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