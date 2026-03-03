from flask import Flask, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download_video():
    url = request.args.get("url")
    filename = f"{uuid.uuid4()}.mp4"

    ydl_opts = {
        'format': 'mp4',
        'outtmpl': filename,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    response = send_file(filename, as_attachment=True)

    os.remove(filename)

    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
