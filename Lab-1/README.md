# URL Shortener

A fast and simple URL shortener built with FastAPI, SQLite, and a modern frontend.

## Features

- Fast API endpoint for shortening URLs
- Web UI for creating and copying short links
- SQLite persistence with duplicate URL detection
- Automatic short-code generation
- Redirect endpoint for short URLs

## Run Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. Open [http://localhost:8000](http://localhost:8000)

## Deploy (Render)

This project is ready for Render web service deployment.

1. Push your project to GitHub.
2. In Render, create a **New Web Service** from your repo.
3. Configure:
   - **Root Directory**: `Lab-1`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy.

After deploy, generated short URLs will use your deployed domain automatically.

## Deploy (Railway)

1. Create a new Railway project from your GitHub repo.
2. Set service root directory to `Lab-1`.
3. Railway usually auto-detects Python; if needed use:
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy.

## Deploy (Vercel)

This app can run on Vercel as a Python serverless function.

1. Keep these files in `Lab-1`:
   - `vercel.json`
   - `api/index.py`
2. From the `Lab-1` directory run:

```bash
vercel
```

3. For production deploy:

```bash
vercel --prod
```

### Important Vercel note

SQLite on Vercel is ephemeral in serverless runtime (`/tmp`).  
That means saved short URLs are not durable across cold starts/redeploys.  
For persistent production data, use a hosted database (for example PostgreSQL).
