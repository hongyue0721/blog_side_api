from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


class PublicCommentPayload(BaseModel):
    post_id: int
    visitor_name: str
    content: str


class UpdatePostPayload(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None


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
            CREATE TABLE IF NOT EXISTS public_comments (
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
        conn.commit()


def list_public_comments_from_sqlite(db_path: Path, post_id: int) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM public_comments WHERE post_id = ? ORDER BY id DESC",
            (post_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def list_all_comments_from_sqlite(db_path: Path) -> List[Dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM public_comments ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


def insert_public_comment_to_sqlite(
    db_path: Path, payload: PublicCommentPayload, post_title: str, post_summary: str
) -> Dict[str, Any]:
    created_at = "2025-12-22T10:05:00Z"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO public_comments (post_id, post_title, post_summary, visitor_name, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.post_id, post_title, post_summary, payload.visitor_name, payload.content, created_at),
        )
        conn.commit()
        comment_id = cursor.lastrowid
    return {"id": comment_id, "created_at": created_at}


config = load_config()

server_host = config.get("server", {}).get("host", "127.0.0.1")
server_port = int(config.get("server", {}).get("port", 8000))
admin_password = str(config.get("admin", {}).get("password", ""))

storage_type = str(config.get("storage", {}).get("storage_type", "json")).lower()
sqlite_path = Path(config.get("storage", {}).get("sqlite_path", "data/blog_api.db"))

data_config = config.get("data", {})
comments_file = Path(data_config.get("comments_file") or data_config.get("pending_file", "data/comments.json"))
posts_file = Path(data_config.get("posts_file", "data/posts.json"))

web_root = Path(__file__).parent / "web"

if storage_type == "sqlite":
    init_sqlite(sqlite_path)
else:
    ensure_data_file(comments_file, [])
    ensure_data_file(posts_file, [])

app = FastAPI(title="Blog Comment API Sample", version="0.2.0")


def require_admin_password(x_admin_password: str | None) -> None:
    if not admin_password:
        return
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")


@app.get("/")
def serve_public_list():
    return FileResponse(web_root / "public.html")


@app.get("/post/{post_id}")
def serve_public_detail(post_id: int):
    return FileResponse(web_root / "public.html")


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


@app.put("/api/v1/posts/{post_id}")
def update_post(post_id: int, payload: UpdatePostPayload, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        raise HTTPException(status_code=501, detail="sqlite not implemented")

    posts = read_json(posts_file)
    for item in posts:
        if int(item.get("id", 0)) == post_id:
            if payload.title is not None:
                item["title"] = payload.title
            if payload.summary is not None:
                item["summary"] = payload.summary
            if payload.content is not None:
                item["content"] = payload.content
            if payload.author is not None:
                item["author"] = payload.author
            write_json(posts_file, posts)
            return {"code": 0, "message": "success", "data": item}
    return {"code": 404, "message": "not found", "data": None}


@app.delete("/api/v1/posts/{post_id}")
def delete_post(post_id: int, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        raise HTTPException(status_code=501, detail="sqlite not implemented")

    posts = read_json(posts_file)
    remaining = [item for item in posts if int(item.get("id", 0)) != post_id]
    if len(remaining) == len(posts):
        return {"code": 404, "message": "not found", "data": None}
    write_json(posts_file, remaining)
    return {"code": 0, "message": "success", "data": {"id": post_id}}


@app.get("/api/v1/comments/public")
def list_public_comments(post_id: int):
    if storage_type == "sqlite":
        data = list_public_comments_from_sqlite(sqlite_path, post_id)
        return {"code": 0, "message": "success", "data": data}

    comments = read_json(comments_file)
    data = [item for item in comments if int(item.get("post_id", 0)) == post_id]
    return {"code": 0, "message": "success", "data": data}


@app.post("/api/v1/comments/public")
def submit_public_comment(payload: PublicCommentPayload):
    if storage_type == "sqlite":
        return {"code": 0, "message": "success", "data": insert_public_comment_to_sqlite(sqlite_path, payload, "", "")}

    posts = read_json(posts_file)
    post_title = ""
    post_summary = ""
    for item in posts:
        if int(item.get("id", 0)) == payload.post_id:
            post_title = str(item.get("title", ""))
            post_summary = str(item.get("summary", ""))
            break

    comments = read_json(comments_file)
    next_id = (max([c.get("id", 0) for c in comments]) + 1) if comments else 1
    comment_record = {
        "id": next_id,
        "post_id": payload.post_id,
        "post_title": post_title,
        "post_summary": post_summary,
        "visitor_name": payload.visitor_name,
        "content": payload.content,
        "created_at": "2025-12-22T10:05:00Z",
    }
    comments.append(comment_record)
    write_json(comments_file, comments)
    return {"code": 0, "message": "success", "data": {"id": next_id, "created_at": comment_record["created_at"]}}


@app.get("/api/v1/comments")
def list_all_comments(x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        data = list_all_comments_from_sqlite(sqlite_path)
    else:
        data = read_json(comments_file)
    return {"code": 0, "message": "success", "data": data}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=server_host, port=server_port)
