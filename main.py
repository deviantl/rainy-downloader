import os
import uuid
import yt_dlp

from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

import asyncio

app = FastAPI()
download_lock = asyncio.Lock()
async def wait_for_download_slot():
    await download_lock.acquire()
def release_download_lock():
    if download_lock.locked():
        download_lock.release()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DOWNLOAD_DIR = "downloads"
YOUTUBE_PROXY = os.getenv("YOUTUBE_PROXY")
YOUTUBE_PROXY_BACKUP = os.getenv("YOUTUBE_PROXY_BACKUP")
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
    proxies = [YOUTUBE_PROXY, YOUTUBE_PROXY_BACKUP]

    for proxy in proxies:
        if not proxy:
            continue

        try:
            options = {
                "quiet": True,
                "skip_download": True,
                "noplaylist": True,
                "proxy": proxy,
                "remote_components": {"ejs:github"},
                "extractor_args": {
                    "youtube": {
                        "player_client": ["mweb"],
                    },
                    "youtubepot-bgutilhttp": {
                        "base_url": ["http://127.0.0.1:4416"],
                    },
                },
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)

            return {
                "title": info.get("title", "Unknown"),
                "thumbnail": info.get("thumbnail", "")
            }

        except Exception:
            continue

    return {
        "error": "Не удалось получить информацию о видео"
    }


@app.post("/download")
async def download(
    url: str = Form(...),
    format: str = Form(...)
):
    await wait_for_download_slot()
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
            "proxy": YOUTUBE_PROXY,
            "cookiefile": COOKIE_FILE,
            "remote_components": {"ejs:github": "github"},
        }

        proxies = [YOUTUBE_PROXY, YOUTUBE_PROXY_BACKUP]
        info = None
        filename = None

        for proxy in proxies:
            if not proxy:
                continue

            try:
                options["proxy"] = proxy

                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)

                break
            except Exception:
                continue

        if info is None or filename is None:
            raise Exception("All proxies failed")
        
        base = os.path.splitext(filename)[0]
        mp4_file = base + ".mp4"

        if os.path.exists(mp4_file):
            filename = mp4_file

        return FileResponse(
            filename,
            media_type="video/mp4",
            filename="video.mp4",
            background=BackgroundTask(os.remove, filename)
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
            "proxy": YOUTUBE_PROXY,
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

        proxies = [YOUTUBE_PROXY, YOUTUBE_PROXY_BACKUP]
        downloaded = False

        for proxy in proxies:
            if not proxy:
                continue

            try:
                options["proxy"] = proxy

                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.extract_info(url, download=True)

                downloaded = True
                break
            except Exception:
                continue

        if not downloaded:
            raise Exception("All proxies failed")
        filename = os.path.join(
            DOWNLOAD_DIR,
            file_id + ".mp3"
        )

        return FileResponse(
    filename,
    media_type="audio/mpeg",
    filename="audio.mp3",
    background=BackgroundTask(os.remove, filename)
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
            "proxy": YOUTUBE_PROXY,
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
            filename="audio.wav",
            background=BackgroundTask(os.remove, filename)
        )   