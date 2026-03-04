from flask import Flask, request, jsonify
import os
import json
import threading
import uuid
import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

app = Flask(__name__)

# ================= Google Drive Setup =================
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '1HAZnoVWlM6tBGYnvHVmdCcQNaZgBdXGH'  # ← Replace this

# Read Service Account from Render Environment Variable
service_account_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT'])
creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES
)

# ================= Job Tracking =================
jobs = {}
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def upload_to_drive(file_path, filename):
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': filename, 'parents':[FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def download_video(job_id, url):
    try:
        output_path = os.path.join(DOWNLOAD_FOLDER, f"{job_id}.mp4")
        ydl_opts = {'format':'best[height<=720]', 'outtmpl': output_path}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        upload_to_drive(output_path, f"{job_id}.mp4")
        jobs[job_id] = "completed"
    except:
        jobs[job_id] = "error"

# ================= Flask Routes =================
@app.route("/start", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url")
    job_id = str(uuid.uuid4())
    jobs[job_id] = "processing"
    thread = threading.Thread(target=download_video, args=(job_id,url))
    thread.start()
    return jsonify({"job_id":job_id,"status":"processing"})

@app.route("/status/<job_id>", methods=["GET"])
def check_status(job_id):
    status = jobs.get(job_id,"not_found")
    return jsonify({"status":status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
