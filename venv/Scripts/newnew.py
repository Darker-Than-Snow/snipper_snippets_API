from flask import Flask, request, jsonify

app = Flask(__name__)

snippets = []
next_id = 1

@app.route('/snippets', methods=['POST'])
def create_snippet():
    global next_id
    data = request.get_json()
    if not data or 'code' not in data or 'language' not in data:
        return jsonify({'error': 'Missing code or language'}), 400

    snippet = {
        'id': next_id,
        'code': data['code'],
        'language': data['language'],
        'description': data.get('description', '')  # Optional description
    }
    snippets.append(snippet)
    next_id += 1
    return jsonify(snippet), 201

@app.route('/snippets', methods=['GET'])
def get_snippets():
    lang = request.args.get('lang')
    if lang:
        filtered_snippets = [s for s in snippets if s['language'] == lang]
        return jsonify(filtered_snippets)
    else:
        return jsonify(snippets)

@app.route('/snippets/<int:snippet_id>', methods=['GET'])
def get_snippet(snippet_id):
    snippet = next((s for s in snippets if s['id'] == snippet_id), None)
    if snippet:
        return jsonify(snippet)
    else:
        return jsonify({'error': 'Snippet not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)