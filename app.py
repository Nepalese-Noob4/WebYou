from flask import Flask, request, jsonify, Response
import yt_dlp
import threading
import os
import time
import re

def progress_hook(d):
    if d['status'] == 'downloading':
        # Clean up escape sequences
        d['progress'] = re.sub(r'\x1b\[[0-9;]*m', '', d['progress'])
        d['eta'] = re.sub(r'\x1b\[[0-9;]*m', '', d['eta'])
        d['speed'] = re.sub(r'\x1b\[[0-9;]*m', '', d['speed'])

        # Ensure total bytes is not zero
        if d.get('total_bytes_estimate') and d['total_bytes'] == 0:
            d['total_bytes'] = d['total_bytes_estimate']

        # Update progress data
        download_progress[d['filename']] = {
            'downloaded_bytes': d['downloaded_bytes'],
            'total_bytes': d['total_bytes'],
            'progress': d['progress'],
            'eta': d['eta'],
            'speed': d['speed'],
            'status': d['status'],
        }
    elif d['status'] == 'finished':
        download_progress[d['filename']]['status'] = 'finished'

app = Flask(__name__)
video_download_progress = {}

# Home Route
@app.route('/')
def index():
    return "Welcome to the WebYou downloader!"

# Video Download Route
@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.json.get('url')
    video_name = request.json.get('name')

    if not video_url or not video_name:
        return jsonify({"error": "Please provide both URL and video name"}), 400

    def download():
        ydl_opts = {
            'outtmpl': f'{video_name}.%(ext)s',
            'progress_hooks': [lambda d: update_progress(d, video_name)],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except yt_dlp.utils.DownloadError as e:
                video_download_progress[video_name] = {"status": "error", "message": str(e)}

        # Auto-delete the video after download
        if os.path.exists(f'{video_name}.mp4'):
            time.sleep(5)  # Keep video for 5 seconds before deletion
            os.remove(f'{video_name}.mp4')
            video_download_progress.pop(video_name, None)

    threading.Thread(target=download).start()

    return jsonify({"status": "Downloading started", "video_name": video_name})

# Progress Route
@app.route('/progress/<video_name>', methods=['GET'])
def progress(video_name):
    progress_info = video_download_progress.get(video_name, {"status": "not_found"})
    return jsonify(progress_info)

def update_progress(d, video_name):
    if d['status'] == 'downloading':
        video_download_progress[video_name] = {
            'status': 'downloading',
            'downloaded_bytes': d.get('downloaded_bytes', 0),
            'total_bytes': d.get('total_bytes', 0),
            'progress': d.get('_percent_str', '0%').strip(),
            'speed': d.get('_speed_str', '0').strip(),
            'eta': d.get('_eta_str', '0').strip()
        }
    elif d['status'] == 'finished':
        video_download_progress[video_name] = {"status": "completed"}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
