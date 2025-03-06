from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import bcrypt
import os

app = Flask(__name__)

# Encryption
ENCRYPTION_KEY = os.getenv("SNIPPR_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    print("Warning: SNIPPR_ENCRYPTION_KEY not set. Using generated key. Store this securely!")
cipher = Fernet(ENCRYPTION_KEY)

def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt(text):
    return cipher.decrypt(text.encode()).decode()

# Authentication
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Data store
snippets = []
users = {}
next_id = 1

@app.route('/snippets', methods=['POST'])
def create_snippet():
    global next_id
    data = request.get_json()
    if not data or 'code' not in data or 'language' not in data:
        return jsonify({'error': 'Missing code or language'}), 400

    snippet = {
        'id': next_id,
        'code': encrypt(data['code']),
        'language': data['language'],
        'description': data.get('description', '')
    }
    snippets.append(snippet)
    next_id += 1
    return jsonify(snippet), 201

@app.route('/snippets', methods=['GET'])
def get_snippets():
    lang = request.args.get('lang')
    filtered_snippets = [s for s in snippets if lang is None or s['language'] == lang]
    for s in filtered_snippets:
        s['code'] = decrypt(s['code'])
    return jsonify(filtered_snippets)

@app.route('/snippets/<int:snippet_id>', methods=['GET'])
def get_snippet(snippet_id):
    snippet = next((s for s in snippets if s['id'] == snippet_id), None)
    if snippet:
        snippet['code'] = decrypt(snippet['code'])
        return jsonify(snippet)
    else:
        return jsonify({'error': 'Snippet not found'}), 404

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400

    email = data['email']
    password = hash_password(data['password'])

    if email in users:
        return jsonify({'error': 'User already exists'}), 400

    users[email] = {'password': password}
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/users', methods=['GET'])
def get_user():
    auth = request.authorization
    if not auth or auth.username not in users or not check_password(auth.password, users[auth.username]['password']):
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({'email': auth.username})

if __name__ == '__main__':
    app.run(debug=True)