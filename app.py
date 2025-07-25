from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import yt_dlp

app = Flask(__name__)
DOWNLOADS_DIR = "downloads"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")
    format = data.get("format", "mp4")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    output_template = os.path.join(DOWNLOADS_DIR, f"%(title).50s-%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo[height<=2160]+bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': False,
        'quiet': True,
        'merge_output_format': format,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio' if format == 'mp3' else 'FFmpegVideoConvertor',
            'preferredcodec': format
        }],
    }

    paths = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])

        for file in os.listdir(DOWNLOADS_DIR):
            paths.append({
                "name": file,
                "path": f"/downloaded/{file}"
            })

        return jsonify({"files": paths})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/downloaded/<filename>")
def downloaded_file(filename):
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
