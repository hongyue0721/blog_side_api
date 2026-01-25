from __future__ import annotations

import json
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


config = load_config()

server_host = config.get("server", {}).get("host", "127.0.0.1")
server_port = int(config.get("server", {}).get("port", 8000))
api_key = str(config.get("auth", {}).get("api_key", ""))

pending_file = Path(config.get("data", {}).get("pending_file", "data/pending.json"))
replies_file = Path(config.get("data", {}).get("replies_file", "data/replies.json"))

ensure_data_file(pending_file, [])
ensure_data_file(replies_file, [])

app = FastAPI(title="Blog Comment API Sample", version="0.1.0")
web_root = Path(__file__).parent / "web"


def require_api_key(x_api_key: str | None) -> None:
    if not api_key:
        return
    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/")
@app.get("/admin")
def serve_admin_page():
    return FileResponse(web_root / "index.html")


@app.get("/api/v1/comments/pending")
def get_pending_comments(since: int = 0, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    pending = read_json(pending_file)
    result: List[Dict[str, Any]] = []
    for item in pending:
        created_at = item.get("created_at")
        created_ts = 0
        if isinstance(created_at, (int, float)):
            created_ts = int(created_at)
        elif isinstance(created_at, str) and created_at:
            try:
                from datetime import datetime

                created_ts = int(datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp())
            except Exception:
                created_ts = 0
        if created_ts >= since:
            result.append(item)

    return {"code": 0, "message": "success", "data": result}


@app.get("/api/v1/comments/replies")
def get_replies(x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
    replies = read_json(replies_file)
    return {"code": 0, "message": "success", "data": replies}


@app.post("/api/v1/comments")
def submit_reply(payload: ReplyPayload, x_api_key: str | None = Header(default=None)):
    require_api_key(x_api_key)
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

    return {"code": 0, "message": "success", "data": {"id": next_id, "created_at": reply_record["created_at"]}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=server_host, port=server_port)
