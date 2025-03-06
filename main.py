from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Load seed data
try:
    with open("seedData.json", "r") as file:
        snippets = json.load(file)
except FileNotFoundError:
    snippets = []

# In-memory data store
snippets_store = {snippet["id"]: snippet for snippet in snippets}
next_id = max(snippets_store.keys()) + 1 if snippets_store else 1

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Snippr API! Use /snippets to interact."}), 200

@app.route("/snippets", methods=["POST"])
def add_snippet():
    global next_id
    data = request.get_json()
    if not data or "language" not in data or "code" not in data:
        return jsonify({"error": "Missing required fields: language, code"}), 400

    snippet = {
        "id": next_id,
        "language": data["language"],
        "code": data["code"]
    }
    snippets_store[next_id] = snippet
    next_id += 1

    return jsonify(snippet), 201

@app.route("/snippets", methods=["GET"])
def get_snippets():
    lang_filter = request.args.get("lang")
    if lang_filter:
        filtered_snippets = [snippet for snippet in snippets_store.values() if snippet["language"].lower() == lang_filter.lower()]
        return jsonify(filtered_snippets)
    return jsonify(list(snigit add .ppets_store.values()))

@app.route("/snippets/<int:snippet_id>", methods=["GET"])
def get_snippet_by_id(snippet_id):
    snippet = snippets_store.get(snippet_id)
    if not snippet:
        return jsonify({"error": "Snippet not found"}), 404
    return jsonify(snippet)

if __name__ == "__main__":
    app.run(debug=True)
