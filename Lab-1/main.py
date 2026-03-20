from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, validator
import sqlite3
import string
import random
from contextlib import contextmanager
import os

# Initialize FastAPI app
app = FastAPI(title="URL Shortener", version="1.0.0")

# Templates
templates = Jinja2Templates(directory="templates")

# Database setup
DATABASE = os.getenv("DATABASE_PATH")
if not DATABASE:
    # On Vercel filesystem is read-only except /tmp.
    DATABASE = "/tmp/urls.db" if os.getenv("VERCEL") else "urls.db"

def init_db():
    """Initialize SQLite database with urls table"""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)")
        conn.commit()

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def validate_url(url: str) -> str:
    """Validate and normalize URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def get_or_create_short_code(original_url: str) -> str:
    """Return existing short code for URL or create a new one."""
    with get_db() as conn:
        existing = conn.execute(
            "SELECT short_code FROM urls WHERE original_url = ?",
            (original_url,)
        ).fetchone()

        if existing:
            return existing['short_code']

        while True:
            short_code = generate_short_code()
            exists = conn.execute(
                "SELECT 1 FROM urls WHERE short_code = ?",
                (short_code,)
            ).fetchone()

            if not exists:
                break

        conn.execute(
            "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
            (original_url, short_code)
        )
        conn.commit()
        return short_code

# Pydantic models
class URLRequest(BaseModel):
    url: str
    
    @validator('url')
    def url_must_be_valid(cls, v):
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        # Basic URL validation
        if len(v) < 10 or '.' not in v:
            raise ValueError('Invalid URL format')
        return v

class URLResponse(BaseModel):
    short_code: str
    short_url: str

# API Endpoints
@app.post("/shorten", response_model=URLResponse)
async def shorten_url(payload: URLRequest, request: Request):
    """Shorten a URL and return the short code"""
    original_url = payload.url
    short_code = get_or_create_short_code(original_url)
    short_url = str(request.url_for("redirect_url", short_code=short_code))

    return URLResponse(short_code=short_code, short_url=short_url)

@app.get("/{short_code}")
async def redirect_url(short_code: str):
    """Redirect to the original URL"""
    with get_db() as conn:
        result = conn.execute(
            "SELECT original_url FROM urls WHERE short_code = ?",
            (short_code,)
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Short URL not found")
        
        return RedirectResponse(url=result['original_url'])

# Web interface
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/shorten-form")
async def shorten_form(request: Request, url: str = Form(...)):
    """Handle form submission"""
    try:
        payload = URLRequest(url=url)
        short_code = get_or_create_short_code(payload.url)
        short_url = str(request.url_for("redirect_url", short_code=short_code))
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>URL Shortened</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .result {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .short-url {{ font-size: 18px; color: #0066cc; font-weight: bold; }}
                a {{ color: #0066cc; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                button {{ background: #0066cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <h1>URL Shortened Successfully!</h1>
            <div class="result">
                <p><strong>Original URL:</strong> {url}</p>
                <p><strong>Short URL:</strong> <span class="short-url">{short_url}</span></p>
                <p><strong>Short Code:</strong> {short_code}</p>
            </div>
            <button onclick="window.location.href='/'">Shorten Another</button>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .error {{ background: #ffe6e6; padding: 20px; border-radius: 8px; color: #cc0000; }}
                button {{ background: #cc0000; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }}
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <div class="error">
                <p>{str(e)}</p>
            </div>
            <button onclick="window.history.back()">Go Back</button>
        </body>
        </html>
        """)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
