# app.py
# This is the backend Python application using Flask and yt-dlp.

# First, you need to install the required libraries.
# Open your terminal or command prompt and run these commands:
# pip install Flask
# pip install yt-dlp
# pip install Flask-CORS

import os
import shutil
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import re

# Create a Flask web application instance
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

@app.route('/download', methods=['POST'])
def download_video():
    """
    Handles the video download request from the frontend.
    This function expects a JSON payload with 'url', 'format', and optionally 'quality'.
    """
    # Parse the JSON data from the request
    data = request.json
    video_url = data.get('url')
    file_format = data.get('format')
    quality = data.get('quality')

    # Basic input validation
    if not video_url or not file_format:
        return jsonify({"error": "URL and format are required."}), 400

    # Ensure the format is either 'mp4' or 'mp3'
    if file_format not in ['mp4', 'mp3']:
        return jsonify({"error": "Invalid format. Please choose 'mp4' or 'mp3'."}), 400

    # Use a temporary directory to store the downloaded file
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Define yt-dlp options based on the requested format and quality
        ydl_opts = {}
        
        # Determine the output filename and safe title
        info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
        safe_title = re.sub(r'[^\w\s-]', '', info.get('title', 'video'))
        output_template = os.path.join(temp_dir, f'{safe_title}.%(ext)s')

        if file_format == 'mp4':
            # Options for MP4 download
            format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if quality and quality != 'best':
                format_str = f'bestvideo[ext=mp4][height<={quality.replace("p", "")}]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': output_template,
                'merge_output_format': 'mp4',
            }
        elif file_format == 'mp3':
            # Options for MP3 download (audio only)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Find the downloaded file
        downloaded_file = None
        for filename in os.listdir(temp_dir):
            if filename.startswith(safe_title):
                downloaded_file = os.path.join(temp_dir, filename)
                break
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            return jsonify({"error": "Download failed. Check the URL."}), 500

        # Send the file to the user
        response = send_file(downloaded_file, as_attachment=True, download_name=os.path.basename(downloaded_file))

        return response

    except Exception as e:
        # Handle potential errors and return an appropriate response
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        # Clean up the temporary directory after the file has been sent
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # Run the Flask app
    # For production, use a more robust server like Gunicorn or uWSGI
    app.run(debug=True, port=5000)
