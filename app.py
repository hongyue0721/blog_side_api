from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import toml
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


class ReplyPayload(BaseModel):
    post_id: int
    parent_id: int
    author: str
    content: str


def load_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent / "config.toml"
    return toml.load(config_path)


def ensure_data_file(path: Path, default: Any) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    ensure_data_file(path, [])
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def init_sqlite(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_comments (
                id INTEGER PRIMARY KEY,
                post_id INTEGER NOT NULL,
                post_title TEXT,
                post_summary TEXT,
                visitor_name TEXT,
                content TEXT,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                parent_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def fetch_pending_from_sqlite(db_path: Path, since: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM pending_comments")
        for row in cursor.fetchall():
            created_at = row["created_at"] or ""
            created_ts = _to_timestamp(created_at)
            if created_ts >= since:
                rows.append(dict(row))
    return rows


def list_replies_from_sqlite(db_path: Path) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM replies ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


def insert_reply_to_sqlite(db_path: Path, payload: ReplyPayload) -> Dict[str, Any]:
    created_at = "2025-12-22T10:05:00Z"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO replies (post_id, parent_id, author, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.post_id, payload.parent_id, payload.author, payload.content, created_at),
        )
        conn.commit()
        reply_id = cursor.lastrowid
    return {"id": reply_id, "created_at": created_at}


def _to_timestamp(created_at: Any) -> int:
    if isinstance(created_at, (int, float)):
        return int(created_at)
    if isinstance(created_at, str) and created_at:
        try:
            from datetime import datetime

            return int(datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp())
        except Exception:
            return 0
    return 0


config = load_config()

server_host = config.get("server", {}).get("host", "127.0.0.1")
server_port = int(config.get("server", {}).get("port", 8000))
api_key = str(config.get("auth", {}).get("api_key", ""))

storage_type = str(config.get("storage", {}).get("storage_type", "json")).lower()
sqlite_path = Path(config.get("storage", {}).get("sqlite_path", "data/blog_api.db"))

pending_file = Path(config.get("data", {}).get("pending_file", "data/pending.json"))
replies_file = Path(config.get("data", {}).get("replies_file", "data/replies.json"))
posts_file = Path(config.get("data", {}).get("posts_file", "data/posts.json"))

web_root = Path(__file__).parent / "web"

if storage_type == "sqlite":
    init_sqlite(sqlite_path)
else:
    ensure_data_file(pending_file, [])
    ensure_data_file(replies_file, [])
    ensure_data_file(posts_file, [])

app = FastAPI(title="Blog Comment API Sample", version="0.1.0")


def require_api_key(x_api_key: str | None) -> None:
    if not api_key:
        return
    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/")
def serve_public_list():
    return FileResponse(web_root / "public.html")


@app.get("/post/{post_id}")
def serve_public_detail(post_id: int):
    return FileResponse(web_root / "post.html")


@app.get("/admin")
def serve_admin_page():
    return FileResponse(web_root / "index.html")


@app.get("/api/v1/posts")
def list_posts():
    if storage_type == "sqlite":
        return {"code": 0, "message": "success", "data": []}
    posts = read_json(posts_file)
    return {"code": 0, "message": "success", "data": posts}


@app.get("/api/v1/posts/{post_id}")
def get_post(post_id: int):
    if storage_type == "sqlite":
        return {"code": 0, "message": "success", "data": None}
    posts = read_json(posts_file)
    for item in posts:
        if int(item.get("id", 0)) == post_id:
            return {"code": 0, "message": "success", "data": item}
    return {"code": 404, "message": "not found", "data": None}


@app.get("/api/v1/comments/pending")
def get_pending_comments(since: int = 0, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)

    if storage_type == "sqlite":
        data = fetch_pending_from_sqlite(sqlite_path, since)
    else:
        pending = read_json(pending_file)
        data = []
        for item in pending:
            created_ts = _to_timestamp(item.get("created_at"))
            if created_ts >= since:
                data.append(item)

    return {"code": 0, "message": "success", "data": data}


@app.get("/api/v1/comments/replies")
def get_replies(x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    if storage_type == "sqlite":
        replies = list_replies_from_sqlite(sqlite_path)
    else:
        replies = read_json(replies_file)
    return {"code": 0, "message": "success", "data": replies}


@app.post("/api/v1/comments")
def submit_reply(payload: ReplyPayload, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)

    if storage_type == "sqlite":
        result = insert_reply_to_sqlite(sqlite_path, payload)
    else:
        replies = read_json(replies_file)
        next_id = (max([r.get("id", 0) for r in replies]) + 1) if replies else 1
        reply_record = {
            "id": next_id,
            "post_id": payload.post_id,
            "parent_id": payload.parent_id,
            "author": payload.author,
            "content": payload.content,
            "created_at": "2025-12-22T10:05:00Z",
        }
        replies.append(reply_record)
        write_json(replies_file, replies)
        result = {"id": next_id, "created_at": reply_record["created_at"]}

    return {"code": 0, "message": "success", "data": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=server_host, port=server_port)
