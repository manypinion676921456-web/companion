import os
import json
from flask import Flask, render_template, request, Response, jsonify
from groq import Groq

app = Flask(__name__)

# Hardcoded API Key to bypass PowerShell environment variable bugs entirely
client = Groq()
# In-memory storage for basic chat memory tracking
chat_memories = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clear', methods=['POST'])
def clear_chat():
    chat_memories.clear()
    return jsonify({"status": "success", "message": "Conversation history cleared."})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        user_message = data.get("message", "").strip()
        
        # Pulls dynamic model name chosen from the HTML dropdown
        # Defaults to the active Llama 3.1 8B if missing
        chosen_model = data.get("model", "llama-3.1-8b-instant")

        if not user_message:
            return jsonify({"error": "Empty message string received."}), 400

        # Set up a generic chat stream context if it doesn't exist yet
        if "active_user" not in chat_memories:
            chat_memories["active_user"] = [
                {"role": "system", "content": "You are Companion, a highly capable AI assistant."}
            ]

        chat_memories["active_user"].append({"role": "user", "content": user_message})

        # Request a real-time streaming text completion from Groq
        completion = client.chat.completions.create(
            model=chosen_model,
            messages=chat_memories["active_user"],
            temperature=0.7,
            max_tokens=2048,
            stream=True
        )

        def generate_stream():
            assistant_reply = ""
            try:
                for chunk in completion:
                    # Capture the token fragment safely
                    token = chunk.choices[0].delta.content
                    if token:
                        assistant_reply += token
                        # Package token into a Server-Sent Events (SSE) format data line
                        yield f"data: {json.dumps({'token': token})}\n\n"
                
                # Append finalized full assistant answer into context memory
                chat_memories["active_user"].append(
                    {"role": "assistant", "content": assistant_reply}
                )
            except Exception as stream_err:
                yield f"data: {json.dumps({'error': str(stream_err)})}\n\n"

        return Response(generate_stream(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({"error": f"Backend processing failure: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)