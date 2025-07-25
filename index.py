from flask import Flask, request, send_file, jsonify
from yt_dlp import YoutubeDL
from threading import Thread
import os
import uuid

app = Flask(__name__)

DOWNLOADS = {}

def progress_hook(d):
    if d['status'] == 'downloading':
        video_id = d['info_dict'].get('id')
        if video_id and video_id in DOWNLOADS:
            percent = d.get('_percent_str', '0.0%').strip()
            try:
                DOWNLOADS[video_id]['progress'] = float(percent.replace('%', ''))
            except:
                DOWNLOADS[video_id]['progress'] = 0.0
    elif d['status'] == 'finished':
        video_id = d['info_dict'].get('id')
        if video_id and video_id in DOWNLOADS:
            DOWNLOADS[video_id]['progress'] = 100.0
            DOWNLOADS[video_id]['filepath'] = d['filename']


def download_worker(url, convert_to):
    ydl_opts = {
        'format': 'bestvideo[height<=2160][fps<=30]+bestaudio/best[height<=2160][fps<=30]',
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'noplaylist': False,
        'postprocessors': []
    }

    if convert_to == 'mp3':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if '_type' in info and info['_type'] == 'playlist':
            # Playlist
            for entry in info['entries']:
                video_id = entry['id']
                if video_id in DOWNLOADS:
                    DOWNLOADS[video_id]['status'] = 'done'
        else:
            # Single video
            video_id = info['id']
            if video_id in DOWNLOADS:
                DOWNLOADS[video_id]['status'] = 'done'
                DOWNLOADS[video_id]['filename'] = ydl.prepare_filename(info)
                print("Selected format:", info.get('format'))

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    convert_to = data.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    # Use a UUID to track the session
    task_id = str(uuid.uuid4())
    DOWNLOADS[task_id] = {
        'progress': 0.0,
        'status': 'downloading',
        'filepath': None
    }

    def thread_func():
        download_worker(url, convert_to)
        DOWNLOADS[task_id]['status'] = 'done'

    Thread(target=thread_func).start()

    return jsonify({'task_id': task_id})

@app.route('/progress/<task_id>')
def progress(task_id):
    if task_id not in DOWNLOADS:
        return jsonify({'error': 'Invalid task ID'}), 404
    return jsonify(DOWNLOADS[task_id])

@app.route('/file/<task_id>')
def file(task_id):
    if task_id not in DOWNLOADS:
        return jsonify({'error': 'Invalid task ID'}), 404
    filepath = DOWNLOADS[task_id].get('filepath')
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
