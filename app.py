from flask import Flask, request, jsonify
import yt_dlp
import threading

app = Flask(__name__)
download_progress = {}

def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'cookies': 'cookies.txt'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Download error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def progress_hook(d):
    if d['status'] == 'downloading':
        download_progress['progress'] = d['_percent_str']
    elif d['status'] == 'finished':
        download_progress['progress'] = '100%'

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if url:
        download_thread = threading.Thread(target=download_video, args=(url,))
        download_thread.start()
        return jsonify({'message': 'Download started.'}), 200
    else:
        return jsonify({'error': 'URL parameter is required.'}), 400

@app.route('/progress', methods=['GET'])
def progress():
    return jsonify({'progress': download_progress.get('progress', '0%')}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
