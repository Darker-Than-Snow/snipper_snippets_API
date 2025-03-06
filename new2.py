from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import bcrypt
import os
import json

app = Flask(__name__)

# Generate a key for encryption (should be stored securely in a real app)
ENCRYPTION_KEY = os.getenv("SNIPPR_ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)

# In-memory data store
snippets = []
users = {}

# Load seed data
try:
    with open('seedData.json', 'r') as f:
        snippets = json.load(f)
        next_id = max(s['id'] for s in snippets) + 1 if snippets else 1
except FileNotFoundError:
    next_id = 1
except json.JSONDecodeError:
    print("Error decoding seedData.json. Starting with empty snippets.")
    next_id = 1

# Helper functions for encryption and decryption
def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

def decrypt(text):
    return cipher.decrypt(text.encode()).decode()

# Helper functions for password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

@app.route("/snippets", methods=["POST"])
def create_snippet():
    data = request.json
    snippet_id = len(snippets) + 1
    snippet = {
        "id": snippet_id,
        "code": encrypt(data["code"]),
        "lang": data["lang"],
        "description": data.get("description")
    }
    snippets.append(snippet)
    return jsonify({"id": snippet_id, "message": "Snippet created successfully"}), 201

@app.route("/snippets", methods=["GET"])
def get_snippets():
    lang = request.args.get("lang")
    filtered_snippets = [s for s in snippets if lang is None or s["lang"].lower() == lang.lower()]
    for s in filtered_snippets:
        s["code"] = decrypt(s["code"])
    return jsonify(filtered_snippets)

@app.route("/snippets/<int:snippet_id>", methods=["GET"])
def get_snippet(snippet_id):
    snippet = next((s for s in snippets if s["id"] == snippet_id), None)
    if snippet is None:
        return jsonify({"error": "Snippet not found"}), 404
    snippet["code"] = decrypt(snippet["code"])
    return jsonify(snippet)

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    email = data["email"]
    password = hash_password(data["password"])
    if email in users:
        return jsonify({"error": "User already exists"}), 400
    users[email] = {"password": password}
    return jsonify({"message": "User created successfully"}), 201

@app.route("/users", methods=["GET"])
def get_user():
    auth = request.authorization
    if not auth or auth.username not in users or not check_password(auth.password, users[auth.username]["password"]):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"email": auth.username})

# Automated tests using pytest
import pytest
from flask.testing import FlaskClient

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_create_snippet(client: FlaskClient):
    response = client.post("/snippets", json={"code": "print('Hello')", "lang": "python", "description": "A simple print statement"})
    assert response.status_code == 201

def test_get_snippets(client: FlaskClient):
    response = client.get("/snippets")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_snippet_by_id(client: FlaskClient):
    client.post("/snippets", json={"code": "console.log('Hello')", "lang": "javascript"})
    response = client.get("/snippets/1")
    assert response.status_code == 200

def test_create_user(client: FlaskClient):
    response = client.post("/users", json={"email": "test@example.com", "password": "securepassword"})
    assert response.status_code == 201

def test_get_user_unauthorized(client: FlaskClient):
    response = client.get("/users", headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp3cm9uZ3Bhc3N3b3Jk"})
    assert response.status_code == 401