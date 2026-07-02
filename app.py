import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-change-this-later")

if os.name == "nt":
    DATA_FILE = os.path.join(os.path.expanduser("~"), "companion_users.json")
else:
    DATA_FILE = "/tmp/users.json"


def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_users(users):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(users, f)
    except Exception as exc:
        print(f"Error saving user database file: {exc}")


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def stream_chat_response(model, messages):
    try:
        client = get_groq_client()
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue

            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue

            content = getattr(delta, "content", None)
            if content:
                yield f"data: {json.dumps({'token': content})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as exc:
        fallback = (
            "I’m running in local fallback mode because no Groq API key is configured. "
            f"Your message was: {messages[-1]['content']}"
        )
        for word in fallback.split():
            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"


@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["user"])


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return "Please fill out all fields."

        users = load_users()
        if username in users:
            return "Username already exists! Try a different one."

        users[username] = generate_password_hash(password)
        save_users(users)
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        users = load_users()
        hashed_password = users.get(username)

        if hashed_password and check_password_hash(hashed_password, password):
            session["user"] = username
            return redirect(url_for("home"))
        return "Invalid username or password!"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/api/chat", methods=["POST"])
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    model = payload.get("model") or os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    messages = [
        {"role": "system", "content": "You are a helpful and intelligent AI companion."},
        {"role": "user", "content": user_message},
    ]

    return Response(
        stream_chat_response(model, messages),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")