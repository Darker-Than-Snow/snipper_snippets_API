from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import bcrypt
import os
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

# Encryption setup
ENCRYPTION_KEY = os.getenv("SNIPPR_ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)

def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt(text):
    return cipher.decrypt(text.encode()).decode()

# JWT secret key
app.config['SECRET_KEY'] = os.getenv("JWT_SECRET", "supersecretkey")

# User and snippet storage
users = {}
snippets = []
next_id = 1

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            token = token.split(" ")[1]  # Expecting "Bearer <token>"
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users.get(data['email'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': 'Token is invalid or expired', 'message': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400
    
    email = data['email']
    if email in users:
        return jsonify({'error': 'User already exists'}), 400
    
    users[email] = {'password': hash_password(data['password'])}
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = users.get(data['email'])
    if not user or not check_password(data['password'], user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = jwt.encode({'email': data['email'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, 
                        app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token': token})

@app.route('/snippets', methods=['POST'])
@token_required
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
@token_required
def get_snippets():
    lang = request.args.get('lang')
    filtered_snippets = [s for s in snippets if lang is None or s['language'] == lang]
    for s in filtered_snippets:
        s['code'] = decrypt(s['code'])
    return jsonify(filtered_snippets)

if __name__ == '__main__':
    app.run(debug=True)
