import os
import uuid
import yt_dlp

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SECRET_COOKIE_FILE = "/etc/secrets/youtube_cookies.txt"
COOKIE_FILE = "/tmp/youtube_cookies.txt" if os.name != "nt" else os.path.join(os.path.dirname(__file__), "youtube_cookies.txt")

import shutil

if os.path.exists(SECRET_COOKIE_FILE):
    shutil.copyfile(SECRET_COOKIE_FILE, COOKIE_FILE)



@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )
@app.get("/privacy")
def privacy(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="privacy.html"
    )
@app.get("/terms")
def terms(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="terms.html"
    )


@app.post("/preview")
def preview(url: str = Form(...)):
    try:
        options = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "remote_components": {"ejs:github"},
            "extractor_args": {"youtube": {"player_client": ["android_vr"]}},
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title", "Unknown"),
            "thumbnail": info.get("thumbnail", "")
        }

    except Exception:
        return {
            "error": "Не удалось получить информацию о видео"
        }


@app.post("/download")
def download(
    url: str = Form(...),
    format: str = Form(...)
):
    file_id = str(uuid.uuid4())

    # MP4
    if format == "mp4":
        output = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".%(ext)s"
        )

        options = {
            "format": (
                "bestvideo[height<=1080][vcodec^=avc1]"
                "+bestaudio[acodec^=mp4a]/"
                "best[height<=1080][vcodec^=avc1]/"
                "best[height<=1080]"
            ),
            "merge_output_format": "mp4",
            "outtmpl": output,
            "noplaylist": True,
            "cookiefile": COOKIE_FILE,
            "remote_components": {"ejs:github": "github"},
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        base = os.path.splitext(filename)[0]
        mp4_file = base + ".mp4"

        if os.path.exists(mp4_file):
            filename = mp4_file

        return FileResponse(
            filename,
            media_type="video/mp4",
            filename="video.mp4"
        )

    # MP3
    elif format == "mp3":
        output = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".%(ext)s"
        )

        options = {
            "format": "bestaudio/best",
            "outtmpl": output,
            "noplaylist": True,
            "cookiefile": COOKIE_FILE,
            "remote_components": {"ejs:github"},
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=True)

        filename = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".mp3"
        )

        return FileResponse(
            filename,
            media_type="audio/mpeg",
            filename="audio.mp3"
        )

    # WAV
    elif format == "wav":
        output = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".%(ext)s"
        )

        options = {
            "format": "bestaudio/best",
            "outtmpl": output,
            "noplaylist": True,
            "cookiefile": COOKIE_FILE,
            "remote_components": {"ejs:github"},
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }
            ],
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(url, download=True)

        filename = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".wav"
        )

        return FileResponse(
            filename,
            media_type="audio/wav",
            filename="audio.wav"
        )