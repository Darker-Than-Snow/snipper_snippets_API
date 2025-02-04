from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Load initial data from seedData.json
try:
    with open('seedData.json', 'r') as f:
        snippets = json.load(f)
except FileNotFoundError:
    snippets = []

# Initialize next_snippet_id *outside* the route function
next_snippet_id = max((snippet['id'] for snippet in snippets), default=0) + 1


@app.route('/snippets', methods=['POST'])
def create_snippet():
    global next_snippet_id  # Declare next_snippet_id as global *before* using it

    data = request.get_json()
    if not data or 'language' not in data or 'code' not in data:
        return jsonify({'error': 'Language and code are required'}), 400

    new_snippet = {
        'id': next_snippet_id,
        'language': data['language'],
        'code': data['code']
    }
    snippets.append(new_snippet)
    next_snippet_id += 1  # Now it's okay to increment
    return jsonify(new_snippet), 201


@app.route('/snippets', methods=['GET'])
def get_all_snippets():
    lang = request.args.get('lang')
    if lang:
        filtered_snippets = [s for s in snippets if s['language'].lower() == lang.lower()]
        return jsonify(filtered_snippets), 200
    return jsonify(snippets), 200


@app.route('/snippets/<int:snippet_id>', methods=['GET'])
def get_snippet_by_id(snippet_id):
    for snippet in snippets:
        if snippet['id'] == snippet_id:
            return jsonify(snippet), 200
    return jsonify({'error': 'Snippet not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)