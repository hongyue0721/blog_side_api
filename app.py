from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml
from fastapi import FastAPI, File, Header, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class PublicCommentPayload(BaseModel):
    post_id: int
    content: str


class CreatePostPayload(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    images: Optional[List[str]] = None


class UpdatePostPayload(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None


class UpdateCommentPayload(BaseModel):
    content: Optional[str] = None


class SettingsPayload(BaseModel):
    avatar: Optional[str] = None
    name: Optional[str] = None
    intro: Optional[str] = None
    background_image: Optional[str] = None
    theme_color: Optional[str] = None
    enable_snow: Optional[bool] = None
    music_url: Optional[str] = None


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
    created_at = _now_local_iso()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO public_comments (post_id, post_title, post_summary, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.post_id, post_title, post_summary, payload.content, created_at),
        )
        conn.commit()
        comment_id = cursor.lastrowid
    return {"id": comment_id, "created_at": created_at}


def update_comment_in_sqlite(db_path: Path, comment_id: int, payload: UpdateCommentPayload) -> Optional[Dict[str, Any]]:
    fields = []
    values: List[Any] = []
    if payload.content is not None:
        fields.append("content = ?")
        values.append(payload.content)
    if not fields:
        return None

    values.append(comment_id)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(f"UPDATE public_comments SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        if cursor.rowcount == 0:
            return None
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM public_comments WHERE id = ?", (comment_id,)).fetchone()
        return dict(row) if row else None


def delete_comment_in_sqlite(db_path: Path, comment_id: int) -> bool:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("DELETE FROM public_comments WHERE id = ?", (comment_id,))
        conn.commit()
        return cursor.rowcount > 0


config = load_config()

server_host = config.get("server", {}).get("host", "127.0.0.1")
server_port = int(config.get("server", {}).get("port", 8000))
admin_password = str(config.get("admin", {}).get("password", ""))

storage_type = str(config.get("storage", {}).get("storage_type", "json")).lower()
sqlite_path = Path(config.get("storage", {}).get("sqlite_path", "data/blog_api.db"))

data_config = config.get("data", {})
comments_file = Path(data_config.get("comments_file") or data_config.get("pending_file", "data/comments.json"))
posts_file = Path(data_config.get("posts_file", "data/posts.json"))
settings_file = Path(data_config.get("settings_file", "data/settings.json"))
images_dir = Path(data_config.get("images_dir", "data/uploads"))
music_dir = Path(data_config.get("music_dir", "data/uploads/music"))

web_root = Path(__file__).parent / "web"
uploads_images_dir = images_dir
uploads_music_dir = music_dir

if storage_type == "sqlite":
    init_sqlite(sqlite_path)
else:
    ensure_data_file(comments_file, [])
    ensure_data_file(posts_file, [])
    ensure_data_file(settings_file, {})

images_dir.mkdir(parents=True, exist_ok=True)
uploads_images_dir.mkdir(parents=True, exist_ok=True)
uploads_music_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Blog Comment API Sample", version="0.2.0")

app.mount("/web", StaticFiles(directory=web_root), name="web")


def require_admin_password(x_admin_password: str | None) -> None:
    if not admin_password:
        return
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")


def _now_local_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


@app.get("/")
def serve_public_list():
    return FileResponse(web_root / "public.html")


@app.get("/post/{post_id}")
def serve_public_detail(post_id: int):
    return FileResponse(web_root / "public.html")


@app.get("/admin")
def serve_admin_page():
    return FileResponse(web_root / "index.html")


@app.get("/uploads/images/{image_name}")
def serve_upload_image(image_name: str):
    image_path = uploads_images_dir / image_name
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(image_path)


@app.get("/uploads/music/{music_name}")
def serve_upload_music(music_name: str):
    music_path = uploads_music_dir / music_name
    if not music_path.exists():
        raise HTTPException(status_code=404, detail="music not found")
    return FileResponse(music_path)


@app.post("/api/v1/uploads/image")
def upload_image(file: UploadFile = File(...), x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")

    suffix = Path(file.filename).suffix
    safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{suffix}"
    target_path = uploads_images_dir / safe_name
    with target_path.open("wb") as target:
        target.write(file.file.read())

    return {
        "code": 0,
        "message": "success",
        "data": {
            "filename": safe_name,
            "url": f"/uploads/images/{safe_name}",
        },
    }


@app.delete("/api/v1/uploads/images/{image_name}")
def delete_image(image_name: str, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    # Security check: prevent directory traversal
    if ".." in image_name or "/" in image_name or "\\" in image_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    target_path = uploads_images_dir / image_name
    if not target_path.exists():
        return {"code": 404, "message": "not found", "data": None}
    
    try:
        target_path.unlink()
        return {"code": 0, "message": "success", "data": {"filename": image_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/uploads/music")
def upload_music(file: UploadFile = File(...), x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".mp3", ".wav", ".ogg", ".m4a", ".flac"]:
         raise HTTPException(status_code=400, detail="Only audio files allowed (mp3, wav, ogg, m4a, flac)")

    safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{suffix}"
    target_path = uploads_music_dir / safe_name
    with target_path.open("wb") as target:
        target.write(file.file.read())

    return {
        "code": 0,
        "message": "success",
        "data": {
            "filename": safe_name,
            "url": f"/uploads/music/{safe_name}",
        },
    }


@app.delete("/api/v1/uploads/music/{music_name}")
def delete_music(music_name: str, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if ".." in music_name or "/" in music_name or "\\" in music_name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    target_path = uploads_music_dir / music_name
    if not target_path.exists():
        return {"code": 404, "message": "not found", "data": None}
    
    try:
        target_path.unlink()
        return {"code": 0, "message": "success", "data": {"filename": music_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/settings")
def get_settings():
    return {"code": 0, "message": "success", "data": read_json(settings_file)}


@app.post("/api/v1/settings")
def update_settings(payload: SettingsPayload, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    current = read_json(settings_file)
    if payload.avatar is not None:
        current["avatar"] = payload.avatar
    if payload.name is not None:
        current["name"] = payload.name
    if payload.intro is not None:
        current["intro"] = payload.intro
    if payload.background_image is not None:
        current["background_image"] = payload.background_image
    if payload.theme_color is not None:
        current["theme_color"] = payload.theme_color
    if payload.enable_snow is not None:
        current["enable_snow"] = payload.enable_snow
    if payload.music_url is not None:
        current["music_url"] = payload.music_url
    write_json(settings_file, current)
    return {"code": 0, "message": "success", "data": current}


@app.get("/api/v1/posts")
def list_posts(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
    if storage_type == "sqlite":
        return {"code": 0, "message": "success", "data": [], "total": 0}
    posts = read_json(posts_file)
    # Sort by id desc (newest first)
    posts.sort(key=lambda x: int(x.get("id", 0)), reverse=True)

    total = len(posts)
    start = (page - 1) * size
    end = start + size
    paginated_posts = posts[start:end]

    for item in paginated_posts:
        item.pop("author", None)
    return {"code": 0, "message": "success", "data": paginated_posts, "total": total}


@app.post("/api/v1/posts")
def create_post(payload: CreatePostPayload, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        raise HTTPException(status_code=501, detail="sqlite not implemented")

    posts = read_json(posts_file)
    next_id = (max([int(item.get("id", 0)) for item in posts]) + 1) if posts else 1
    record = {
        "id": next_id,
        "title": payload.title,
        "summary": payload.summary or payload.content[:120] + ("..." if len(payload.content) > 120 else ""),
        "content": payload.content,
        "images": payload.images or [],
        "created_at": _now_local_iso(),
    }
    posts.append(record)
    write_json(posts_file, posts)
    return {"code": 0, "message": "success", "data": record}


@app.get("/api/v1/posts/{post_id}")
def get_post(post_id: int):
    if storage_type == "sqlite":
        return {"code": 0, "message": "success", "data": None}
    posts = read_json(posts_file)
    for item in posts:
        if int(item.get("id", 0)) == post_id:
            item.pop("author", None)
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
            if payload.images is not None:
                item["images"] = payload.images
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
        for item in data:
            item.pop("visitor_name", None)
        return {"code": 0, "message": "success", "data": data}

    comments = read_json(comments_file)
    data = [item for item in comments if int(item.get("post_id", 0)) == post_id]
    for item in data:
        item.pop("visitor_name", None)
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
        "content": payload.content,
        "created_at": _now_local_iso(),
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
    for item in data:
        item.pop("visitor_name", None)
    return {"code": 0, "message": "success", "data": data}


@app.put("/api/v1/comments/{comment_id}")
def update_comment(
    comment_id: int, payload: UpdateCommentPayload, x_admin_password: str | None = Header(default=None)
):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        updated = update_comment_in_sqlite(sqlite_path, comment_id, payload)
        if not updated:
            return {"code": 404, "message": "not found", "data": None}
        updated.pop("visitor_name", None)
        return {"code": 0, "message": "success", "data": updated}

    comments = read_json(comments_file)
    for item in comments:
        if int(item.get("id", 0)) == comment_id:
            if payload.content is not None:
                item["content"] = payload.content
            item["updated_at"] = _now_local_iso()
            item.pop("visitor_name", None)
            write_json(comments_file, comments)
            return {"code": 0, "message": "success", "data": item}
    return {"code": 404, "message": "not found", "data": None}


@app.delete("/api/v1/comments/{comment_id}")
def delete_comment(comment_id: int, x_admin_password: str | None = Header(default=None)):
    require_admin_password(x_admin_password)
    if storage_type == "sqlite":
        ok = delete_comment_in_sqlite(sqlite_path, comment_id)
        if not ok:
            return {"code": 404, "message": "not found", "data": None}
        return {"code": 0, "message": "success", "data": {"id": comment_id}}

    comments = read_json(comments_file)
    remaining = [item for item in comments if int(item.get("id", 0)) != comment_id]
    if len(remaining) == len(comments):
        return {"code": 404, "message": "not found", "data": None}
    write_json(comments_file, remaining)
    return {"code": 0, "message": "success", "data": {"id": comment_id}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=server_host, port=server_port)
