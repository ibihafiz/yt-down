from flask import Flask, request, render_template_string, send_file
import os
import uuid
import yt_dlp
import subprocess

app = Flask(__name__)

# Writable folder for serverless platforms like Vercel
DOWNLOAD_FOLDER = "/tmp"

# Inline HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YouTube Downloader SaaS</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-dark text-white">
<div class="container mt-5">
    <h2 class="mb-4">YouTube Video & Audio Downloader</h2>
    <form method="post">
        <div class="mb-3">
            <label for="url" class="form-label">YouTube Link</label>
            <input type="text" class="form-control" id="url" name="url" placeholder="Paste YouTube URL here" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Select Format</label><br>
            <input type="radio" id="video" name="format" value="video" checked>
            <label for="video">Video</label>
            <input type="radio" id="audio" name="format" value="audio">
            <label for="audio">Audio (MP3)</label>
        </div>
        <div class="mb-3 form-check">
            <input type="checkbox" class="form-check-input" id="trim" name="trim">
            <label class="form-check-label" for="trim">Trim file (start-end)</label>
        </div>
        <div class="row mb-3">
            <div class="col">
                <label for="start">Start Time (HH:MM:SS)</label>
                <input type="text" class="form-control" name="start" placeholder="00:00:00">
            </div>
            <div class="col">
                <label for="end">End Time (HH:MM:SS)</label>
                <input type="text" class="form-control" name="end" placeholder="00:00:30">
            </div>
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

@app.route('/', methods=['GET', 'POST'])
def index():
    download_url = None
    error = None

    if request.method == 'POST':
        url = request.form.get('url')
        format_type = request.form.get('format')
        do_trim = request.form.get('trim') == 'on'
        start_time = request.form.get('start')
        end_time = request.form.get('end')

        if not url:
            error = "No URL provided."
        else:
            try:
                file_id = str(uuid.uuid4())
                output_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

                ydl_opts = {
                    'outtmpl': output_path,
                    'quiet': True,
                }

                if format_type == 'audio':
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '256',
                        }]
                    })
                else:
                    ydl_opts.update({
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    if format_type == 'audio':
                        filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

                trimmed_file = filename

                if do_trim and start_time and end_time:
                    trimmed_file = filename.replace(".", "_trimmed.")
                    subprocess.run([
                        "ffmpeg", "-i", filename,
                        "-ss", start_time,
                        "-to", end_time,
                        "-c", "copy", trimmed_file
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    if os.path.exists(trimmed_file):
                        os.remove(filename)

                download_url = f"/download/{os.path.basename(trimmed_file)}"

            except Exception as e:
                error = str(e)

    return render_template_string(HTML_TEMPLATE, download_url=download_url, error=error)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(DOWNLOAD_FOLDER, filename), as_attachment=True)

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
