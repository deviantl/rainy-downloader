deno run --allow-net --allow-read --allow-env bgutil-yt-dlp-pot-provider/server/src/main.ts &
uvicorn main:app --host 0.0.0.0 --port $PORT