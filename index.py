from flask import Flask, request, render_template, send_file
import os
import uuid
import yt_dlp
import subprocess

# Flask setup
app = Flask(__name__, template_folder="../templates")

# Writable folder for Vercel or serverless environments
DOWNLOAD_FOLDER = "/tmp"

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
                # Generate unique filename
                file_id = str(uuid.uuid4())
                output_path = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

                # yt-dlp download options
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
                            'preferredquality': '256',  # 256kbps
                        }]
                    })
                else:
                    ydl_opts.update({
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
                    })

                # Download video/audio
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                    if format_type == 'audio':
                        filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

                trimmed_file = filename

                # Trim if checkbox is selected
                if do_trim and start_time and end_time:
                    trimmed_file = filename.replace(".", "_trimmed.")
                    trim_cmd = [
                        "ffmpeg", "-i", filename,
                        "-ss", start_time,
                        "-to", end_time,
                        "-c", "copy",
                        trimmed_file
                    ]
                    subprocess.run(trim_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    if os.path.exists(trimmed_file):
                        os.remove(filename)  # delete original untrimmed

                download_url = f"/api/download/{os.path.basename(trimmed_file)}"

            except Exception as e:
                error = str(e)

    return render_template("index.html", download_url=download_url, error=error)

@app.route('/api/download/<filename>')
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

# Only needed for local testing
if __name__ == '__main__':
    app.run(debug=True)
