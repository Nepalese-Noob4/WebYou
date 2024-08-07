from flask import Flask, request, jsonify, send_file
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = 'downloads'

@app.route('/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    # Create download directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    # Define the output file path
    output_path = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')

    # Download the video
    try:
        ydl_opts = {
            'outtmpl': output_path,
            'progress_hooks': [download_progress_hook],
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return jsonify({"message": "Download completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/progress', methods=['GET'])
def progress():
    # Return the current download progress (implement this based on your progress tracking)
    return jsonify({"progress": "0%"}), 200

def download_progress_hook(d):
    if d['status'] == 'finished':
        print(f"\nDone downloading video: {d['filename']}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
