# Deployment Guide - Render

## Prerequisites

- Render account (free tier works)
- GitHub repository connected to Render
- FFmpeg requirement (see below)

## Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

### 2. Create New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`

### 3. Configure Environment Variables (Optional)

In Render dashboard, add these if needed:
- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: `*`)

### 4. Deploy

Render will automatically:
- Run `build.sh` (install dependencies)
- Start app with `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check on `/health` endpoint

## ⚠️ Important: FFmpeg Requirement

**Render Free Plan does NOT include FFmpeg by default.**

### Option 1: Use Native Audio Format (Recommended for Free Plan)
- Set audio format to `m4a` or `best` (no conversion needed)
- This bypasses FFmpeg requirement

### Option 2: Use Docker with FFmpeg
Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then in Render:
- Choose "Docker" as environment
- Set `PORT` environment variable to `8000`

### Option 3: Upgrade to Paid Plan
Render paid plans allow custom native dependencies via `render-build.sh`:

```bash
#!/usr/bin/env bash
apt-get update
apt-get install -y ffmpeg
pip install -r requirements.txt
```

## Health Check

Your app exposes `/health` endpoint that returns:
```json
{
  "status": "ok",
  "ffmpeg_available": true/false,
  "queue_active": false
}
```

Check `ffmpeg_available` after deployment to confirm audio conversion will work.

## CORS Configuration

Default: `allow_origins=["*"]` (allows all origins)

For production security, update `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Or use environment variable:
```python
import os
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
```

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Verify Python version (3.9+ required)
- Ensure all dependencies in `requirements.txt`

### App Crashes
- Check app logs in Render dashboard
- Verify health check returns 200 OK
- Check FFmpeg availability via `/health` endpoint

### Download Fails
- If FFmpeg not available, use `m4a` or `best` format (no conversion)
- Check yt-dlp can access YouTube (some regions may block)
- Verify temp directory permissions

### 503 Queue Busy
- This is expected behavior when download is in progress
- Only one download at a time to avoid resource exhaustion
- User should wait and retry

## Monitoring

Render free tier includes:
- Automatic health checks
- Basic metrics (CPU, memory)
- App logs (last 7 days)

Monitor your app at: `https://your-app-name.onrender.com`

## Cost Considerations

**Free Tier Limitations:**
- Spins down after 15 minutes of inactivity
- Cold start takes 30-60 seconds
- 750 hours/month free compute

**Paid Tier ($7/month):**
- Always-on instances
- Custom domains
- Native dependency support (FFmpeg)
- Better performance

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Render web service
3. ✅ Wait for build to complete
4. ✅ Test `/health` endpoint
5. ✅ Test download with `m4a` format first
6. ⚠️ If MP3 needed, implement Docker or upgrade plan
