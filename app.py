from flask import Flask, request, jsonify, send_file, render_template
import os
import yt_dlp
from threading import Thread
from uuid import uuid4

app = Flask(__name__)
handler = app  # for vercel-style fallback

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_video(link, format_type, file_id):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
        'format': 'bestvideo[height<=2160][fps<=30]+bestaudio/best[height<=2160][fps<=30]',
        'noplaylist': False,
        'quiet': True
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/download", methods=["POST"])
def download():
    data = request.json
    link = data.get("link")
    format_type = data.get("format", "mp4")

    if not link:
        return jsonify({"error": "No link provided"}), 400

    file_id = str(uuid4())
    t = Thread(target=download_video, args=(link, format_type, file_id))
    t.start()

    return jsonify({"status": "started", "file_id": file_id})

@app.route("/api/status/<file_id>")
def status(file_id):
    for ext in ["mp4", "mkv", "webm", "mp3"]:
        path = f"{DOWNLOAD_FOLDER}/{file_id}.{ext}"
        if os.path.exists(path):
            return jsonify({"status": "completed", "download_url": f"/api/downloaded/{file_id}.{ext}"})
    return jsonify({"status": "processing"})

@app.route("/api/downloaded/<filename>")
def serve_file(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404
