cd bgutil-ytdlp-pot-provider/server && npm ci --omit=dev && cd ../..
deno run --allow-net --allow-read --allow-env --allow-ffi bgutil-ytdlp-pot-provider/server/src/main.ts &
uvicorn main:app --host 0.0.0.0 --port $PORT