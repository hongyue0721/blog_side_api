# blog_side_api（博客端可运行样板）

本目录提供一个可运行的博客端 API 样板，包含：
- 可执行服务（FastAPI，含管理前端）
- 清晰的中文注释配置文件
- 与 bot 端插件的 API 对接示例

## ✨ 功能说明
- `GET /` 或 `/admin`：管理前端（评论列表/回复查看）
- `GET /api/v1/comments/pending`：拉取待处理评论
- `GET /api/v1/comments/replies`：获取回复记录
- `POST /api/v1/comments`：提交机器人回复

## 📦 目录结构
```
blog_side_api/
├── app.py               # FastAPI 示例服务
├── config.toml          # 配置文件（中文注释）
├── requirements.txt     # 依赖
├── README.md            # 使用说明
├── STRUCTURE.md         # 结构说明
└── data/
    ├── pending.json     # 待处理评论数据（示例）
    └── replies.json     # 回复结果存储（示例）
```

## 🚀 快速启动
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动服务：
   ```bash
   python app.py
   ```
3. 默认监听：`http://127.0.0.1:8000`
4. 打开管理前端：`http://127.0.0.1:8000/admin`

## 🔧 配置说明
请编辑 `config.toml`，字段均带中文注释。关键字段：
- `server.host` / `server.port`
- `auth.api_key`（与 bot 端一致）
- `storage.storage_type`：`json` 或 `sqlite`
- `storage.sqlite_path`：SQLite 数据库文件路径（仅 sqlite 时生效）
- `data.pending_file` / `data.replies_file`（JSON 数据文件路径，仅 json 时使用）

### 服务器部署说明（含虚拟环境，新手可直接照做）
1. 上传 `blog_side_api/` 全目录到服务器（建议放在 `/opt/blog_side_api`）
2. 进入目录：
   ```bash
   cd /opt/blog_side_api
   ```
3. 创建虚拟环境（第一次执行）：
   ```bash
   python3 -m venv .venv
   ```
4. 激活虚拟环境：
   ```bash
   source .venv/bin/activate
   ```
   > 激活后命令行前缀会出现 `(venv)` 或 `(.venv)`，表示成功
5. 升级 pip（推荐）：
   ```bash
   python -m pip install --upgrade pip
   ```
6. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
7. 修改配置：
   - 编辑 [`blog_side_api/config.toml`](blog_side_api/config.toml:1)
   - 设置 `server.host`、`server.port`、`auth.api_key`
   - 选择存储方式：
     - JSON：`storage.storage_type = "json"`
     - SQLite：`storage.storage_type = "sqlite"` 且设置 `storage.sqlite_path`
8. 启动服务：
   ```bash
   python app.py
   ```
9. 打开管理前端：
   - 浏览器访问：`http://<服务器IP>:<端口>/admin`

> 停止服务：按 `Ctrl + C`。下次启动前记得再次执行 `source .venv/bin/activate`。

## 🧪 测试示例
### 获取待处理评论
```bash
curl "http://127.0.0.1:8000/api/v1/comments/pending?since=0" -H "X-API-KEY: your-key"
```

### 提交回复
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/comments" \
  -H "X-API-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d "{\"post_id\":5,\"parent_id\":123,\"author\":\"bot\",\"content\":\"谢谢你的评论！\"}"
```

### 查看回复记录
```bash
curl "http://127.0.0.1:8000/api/v1/comments/replies" -H "X-API-KEY: your-key"
```

## ⚠️ 注意
此样板为教学用途，数据以 JSON 文件模拟存储，实际部署请替换为数据库。
