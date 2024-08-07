from flask import Flask, send_file, request, jsonify
import yt_dlp
import os
import threading

app = Flask(__name__)
download_progress = 0

def download_video(url, filename):
    global download_progress
    ydl_opts = {
        'outtmpl': filename,
        'progress_hooks': [progress_hook]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def progress_hook(d):
    global download_progress
    if d['status'] == 'downloading':
        download_progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100

@app.route('/')
def home():
    return 'Flask application is running!'

@app.route('/download')
def download_video_route():
    url = request.args.get('url')
    filename = 'downloaded_video.mp4'
    
    if not os.path.exists(filename):
        download_thread = threading.Thread(target=download_video, args=(url, filename))
        download_thread.start()
        return jsonify({'message': 'Downloading video...', 'filename': filename})

    return send_file(filename, as_attachment=True)

@app.route('/progress')
def progress():
    return jsonify({'progress': download_progress})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
