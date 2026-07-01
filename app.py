import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
# Secure secret key for handling logged-in user sessions
app.secret_key = "super-secret-key-change-this-later"

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Path to store our user credentials safely in a file
DATA_FILE = "/tmp/users.json"

# Helper function to load users from our file database
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# Helper function to save users to our file database
def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

# ------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------

# 1. Main Chat Page (Protected)
@app.route('/')
def home():
    if "user" not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session["user"])

# 2. Sign Up Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return "Please fill out all fields."

        users = load_users()
        if username in users:
            return "Username already exists! Try a different one."

        # Scramble the password and save the new user
        users[username] = generate_password_hash(password)
        save_users(users)
        return redirect(url_for('login'))

    return render_template('signup.html')

# 3. Log In Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        users = load_users()
        hashed_password = users.get(username)

        # Verify username exists and password matches the hash
        if hashed_password and check_password_hash(hashed_password, password):
            session["user"] = username
            return redirect(url_for('home'))
        else:
            return "Invalid username or password!"

    return render_template('login.html')

# 4. Log Out Process
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

# 5. AI Chat Routing Endpoint
@app.route('/chat', methods=['POST'])
def chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Call Groq AI with Llama 3.3
        completion = client.chat.completions.create(
            model="llama-3.3-70b-specdec",
            messages=[
                {"role": "system", "content": "You are a helpful and intelligent AI companion."},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = completion.choices[0].message.content
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)