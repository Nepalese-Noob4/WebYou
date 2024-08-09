from flask import Flask, request, render_template_string, jsonify, send_file, redirect, url_for
import yt_dlp
import threading
import os
import re

app = Flask(__name__)
video_download_progress = {}
video_title = ""
downloaded_video_path = ""

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    os.chmod(directory, 0o755)

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def strip_ansi_escape_sequences(text):
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', text)

def update_progress(d, video_name):
    if d['status'] == 'downloading':
        video_download_progress[video_name] = {
            'status': 'downloading',
            'downloaded_bytes': d.get('downloaded_bytes', 0),
            'total_bytes': d.get('total_bytes', 0),
            'progress': strip_ansi_escape_sequences(d.get('_percent_str', '0%')).strip(),
            'speed': strip_ansi_escape_sequences(d.get('_speed_str', '0')).strip(),
            'eta': strip_ansi_escape_sequences(d.get('_eta_str', '0')).strip()
        }
    elif d['status'] == 'finished':
        video_download_progress[video_name] = {"status": "completed"}

@app.route('/', methods=['GET', 'POST'])
def index():
    global video_title, downloaded_video_path
    if request.method == 'POST':
        video_url = request.form.get('url')
        if video_url:
            video_title = ""
            def download():
                global video_title, downloaded_video_path
                ydl_opts = {
                    'outtmpl': f'{os.getenv("HOME")}/storage/downloads/%(title)s.%(ext)s',
                    'progress_hooks': [lambda d: update_progress(d, sanitize_filename(d["info_dict"].get('title', 'video')))],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info_dict = ydl.extract_info(video_url, download=False)
                        video_title = sanitize_filename(info_dict.get('title', 'video'))
                        ensure_directory(f'{os.getenv("HOME")}/storage/downloads')
                        downloaded_video_path = ydl.prepare_filename(info_dict)
                        ydl.download([video_url])
                    except yt_dlp.utils.DownloadError as e:
                        video_download_progress[video_title] = {"status": "error", "message": str(e)}

            threading.Thread(target=download).start()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Downloader</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .form { margin-bottom: 20px; }
            .progress { margin-top: 20px; }
            video { margin-top: 20px; width: 100%; max-width: 600px; }
        </style>
        <script>
            function fetchProgress() {
                fetch('/progress')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('status').innerText = 'Status: ' + data.status;
                        if (data.status === 'downloading') {
                            document.getElementById('downloaded_bytes').innerText = 'Downloaded Bytes: ' + data.downloaded_bytes;
                            document.getElementById('total_bytes').innerText = 'Total Bytes: ' + data.total_bytes;
                            document.getElementById('progress').innerText = 'Progress: ' + data.progress;
                            document.getElementById('speed').innerText = 'Speed: ' + data.speed;
                            document.getElementById('eta').innerText = 'ETA: ' + data.eta;
                        } else if (data.status === 'completed') {
                            window.location.href = "/play";
                        } else if (data.status === 'error') {
                            document.getElementById('status').innerText = 'Error: ' + data.message;
                        }
                    });
            }

            function startFetchingProgress() {
                setInterval(fetchProgress, 2000); // Fetch progress every 2 seconds
            }
        </script>
    </head>
    <body onload="startFetchingProgress()">
        <h1>Video Downloader</h1>
        <form method="POST">
            <label for="url">YouTube URL:</label>
            <input type="text" id="url" name="url" required />
            <button type="submit">Download</button>
        </form>
        <div class="progress">
            <h2>Download Progress</h2>
            <p id="status">Status: Not started</p>
            <p id="downloaded_bytes">Downloaded Bytes: N/A</p>
            <p id="total_bytes">Total Bytes: N/A</p>
            <p id="progress">Progress: N/A</p>
            <p id="speed">Speed: N/A</p>
            <p id="eta">ETA: N/A</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/progress', methods=['GET'])
def progress():
    global video_title
    progress_info = video_download_progress.get(video_title, {"status": "not_found"})
    return jsonify(progress_info)

@app.route('/play', methods=['GET'])
def play_video():
    global downloaded_video_path

    if os.path.exists(downloaded_video_path):
        # Render the video player
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Watch Video</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                video { width: 100%; max-width: 600px; }
            </style>
        </head>
        <body>
            <h1>Watch Video</h1>
            <video controls autoplay onended="deleteVideo()">
                <source src="{{ url_for('serve_video') }}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <script>
                function deleteVideo() {
                    fetch('/delete_video')
                        .then(response => {
                            if (response.ok) {
                                alert("Video file deleted successfully.");
                            } else {
                                alert("Failed to delete the video file.");
                            }
                        });
                }
            </script>
        </body>
        </html>
        ''')
    else:
        return "Video not found or already deleted.", 404

@app.route('/serve_video', methods=['GET'])
def serve_video():
    global downloaded_video_path

    if os.path.exists(downloaded_video_path):
        return send_file(downloaded_video_path)
    else:
        return "Video not found.", 404

@app.route('/delete_video', methods=['GET'])
def delete_video():
    global downloaded_video_path

    try:
        if os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
        return "Video deleted successfully.", 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
