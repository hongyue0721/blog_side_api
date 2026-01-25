# blog_side_api 结构说明

本文档用于说明博客端 API 样板结构与文件职责，便于发布到 GitHub。

## 目录结构
```
blog_side_api/
├── app.py               # FastAPI 示例服务
├── config.toml          # 配置文件（中文注释）
├── requirements.txt     # 依赖
├── README.md            # 使用说明
├── STRUCTURE.md         # 结构说明
├── web/
│   └── index.html       # 管理前端页面
└── data/
    ├── pending.json     # 待处理评论数据（示例）
    └── replies.json     # 回复结果存储（示例）
```

## 文件职责
- `app.py`：API 主入口，提供 pending 与 reply 接口。
- `config.toml`：服务配置（带中文注释）。
- `requirements.txt`：依赖列表。
- `data/`：示例数据，模拟评论队列与回复存储。

## 备注
- 该样板面向教学与对接验证，真实部署需替换为数据库与权限方案。
