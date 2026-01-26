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
│   ├── index.html       # 管理前端单页（Tab 切换）
│   ├── public.html      # 公开博客单页（列表 + 详情 + 评论）
│   └── post.html        # 旧版详情页（当前未被路由使用，保留作参考）
└── data/
    ├── comments.json    # 评论数据（示例）
    ├── posts.json       # 公开博客示例数据（含图片字段）
    └── uploads/         # 管理端上传图片保存位置（可配置）
```

## 文件职责
- `app.py`：API 主入口，提供评论、公开列表与管理接口。
- `config.toml`：服务配置（带中文注释）。
- `requirements.txt`：依赖列表。
- `web/`：公开博客单页、评论入口与管理前端单页。
- `data/`：示例数据，模拟评论与公开文章与上传图片。

## 备注
- 该样板面向教学与对接验证，真实部署需替换为数据库与权限方案。
