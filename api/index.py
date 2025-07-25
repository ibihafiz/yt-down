from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp"

@app.route("/api/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")
    convert_to = data.get("convert_to", "mp4")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    out_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo[height<=2160][fps<=30]+bestaudio/best[height<=2160][fps<=30]',
        'outtmpl': out_path,
        'merge_output_format': convert_to,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = convert_to
            final_path = out_path.replace("%(ext)s", ext)
        return send_file(final_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
