from flask import Flask, request, render_template_string, send_file
import os
import uuid
import yt_dlp
import subprocess

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouTube Downloader</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-white">
<div class="container mt-5">
    <h2>YouTube Downloader with Trimmer</h2>
    <form method="post">
        <div class="mb-3">
            <label>YouTube URL</label>
            <input type="text" class="form-control" name="url" required>
        </div>
        <div class="mb-3">
            <label>Select Format</label><br>
            <input type="radio" name="format" value="video" checked> Video
            <input type="radio" name="format" value="audio"> Audio (MP3)
        </div>
        <div class="mb-3">
            <input type="checkbox" name="trim" id="trim">
            <label for="trim">Enable Trimming</label>
        </div>
        <div class="mb-3">
            <label>Start Time (e.g. 00:00:05)</label>
            <input type="text" class="form-control" name="start" value="00:00:00">
        </div>
        <div class="mb-3">
            <label>End Time (e.g. 00:00:20)</label>
            <input type="text" class="form-control" name="end" value="00:00:20">
        </div>
        <button type="submit" class="btn btn-success">Download</button>
    </form>
    {% if download_url %}
        <div class="alert alert-info mt-4">
            <strong>Download ready:</strong> <a href="{{ download_url }}" class="text-white">Click here</a>
        </div>
    {% elif error %}
        <div class="alert alert-danger mt-4">Error: {{ error }}</div>
    {% endif %}
</div>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    download_url = None
    error = None

    if request.method == "POST":
        url = request.form.get("url")
        format_type = request.form.get("format")
        trim_enabled = request.form.get("trim")
        start_time = request.form.get("start")
        end_time = request.form.get("end")

        try:
            file_id = str(uuid.uuid4())
            output_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

            ydl_opts = {
                'outtmpl': output_path,
                'quiet': True
            }

            if format_type == "audio":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '256',
                    }]
                })
            else:
                ydl_opts['format'] = 'best[ext=mp4]'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if format_type == "audio":
                    filename = filename.rsplit(".", 1)[0] + ".mp3"

            # Apply trimming if enabled
            if trim_enabled:
                trimmed_filename = filename.rsplit(".", 1)[0] + "_trimmed." + filename.rsplit(".", 1)[1]
                subprocess.call([
                    "ffmpeg", "-y", "-i", filename,
                    "-ss", start_time,
                    "-to", end_time,
                    "-c", "copy",
                    trimmed_filename
                ])
                filename = trimmed_filename

            download_url = f"/download/{os.path.basename(filename)}"

        except Exception as e:
            error = str(e)

    return render_template_string(HTML_TEMPLATE, download_url=download_url, error=error)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
