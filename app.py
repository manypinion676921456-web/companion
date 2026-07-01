import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
# Secure session key for tracking log-ins
app.secret_key = "super-secret-key-change-this-later" 

# Initialize Groq client using your environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Simple, reliable storage that works across Render's basic workers without crashing
USERS_DB = {}

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
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            return "Please fill out all fields."

        if username in USERS_DB:
            return "Username already exists! Try a different one."
        
        # Securely hash password and save it
        USERS_DB[username] = generate_password_hash(password)
        return redirect(url_for('login'))
            
    return render_template('signup.html')

# 3. Log In Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        hashed_password = USERS_DB.get(username)

        if hashed_password and check_password_hash(hashed_password, password):
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
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)