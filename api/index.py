from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get("url")
    format_type = data.get("format")
    return jsonify({"message": f"Download started for {url} as {format_type}"})

handler = app  # Vercel needs this
